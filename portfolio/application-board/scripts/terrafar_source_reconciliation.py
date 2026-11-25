#!/usr/bin/env python3
"""Build a privacy-minimized source-to-run reconciliation from existing TERRAFAR records."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
MAINT = APP / "maintenance/terrafar-source-audit"
REGISTRY = MAINT / "registry/source_registry.json"
SEEDS = MAINT / "registry/seed_mapping.json"
OCCURRENCES = MAINT / "registry/occurrence_disposition.json"
CATALOG = MAINT / "adapter_catalog.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def next_action(outcome: str, reason: str, adapter_present: bool) -> str:
    if outcome == "needs_endpoint":
        return "定位正式机会栏目或招生入口，建立明确机构、类型、筛选和分页范围的适配器"
    if outcome == "partial":
        return "补齐分页/列表完整性证据或有效语义基线；当前不得记为无更新"
    if outcome == "blocked":
        return "保留来源并遵守站点访问限制；仅在官方允许的路径恢复检查"
    if outcome == "failed":
        return "保留失败状态，按DNS/TLS/HTTP/超时原因有界重试并继续检查其他来源"
    if outcome == "not_attempted":
        return "保留未执行状态，等待后续轮转，不记为无更新"
    if outcome in {"checked_changed", "checked_unchanged", "checked_empty"}:
        return "已完成登记适配器明确限定的范围；不外推为机构全站覆盖"
    if adapter_present:
        return "核对适配器目标与登记范围，保留待处理状态"
    return "仅有来源登记；继续定位官方具体栏目"


def result_network_metrics(result: dict) -> dict:
    endpoints=result.get("endpoints") or []
    target_attempts=[attempt for endpoint in endpoints for attempt in endpoint.get("attempts",[])
                     if attempt.get("endpoint")!="robots.txt"]
    robots_attempts=[attempt for endpoint in endpoints
                     for attempt in (endpoint.get("robots") or {}).get("attempts",[])]
    target_sent=[attempt for attempt in target_attempts if attempt.get("request_sent")]
    target_responses=[attempt for attempt in target_attempts if attempt.get("http_status") is not None]
    robots_sent=[attempt for attempt in robots_attempts if attempt.get("request_sent")]
    counts_exact=all("http_request_count" in attempt and attempt.get("http_request_count_exact") is True
                      for attempt in target_attempts+robots_attempts)
    return {
        "target_http_requests":sum(int(attempt.get("http_request_count",bool(attempt.get("request_sent")))) for attempt in target_attempts),
        "target_http_responses":len(target_responses)+sum(len(attempt.get("redirect_chain") or []) for attempt in target_attempts),
        "robots_http_requests":sum(int(attempt.get("http_request_count",bool(attempt.get("request_sent")))) for attempt in robots_attempts),
        "robots_http_responses":sum(attempt.get("http_status") is not None for attempt in robots_attempts)+sum(len(attempt.get("redirect_chain") or []) for attempt in robots_attempts),
        "target_request_sent_attempt_rows":len(target_sent),
        "robots_request_sent_attempt_rows":len(robots_sent),
        "http_request_counts_exact":counts_exact,
        "target_response_bodies_with_bytes":sum(int(endpoint.get("response_body_bytes") or 0)>0 for endpoint in endpoints),
        "target_response_body_bytes":sum(int(endpoint.get("response_body_bytes") or 0) for endpoint in endpoints),
        "response_body_size_fields_recorded":sum("response_body_bytes" in endpoint for endpoint in endpoints),
        "response_body_size_counts_exact":all("response_body_bytes" in endpoint for endpoint in endpoints),
    }


def build_reconciliation(registry: dict, seed_mapping: dict, occurrences: dict, catalog: dict,
                         source_checks: list[dict], candidate_ledger: dict,
                         previous_ledger: dict | None = None) -> tuple[list[dict], dict]:
    sources = {row["source_id"]: row for row in registry.get("sources", [])}
    checks = {row["source_id"]: row for row in source_checks}
    overrides = catalog.get("source_overrides", {})
    occurrence_urls: dict[str, list[str]] = {}
    for occurrence in occurrences.get("occurrences", []):
        if occurrence.get("disposition") != "retained_or_mapped_source":
            continue
        seed_id = occurrence.get("source_id")
        original_url = occurrence.get("original_url")
        if seed_id and original_url:
            occurrence_urls.setdefault(seed_id, [])
            if original_url not in occurrence_urls[seed_id]:
                occurrence_urls[seed_id].append(original_url)

    tasks_by_source: dict[str, Counter] = {}
    tasks = candidate_ledger.get("tasks", {})
    for task in tasks.values():
        source_id = task.get("source_id")
        tasks_by_source.setdefault(source_id, Counter())[task.get("status", "unknown")] += 1

    rows = []
    for seed in seed_mapping.get("mappings", []):
        seed_id = seed["seed_source_id"]
        source_id = seed["registry_source_id"]
        source = sources.get(source_id, {})
        result = checks.get(source_id, {})
        endpoints = result.get("endpoints") or source.get("monitor_endpoints") or []
        source_override = overrides.get(source_id, {})
        adapter_names = list(dict.fromkeys(
            endpoint.get("adapter") or source.get("adapter") or ""
            for endpoint in endpoints if endpoint.get("adapter") or source.get("adapter")
        ))
        monitor_urls = list(dict.fromkeys(
            endpoint.get("url", "") for endpoint in endpoints if endpoint.get("url")
        ))
        endpoint_scopes = []
        for endpoint in endpoints:
            scope = endpoint.get("scope")
            if scope:
                endpoint_scopes.append({
                    "endpoint_id": endpoint.get("endpoint_id"),
                    "url": endpoint.get("url"),
                    "adapter": endpoint.get("adapter"),
                    "scope": scope,
                    "outcome": endpoint.get("outcome"),
                })
        status_codes=[]
        for endpoint in endpoints:
            target_attempts=[attempt for attempt in endpoint.get("attempts",[])
                             if attempt.get("endpoint")!="robots.txt"]
            codes=[attempt.get("http_status") for attempt in target_attempts]
            codes.extend(hop.get("status") for attempt in target_attempts
                         if attempt.get("endpoint")!="robots.txt"
                         for hop in attempt.get("redirect_chain",[]))
            if not target_attempts:
                codes.append(endpoint.get("http_status"))
            for code in codes:
                if code is not None and code not in status_codes: status_codes.append(code)
        reason = result.get("reason") or ""
        ledger_counts = tasks_by_source.get(source_id, Counter())
        network=result_network_metrics(result)
        rows.append({
            "seed_source_id": seed_id,
            "registry_source_id": source_id,
            "mapping_decision": seed.get("decision", "unknown"),
            "original_directory_urls": json.dumps(occurrence_urls.get(seed_id, []), ensure_ascii=False),
            "seed_canonical_url": seed.get("canonical_url", ""),
            "registry_active": str(bool(source.get("active"))).lower() if source else "missing",
            "registry_enabled_for_daily_audit": str(bool(source.get("enabled_for_daily_audit"))).lower() if source else "missing",
            "verification_status": source.get("verification_status", "missing"),
            "source_layer": source.get("source_layer", ""),
            "page_kind": source.get("page_kind", ""),
            "monitor_endpoints": json.dumps(monitor_urls, ensure_ascii=False),
            "source_role": json.dumps({
                "source_name": source.get("name", ""),
                "source_layer": source.get("source_layer", ""),
                "page_kind": source.get("page_kind", ""),
            }, ensure_ascii=False),
            "adapter": json.dumps(adapter_names, ensure_ascii=False),
            "adapter_scope": json.dumps(endpoint_scopes or {
                "catalog_filter": source_override.get("filter"),
                "catalog_opportunity_type": source_override.get("opportunity_type"),
                "catalog_pagination": source_override.get("pagination"),
                "catalog_completeness_rule": source_override.get("completeness_rule"),
            }, ensure_ascii=False),
            "latest_run_id": result.get("run_id", ""),
            "latest_outcome": result.get("outcome", "not_observed"),
            "worker_dispatched": str(bool(result.get("attempted"))).lower(),
            **network,
            "actual_http_statuses": json.dumps(status_codes),
            "candidate_observations_this_run": int(result.get("candidate_count") or 0),
            "ledger_pending_tasks": ledger_counts.get("pending", 0),
            "ledger_verified_tasks": ledger_counts.get("verified", 0),
            "ledger_failed_tasks": ledger_counts.get("verification_failed", 0),
            "ledger_insufficient_evidence_tasks": ledger_counts.get("insufficient_evidence", 0),
            "content_complete": str(bool(result.get("content_complete"))).lower(),
            "target_validated": str(bool(result.get("target_validated"))).lower(),
            "human_reviewed_count": 0,
            "release_allowed_count": 0,
            "formal_data_write": "false",
            "frontend_visible_from_this_run": "false",
            "next_action": next_action(result.get("outcome", "not_observed"), reason, bool(adapter_names)),
            "technical_reason": reason,
        })

    status_counts = Counter(row.get("outcome", "unknown") for row in source_checks)
    result_ids=[row.get("source_id") for row in source_checks]
    source_network=[result_network_metrics(row) for row in source_checks]
    ledger_counts = Counter(task.get("status", "unknown") for task in tasks.values())
    previous_ids = set((previous_ledger or {}).get("tasks", {}))
    current_ids = set(tasks)
    complete = sum(status_counts.get(status, 0) for status in (
        "checked_changed", "checked_unchanged", "checked_empty"
    ))
    funnel_by_explicit_type: dict[str, Counter] = {}
    for source_id, source in sources.items():
        declared_type = overrides.get(source_id, {}).get("opportunity_type") or "unclassified_or_unknown"
        result = checks.get(source_id, {})
        bucket = funnel_by_explicit_type.setdefault(declared_type, Counter())
        bucket["registered_sources"] += 1
        bucket[f"outcome:{result.get('outcome', 'not_observed')}"] += 1
        bucket["sources_with_target_http_request"] += int(result_network_metrics(result)["target_http_requests"] > 0)
        bucket["candidate_observations"] += int(result.get("candidate_count") or 0)
    funnel_by_region: dict[str, Counter] = {"unclassified_or_unknown": Counter()}
    for source_id in sources:
        result = checks.get(source_id, {})
        bucket = funnel_by_region["unclassified_or_unknown"]
        bucket["registered_sources"] += 1
        bucket[f"outcome:{result.get('outcome', 'not_observed')}"] += 1
        bucket["sources_with_target_http_request"] += int(result_network_metrics(result)["target_http_requests"] > 0)
        bucket["candidate_observations"] += int(result.get("candidate_count") or 0)
    worker_started=sum(bool(row.get("attempted")) for row in source_checks)
    target_requested=sum(item["target_http_requests"] > 0 for item in source_network)
    candidate_observations=sum(int(row.get("candidate_count") or 0) for row in source_checks)
    verified_tasks=ledger_counts.get("verified", 0)
    open_review_tasks=sum(ledger_counts.get(status, 0) for status in ("pending", "verification_failed", "insufficient_evidence"))
    report = {
        "report_format": "terrafar-source-reconciliation-v1",
        "source_check_run_id": source_checks[0].get("run_id") if source_checks else None,
        "registry_sources": len(registry.get("sources", [])),
        "planned_source_results": len(source_checks),
        "unique_source_results": len(set(result_ids)),
        "registry_sources_without_result": len(set(sources)-set(result_ids)),
        "source_result_ids_outside_registry": len(set(result_ids)-set(sources)),
        "source_status_counts": dict(sorted(status_counts.items())),
        "complete_range_checks": complete,
        "opportunity_flow": {
            "planned_sources": len(source_checks),
            "source_workers_started": worker_started,
            "sources_with_target_http_request": target_requested,
            "complete_configured_scope_checks": complete,
            "raw_candidate_observations": candidate_observations,
            "current_deduplicated_ledger_tasks": len(current_ids),
            "ledger_tasks_with_verified_status": verified_tasks,
            "open_review_or_recheck_tasks": open_review_tasks,
            "human_sample_reviewed_tasks": 0,
            "release_allowed_tasks": 0,
            "formal_site_writes": 0,
            "frontend_records_written_by_this_run": 0,
            "default_interface_visible_records_from_this_run": 0,
            "type_and_region_note": "The registry has no region or opportunity-type classification for most sources. Type buckets below count only explicit adapter catalog declarations; no title, domain, or institution-name inference is used.",
        },
        "source_funnel_by_explicit_adapter_opportunity_type": {
            key: dict(sorted(value.items())) for key, value in sorted(funnel_by_explicit_type.items())
        },
        "source_funnel_by_region": {
            key: dict(sorted(value.items())) for key, value in sorted(funnel_by_region.items())
        },
        "actual_network_counts": {
            "sources_with_target_http_request": sum(item["target_http_requests"] > 0 for item in source_network),
            "target_http_requests": sum(item["target_http_requests"] for item in source_network),
            "target_http_responses": sum(item["target_http_responses"] for item in source_network),
            "robots_http_requests": sum(item["robots_http_requests"] for item in source_network),
            "robots_http_responses": sum(item["robots_http_responses"] for item in source_network),
            "target_request_sent_attempt_rows":sum(item["target_request_sent_attempt_rows"] for item in source_network),
            "robots_request_sent_attempt_rows":sum(item["robots_request_sent_attempt_rows"] for item in source_network),
            "http_request_counts_exact":all(item["http_request_counts_exact"] for item in source_network),
            "target_response_bodies_with_bytes":sum(item["target_response_bodies_with_bytes"] for item in source_network),
            "target_response_body_bytes": sum(item["target_response_body_bytes"] for item in source_network),
            "response_body_size_fields_recorded":sum(item["response_body_size_fields_recorded"] for item in source_network),
            "response_body_size_counts_exact":all(item["response_body_size_counts_exact"] for item in source_network),
        },
        "seed_mapping_rows": len(seed_mapping.get("mappings", [])),
        "seed_source_ids_mapped": len({row["registry_source_id"] for row in rows}),
        "seed_directory_occurrences": len(occurrences.get("occurrences", [])),
        "candidate_observations_this_run": sum(int(row.get("candidate_count") or 0) for row in source_checks),
        "candidate_review_tasks_current": len(current_ids),
        "candidate_review_task_status_counts": dict(sorted(ledger_counts.items())),
        "candidate_review_tasks_added_since_previous_ledger": len(current_ids - previous_ids) if previous_ledger is not None else None,
        "candidate_review_tasks_missing_since_previous_ledger": len(previous_ids - current_ids) if previous_ledger is not None else None,
        "human_reviewed_tasks": 0,
        "release_allowed_tasks": 0,
        "formal_site_writes": 0,
        "opportunity_type_coverage": {
            "source_registry_has_explicit_opportunity_type_field": any(
                "opportunity_type" in source for source in registry.get("sources", [])
            ),
            "configured_adapter_sources": len(catalog.get("source_overrides", {})),
            "explicit_adapter_opportunity_type_counts": dict(sorted(Counter(
                override.get("opportunity_type", "unclassified_or_unknown")
                for override in overrides.values() if override.get("opportunity_type")
            ).items())),
            "unclassified_registry_sources": sum(source_id not in overrides or not overrides[source_id].get("opportunity_type") for source_id in sources),
            "limitation": "Most registry rows do not carry a classified opportunity type; do not infer MSc/PhD/postdoc/faculty/assistant totals from source URL or title.",
        },
        "interpretation": [
            "HTTP request or page retrieval is separate from complete range checking.",
            "Complete status applies only to the explicitly configured adapter scope, not institution-wide coverage.",
            "Candidate observations are not necessarily new unique tasks; persistent task deltas compare stable IDs.",
            "Human review and release authorization were not performed by this report.",
            "No candidate was written to formal site data by this run.",
        ],
    }
    return rows, report


def write_outputs(rows: list[dict], report: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "source_directory_mapping.csv"
    if rows:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (output_dir / "source_funnel_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# TERRAFAR source reconciliation",
        "",
        f"- Run: `{report.get('source_check_run_id') or 'unknown'}`",
        f"- Registry / planned source results: {report['registry_sources']} / {report['planned_source_results']}",
        f"- Seed rows / mapped registry IDs: {report['seed_mapping_rows']} / {report['seed_source_ids_mapped']}",
        f"- Complete configured-scope checks: {report['complete_range_checks']}",
        f"- Sources with target HTTP requests: {report['actual_network_counts']['sources_with_target_http_request']}",
        f"- Target HTTP requests / responses: {report['actual_network_counts']['target_http_requests']} / {report['actual_network_counts']['target_http_responses']}",
        f"- Robots HTTP requests / responses: {report['actual_network_counts']['robots_http_requests']} / {report['actual_network_counts']['robots_http_responses']}",
        f"- Exact request counts in per-attempt logs: {report['actual_network_counts'].get('http_request_counts_exact',False)}",
        f"- Target response bodies with bytes / captured bytes: {report['actual_network_counts']['target_response_bodies_with_bytes']} / {report['actual_network_counts']['target_response_body_bytes']}",
        f"- Exact response-body size coverage: {report['actual_network_counts']['response_body_size_counts_exact']} ({report['actual_network_counts']['response_body_size_fields_recorded']} endpoint fields)",
        f"- Candidate observations this run: {report['candidate_observations_this_run']}",
        f"- Persistent review tasks: {report['candidate_review_tasks_current']}",
        f"- Newly created stable review tasks vs prior ledger: {report['candidate_review_tasks_added_since_previous_ledger']}",
        f"- Missing prior tasks: {report['candidate_review_tasks_missing_since_previous_ledger']}",
        "- Human review / release authorized / formal site writes: 0 / 0 / 0",
        "",
        "## Source results",
        "",
    ]
    lines.extend(f"- `{status}`: {count}" for status, count in report["source_status_counts"].items())
    lines.extend(["", "## Opportunity flow (not a global opportunity count)", ""])
    lines.extend(f"- {key}: {value}" for key, value in report["opportunity_flow"].items())
    lines.extend(["", "## Explicit adapter type buckets", ""])
    lines.extend(f"- `{key}`: {json.dumps(value, ensure_ascii=False, sort_keys=True)}" for key, value in report["source_funnel_by_explicit_adapter_opportunity_type"].items())
    lines.extend(["", "## Region classification", "", "- `unclassified_or_unknown`: region totals are unavailable because registry records do not carry an explicit region field; no domain-based inference was applied.", "", "The CSV contains source IDs, original public URLs, configured monitor endpoints, adapter scope, HTTP status, technical result, aggregate task counts, and the next technical action. It does not include candidate titles, evidence excerpts, or stable candidate task IDs.", ""])
    (output_dir / "source_funnel_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-checks", type=Path, required=True)
    parser.add_argument("--candidate-ledger", type=Path, required=True)
    parser.add_argument("--daily-report", type=Path)
    parser.add_argument("--previous-ledger", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    checks = [json.loads(line) for line in args.source_checks.read_text(encoding="utf-8").splitlines() if line.strip()]
    registry = read_json(REGISTRY)
    seeds = read_json(SEEDS)
    occurrences = read_json(OCCURRENCES)
    catalog = read_json(CATALOG)
    ledger = read_json(args.candidate_ledger)
    previous = read_json(args.previous_ledger) if args.previous_ledger else None
    rows, report = build_reconciliation(registry, seeds, occurrences, catalog, checks, ledger, previous)
    if args.daily_report and args.daily_report.is_file():
        daily=read_json(args.daily_report)
        report["daily_report_network_metrics"]=daily.get("network_metrics")
        report["http_request_budget_reservations"]=daily.get("http_request_budget",{}).get("used")
        if isinstance(daily.get("network_metrics"),dict):
            report["actual_network_counts"].update(daily["network_metrics"])
    write_outputs(rows, report, args.output_dir)
    print(json.dumps({"rows": len(rows), "report_path": str(args.output_dir / "source_funnel_report.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
