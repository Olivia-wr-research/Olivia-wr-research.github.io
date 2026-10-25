#!/usr/bin/env python3
"""Run an owner-enabled PRIVATE maintenance cycle against one S3 authority.

Not wired into the public workflow. stdout is operational status only; detailed
output stays in the encrypted state. No source adaptation or content publication.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import terrafar_private_store as storage
import terrafar_restore_run_state as restore
import terrafar_review_store as reviews
import terrafar_state_archive as crypto
import terrafar_select_checkpoint as checkpoints

APP = Path(__file__).resolve().parents[1]
MAINT = APP / "maintenance/terrafar-source-audit"
WORKFLOW = ".github/workflows/terrafar-private-maintenance.yml"
REVIEW_PREFIX = "TERRAFAR private review · "


def pipeline_versions():
    names = ('terrafar_model_executor.py', 'terrafar_detail_capture.py',
             'terrafar_native_review.py', 'terrafar_pipeline_funnel.py',
             'terrafar_independent_eval.py')
    return {name: hashlib.sha256((APP / 'scripts' / name).read_bytes()).hexdigest() for name in names}


def check_pipeline_versions(workspace):
    if any((workspace / name).exists() for name in ('page_snapshots', 'model_results', 'pipeline_diagnostics')):
        version_file = workspace / 'pipeline_versions.json'
        if not version_file.is_file() or storage.read_json(version_file) != pipeline_versions():
            raise storage.StoreError('private_pipeline_requires_reviewed_version_migration')


def check_review_deliveries(journal, api=None):
    repository = os.environ["GITHUB_REPOSITORY"]
    token = os.environ.get("GH_TOKEN")
    if api is None:
        if not token:
            raise storage.StoreError("private_cycle_delivery_history_token_missing")
        api = checkpoints.GitHubAPI(repository, token)
    runs = api.pages("actions/workflows/terrafar-private-maintenance.yml/runs", "workflow_runs", {"event": "workflow_dispatch"})
    pending = reviews.unconfirmed_review_runs(runs, journal, os.environ["GITHUB_RUN_ID"], repository,
        workflow=WORKFLOW, authorized_branches={"main"}, run_prefix=REVIEW_PREFIX)
    if pending:
        raise storage.StoreError("private_cycle_unconfirmed_review_delivery_blocks_maintenance")


def run_command(args, log):
    subprocess.run(args, cwd=APP, stdout=log, stderr=log, check=True)


def run_cycle(vault, workspace, mode="daily", review_input=None, detail_limit=0):
    if not 0 <= detail_limit <= 10:
        raise storage.StoreError('private_pipeline_detail_limit_invalid')
    receipt = workspace.parent / (workspace.name + "-receipt.json")
    vault.restore(workspace, receipt)
    check_pipeline_versions(workspace)
    if (workspace / "source_registry.json").read_bytes() != (MAINT / "registry/source_registry.json").read_bytes():
        raise storage.StoreError("private_cycle_registry_requires_reviewed_migration")
    if storage.read_json(workspace / "runtime_versions.json") != restore.version_hashes(MAINT / "registry/source_registry.json"):
        raise storage.StoreError("private_cycle_implementation_requires_reviewed_migration")
    journal = storage.read_json(workspace / "quality_journal.json")
    check_review_deliveries(journal)
    if mode == "review" and any(e.get("type") == "review_input_imported" and str(e.get("actions_run_id")) == os.environ["GITHUB_RUN_ID"]
                                for e in journal.get("events", [])):
        raise storage.StoreError("private_cycle_review_already_committed_do_not_replay")
    run_id = "terrafar-private-" + os.environ["GITHUB_RUN_ID"] + "-" + os.environ["GITHUB_RUN_ATTEMPT"]
    if not all(part.isdigit() for part in (os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"])):
        raise storage.StoreError("private_cycle_run_identity_invalid")
    run_dir = MAINT / "runs" / run_id
    if run_dir.exists() or (workspace / "runs" / run_id).exists():
        raise storage.StoreError("private_cycle_run_identity_already_exists")
    # Recreate the exact relative evidence paths used by the existing quality gate.
    for prior in (workspace / "runs").glob("*"):
        target = MAINT / "runs" / prior.name
        if target.exists():
            existing = {p.relative_to(target).as_posix(): storage.sha(p.read_bytes())
                        for p in target.rglob("*") if p.is_file() and not p.is_symlink()}
            incoming = {p.relative_to(prior).as_posix(): storage.sha(p.read_bytes())
                        for p in prior.rglob("*") if p.is_file()}
            if existing != incoming or any(p.is_symlink() for p in target.rglob("*")):
                raise storage.StoreError("private_cycle_historical_run_path_collision")
        else:
            shutil.copytree(prior, target)
    run_dir.mkdir(parents=True)
    failure = None
    with (run_dir / "runtime.log").open("wb") as log:
        def command(args):
            run_command(args, log)
        try:
            if mode == "review":
                if review_input is None:
                    raise storage.StoreError("private_cycle_review_input_required")
                # The input is owner-delivered to the PRIVATE runner repository.
                # It is never obtained from the public branch or a public artifact.
                approved = MAINT / "quality/review-inputs"
                if (review_input.is_symlink() or not review_input.resolve().is_relative_to(approved.resolve())
                        or review_input.suffix != ".cms" or review_input.stat().st_size > storage.MAX_FILE):
                    raise storage.StoreError("private_cycle_review_input_location_invalid")
                shutil.copyfile(review_input, run_dir / "review-input.cms")
                with tempfile.TemporaryDirectory(dir=MAINT / "quality", prefix="private-input-") as tmp:
                    unpacked = Path(tmp) / "unpacked"
                    crypto.decrypt_archive(review_input, unpacked, vault.certificate,
                                           max_extracted_bytes=storage.MAX_FILE, max_members=4)
                    args = ["python3", "scripts/terrafar_review_store.py", "import-inputs",
                            "--journal", str(workspace / "quality_journal.json"), "--batch", str(workspace / "quality_batch.json"),
                            "--delivery-workflow", WORKFLOW]
                    for name, flag in (("decision.json", "--decision"), ("recheck.json", "--recheck")):
                        p = unpacked / "state" / name
                        if p.exists(): args += [flag, str(p.relative_to(APP))]
                    command(args)
            else:
                command(["python3", "scripts/terrafar_source_audit.py", "run", "--live", "--all-sources",
                         "--concurrency", "4", "--timeout", "15", "--retries", "1", "--per-host-delay", "1",
                         "--http-request-budget", "6000", "--require-state", "--require-candidate-ledger",
                         "--state-dir", str(workspace), "--run-id", run_id])
                if detail_limit:
                    # Opt-in only after private owner authorization and restore.
                    # No native dispatcher or paid model API is implied here.
                    from terrafar_model_executor import atomic_private_json
                    atomic_private_json(workspace / 'pipeline_versions.json', pipeline_versions())
                    command(['python3', 'scripts/terrafar_detail_capture.py',
                             '--ledger', str(workspace / 'candidate_ledger.json'),
                             '--registry', str(MAINT / 'registry/source_registry.json'),
                             '--snapshot-dir', str(workspace / 'page_snapshots' / run_id),
                             '--results', str(workspace / 'pipeline_diagnostics' / run_id / 'detail-results.jsonl'),
                             '--run-id', run_id, '--limit', str(detail_limit), '--http-request-budget', '60'])
                    command(['python3', 'scripts/terrafar_pipeline_funnel.py', '--run-dir', str(run_dir),
                             '--ledger', str(workspace / 'candidate_ledger.json'),
                             '--detail-results', str(workspace / 'pipeline_diagnostics' / run_id / 'detail-results.jsonl'),
                             '--output-dir', str(workspace / 'pipeline_diagnostics' / run_id)])
                    command(['python3', 'scripts/terrafar_independent_eval.py',
                             '--ledger', str(workspace / 'candidate_ledger.json'),
                             '--output-dir', str(workspace / 'pipeline_diagnostics' / run_id / 'independent-eval')])
                command(["node", "--input-type=module", "-e",
                         "import {writeFileSync} from 'node:fs'; import {geographyCatalog} from './dist/geography-catalog.mjs';"
                         "writeFileSync(process.argv[1],JSON.stringify(geographyCatalog));", str(workspace / "active_catalog.json")])
                command(["python3", "scripts/terrafar_quality_gate.py", "build", "--run-dir", str(run_dir),
                         "--registry", str(MAINT / "registry/source_registry.json"),
                         "--ledger", str(workspace / "candidate_ledger.json"), "--output", str(workspace / "quality_batch.json"),
                         "--journal", str(workspace / "quality_journal.json"), "--catalog", str(workspace / "active_catalog.json")])
            command(["python3", "scripts/terrafar_quality_gate.py", "export", "--batch", str(workspace / "quality_batch.json"),
                     "--output-dir", str(run_dir / "quality-review")])
        except Exception:
            failure = True
    # Save valid partial work and actual decisions even when a later export fails.
    # Validation/CAS failure leaves the previous authority untouched. A killed
    # runner can lose this cycle's uncommitted work, never the previous snapshot.
    shutil.copytree(run_dir, workspace / "runs" / run_id)
    result = vault.save(workspace, receipt)
    return {**result, "cycle": "failed" if failure else "completed", "release_published": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--mode", choices=("daily", "review"), default="daily")
    p.add_argument("--review-input", type=Path)
    p.add_argument("--detail-limit", type=int, default=0, help='Optional private detail stage; 0 keeps it disabled')
    args = p.parse_args()
    try:
        if (os.environ.get("TERRAFAR_PRIVATE_STORAGE_APPROVED") != "true"
                or os.environ.get("GITHUB_REPOSITORY_VISIBILITY") != "private"):
            raise storage.StoreError("private_cycle_owner_approval_and_private_runner_required")
        backend = storage.S3(os.environ["TERRAFAR_STATE_BUCKET"], os.environ["TERRAFAR_STATE_PREFIX"], os.environ["TERRAFAR_AWS_ACCOUNT_ID"])
        vault = storage.Vault(backend, reviews.RECIPIENT_CERTIFICATE)
        result = run_cycle(vault, args.workspace, args.mode, args.review_input, args.detail_limit)
        print(json.dumps(result, sort_keys=True))
        if result["cycle"] != "completed": raise SystemExit(2)
    except Exception as error:
        print(json.dumps({"status": "blocked", "reason": storage.safe_reason(error)}))
        raise SystemExit(2) from None


if __name__ == "__main__": main()
