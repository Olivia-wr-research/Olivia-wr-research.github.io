#!/usr/bin/env python3
"""Persist review reports separately from the opportunity site.

The report branch is a durable authority for human rejections. A successful
source artifact can be older than a subsequent human review, so source-state
restoration must reconcile this journal before building another daily batch.
This script never changes main or publishes opportunities.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import urllib.error
import urllib.request

import terrafar_quality_gate as quality
import terrafar_state_archive as state_archive

BRANCH = "terrafar-review"
ROOT = "quality"
JOURNAL = f"{ROOT}/quality_journal.json"
MANIFEST = f"{ROOT}/store-manifest.json"
REVIEW_FILES = {"review.json", "review.md"}
PRIVATE_ARCHIVE = f"{ROOT}/private-review.cms"
STORE_FORMAT = "terrafar-review-store-v2-encrypted"
CHUNKED_STORE_FORMAT = "terrafar-review-store-v3-encrypted-parts"
PRIVATE_PARTS = f"{ROOT}/private-review.parts"
PART_BYTES = 24 * 1024
MAX_PARTS = 4096
RECIPIENT_CERTIFICATE = Path(__file__).resolve().parents[1] / "maintenance/terrafar-source-audit/state_archive_recipient.pem"
AUTHORIZED_BRANCHES = {"main", "codex/terrafar-full-coverage-quality-gate-20261024",
                       "codex/terrafar-daily-review-integrated-20261024"}
WORKFLOW = ".github/workflows/terrafar-source-maintenance.yml"
REVIEW_RUN_PREFIX = "TERRAFAR review · "


def encrypted_paths(manifest: dict) -> list[str]:
    """Validate the bounded, ordered ciphertext layout before reading any paths."""
    if manifest.get("private_archive") != PRIVATE_ARCHIVE:
        raise ValueError("review_report_private_archive_identity_invalid")
    if manifest.get("format") == STORE_FORMAT:
        if "encrypted_parts" in manifest:
            raise ValueError("review_report_v2_cannot_declare_parts")
        return [PRIVATE_ARCHIVE]
    parts = manifest.get("encrypted_parts")
    if (manifest.get("format") != CHUNKED_STORE_FORMAT or not isinstance(parts, list)
            or not 1 <= len(parts) <= MAX_PARTS):
        raise ValueError("review_report_encrypted_parts_invalid")
    for number, part in enumerate(parts, 1):
        if (not isinstance(part, dict) or set(part) != {"path", "sha256", "decoded_bytes"}
                or part["path"] != f"{PRIVATE_PARTS}/{number:06d}.b64"
                or not isinstance(part["sha256"], str) or not quality.HASH.fullmatch(part["sha256"])
                or type(part["decoded_bytes"]) is not int or not 1 <= part["decoded_bytes"] <= PART_BYTES
                or (number < len(parts) and part["decoded_bytes"] != PART_BYTES)
                or manifest.get("file_sha256", {}).get(part["path"]) != part["sha256"]):
            raise ValueError("review_report_encrypted_part_order_size_or_hash_invalid")
    return [part["path"] for part in parts]


def assemble_cipher(manifest: dict, files: dict[str, bytes]) -> bytes:
    paths = encrypted_paths(manifest)
    if manifest["format"] == STORE_FORMAT:
        cipher = files.get(PRIVATE_ARCHIVE, b"")
    else:
        chunks = []
        for part, path in zip(manifest["encrypted_parts"], paths):
            payload = files.get(path, b"")
            if (len(payload) > 4 * ((PART_BYTES + 2) // 3) + 1
                    or hashlib.sha256(payload).hexdigest() != part["sha256"]):
                raise ValueError("review_report_encrypted_part_missing_or_corrupt")
            try:
                chunk = base64.b64decode(payload[:-1], validate=True)
            except (ValueError, base64.binascii.Error) as error:
                raise ValueError("review_report_encrypted_part_base64_invalid") from error
            if (payload != base64.b64encode(chunk) + b"\n" or len(chunk) != part["decoded_bytes"]):
                raise ValueError("review_report_encrypted_part_not_canonical")
            chunks.append(chunk)
        cipher = b"".join(chunks)
    if hashlib.sha256(cipher).hexdigest() != manifest.get("encrypted_review_sha256"):
        raise ValueError("review_report_encrypted_archive_missing_or_invalid")
    state_archive.validate_ciphertext(cipher)
    return cipher


def write_cipher_parts(directory: Path, ciphertext: bytes) -> list[dict]:
    if len(ciphertext) > PART_BYTES * MAX_PARTS:
        raise ValueError("review_report_ciphertext_exceeds_bounded_storage")
    parts = []
    for offset in range(0, len(ciphertext), PART_BYTES):
        chunk = ciphertext[offset:offset + PART_BYTES]
        relative = f"{PRIVATE_PARTS}/{len(parts) + 1:06d}.b64"
        payload = base64.b64encode(chunk) + b"\n"
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        parts.append({"path": relative, "sha256": hashlib.sha256(payload).hexdigest(), "decoded_bytes": len(chunk)})
    return parts


def validate_journal(journal: dict) -> None:
    if (not isinstance(journal, dict) or journal.get("format") != "terrafar-quality-journal-v1"
            or journal.get("schema_version") != quality.VERSION or journal.get("timezone") != quality.TIMEZONE
            or not isinstance(journal.get("batches"), dict) or not isinstance(journal.get("required_source_ids"), list)):
        raise ValueError("review_store_journal_format_invalid")
    for day, batch in journal["batches"].items():
        if (batch.get("date") != day or batch.get("batch_id") != f"terrafar-quality-{day}"
                or batch.get("content_digest") != quality.digest(quality.content_payload(batch))
                or batch.get("sample") != quality.sample_records(batch["records"], batch["content_digest"])):
            raise ValueError("review_store_batch_identity_digest_or_sample_invalid")
        if len({row["record_id"] for row in batch["records"]}) != len(batch["records"]):
            raise ValueError("review_store_record_identity_not_unique")
        if any(row.get("record_digest") != quality.digest(row["payload"]) for row in batch["records"]):
            raise ValueError("review_store_record_payload_digest_invalid")
        if not isinstance(batch.get("events"), list) or not isinstance(batch.get("review_history"), list):
            raise ValueError("review_store_history_missing")
        for audit in batch.get("independent_audit_history", []):
            if (audit.get("audit_id") != quality.digest({key: value for key, value in audit.items() if key != "audit_id"})
                    or audit.get("actor_kind") not in {"agent", "automated_audit"}
                    or not audit.get("evidence") or not all(quality.valid_evidence(row) for row in audit["evidence"])):
                raise ValueError("review_store_independent_audit_digest_or_evidence_invalid")
        if batch.get("failure_resolved"):
            if (not batch.get("had_failure") or batch["recheck"].get("required")
                    or batch["human_review"].get("decision") != "pass"
                    or batch["human_review"].get("content_digest") != batch["content_digest"]
                    or any(quality.record_blockers(row) for row in batch["records"])):
                raise ValueError("review_store_failure_resolution_invalid")


def is_extension(new: dict, old: dict) -> bool:
    """Only accept monotonic histories; divergent branch histories need review."""
    if not set(old["required_source_ids"]).issubset(new["required_source_ids"]):
        return False
    previous_events = old.get("events", [])
    if new.get("events", [])[:len(previous_events)] != previous_events:
        return False
    if old.get("initial_release_approved") and (not new.get("initial_release_approved")
            or old.get("initial_release_receipt") != new.get("initial_release_receipt")):
        return False
    for day, previous in old["batches"].items():
        current = new["batches"].get(day)
        if not current or current["revision"] < previous["revision"]:
            return False
        for key in ("events", "review_history", "independent_audit_history"):
            prior_history = previous.get(key, [])
            if current.get(key, [])[:len(prior_history)] != prior_history:
                return False
        if previous.get("had_failure") and not current.get("had_failure"):
            return False
        if not {row["record_id"] for row in previous["records"]}.issubset(row["record_id"] for row in current["records"]):
            return False
        if current["events"] == previous["events"] and current["content_digest"] != previous["content_digest"]:
            return False
    return True


def reconcile(local: dict | None, remote: dict | None) -> tuple[dict, str]:
    for value in (local, remote):
        if value is not None:
            validate_journal(value)
    if remote is None:
        return copy.deepcopy(local or quality.empty_journal()), "first_report_branch_initialization"
    if local is None or is_extension(remote, local):
        return copy.deepcopy(remote), "report_branch_contains_latest_history"
    if is_extension(local, remote):
        return copy.deepcopy(local), "artifact_extends_report_history_without_losing_reviews"
    raise ValueError("review_authority_history_diverged_refuse_to_overwrite_or_drop_failure")


class GitHub:
    def __init__(self, repository: str):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("repository_identity_invalid")
        self.repository = repository
        self.token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("github_token_missing")

    def request(self, endpoint: str, method: str = "GET", data=None, raw: bool = False):
        headers = {"Authorization": "Bearer " + self.token,
                   "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "TERRAFAR-review-store"}
        body = json.dumps(data).encode() if data is not None else None
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request("https://api.github.com" + endpoint, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=45) as response:
            value = response.read()
        return value if raw else json.loads(value)

    def head(self) -> str | None:
        # Distinguish an absent review branch from an inaccessible repository.
        self.request(f"/repos/{self.repository}")
        try:
            return self.request(f"/repos/{self.repository}/git/ref/heads/{BRANCH}")["object"]["sha"]
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise

    def file(self, path: str, commit: str) -> bytes:
        return self.request(f"/repos/{self.repository}/contents/{path}?ref={commit}", raw=True)

    def review_runs(self) -> list[dict]:
        runs = []
        page = 1
        while True:
            result = self.request(f"/repos/{self.repository}/actions/workflows/terrafar-source-maintenance.yml/runs?event=workflow_dispatch&per_page=100&page={page}")
            if not isinstance(result.get("workflow_runs"), list):
                raise ValueError("review_delivery_history_unavailable")
            current = result["workflow_runs"]
            runs.extend(row for row in current if str(row.get("display_title", "")).startswith(REVIEW_RUN_PREFIX))
            if len(current) < 100:
                return runs
            page += 1


def unconfirmed_review_runs(runs: list[dict], authority: dict | None, current_run_id: str | None,
                            repository: str | None = None) -> list[str]:
    """Only the published authority can acknowledge a delivered review input."""
    receipts = {str(event["actions_run_id"]) for event in (authority or {}).get("events", [])
                if event.get("type") == "review_input_imported" and event.get("actions_run_id")
                and event.get("input_sha256") and quality.HASH.fullmatch(str(event.get("input_sha256", "")))}
    eligible = []
    for run in runs:
        if (not str(run.get("display_title", "")).startswith(REVIEW_RUN_PREFIX)
                or run.get("event") != "workflow_dispatch" or run.get("head_branch") not in AUTHORIZED_BRANCHES):
            continue
        if repository is not None:
            origin = (run.get("head_repository") or {}).get("full_name")
            if not origin:
                raise ValueError("review_delivery_repository_identity_unavailable")
            if origin != repository:
                continue
        if str(run.get("path", "")).split("@", 1)[0] != WORKFLOW:
            raise ValueError("review_delivery_workflow_identity_unavailable")
        eligible.append(run)
    current = next((run for run in eligible if str(run.get("id")) == str(current_run_id or "")), None)
    current_number = current.get("run_number") if current else None
    pending = []
    for run in eligible:
        run_id = str(run.get("id", ""))
        if run.get("status") != "completed":
            continue
        if run_id and run_id not in receipts and run_id != str(current_run_id or ""):
            # A later review may itself have failed at this guard. Permit the
            # earliest actual review transaction to recover first, otherwise
            # two failed review runs would permanently block one another.
            # A daily/source run has no eligible review identity and cannot use
            # this exception merely because its numeric run ID is older.
            if (isinstance(current_number, int) and current_number > 0
                    and isinstance(run.get("run_number"), int) and run["run_number"] > current_number):
                continue
            pending.append(run_id)
    return sorted(set(pending))


def _read_remote_authority(api: GitHub, head: str, repository: str, recipient_certificate: Path) -> dict:
    """Only the encrypted journal is authority; public summaries cannot approve anything."""
    manifest = json.loads(api.file(MANIFEST, head))
    if (manifest.get("format") not in {STORE_FORMAT, CHUNKED_STORE_FORMAT} or manifest.get("repository") != repository
            or manifest.get("branch") != BRANCH or manifest.get("private_archive") != PRIVATE_ARCHIVE
            or manifest.get("source_branch") not in AUTHORIZED_BRANCHES):
        raise ValueError("review_authority_manifest_or_journal_hash_invalid")
    encrypted = assemble_cipher(manifest, {path: api.file(path, head) for path in encrypted_paths(manifest)})
    if (hashlib.sha256(encrypted).hexdigest() != manifest.get("encrypted_review_sha256")
            or hashlib.sha256(recipient_certificate.read_bytes()).hexdigest() != manifest.get("state_encryption_certificate_sha256")):
        raise ValueError("review_authority_archive_or_certificate_hash_invalid")
    with tempfile.TemporaryDirectory(prefix="terrafar-review-authority-") as tmp:
        root = Path(tmp)
        archive = root / "private-review.cms"
        archive.write_bytes(encrypted)
        os.chmod(archive, 0o600)
        state_archive.decrypt_archive(archive, root / "unpacked", recipient_certificate)
        journal_bytes = (root / "unpacked/state/quality_journal.json").read_bytes()
        if hashlib.sha256(journal_bytes).hexdigest() != manifest.get("journal_sha256"):
            raise ValueError("review_authority_manifest_or_journal_hash_invalid")
        journal = json.loads(journal_bytes)
    validate_journal(journal)
    return journal


def load_authority(repository: str, journal_path: Path, info_path: Path,
                   recipient_certificate: Path = RECIPIENT_CERTIFICATE) -> dict:
    api = GitHub(repository)
    head = api.head()
    local = quality.read_json(journal_path) if journal_path.exists() else None
    remote = _read_remote_authority(api, head, repository, recipient_certificate) if head else None
    # A missing key, invalid cipher, unknown authority format, or interrupted
    # delivery fails closed; never replace an encrypted authority with old plaintext.
    undelivered = unconfirmed_review_runs(api.review_runs(), remote, os.environ.get("GITHUB_RUN_ID"), repository)
    if undelivered:
        raise ValueError("unconfirmed_review_delivery_blocks_maintenance: " + ",".join(undelivered)
                         + "; rerun all jobs of the original review run to replay its input and publish the receipt")
    journal, selection = reconcile(local, remote)
    quality.write_json(journal_path, journal)
    os.chmod(journal_path, 0o600)
    info = {"format": "terrafar-review-authority-v1", "repository": repository, "branch": BRANCH,
            "head_sha": head, "selection": selection, "loaded_at": quality.now(),
            "journal_sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest()}
    quality.write_json(info_path, info)
    return info


def controlled_input(app_root: Path, supplied: str) -> Path:
    raw = Path(supplied)
    approved = (app_root / "maintenance/terrafar-source-audit/quality").resolve()
    actual = (app_root / raw).resolve()
    if (raw.is_absolute() or ".." in raw.parts or actual.suffix != ".json" or not actual.is_relative_to(approved)
            or not actual.is_file() or actual.stat().st_size > 16 * 1024 * 1024):
        raise ValueError("review_input_must_be_bounded_json_under_quality_directory")
    return actual


def import_inputs(app_root: Path, journal_path: Path, batch_path: Path, decision: str | None, recheck: str | None) -> dict:
    if not decision and not recheck:
        raise ValueError("review_mode_requires_actual_review_or_recheck_input")
    journal = quality.read_json(journal_path)
    validate_journal(journal)
    operations = []
    if recheck:
        path = controlled_input(app_root, recheck)
        value = quality.read_json(path)
        if not isinstance(value, list) or not value:
            raise ValueError("recheck_input_requires_nonempty_array")
        batch_ids = {row.get("batch_id") for row in value}
        if len(batch_ids) != 1:
            raise ValueError("recheck_input_must_belong_to_one_daily_batch")
        operations.append(("recheck", path, next(iter(batch_ids))))
    if decision:
        path = controlled_input(app_root, decision)
        operations.append(("review", path, quality.read_json(path).get("batch_id")))
    if len({batch_id for _, _, batch_id in operations}) != 1:
        raise ValueError("review_and_recheck_inputs_must_belong_to_same_day")
    batch_id = operations[0][2]
    matches = [batch for batch in journal["batches"].values() if batch["batch_id"] == batch_id]
    if len(matches) != 1:
        raise ValueError("review_input_batch_not_in_authority_journal")
    quality.write_json(batch_path, matches[0])
    for kind, path, _ in operations:
        if kind == "recheck":
            batch = quality.apply_rechecks(batch_path, journal_path, path)
        else:
            batch = quality.review_batch(batch_path, journal_path, path)
    inputs = [{"kind": kind, "path": str(path.relative_to(app_root.resolve())),
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for kind, path, _ in operations]
    actions_run_id = os.environ.get("GITHUB_RUN_ID")
    if actions_run_id is not None and not actions_run_id.isdigit():
        raise ValueError("review_import_actions_run_id_invalid")
    receipt = {"type": "review_input_imported", "actions_run_id": actions_run_id,
               "actions_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "workflow_path": WORKFLOW,
               "input_sha256": quality.digest(inputs), "inputs": inputs, "at": quality.now(),
               "batch_id": batch["batch_id"], "revision": batch["revision"], "content_digest": batch["content_digest"],
               "human_decision": batch["human_review"]["decision"], "recheck_required": batch["recheck"]["required"]}
    with quality.locked_journal(journal_path) as journal:
        quality.current_batch(batch_path, journal)
        journal.setdefault("events", []).append(receipt)
        quality.write_json(journal_path, journal)
    return {"batch_id": batch["batch_id"], "revision": batch["revision"], "status": batch["status"],
            "human_decision": batch["human_review"]["decision"], "release_allowed": batch["release_gate"]["allowed"],
            "import_receipt": receipt}


PUBLIC_BLOCKERS = frozenset({
    "full_source_scope_not_complete", "source_semantic_audit_failed", "non_live_run_cannot_authorize_release",
    "record_review_or_field_evidence_incomplete", "initial_catalog_review_incomplete",
    "current_revision_human_sample_not_approved", "entire_daily_batch_requires_recheck",
    "earlier_failed_daily_batch_unresolved", "actual_target_files_not_equal_reviewed_version",
})
PUBLIC_SUMMARY_KEYS = frozenset({"format", "date", "revision", "status", "human_review", "release_allowed",
    "required_sources", "attempted_sources", "machine_complete_sources", "effective_complete_sources",
    "independently_invalidated_source_count", "source_status_counts", "record_count", "catalog_record_count",
    "recheck_required", "recheck_record_count", "recheck_completed_count", "unresolved_failure_day_count",
    "blockers", "unknown_blocker_count", "details_encrypted", "generation_context", "data_origin_run_ids"})
PUBLIC_STATUSES = {"blocked", "recheck_required", "ready_for_release", "awaiting_human_review"}


def public_summary(batch: dict, journal: dict, generation_context: str = "github_actions",
                   data_origin_run_ids: list[str] | None = None) -> dict:
    """Counts and enums only. No candidate names, IDs, notes, URLs, or field evidence."""
    gate = quality.evaluate(batch, journal)
    coverage = gate["source_coverage"]
    status = ("recheck_required" if batch["recheck"].get("required") else
              "ready_for_release" if gate["allowed"] else
              "awaiting_human_review" if gate["blockers"] == ["current_revision_human_sample_not_approved"] else "blocked")
    decision = batch["human_review"].get("decision")
    summary = {"format": "terrafar-public-quality-summary-v1", "date": batch["date"],
        "revision": batch["revision"], "status": status,
        "human_review": decision if decision in {"pending", "pass", "fail"} else "pending",
        "release_allowed": gate["allowed"], "required_sources": coverage["required"],
        "attempted_sources": coverage["attempted"], "machine_complete_sources": coverage["machine_complete"],
        "effective_complete_sources": coverage["complete"],
        "independently_invalidated_source_count": len(coverage["independently_invalidated_source_ids"]),
        "source_status_counts": coverage["counts"], "record_count": len(batch["records"]),
        "catalog_record_count": len((batch.get("catalog_inventory") or {}).get("records", [])),
        "recheck_required": bool(batch["recheck"].get("required")),
        "recheck_record_count": len(batch["recheck"].get("required_record_ids", [])),
        "recheck_completed_count": len(batch["recheck"].get("completed", {})),
        "unresolved_failure_day_count": len(gate["unresolved_failure_dates"]),
        "blockers": sorted(set(gate["blockers"]) & PUBLIC_BLOCKERS),
        "unknown_blocker_count": len(set(gate["blockers"]) - PUBLIC_BLOCKERS), "details_encrypted": True,
        "generation_context": generation_context, "data_origin_run_ids": data_origin_run_ids or []}
    validate_public_summary(summary)
    return summary


def validate_public_summary(value: dict) -> None:
    if not isinstance(value, dict) or set(value) != PUBLIC_SUMMARY_KEYS:
        raise ValueError("public_review_summary_unknown_or_missing_fields")
    if (value["format"] != "terrafar-public-quality-summary-v1"
            or not isinstance(value["date"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value["date"])
            or value["status"] not in PUBLIC_STATUSES or value["human_review"] not in {"pending", "pass", "fail"}
            or value["details_encrypted"] is not True
            or value["generation_context"] not in {"github_actions", "local_reconstruction"}
            or not isinstance(value["data_origin_run_ids"], list)
            or any(not isinstance(item, str) or not re.fullmatch(r"[0-9]{1,32}", item) for item in value["data_origin_run_ids"])
            or (value["generation_context"] == "local_reconstruction" and not value["data_origin_run_ids"])):
        raise ValueError("public_review_summary_invalid_identity_or_enum")
    bool_keys = {"release_allowed", "recheck_required", "details_encrypted"}
    non_count_keys = {"format", "date", "status", "human_review", "blockers", "source_status_counts", "generation_context", "data_origin_run_ids"} | bool_keys
    if (any(type(value[key]) is not bool for key in bool_keys)
            or any(type(value[key]) is not int or value[key] < 0 for key in PUBLIC_SUMMARY_KEYS - non_count_keys)
            or not isinstance(value["blockers"], list) or any(item not in PUBLIC_BLOCKERS for item in value["blockers"])
            or not isinstance(value["source_status_counts"], dict)
            or set(value["source_status_counts"]) - quality.STATUSES
            or any(type(number) is not int or number < 0 for number in value["source_status_counts"].values())):
        raise ValueError("public_review_summary_invalid_count_or_blocker")


def public_markdown(summary: dict, chunked: bool = False) -> str:
    validate_public_summary(summary)
    context = ("**历史证据重建报告。** 此材料在本地从已保存的实际运行证据生成，数据来源运行："
               + ", ".join(summary["data_origin_run_ids"]) + "。最新加密候选账本尚未通过本次重建恢复；"
               "这不是新的 Actions 执行或最新账本核验完成的声明。\n\n"
               if summary["generation_context"] == "local_reconstruction" else "")
    rendered = ("# TERRAFAR 每日核验状态\n\n" + context +
        f"- 日期：{summary['date']}；修订：{summary['revision']}。\n"
        f"- 来源计划 / 尝试：{summary['required_sources']} / {summary['attempted_sources']}。\n"
        f"- 机器完整范围检查 / 独立审核后有效：{summary['machine_complete_sources']} / {summary['effective_complete_sources']}。\n"
        f"- 当日审核记录：{summary['record_count']}；正式目录快照：{summary['catalog_record_count']}。\n"
        f"- 人工抽检：`{summary['human_review']}`；状态：`{summary['status']}`。\n"
        f"- 整批重核要求：{summary['recheck_required']}；完成 / 要求：{summary['recheck_completed_count']} / {summary['recheck_record_count']}。\n"
        f"- 发布门：{'通过' if summary['release_allowed'] else '未通过'}。\n\n"
        "## 查看完整材料\n\n"
        "候选文本、字段证据、抽检清单和审核历史保存在同目录上级的 `private-review.cms` 加密包中。"
        "由持有匹配私钥的所有者下载并在本地解密；请勿把私钥提交到仓库、聊天或日志。"
        "解密后的 `quality/latest/review.json` 可导入本地审核页面；人工决定必须绑定该版本。"
        "公开摘要仅供查看运行情况，不能替代完整材料或证明人工已经批准。\n")
    if chunked:
        rendered = rendered.replace(
            "候选文本、字段证据、抽检清单和审核历史保存在同目录上级的 `private-review.cms` 加密包中。",
            "候选文本、字段证据、抽检清单和审核历史加密保存于 `quality/private-review.parts/`。"
            "请从同一提交下载整个核验分支及 `quality/store-manifest.json`，在可信本地环境运行 "
            "`terrafar_review_store.py decrypt-store` 自动校验并合并解密；不要手工拼接分片。")
    return rendered


def export_store(journal_path: Path, directory: Path, authority_info: Path, repository: str,
                 recipient_certificate: Path = RECIPIENT_CERTIFICATE, generation_context: str = "github_actions",
                 data_origin_run_ids: list[str] | None = None) -> dict:
    journal = quality.read_json(journal_path)
    validate_journal(journal)
    if not journal["batches"]:
        raise ValueError("review_store_cannot_publish_empty_history_as_success")
    authority = quality.read_json(authority_info)
    if authority.get("repository") != repository or authority.get("branch") != BRANCH:
        raise ValueError("review_authority_repository_or_branch_mismatch")
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("review_store_export_destination_must_be_empty")
    root = directory / ROOT
    root.mkdir(parents=True, exist_ok=True)
    summaries = []
    latest_day = max(journal["batches"])
    with tempfile.TemporaryDirectory(prefix="terrafar-private-review-") as tmp:
        private = Path(tmp) / "state"
        private.mkdir(mode=0o700)
        quality.write_json(private / "quality_journal.json", journal)
        private_root = private / "quality"
        for day, stored in sorted(journal["batches"].items()):
            batch = copy.deepcopy(stored)
            batch["release_gate"] = quality.evaluate(batch, journal)
            quality.export_batch(batch, private_root / day)
            summary = public_summary(batch, journal, generation_context, data_origin_run_ids)
            summaries.append(summary)
            quality.write_json(root / day / "review.json", summary)
            (root / day / "review.md").write_text(public_markdown(summary), encoding="utf-8")
        latest = copy.deepcopy(journal["batches"][latest_day])
        latest["release_gate"] = quality.evaluate(latest, journal)
        quality.export_batch(latest, private_root / "latest", journal)
        state_archive.encrypt_directory(private, directory / PRIVATE_ARCHIVE, recipient_certificate)
        journal_sha = hashlib.sha256((private / "quality_journal.json").read_bytes()).hexdigest()
    cipher_path = directory / PRIVATE_ARCHIVE
    ciphertext = cipher_path.read_bytes()
    cipher_hash = hashlib.sha256(ciphertext).hexdigest()
    parts = write_cipher_parts(directory, ciphertext) if len(ciphertext) > PART_BYTES else []
    if parts:
        cipher_path.unlink()
        for summary in summaries:
            (root / summary["date"] / "review.md").write_text(public_markdown(summary, True), encoding="utf-8")
    last_summary = next(row for row in summaries if row["date"] == latest_day)
    quality.write_json(root / "latest/review.json", last_summary)
    (root / "latest/review.md").write_text(public_markdown(last_summary, bool(parts)), encoding="utf-8")
    quality.write_json(root / "index.json", {"format": "terrafar-public-quality-index-v1",
        "latest_date": latest_day, "details_encrypted": True, "batches": list(reversed(summaries))})
    files = {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(root.rglob("*")) if path.is_file()}
    manifest = {"format": CHUNKED_STORE_FORMAT if parts else STORE_FORMAT, "repository": repository, "branch": BRANCH,
        "generated_at": quality.now(), "expected_previous_head": authority["head_sha"],
        "source_actions_run_id": os.environ.get("GITHUB_RUN_ID") if generation_context == "github_actions" else None,
        "source_commit_sha": os.environ.get("GITHUB_SHA"), "generation_context": generation_context,
        "data_origin_run_ids": data_origin_run_ids or [],
        "source_branch": os.environ.get("GITHUB_REF_NAME"), "latest_date": latest_day,
        "journal_sha256": journal_sha, "private_archive": PRIVATE_ARCHIVE,
        "encrypted_review_sha256": cipher_hash,
        "state_encryption_certificate_sha256": hashlib.sha256(recipient_certificate.read_bytes()).hexdigest(),
        "file_sha256": files, "batch_count": len(journal["batches"])}
    if parts:
        manifest["encrypted_parts"] = parts
    quality.write_json(root / "store-manifest.json", manifest)
    validate_store(directory, repository, recipient_certificate)
    return {"directory": str(directory), "batch_count": len(journal["batches"]), "latest_date": latest_day,
            "file_count": len(files) + 1, "release_allowed": last_summary["release_allowed"], "details_encrypted": True}


def validate_store(directory: Path, repository: str, recipient_certificate: Path | None = None) -> tuple[dict, dict[str, bytes]]:
    manifest = quality.read_json(directory / MANIFEST)
    manifest_keys = {"format", "repository", "branch", "generated_at", "expected_previous_head", "source_actions_run_id",
        "source_commit_sha", "source_branch", "latest_date", "journal_sha256", "private_archive",
        "encrypted_review_sha256", "state_encryption_certificate_sha256", "file_sha256", "batch_count",
        "generation_context", "data_origin_run_ids"}
    if manifest.get("format") == CHUNKED_STORE_FORMAT:
        manifest_keys.add("encrypted_parts")
    if (set(manifest) != manifest_keys or manifest.get("format") not in {STORE_FORMAT, CHUNKED_STORE_FORMAT} or manifest.get("repository") != repository
            or manifest.get("branch") != BRANCH or manifest.get("source_branch") not in AUTHORIZED_BRANCHES
            or manifest.get("private_archive") != PRIVATE_ARCHIVE):
        raise ValueError("review_report_not_from_an_authorized_branch_or_repository")
    for key in ("journal_sha256", "encrypted_review_sha256", "state_encryption_certificate_sha256"):
        if not isinstance(manifest.get(key), str) or not quality.HASH.fullmatch(manifest[key]):
            raise ValueError("review_report_manifest_hash_invalid")
    if (manifest.get("generation_context") not in {"github_actions", "local_reconstruction"}
            or (manifest["generation_context"] == "github_actions" and (not isinstance(manifest.get("source_actions_run_id"), str)
                or not re.fullmatch(r"[0-9]{1,32}", manifest["source_actions_run_id"])))
            or (manifest["generation_context"] == "local_reconstruction" and manifest.get("source_actions_run_id") is not None)
            or not isinstance(manifest.get("source_commit_sha"), str)
            or not re.fullmatch(r"[0-9a-f]{40}", manifest["source_commit_sha"])
            or (manifest.get("expected_previous_head") is not None and not re.fullmatch(r"[0-9a-f]{40}", str(manifest["expected_previous_head"])))):
        raise ValueError("review_report_manifest_provenance_invalid")
    if (not isinstance(manifest.get("generated_at"), str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)", manifest["generated_at"])
            or not isinstance(manifest.get("file_sha256"), dict)):
        raise ValueError("review_report_manifest_metadata_invalid")
    private_paths = set(encrypted_paths(manifest))
    expected = set(manifest.get("file_sha256", {})) | {MANIFEST}
    actual = {str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError("review_report_manifest_file_set_mismatch")
    files = {}
    for relative in sorted(expected):
        path = directory / relative
        pieces = Path(relative).parts
        allowed = (relative in private_paths | {MANIFEST, f"{ROOT}/index.json"} or
                   (len(pieces) == 3 and pieces[0] == ROOT and (pieces[1] == "latest" or re.fullmatch(r"\d{4}-\d{2}-\d{2}", pieces[1]))
                    and pieces[2] in REVIEW_FILES))
        if not allowed or path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("review_report_path_not_allowed")
        payload = path.read_bytes()
        if relative != MANIFEST and hashlib.sha256(payload).hexdigest() != manifest["file_sha256"][relative]:
            raise ValueError("review_report_file_digest_mismatch")
        files[relative] = payload
    assemble_cipher(manifest, files)
    if recipient_certificate is not None and hashlib.sha256(recipient_certificate.read_bytes()).hexdigest() != manifest["state_encryption_certificate_sha256"]:
        raise ValueError("review_report_recipient_certificate_mismatch")
    index = json.loads(files[f"{ROOT}/index.json"])
    if (set(index) != {"format", "latest_date", "details_encrypted", "batches"}
            or index["format"] != "terrafar-public-quality-index-v1" or index["details_encrypted"] is not True
            or not isinstance(index["batches"], list)):
        raise ValueError("public_review_index_invalid")
    for row in index["batches"]:
        validate_public_summary(row)
        if row["generation_context"] != manifest["generation_context"] or row["data_origin_run_ids"] != manifest["data_origin_run_ids"]:
            raise ValueError("public_review_generation_provenance_mismatch")
    dates = [row["date"] for row in index["batches"]]
    if (not dates or dates != sorted(set(dates), reverse=True) or dates[0] != manifest["latest_date"]
            or index["latest_date"] != dates[0] or type(manifest["batch_count"]) is not int or manifest["batch_count"] != len(dates)):
        raise ValueError("public_review_index_dates_invalid")
    required = private_paths | {MANIFEST, f"{ROOT}/index.json"}
    for label, summary in [(row["date"], row) for row in index["batches"]] + [("latest", index["batches"][0])]:
        jpath, mpath = f"{ROOT}/{label}/review.json", f"{ROOT}/{label}/review.md"
        required.update({jpath, mpath})
        if (json.loads(files.get(jpath, b"{}")) != summary
                or files.get(mpath) != public_markdown(summary, manifest["format"] == CHUNKED_STORE_FORMAT).encode()):
            raise ValueError("public_review_summary_or_markdown_not_canonical")
    if expected != required:
        raise ValueError("public_review_file_set_not_minimal")
    return manifest, files


def decrypt_store(directory: Path, repository: str, destination: Path,
                  recipient_certificate: Path = RECIPIENT_CERTIFICATE) -> dict:
    """Verify a downloaded branch snapshot and decrypt it only in the owner's local workspace."""
    manifest, files = validate_store(directory, repository, recipient_certificate)
    if destination.is_symlink() or (destination.exists() and (not destination.is_dir() or any(destination.iterdir()))):
        raise ValueError("review_decrypt_destination_must_be_empty")
    with tempfile.TemporaryDirectory(prefix="terrafar-local-review-") as tmp:
        root = Path(tmp)
        archive = root / "private-review.cms"
        archive.write_bytes(assemble_cipher(manifest, files))
        os.chmod(archive, 0o600)
        state_archive.decrypt_archive(archive, root / "unpacked", recipient_certificate)
        journal = root / "unpacked/state/quality_journal.json"
        if hashlib.sha256(journal.read_bytes()).hexdigest() != manifest["journal_sha256"]:
            raise ValueError("review_authority_manifest_or_journal_hash_invalid")
        validate_journal(quality.read_json(journal))
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(destination, 0o700)
        shutil.copytree(root / "unpacked/state", destination / "state")
    return {"destination": str(destination), "batch_count": manifest["batch_count"],
            "latest_date": manifest["latest_date"], "journal_sha256": manifest["journal_sha256"]}


def publish_store(directory: Path, repository: str, recipient_certificate: Path = RECIPIENT_CERTIFICATE) -> dict:
    manifest, files = validate_store(directory, repository, recipient_certificate)
    api = GitHub(repository)
    expected = manifest["expected_previous_head"]
    if api.head() != expected:
        raise ValueError("review_branch_head_changed_refuse_stale_report_push")
    base_tree = None
    existing = {}
    obsolete = set()
    if expected:
        base_tree = api.request(f"/repos/{repository}/git/commits/{expected}")["tree"]["sha"]
        tree = api.request(f"/repos/{repository}/git/trees/{base_tree}?recursive=1")
        if tree.get("truncated"):
            raise ValueError("review_branch_tree_truncated")
        existing = {entry["path"]: entry["sha"] for entry in tree["tree"] if entry["type"] == "blob"}
        obsolete = set(existing) - set(files)
        if obsolete:
            # A change in encrypted length can remove tail parts; upgrading v2
            # also removes its single ciphertext. Never delete history or carry
            # forward any other unexpected file. Validate the old whole store at
            # the same pinned HEAD before permitting these atomic deletions.
            if any(path != PRIVATE_ARCHIVE and not re.fullmatch(re.escape(PRIVATE_PARTS) + r"/\d{6}\.b64", path)
                   for path in obsolete):
                raise ValueError("review_branch_contains_unapproved_files_refuse_to_carry_forward")
            previous_bytes = api.file(MANIFEST, expected)
            previous = json.loads(previous_bytes)
            previous_private = set(encrypted_paths(previous))
            if not obsolete.issubset(previous_private) or set(existing) != set(previous.get("file_sha256", {})) | {MANIFEST}:
                raise ValueError("review_branch_contains_unapproved_files_refuse_to_carry_forward")
            with tempfile.TemporaryDirectory(prefix="terrafar-previous-public-review-") as tmp:
                old_root = Path(tmp)
                for relative in existing:
                    path = old_root / relative
                    if ".." in Path(relative).parts or not path.resolve().is_relative_to(old_root.resolve()):
                        raise ValueError("review_report_path_not_allowed")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(previous_bytes if relative == MANIFEST else api.file(relative, expected))
                validate_store(old_root, repository, recipient_certificate)
    entries = [{"path": path, "mode": "100644", "type": "blob", "sha": None} for path in sorted(obsolete)]
    for relative, payload in files.items():
        git_sha = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        if existing.get(relative) == git_sha:
            continue
        blob = api.request(f"/repos/{repository}/git/blobs", "POST", {"content": base64.b64encode(payload).decode(), "encoding": "base64"})
        entries.append({"path": relative, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    if not entries:
        return {"branch": BRANCH, "commit_sha": expected, "changed_files": 0}
    tree_data = {"tree": entries}
    if base_tree:
        tree_data["base_tree"] = base_tree
    tree = api.request(f"/repos/{repository}/git/trees", "POST", tree_data)
    commit = api.request(f"/repos/{repository}/git/commits", "POST", {
        "message": (f"Update daily review reports from Actions {manifest['source_actions_run_id']}" if manifest["generation_context"] == "github_actions"
                    else "Preserve historical review evidence with encrypted authority"),
        "tree": tree["sha"], "parents": [expected] if expected else []})
    if expected:
        # A concurrent commit is not our descendant; GitHub rejects this non-force update.
        api.request(f"/repos/{repository}/git/refs/heads/{BRANCH}", "PATCH", {"sha": commit["sha"], "force": False})
    else:
        api.request(f"/repos/{repository}/git/refs", "POST", {"ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]})
    return {"branch": BRANCH, "commit_sha": commit["sha"], "changed_files": len(entries),
            "url": f"https://github.com/{repository}/tree/{BRANCH}/{ROOT}"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    load = commands.add_parser("load-authority")
    load.add_argument("--repository", required=True)
    load.add_argument("--journal", type=Path, required=True)
    load.add_argument("--authority-info", type=Path, required=True)
    load.add_argument("--recipient-certificate", type=Path, default=RECIPIENT_CERTIFICATE)
    inputs = commands.add_parser("import-inputs")
    inputs.add_argument("--app-root", type=Path, default=Path.cwd())
    inputs.add_argument("--journal", type=Path, required=True)
    inputs.add_argument("--batch", type=Path, required=True)
    inputs.add_argument("--decision")
    inputs.add_argument("--recheck")
    export = commands.add_parser("export-store")
    export.add_argument("--journal", type=Path, required=True)
    export.add_argument("--authority-info", type=Path, required=True)
    export.add_argument("--repository", required=True)
    export.add_argument("--directory", type=Path, required=True)
    export.add_argument("--recipient-certificate", type=Path, default=RECIPIENT_CERTIFICATE)
    export.add_argument("--generation-context", choices=["github_actions", "local_reconstruction"], default="github_actions")
    export.add_argument("--data-origin-run-id", action="append", default=[])
    publish = commands.add_parser("publish-store")
    publish.add_argument("--repository", required=True)
    publish.add_argument("--directory", type=Path, required=True)
    publish.add_argument("--recipient-certificate", type=Path, default=RECIPIENT_CERTIFICATE)
    decrypt = commands.add_parser("decrypt-store")
    decrypt.add_argument("--repository", required=True)
    decrypt.add_argument("--directory", type=Path, required=True)
    decrypt.add_argument("--destination", type=Path, required=True)
    decrypt.add_argument("--recipient-certificate", type=Path, default=RECIPIENT_CERTIFICATE)
    args = parser.parse_args()
    if args.command == "load-authority":
        result = load_authority(args.repository, args.journal, args.authority_info, args.recipient_certificate)
    elif args.command == "import-inputs":
        result = import_inputs(args.app_root, args.journal, args.batch, args.decision, args.recheck)
    elif args.command == "export-store":
        result = export_store(args.journal, args.directory, args.authority_info, args.repository, args.recipient_certificate,
                              args.generation_context, args.data_origin_run_id)
    elif args.command == "decrypt-store":
        result = decrypt_store(args.directory, args.repository, args.destination, args.recipient_certificate)
    else:
        result = publish_store(args.directory, args.repository, args.recipient_certificate)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
