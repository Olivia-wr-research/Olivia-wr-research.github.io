#!/usr/bin/env python3
"""Encrypt and restore private TERRAFAR state for repository-readable Actions artifacts."""
from __future__ import annotations

import argparse
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

MAGIC = b"TERRAFAR-CMS-STATE-V1\n"
DEFAULT_KEY_ENV = "TERRAFAR_STATE_DECRYPTION_KEY"


def _run_openssl(args: list[str], *, input_bytes: bytes | None = None) -> bytes:
    try:
        completed = subprocess.run(
            ["openssl", "cms", *args], input=input_bytes, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError("openssl_cms_unavailable") from error
    if completed.returncode != 0:
        raise ValueError("state_archive_cryptographic_operation_failed")
    return completed.stdout


def _tar_bytes(source_dir: Path) -> bytes:
    if not source_dir.is_dir() or source_dir.is_symlink():
        raise ValueError("state_archive_source_must_be_a_regular_directory")
    for path in source_dir.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("state_archive_source_contains_non_regular_entry")
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        archive.add(source_dir, arcname="state", recursive=True)
    return buffer.getvalue()


def validate_ciphertext(ciphertext: bytes) -> None:
    """Validate the CMS envelope without exposing plaintext or requiring its key."""
    if not ciphertext.startswith(MAGIC):
        raise ValueError("state_archive_format_unsupported")
    der = ciphertext[len(MAGIC):]
    # CMS SignedData/Data can contain plaintext. Require the outer content type
    # to be EnvelopedData (1.2.840.113549.1.7.3), not merely any valid CMS object.
    if len(der) < 2 or der[0] != 0x30:
        raise ValueError("state_archive_requires_enveloped_data")
    length_octets = der[1] & 0x7f if der[1] & 0x80 else 0
    if der[1] == 0x80 or length_octets > 8 or len(der) < 2 + length_octets:
        raise ValueError("state_archive_requires_definite_der")
    start = 2 + length_octets
    declared = int.from_bytes(der[2:start], "big") if length_octets else der[1]
    if declared != len(der) - start or der[start:start + 11] != bytes.fromhex("06092a864886f70d010703"):
        raise ValueError("state_archive_requires_enveloped_data")
    _run_openssl(["-cmsout", "-noout", "-inform", "DER"], input_bytes=der)


def encrypt_directory(source_dir: Path, output: Path, recipient_certificate: Path) -> dict:
    if not recipient_certificate.is_file():
        raise FileNotFoundError("state_archive_recipient_certificate_missing")
    plaintext = _tar_bytes(source_dir)
    cms = _run_openssl(
        ["-encrypt", "-aes-256-cbc", "-binary", "-outform", "DER", str(recipient_certificate)],
        input_bytes=plaintext,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    temp.write_bytes(MAGIC + cms)
    os.chmod(temp, 0o600)
    temp.replace(output)
    return {"encrypted_bytes": output.stat().st_size, "plaintext_archive_bytes": len(plaintext)}


def _private_key_from_env(key_env: str) -> Path:
    value = os.environ.get(key_env)
    if not value:
        raise ValueError(f"required_decryption_secret_missing:{key_env}")
    handle = tempfile.NamedTemporaryFile(prefix="terrafar-private-key-", suffix=".pem", delete=False)
    path = Path(handle.name)
    try:
        os.chmod(path, 0o600)
        handle.write(value.encode("utf-8"))
        handle.flush()
    finally:
        handle.close()
    return path


def _safe_extract_state(tar_bytes: bytes, destination: Path) -> int:
    if destination.is_symlink():
        raise ValueError("state_archive_destination_must_be_regular")
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("state_archive_destination_must_be_empty")
    count = 0
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as archive:
        for member in archive.getmembers():
            member_path = PurePosixPath(member.name)
            if member_path.is_absolute() or ".." in member_path.parts or not member_path.parts or member_path.parts[0] != "state":
                raise ValueError("state_archive_path_rejected")
            target = destination.joinpath(*member_path.parts)
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError("state_archive_path_rejected")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise ValueError("state_archive_non_regular_file_rejected")
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("state_archive_member_unreadable")
            with stream, target.open("xb") as out:
                shutil.copyfileobj(stream, out)
            os.chmod(target, 0o600)
            count += 1
    if count == 0:
        raise ValueError("state_archive_empty")
    return count


def decrypt_archive(input_path: Path, destination: Path, recipient_certificate: Path,
                    key_env: str = DEFAULT_KEY_ENV) -> dict:
    if not recipient_certificate.is_file():
        raise FileNotFoundError("state_archive_recipient_certificate_missing")
    ciphertext = input_path.read_bytes()
    validate_ciphertext(ciphertext)
    key_path = _private_key_from_env(key_env)
    try:
        plaintext = _run_openssl(
            ["-decrypt", "-binary", "-inform", "DER", "-recip", str(recipient_certificate), "-inkey", str(key_path)],
            input_bytes=ciphertext[len(MAGIC):],
        )
    finally:
        key_path.unlink(missing_ok=True)
    file_count = _safe_extract_state(plaintext, destination)
    return {"restored_files": file_count, "encrypted_bytes": len(ciphertext)}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    enc = sub.add_parser("encrypt")
    enc.add_argument("--source-dir", type=Path, required=True)
    enc.add_argument("--output", type=Path, required=True)
    enc.add_argument("--recipient-certificate", type=Path, required=True)
    dec = sub.add_parser("decrypt")
    dec.add_argument("--input", type=Path, required=True)
    dec.add_argument("--destination", type=Path, required=True)
    dec.add_argument("--recipient-certificate", type=Path, required=True)
    dec.add_argument("--key-env", default=DEFAULT_KEY_ENV)
    args = parser.parse_args()
    if args.command == "encrypt":
        result = encrypt_directory(args.source_dir, args.output, args.recipient_certificate)
    else:
        result = decrypt_archive(args.input, args.destination, args.recipient_certificate, args.key_env)
    print(__import__("json").dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
