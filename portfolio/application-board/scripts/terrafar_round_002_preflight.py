#!/usr/bin/env python3
"""Probe one control and four frozen sample domains before any sample page fetch."""
from __future__ import annotations

import argparse
import importlib.util
import ipaddress
import json
import socket
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "portfolio/application-board"
AUDIT_PATH = APP / "scripts/terrafar_source_audit.py"
REGISTRY_PATH = APP / "maintenance/terrafar-source-audit/registry/source_registry.json"
DEFAULT_SAMPLE = APP / "maintenance/terrafar-source-audit/round_002/sample_manifest.json"

spec = importlib.util.spec_from_file_location("terrafar_source_audit", AUDIT_PATH)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


def timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ordinary_robots(url: str, timeout: int, addresses: list[str]) -> dict:
    parts = urllib.parse.urlsplit(url)
    target = urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    target_parts = urllib.parse.urlsplit(target)
    request_target = target_parts.path or "/"
    robots_path = (parts.path or "/") + (("?" + parts.query) if parts.query else "")
    connection = None
    try:
        connection = audit.pinned_connection(target_parts, addresses, timeout)
        connection.request("GET", request_target, headers={"User-Agent": audit.UA, "Accept": "text/plain,*/*;q=0.5"})
        response = connection.getresponse()
        body = response.read(512_001)
        return {
            "status": response.status,
            "request_attempted": True,
            "location": response.getheader("Location"),
            "redirect_followed": False,
            "body_bytes_read": len(body),
            "body_sha256": audit.sha(body),
            "robots_allows_source_path": not audit.parse_robots(body.decode("utf-8", "replace"), robots_path) if response.status == 200 and len(body) <= 512_000 else None,
            "tls": "default_certificate_validation_with_dns_ip_pinning",
        }
    except Exception as error:  # Do not expose proxy config, request headers, or credentials.
        return {"status": None, "request_attempted": True, "error_type": type(error).__name__, "redirect_followed": False, "tls": "default_certificate_validation_with_dns_ip_pinning"}
    finally:
        if connection is not None:
            connection.close()


def dns_record(host: str) -> dict:
    try:
        addresses = sorted({item[4][0].split("%")[0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
        classified = [{"address": value, "is_global": ipaddress.ip_address(value).is_global} for value in addresses]
        return {"addresses": classified, "error_type": None}
    except Exception as error:
        return {"addresses": [], "error_type": type(error).__name__}


def probe(source_id: str, url: str, timeout: int, proxy_configured: bool = False) -> dict:
    host = urllib.parse.urlsplit(url).hostname
    resolved = dns_record(host)
    non_global = any(not item["is_global"] for item in resolved["addresses"])
    no_addresses = not resolved["addresses"]
    # Do not send even a robots request to a non-global/unresolved target.
    if non_global or no_addresses:
        ordinary = {"status": None, "request_attempted": False, "skipped": "non_global_or_unresolved_dns", "redirect_followed": False}
    elif proxy_configured:
        ordinary = {"status": None, "request_attempted": False, "skipped": "proxy_configured_unverified_by_address_pinning", "redirect_followed": False}
    else:
        ordinary = ordinary_robots(url, timeout, [item["address"] for item in resolved["addresses"]])
    runner_result = audit.robots_gate(url, timeout=timeout, rate=0.25, retries=0)
    return {
        "source_id": source_id,
        "host": host,
        "url": url,
        "dns": resolved,
        "runner_guard": "private_or_non_global_address" if non_global else "destination_dns_resolution_failed" if no_addresses else "public_address_set",
        "ordinary_https_robots": ordinary,
        "runner_robots": runner_result,
        "source_page_request": {"attempted": False, "body_bytes": 0, "reason": "preflight_only_no_target_page_fetch"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-manifest", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()

    sample = json.loads(args.sample_manifest.read_text(encoding="utf-8"))
    source_ids = sample.get("preflight_source_ids", [])
    if len(source_ids) != 4 or len(set(source_ids)) != 4:
        raise ValueError("preflight_requires_exactly_four_distinct_sample_source_ids")
    rows = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["sources"]
    by_id = {row["source_id"]: row for row in rows}
    unknown = [source_id for source_id in source_ids if source_id not in by_id]
    if unknown:
        raise ValueError("preflight_source_id_missing:" + ",".join(unknown))

    targets = [("connectivity_control", sample["preflight_control_url"])]
    targets.extend((source_id, by_id[source_id]["canonical_url"]) for source_id in source_ids)
    if len({urllib.parse.urlsplit(url).hostname for _, url in targets}) != 5:
        raise ValueError("preflight_must_cover_exactly_five_distinct_hosts")

    allowed_hosts = sorted({urllib.parse.urlsplit(url).hostname.lower().rstrip(".") for _, url in targets})
    audit.configure_request_budget(10)
    audit.configure_request_host_scope(allowed_hosts)
    proxies = urllib.request.getproxies()
    results = [probe(source_id, url, args.timeout, proxy_configured=bool(proxies)) for source_id, url in targets]
    source_results = results[1:]
    transport_responses = sum(item["runner_robots"].get("status") is not None for item in source_results)
    address_guard_blocks = sum(item["runner_robots"].get("reason") == "runner_safety_guard_block" and item["runner_robots"].get("error_detail") in {"private_or_non_global_address", "destination_dns_resolution_failed", "invalid_dns_address", "non_public_http_url"} for item in source_results)
    transport_configuration_blocks = sum(item["runner_robots"].get("error_detail") == "proxy_configured_unverified_by_pinned_transport" for item in source_results)
    control_reached = results[0]["runner_robots"].get("status") is not None
    systemic = address_guard_blocks >= 3 or (not control_reached and transport_responses == 0)
    passed = not systemic and control_reached and transport_responses >= 2
    record = {
        "schema_version": 1,
        "run_id": "round002-preflight-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "started_at": timestamp(),
        "finished_at": timestamp(),
        "python_version": sys.version.split()[0],
        "registry_sha256": audit.sha(REGISTRY_PATH.read_bytes()),
        "sample_manifest_sha256": audit.sha(args.sample_manifest.read_bytes()),
        "proxy": {"configured": bool(proxies), "schemes": sorted(proxies)},
        "request_scope": {"distinct_hosts": 5, "allowed_hostnames": allowed_hosts, "redirects_outside_allowlist_rejected": True, "ordinary_https_request_limit": 5, "ordinary_https_attempts": sum(item["ordinary_https_robots"].get("request_attempted", False) for item in results), "runner_http_request_budget": audit.http_request_budget_stats(), "maximum_total_http_requests": 15, "control_hosts": 1, "registered_source_hosts": 4, "target_page_requests": 0, "retries": 0, "concurrency": 1},
        "environment_preflight_passed": passed,
        "systemic_environment_block": systemic,
        "runner_transport_responses_from_sample_hosts": transport_responses,
        "address_guard_blocks_from_sample_hosts": address_guard_blocks,
        "runner_transport_configuration_blocks_from_sample_hosts": transport_configuration_blocks,
        "results": results,
        "decision": "continue_to_ten_source_smoke" if passed else "circuit_break_before_sample_fetch",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("run_id", "environment_preflight_passed", "systemic_environment_block", "runner_transport_responses_from_sample_hosts", "address_guard_blocks_from_sample_hosts", "runner_transport_configuration_blocks_from_sample_hosts", "decision")}, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
