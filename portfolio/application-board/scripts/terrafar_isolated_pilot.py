#!/usr/bin/env python3
"""Bounded new-input transport trial; stdout contains aggregate numbers only.

This does not restore or replace historical authority. Raw responses and
candidates remain in an isolated private directory. The Actions wrapper must
not upload that directory, including encrypted versions of its contents.
"""
import argparse
from contextlib import redirect_stdout, redirect_stderr
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace

import terrafar_source_audit as audit
import terrafar_candidate_ledger as ledger
import terrafar_detail_capture as details
from terrafar_model_executor import safe_private_directory, atomic_private_json

SOURCE_IDS = (
    'eth-doctoral-listing', 'jobbnorge-uio', 'doc-446f8d108f9611b8',
    'doc-350282ccffe5f525', 'geo-intake-ubc-dec2026', 'geo-programme-oxford-geography',
    'geo-project-rmit-phenology', 'geo-project-rmit-spatial-health',
    'src-17456e71-1ce5-5ac3-b562-4e6dddf8308a', 'geo-oct17-wur-coastal-peat',
)


def run(root, run_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', run_id):
        raise ValueError('isolated_pilot_run_id_invalid')
    root = safe_private_directory(root)
    if any(root.iterdir()):
        raise ValueError('isolated_pilot_requires_new_directory_no_history_overwrite')
    os.umask(0o077)
    atomic_private_json(root/'plan.json', {'source_ids': list(SOURCE_IDS),
        'authority': 'isolated_new_input_not_historical_restore',
        'max_http_requests_including_robots_and_retries': 100, 'max_details': 10})
    public = {'format': 'terrafar-isolated-pilot-aggregate-v1', 'run_id': run_id,
              'planned_sources': len(SOURCE_IDS), 'historical_restore': False,
              'external_private_save': False, 'api_calls': 0, 'published': 0}
    with (root/'runtime.log').open('w') as log, redirect_stdout(log), redirect_stderr(log):
        # DNS safety preflight in the CURRENT execution environment, no HTTP.
        safe = 0
        for url in ('https://jobs.ethz.ch/', 'https://jobs.helsinki.fi/', 'https://www.ox.ac.uk/'):
            try:
                audit.resolve_public_url(url)
                safe += 1
            except Exception:
                pass
        public['preflight_safe_hosts'] = safe
        if not safe:
            public.update(status='blocked_preflight', http_budget_slots_used=0)
        else:
            prior_runs = audit.RUNS
            try:
                audit.RUNS = root/'runs'
                audit.run(SimpleNamespace(live=True, budget=10, concurrency=2, timeout=12,
                    retries=1, per_host_delay=1, http_request_budget=70, all_sources=False,
                    source_ids_file=str(root/'plan.json'), state_dir=str(root/'state'),
                    candidate_ledger=str(root/'state/candidate_ledger.json'),
                    require_state=False, require_candidate_ledger=False,
                    capture_responses_dir=str(root/'http-responses'), run_id=run_id))
                report = json.loads((audit.RUNS/run_id/'daily_report.json').read_text())
                capture = details.capture_batch(root/'state/candidate_ledger.json', audit.REGISTRY,
                    root/'page_snapshots', root/'detail-results.jsonl', run_id,
                    limit=10, timeout=12, retries=1, per_host_delay=1, http_budget=30)
                atomic_private_json(root/'detail-report.json', capture)
                value = ledger.load_ledger(root/'state/candidate_ledger.json', require_existing=True)
                total = report['http_request_budget']['used'] + capture['request_budget_slots_used']
                if total > 100:
                    raise RuntimeError('isolated_pilot_http_budget_exceeded')
                sent = report['network_metrics']['sources_with_target_http_request']
                public.update(status='transport_executed' if sent else 'blocked_no_target_request',
                    http_budget_slots_used=total,
                    source_status_counts={k:int(v) for k,v in report['status_counts'].items()},
                    source_network_metrics={k:v for k,v in report['network_metrics'].items()
                                            if isinstance(v, (int,bool))},
                    discovered_candidate_records=len(value['tasks']),
                    pending_review_tasks=len(ledger.review_queue(value)),
                    detail_counts={k:capture[k] for k in ('planned','captured','unchanged','partial',
                                                        'blocked','failed','not_attempted','http_requests_sent')})
            finally:
                audit.RUNS = prior_runs
    atomic_private_json(root/'aggregate.json', public)
    return public


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-dir', required=True)
    p.add_argument('--run-id', required=True)
    args=p.parse_args()
    try:
        result=run(Path(args.private_dir), args.run_id)
    except Exception:
        # No stack trace/URL/candidate fields in public Actions logs.
        print(json.dumps({'status':'isolated_pilot_internal_failure', 'published':0}))
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True))
    if result['status']!='transport_executed':
        raise SystemExit(3)


if __name__=='__main__':
    main()
