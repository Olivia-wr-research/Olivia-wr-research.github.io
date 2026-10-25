#!/usr/bin/env python3
"""Private, versioned S3 state. No public artifacts, automatic bootstrap or rollback.

Each regular file is CMS encrypted with the EXISTING recipient. An encrypted
inventory references immutable version IDs. Only latest.json is mutable, using
If-Match. Source state, candidate history, review decisions and evidence therefore
advance in one transaction. S3/IAM is the integrity authority (CMS is not a signature).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

import terrafar_candidate_ledger as ledger
import terrafar_review_store as reviews
import terrafar_state_archive as crypto

FORMAT = "terrafar-private-s3-v1"
MAX_FILE = 32 * 1024 * 1024
MAX_INDEX = 16 * 1024 * 1024
MAX_FILES = 20000
HASH = re.compile(r"[0-9a-f]{64}")
CORE = ("source_registry.json", "state.json", "candidate_ledger.json", "quality_journal.json")


class StoreError(ValueError):
    pass


def safe_reason(error):
    if isinstance(error, StoreError) and re.fullmatch(r"private_[a-z_]{1,100}", str(error)):
        return str(error)
    if isinstance(error, ValueError) and str(error).startswith("required_decryption_secret_missing:"):
        return "private_store_matching_key_missing"
    if isinstance(error, ValueError) and str(error) == "state_archive_cryptographic_operation_failed":
        return "private_store_key_or_cipher_validation_failed"
    return "private_persistence_failed_no_reset_or_fallback"


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def path_ok(name):
    if not isinstance(name, str):
        return False
    p = PurePosixPath(name)
    return (str(p) == name and not p.is_absolute()
            and bool(p.parts) and not {".", ".."}.intersection(p.parts)
            and not any(ord(c) < 32 or c == "\\" for c in name))


def inventory(root):
    if not root.is_dir() or root.is_symlink():
        raise StoreError("private_state_directory_required")
    result = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink() or not (p.is_dir() or p.is_file()):
            raise StoreError("private_state_non_regular_entry")
        if p.is_dir():
            continue
        name = p.relative_to(root).as_posix()
        if p.name.startswith(".env") or p.suffix in {".pem", ".key", ".p12", ".pfx"}:
            raise StoreError("private_state_key_or_environment_file_rejected")
        if not path_ok(name) or p.stat().st_size > MAX_FILE:
            raise StoreError("private_state_path_or_size_limit")
        result[name] = {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
        if len(result) > MAX_FILES:
            raise StoreError("private_state_file_count_limit")
    if not set(CORE).issubset(result):
        raise StoreError("private_state_required_history_missing")
    return result


def validate_state(root):
    files = inventory(root)
    registry = read_json(root / CORE[0])
    ids = [r["source_id"] for r in registry["sources"]]
    if not ids or len(ids) != len(set(ids)) or any(not isinstance(s, str) or not s for s in ids):
        raise StoreError("private_state_source_identity_invalid")
    state = read_json(root / "state.json")
    if state.get("schema_version") != 1 or not isinstance(state.get("snapshots"), dict):
        raise StoreError("private_state_schema_invalid")
    # Migration belongs to the existing reviewed importer, never to this transport.
    candidates = ledger.load_ledger(root / "candidate_ledger.json", require_existing=True)
    if candidates != read_json(root / "candidate_ledger.json"):
        raise StoreError("private_state_requires_explicit_schema_migration")
    if any(t["source_id"] not in ids for t in candidates["tasks"].values()):
        raise StoreError("private_state_unknown_candidate_source")
    journal = read_json(root / "quality_journal.json")
    reviews.validate_journal(journal)
    if set(journal["required_source_ids"]) != set(ids):
        raise StoreError("private_state_review_source_set_mismatch")
    return files


def extends(new_root, old_root):
    new, old = validate_state(new_root), validate_state(old_root)
    # Exact registry bytes here. Source-set/config changes require a separate reviewed migration.
    if new[CORE[0]] != old[CORE[0]]:
        raise StoreError("private_state_registry_changed_requires_migration")
    n, o = (read_json(root / "candidate_ledger.json") for root in (new_root, old_root))
    if (n["revision"] < o["revision"] or n["events"][:len(o["events"])] != o["events"]
            or not set(o["tasks"]).issubset(n["tasks"])):
        raise StoreError("private_state_candidate_history_loss")
    for key, previous in o["tasks"].items():
        current = n["tasks"][key]
        for identity in ("candidate_id", "source_id", "endpoint_id", "candidate_key"):
            if current.get(identity) != previous.get(identity):
                raise StoreError("private_state_candidate_identity_changed")
        for history, value in previous.items():
            if history.endswith("history") and isinstance(value, list) and current.get(history, [])[:len(value)] != value:
                raise StoreError("private_state_candidate_review_history_loss")
    if not reviews.is_extension(read_json(new_root / "quality_journal.json"), read_json(old_root / "quality_journal.json")):
        raise StoreError("private_state_review_history_loss")
    # Old evidence is immutable. Only root runtime files may change; historical
    # files live in subdirectories and cannot disappear or be silently replaced.
    for name, entry in old.items():
        if name == "http-responses/index.jsonl" and name in new:
            if not (new_root / name).read_bytes().startswith((old_root / name).read_bytes()):
                raise StoreError("private_state_response_index_history_loss")
            continue
        if name not in new or ("/" in name and new[name] != entry):
            raise StoreError("private_state_historical_file_loss_or_rewrite")
    return new


class S3:
    """AWS S3 only; no user supplied endpoint or redirects with credentials."""
    def __init__(self, bucket, prefix, owner, client=None):
        if (not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket)
                or not re.fullmatch(r"[0-9]{12}", owner) or not path_ok(prefix)
                or not re.fullmatch(r"[A-Za-z0-9/_-]+", prefix)):
            raise StoreError("private_store_destination_invalid")
        if client is None:
            import boto3
            from botocore.config import Config
            client = boto3.client("s3", config=Config(retries={"mode": "standard", "max_attempts": 3}))
        self.client, self.bucket, self.prefix, self.owner = client, bucket, prefix, owner

    def preflight(self):
        args = {"Bucket": self.bucket, "ExpectedBucketOwner": self.owner}
        c = self.client
        block = c.get_public_access_block(**args)["PublicAccessBlockConfiguration"]
        if any(block.get(k) is not True for k in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")):
            raise StoreError("private_store_public_access_block_required")
        if c.get_bucket_policy_status(**args).get("PolicyStatus", {}).get("IsPublic") is not False:
            raise StoreError("private_store_nonpublic_policy_required")
        if c.get_bucket_versioning(**args).get("Status") != "Enabled":
            raise StoreError("private_store_versioning_required")
        rules = c.get_bucket_ownership_controls(**args).get("OwnershipControls", {}).get("Rules", [])
        if rules != [{"ObjectOwnership": "BucketOwnerEnforced"}]:
            raise StoreError("private_store_owner_enforced_required")
        try:
            lifecycle = c.get_bucket_lifecycle_configuration(**args)
        except Exception as error:
            if getattr(error, "response", {}).get("Error", {}).get("Code") != "NoSuchLifecycleConfiguration":
                raise StoreError("private_store_lifecycle_check_failed") from None
            lifecycle = {}
        for rule in lifecycle.get("Rules", []):
            if rule.get("Status") == "Enabled" and any(k in rule for k in (
                    "Expiration", "NoncurrentVersionExpiration", "Transitions", "NoncurrentVersionTransitions")):
                raise StoreError("private_store_expiration_or_archive_transition_requires_review")

    def key(self, key):
        if key != "latest.json" and not re.fullmatch(r"objects/[0-9a-f]{64}\.cms", key):
            raise StoreError("private_store_object_key_invalid")
        return self.prefix + "/" + key

    def get(self, key, version=None):
        args = dict(Bucket=self.bucket, Key=self.key(key), ExpectedBucketOwner=self.owner)
        if version:
            args["VersionId"] = version
        try:
            r = self.client.get_object(**args)
        except Exception as e:
            code = getattr(e, "response", {}).get("Error", {}).get("Code")
            if code in {"NoSuchKey", "NoSuchVersion"}:
                return None
            raise StoreError("private_store_read_failed") from None
        with r["Body"] as stream:
            data = stream.read(MAX_FILE + MAX_INDEX + 1024 * 1024)
            if stream.read(1):
                raise StoreError("private_store_object_size_limit")
        version_id = r.get("VersionId")
        if not version_id or version_id == "null" or not r.get("ETag"):
            raise StoreError("private_store_version_metadata_missing")
        return data, r["ETag"], version_id

    def put(self, key, data, etag=None):
        args = dict(Bucket=self.bucket, Key=self.key(key), ExpectedBucketOwner=self.owner,
                    Body=data, ServerSideEncryption="AES256", ContentType="application/octet-stream")
        args.update({"IfMatch": etag} if etag is not None else {"IfNoneMatch": "*"})
        try:
            r = self.client.put_object(**args)
        except Exception:
            # Includes conflict and ambiguous timeout; coordinator checks the pointer.
            raise StoreError("private_store_write_failed_or_conflict") from None
        if not r.get("VersionId") or r["VersionId"] == "null":
            raise StoreError("private_store_version_metadata_missing")
        return r["VersionId"]


class Vault:
    def __init__(self, backend, certificate):
        self.backend, self.certificate = backend, certificate
        self.cert_hash = sha(certificate.read_bytes())

    def encrypt(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); (p / "input").mkdir(mode=0o700)
            (p / "input/payload").write_bytes(data)
            crypto.encrypt_directory(p / "input", p / "out.cms", self.certificate)
            return (p / "out.cms").read_bytes()

    def decrypt(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); (p / "in.cms").write_bytes(data)
            crypto.decrypt_archive(p / "in.cms", p / "out", self.certificate,
                                   max_extracted_bytes=MAX_FILE, max_members=2)
            files = list((p / "out").rglob("*"))
            if {f.relative_to(p / "out").as_posix() for f in files} != {"state", "state/payload"}:
                raise StoreError("private_store_envelope_layout_invalid")
            data = (p / "out/state/payload").read_bytes()
            if len(data) > MAX_FILE:
                raise StoreError("private_store_plaintext_size_limit")
            return data

    def object(self, data):
        cipher = self.encrypt(data)
        key = f"objects/{sha(cipher)}.cms"
        version = self.backend.put(key, cipher)
        result = self.backend.get(key, version)
        if result is None or result[0] != cipher:
            raise StoreError("private_store_readback_failed")
        return {"key": key, "version_id": version, "cipher_sha256": sha(cipher)}

    def open_object(self, entry):
        if (not isinstance(entry, dict) or not HASH.fullmatch(str(entry.get("cipher_sha256", "")))
                or entry.get("key") != f"objects/{entry['cipher_sha256']}.cms"
                or not isinstance(entry.get("version_id"), str) or not entry["version_id"]):
            raise StoreError("private_store_object_reference_invalid")
        result = self.backend.get(entry["key"], entry["version_id"])
        if result is None or sha(result[0]) != entry["cipher_sha256"]:
            raise StoreError("private_store_object_missing_or_corrupt")
        return self.decrypt(result[0])

    def head(self):
        r = self.backend.get("latest.json")
        if r is None:
            return None
        value = json.loads(r[0])
        if (set(value) != {"format", "sequence", "parent_sha256", "certificate_sha256", "inventory"}
                or value["format"] != FORMAT or type(value["sequence"]) is not int or value["sequence"] < 1
                or (value["parent_sha256"] is not None and not HASH.fullmatch(str(value["parent_sha256"])))
                or value["certificate_sha256"] != self.cert_hash):
            raise StoreError("private_store_pointer_or_recipient_mismatch")
        return value, r[1], r[2], sha(r[0])

    def unpack(self, head, destination):
        data = self.open_object(head[0]["inventory"])
        if len(data) > MAX_INDEX:
            raise StoreError("private_store_inventory_size_limit")
        manifest = json.loads(data)
        if (set(manifest) != {"format", "sequence", "parent_sha256", "files"}
                or any(manifest[k] != head[0][k] for k in ("format", "sequence", "parent_sha256"))
                or not isinstance(manifest["files"], dict) or len(manifest["files"]) > MAX_FILES):
            raise StoreError("private_store_inventory_binding_invalid")
        destination.mkdir(mode=0o700)
        for name, entry in manifest["files"].items():
            if (not path_ok(name) or set(entry) != {"sha256", "bytes", "object"}
                    or not HASH.fullmatch(str(entry["sha256"])) or type(entry["bytes"]) is not int
                    or not 0 <= entry["bytes"] <= MAX_FILE):
                raise StoreError("private_store_file_reference_invalid")
            data = self.open_object(entry["object"])
            if sha(data) != entry["sha256"] or len(data) != entry["bytes"]:
                raise StoreError("private_store_plaintext_hash_mismatch")
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            target.write_bytes(data); target.chmod(0o600)
        validate_state(destination)
        return manifest

    def restore(self, destination, receipt):
        self.backend.preflight()
        if destination.exists() or receipt.exists():
            raise StoreError("private_store_restore_destination_must_not_exist")
        head = self.head()
        if head is None:
            raise StoreError("private_store_missing_head_no_automatic_bootstrap")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
            staged = Path(tmp) / "restored"
            self.unpack(head, staged)
            # Only expose a completely verified snapshot to the caller.
            staged.replace(destination)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_bytes(encoded({"head_sha256": head[3], "sequence": head[0]["sequence"]}))
        receipt.chmod(0o600)
        return {"status": "restored", "sequence": head[0]["sequence"]}

    def save(self, source, receipt=None, bootstrap=False):
        self.backend.preflight()
        current = self.head()
        # Prove the existing key works BEFORE creating any new stored objects.
        if self.decrypt(self.encrypt(b"TERRAFAR private-store key preflight")) != b"TERRAFAR private-store key preflight":
            raise StoreError("private_store_key_preflight_failed")
        files = validate_state(source)
        if current is None:
            if not bootstrap:
                raise StoreError("private_store_missing_head_no_automatic_bootstrap")
            previous, sequence, parent = {}, 1, None
        else:
            if bootstrap or receipt is None or read_json(receipt) != {"head_sha256": current[3], "sequence": current[0]["sequence"]}:
                raise StoreError("private_store_stale_or_missing_restore_receipt")
            with tempfile.TemporaryDirectory() as tmp:
                old = Path(tmp) / "old"
                prior = self.unpack(current, old)
                extends(source, old)
            previous, sequence, parent = prior["files"], current[0]["sequence"] + 1, current[3]
        entries = {}
        for name, info in files.items():
            old = previous.get(name)
            data = (source / name).read_bytes()
            if sha(data) != info["sha256"] or len(data) != info["bytes"]:
                raise StoreError("private_state_changed_during_capture")
            obj = old["object"] if old and all(old[k] == info[k] for k in info) else self.object(data)
            entries[name] = {**info, "object": obj}
        if inventory(source) != files:
            raise StoreError("private_state_changed_during_capture")
        manifest = {"format": FORMAT, "sequence": sequence, "parent_sha256": parent, "files": entries}
        if len(encoded(manifest)) > MAX_INDEX:
            raise StoreError("private_store_inventory_size_limit")
        pointer = {k: manifest[k] for k in ("format", "sequence", "parent_sha256")}
        pointer.update(certificate_sha256=self.cert_hash, inventory=self.object(encoded(manifest)))
        data = encoded(pointer)
        try:
            self.backend.put("latest.json", data, current[1] if current else None)
        except StoreError:
            # A network timeout after commit must not replay the transaction or
            # erase a newer review. Exact readback is the only safe acknowledgement.
            r = self.backend.get("latest.json")
            if r is None or r[0] != data:
                raise StoreError("private_store_commit_unconfirmed_stop_without_rollback") from None
        r = self.backend.get("latest.json")
        if r is None or r[0] != data:
            raise StoreError("private_store_commit_readback_changed")
        return {"status": "committed", "sequence": sequence, "head_sha256": sha(data), "files": len(files)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("restore", "save", "bootstrap"))
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--certificate", type=Path, default=reviews.RECIPIENT_CERTIFICATE)
    args = p.parse_args()
    try:
        # No credentials or details in stdout/stderr. Tests exercise Vault directly.
        if (os.environ.get("TERRAFAR_PRIVATE_STORAGE_APPROVED") != "true"
                or os.environ.get("GITHUB_REPOSITORY_VISIBILITY") != "private"):
            raise StoreError("private_store_owner_approval_and_private_runner_required")
        if args.command == "bootstrap" and os.environ.get("TERRAFAR_PRIVATE_BOOTSTRAP_APPROVED") != "true":
            raise StoreError("private_store_explicit_bootstrap_approval_required")
        backend = S3(os.environ["TERRAFAR_STATE_BUCKET"], os.environ["TERRAFAR_STATE_PREFIX"], os.environ["TERRAFAR_AWS_ACCOUNT_ID"])
        vault = Vault(backend, args.certificate)
        if args.command == "restore":
            if args.receipt is None:
                raise StoreError("private_store_restore_receipt_required")
            result = vault.restore(args.directory, args.receipt)
        else:
            result = vault.save(args.directory, args.receipt, args.command == "bootstrap")
        print(json.dumps(result, sort_keys=True))
    except Exception as error:
        # Exception strings from files, crypto and cloud SDKs can contain private data.
        print(json.dumps({"status": "blocked", "reason": safe_reason(error)}))
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
