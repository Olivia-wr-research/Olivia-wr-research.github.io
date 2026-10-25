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


def import_reviews(ledger_path, snapshot_dir, result_dir, assignment, submissions, run_id, deferred=None):
    out = executor.safe_private_directory(result_dir)
    if assignment.get('format') != 'terrafar-model-assignment-v1':
        raise ValueError('native_assignment_invalid')
    if assignment.get('skill') != ledger_api.skill_pin():
        raise ValueError('native_skill_changed')
    if not isinstance(assignment.get('tasks'), list) or not assignment['tasks']:
        raise ValueError('native_assignment_tasks_invalid')
    if not isinstance(submissions, list) or (deferred is not None and not isinstance(deferred, list)):
        raise ValueError('native_submission_or_defer_list_invalid')
    deferred = deferred or []
    if len(assignment['tasks']) > executor.MAX_BATCH_SIZE:
        raise ValueError('native_assignment_count_invalid')
    task_ids = [t.get('task_id') for t in assignment['tasks'] if isinstance(t, dict)]
    if len(task_ids) != len(assignment['tasks']) or len(set(task_ids)) != len(task_ids):
        raise ValueError('native_assignment_tasks_invalid')
    tasks = {t['task_id']: t for t in assignment['tasks']}
    submitted_ids = [s.get('task_id') for s in submissions if isinstance(s, dict)]
    deferred_ids = [r.get('task_id') for r in deferred if isinstance(r, dict)]
    if (len(submitted_ids) != len(submissions) or len(deferred_ids) != len(deferred)
            or not 1 <= len(submissions) + len(deferred) <= executor.MAX_BATCH_SIZE
            or len(set(submitted_ids)) != len(submitted_ids)
            or len(set(deferred_ids)) != len(deferred_ids)
            or set(submitted_ids) & set(deferred_ids)
            or any(task_id not in tasks for task_id in submitted_ids + deferred_ids)):
        raise ValueError('native_submission_count_or_duplicates_invalid')
    # Validate all explicit deferrals before merging any result in the batch.
    for record in deferred:
        task = tasks[record['task_id']]
        lease = task.get('lease') if isinstance(task.get('lease'), dict) else {}
        if task.get('skill') != ledger_api.skill_pin():
            raise ValueError('native_skill_changed')
        expected = {'task_id': task.get('task_id'), 'candidate_id': task.get('candidate_id'),
                    'candidate_fingerprint': task.get('candidate_fingerprint'),
                    'attempt_id': lease.get('attempt_id'), 'lease_id': lease.get('lease_id'),
                    'owner': lease.get('owner')}
        if (any(not isinstance(value, str) or not value.strip() for value in expected.values())
                or any(record.get(key) != value for key, value in expected.items())):
            raise ValueError('deferred_claim_identity_mismatch')
        reason = record.get('reason')
        if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
            raise ValueError('deferred_claim_reason_required')
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
    deferred_count = deferred_replayed = 0
    for record in deferred:
        task = tasks[record['task_id']]
        with ledger_api.ledger_lock(ledger_path):
            ledger = ledger_api.load_ledger(ledger_path, require_existing=True)
            outcome = executor.release_deferred_claim(ledger, task, record, run_id, out)
            if outcome == 'deferred':
                ledger_api.save_ledger(ledger_path, ledger)
                deferred_count += 1
            else:
                deferred_replayed += 1
    return {'merged_native_results': merged, 'idempotent_replays': replayed,
            'deferred': deferred_count, 'idempotent_defer_replays': deferred_replayed,
            'paid_api_calls': 0, 'human_approvals': 0, 'published': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('ledger', 'snapshots', 'results', 'assignment', 'submissions'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--deferred', type=Path)
    p.add_argument('--run-id', required=True)
    a = p.parse_args()
    deferred = json.loads(a.deferred.read_text()) if a.deferred else None
    print(json.dumps(import_reviews(a.ledger, a.snapshots, a.results,
                     json.loads(a.assignment.read_text()), json.loads(a.submissions.read_text()), a.run_id,
                     deferred=deferred)))


if __name__ == '__main__':
    main()
