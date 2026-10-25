#!/usr/bin/env python3
"""Import actual interactive native reviews through the leased model merge path.

This is an import protocol, not a model dispatcher or proof of human review.
The session/task receipt must identify a real interactive execution. It cannot
enable scheduled model calls or approve content for publication.
"""
import argparse
import json
from pathlib import Path

import terrafar_candidate_ledger as ledger_api
import terrafar_model_executor as executor


def import_reviews(ledger_path, snapshot_dir, result_dir, assignment, submissions, run_id):
    out = executor.safe_private_directory(result_dir)
    if assignment.get('format') != 'terrafar-model-assignment-v1':
        raise ValueError('native_assignment_invalid')
    tasks = {t['task_id']: t for t in assignment['tasks']}
    if not 1 <= len(submissions) <= executor.MAX_BATCH_SIZE or len({s['task_id'] for s in submissions}) != len(submissions):
        raise ValueError('native_submission_count_or_duplicates_invalid')
    merged = replayed = 0
    for submission in submissions:
        task = tasks[submission['task_id']]
        native = submission['execution']
        if (native.get('mode') != 'native_codex_session' or not native.get('session_id')
                or not native.get('agent_name') or not native.get('execution_reference')
                or native.get('api_calls') != 0 or native.get('human_reviewed') is not False):
            raise ValueError('native_execution_receipt_invalid')
        snapshot = executor.load_snapshot(snapshot_dir, task)
        if submission.get('input_sha256') != snapshot['text_sha256']:
            raise ValueError('native_input_snapshot_mismatch')
        receipt = {**native, 'provider': 'native_codex_session', 'model': native.get('model'),
                   'provider_response_id': None, 'input_tokens': None, 'output_tokens': None,
                   'estimated_cost_usd': None, 'task_id': task['task_id'],
                   'attempt_id': task['lease']['attempt_id'], 'skill_sha256': task['skill']['sha256'],
                   'input_sha256': snapshot['text_sha256']}
        result = executor.validate_model_result(submission['result'], task, snapshot, receipt, submission['processed_at'])
        result['finding']['native_submission_sha256'] = ledger_api.digest(submission)
        bundle = {'format': 'terrafar-model-result-bundle-v1', 'run_id': run_id,
                  'assignment': executor.task_assignment(assignment, task['task_id']),
                  'result': result, 'receipt': receipt}
        bundle['result_sha256'] = ledger_api.digest(bundle)
        filename = f"{task['task_id']}-{receipt['attempt_id']}.json"
        with ledger_api.ledger_lock(ledger_path):
            ledger = ledger_api.load_ledger(ledger_path, require_existing=True)
            state = executor._execution_state(ledger)['tasks'][task['task_id']]
            if state['status'] == 'completed':
                prior = json.loads((out / filename).read_text())
                if prior['result']['finding'].get('native_submission_sha256') != ledger_api.digest(submission):
                    raise ValueError('native_completed_result_conflict')
                replayed += 1
                continue
            lease = state.get('lease') or {}
            if (lease != task['lease'] or executor.parse_utc(lease['expires_at']) <= executor.parse_utc(executor.utc_now())):
                raise ValueError('native_lease_expired_or_replaced')
            if task['skill'] != ledger_api.skill_pin():
                raise ValueError('native_skill_changed')
            attempt = next(a for a in state['attempts'] if a['attempt_id'] == receipt['attempt_id'])
            if not attempt.get('run_id'):
                raise ValueError('native_claim_origin_run_missing')
            # Import may occur in a later process/run. Recovery binds the bundle
            # to the original claim; merge provenance records the new run.
            bundle['run_id'] = attempt['run_id']
            bundle.pop('result_sha256', None)
            bundle['result_sha256'] = ledger_api.digest(bundle)
            # Persist before mutation: interruption is recoverable by existing
            # recover_saved_results, bound to this attempt and snapshot.
            executor.atomic_private_json(out / filename, bundle)
            saved_sha = executor.sha256_bytes((out / filename).read_bytes())
            attempt.update({'native_results_received': 1, 'provider_call_invocations': 0,
                            'result_file': filename, 'result_sha256': saved_sha})
            ledger_api.save_ledger(ledger_path, ledger)
            executor._merge_saved_result(ledger, {**bundle, 'result_sha256': saved_sha}, run_id,
                                         task['task_id'], receipt['attempt_id'])
            ledger_api.save_ledger(ledger_path, ledger)
            merged += 1
    return {'merged_native_results': merged, 'idempotent_replays': replayed,
            'paid_api_calls': 0, 'human_approvals': 0, 'published': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('ledger', 'snapshots', 'results', 'assignment', 'submissions'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--run-id', required=True)
    a = p.parse_args()
    print(json.dumps(import_reviews(a.ledger, a.snapshots, a.results,
                     json.loads(a.assignment.read_text()), json.loads(a.submissions.read_text()), a.run_id)))


if __name__ == '__main__':
    main()
