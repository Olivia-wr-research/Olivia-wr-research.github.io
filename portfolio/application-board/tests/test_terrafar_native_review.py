"""Synthetic protocol tests; none is evidence of a real model invocation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_terrafar_ai_pipeline import observation, snapshot_for, supported_model_result
import terrafar_candidate_ledger as ledger
import terrafar_model_executor as ex
import terrafar_native_review as native
import terrafar_detail_capture as detail
import terrafar_private_cycle as cycle
import terrafar_web_receipts as web


class NativeReviewTests(unittest.TestCase):
    def fixture(self, root):
        lp = root / 'ledger.json'
        value = ledger.empty_ledger()
        ledger.merge_observations(value, [observation()], 'synthetic-run')
        assignment = ex.claim_batch(value, 'synthetic-native', run_id='synthetic-run')
        ledger.save_ledger(lp, value)
        task = assignment['tasks'][0]
        snap = snapshot_for(task)
        sp = root / 'snapshots'; sp.mkdir()
        ex.atomic_private_json(sp / (task['candidate_id'] + '.json'), snap)
        submission = {'task_id': task['task_id'], 'input_sha256': snap['text_sha256'],
            'processed_at': ex.utc_now(), 'execution': {'mode': 'native_codex_session',
            'session_id': 'synthetic-session', 'agent_name': 'synthetic-native',
            'execution_reference': 'offline protocol fixture', 'api_calls': 0, 'human_reviewed': False},
            'result': supported_model_result(task['candidate_url'])}
        return lp, sp, assignment, submission

    def test_native_import_replays_without_second_review_and_conflict_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); lp, sp, assignment, sub = self.fixture(root)
            report = native.import_reviews(lp, sp, root/'results', assignment, [sub], 'synthetic-run')
            self.assertEqual(report['merged_native_results'], 1)
            first = lp.read_bytes()
            replay = native.import_reviews(lp, sp, root/'results', assignment, [sub], 'synthetic-run')
            self.assertEqual(replay['idempotent_replays'], 1)
            self.assertEqual(first, lp.read_bytes())
            changed = copy.deepcopy(sub); changed['result']['reason'] = 'changed'
            with self.assertRaisesRegex(ValueError, 'native_completed_result_conflict'):
                native.import_reviews(lp, sp, root/'results', assignment, [changed], 'synthetic-run')

    def test_native_wrong_snapshot_and_replaced_lease_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); lp, sp, assignment, sub = self.fixture(root)
            bad = copy.deepcopy(sub); bad['input_sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'native_input_snapshot_mismatch'):
                native.import_reviews(lp, sp, root/'results', assignment, [bad], 'synthetic-run')
            value = ledger.load_ledger(lp); task = assignment['tasks'][0]
            value['model_execution']['tasks'][task['task_id']]['lease']['lease_id'] = 'replaced'
            ledger.save_ledger(lp,value)
            with self.assertRaisesRegex(ValueError,'native_lease_expired_or_replaced'):
                native.import_reviews(lp,sp,root/'results',assignment,[sub],'synthetic-run')

    def test_partial_text_is_preserved_but_cannot_be_terminal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); lp,sp,a,sub=self.fixture(root)
            task=a['tasks'][0]; p=sp/(task['candidate_id']+'.json')
            snap=json.loads(p.read_text());snap['capture_status']='partial';ex.atomic_private_json(p,snap)
            with self.assertRaisesRegex(ex.ModelExecutionError,'partial_snapshot'):
                native.import_reviews(lp,sp,root/'results',a,[sub],'synthetic-run')
            sub['result']['status']='insufficient_evidence'
            native.import_reviews(lp,sp,root/'results',a,[sub],'synthetic-run')
            saved=ledger.load_ledger(lp)
            self.assertEqual(saved['tasks'][task['candidate_id']]['status'],'insufficient_evidence')
            self.assertTrue(ledger.review_queue(saved))

    def test_truncation_returns_partial_reason_and_keeps_text(self):
        text,reason=detail._text_from_response(('<p>'+'x'*(detail.MAX_TEXT_CHARS+10)+'</p>').encode(),'text/html')
        self.assertEqual(len(text),detail.MAX_TEXT_CHARS)
        self.assertEqual(reason,'visible_text_limit_reached')

    def test_capture_hash_is_restored_across_distinct_run_directories(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);lp,sp,a,sub=self.fixture(root)
            value=ledger.load_ledger(lp);task=ledger.review_queue(value)[0]
            snap=snapshot_for(task);snap['capture_run_id']='capture-one'
            self.assertIsNone(detail.record_snapshot(lp,task,snap))
            snap2=copy.deepcopy(snap);snap2['capture_run_id']='capture-two'
            self.assertEqual(detail.record_snapshot(lp,task,snap2),snap['text_sha256'])
            restored=ledger.load_ledger(lp)
            self.assertEqual(len(restored['detail_capture']['events']),2)
            self.assertEqual(len(ledger.review_queue(restored)),1)
            snap2['capture_status']='partial';snap2['capture_run_id']='capture-three'
            detail.record_snapshot(lp,task,snap2)
            snap2['capture_run_id']='capture-four'
            self.assertIsNone(detail.record_snapshot(lp,task,snap2))

    def test_same_url_detail_requires_registered_detail_scope(self):
        task={'source_id':'s','endpoint_id':'s:1','source_url':'https://x.example/job','candidate_url':'https://x.example/job'}
        mapping={('s','s:1'):task['source_url']}
        self.assertFalse(detail._eligible_task(task,mapping)[0])
        self.assertTrue(detail._eligible_task(task,mapping,{('s','s:1')})[0])

    def test_negated_open_phrase_never_confirms_portal_open(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);_,_,a,sub=self.fixture(root);task=a['tasks'][0]
            task['review_task_kind']='current_open_status_review'
            snap=snapshot_for(task,'application_portal')
            for text in ('We are not currently accepting new applications.',
                         "We aren't currently accepting applications.",
                         'We aren’t currently accepting applications.'):
                snap['text']=text
                r={'status':'insufficient_evidence','fields':[], 'current_open_status':'open',
                   'evidence':[{'field':'current_open_status','url':snap['url'],'claim':'open',
                                'quote':snap['text'],'locator':'Status'}]}
                with self.assertRaisesRegex(ex.ModelExecutionError,'does_not_confirm_state'):
                    ex.validate_model_result(r,task,snap,{'provider':'offline-test'})

    def test_switches_and_key_do_not_authorize_paid_api(self):
        ready,reason=ex.provider_preflight({'TERRAFAR_MODEL_PROVIDER':'openai_responses',
            'TERRAFAR_MODEL_CALLS_AUTHORIZED':'true','TERRAFAR_MODEL_BUDGET_APPROVED':'true',
            'OPENAI_API_KEY':'synthetic-not-a-key','TERRAFAR_MODEL_NAME':'synthetic'})
        self.assertFalse(ready);self.assertIn('budget_reservation',reason)

    def test_private_payload_missing_version_pin_fails_before_daily_work(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'page_snapshots').mkdir()
            with self.assertRaisesRegex(Exception,'reviewed_version_migration'):
                cycle.check_pipeline_versions(root)

    def test_web_display_does_not_invent_http_status_or_complete_body(self):
        pages=web.index_receipts([{'tool':'web.run','captured_at':ex.utc_now(),
            'request_response':'Title (https://x.example/job)\nTotal lines: 10\nL0: vacancy\nL1: text'}])
        self.assertEqual(pages[0]['capture_status'],'partial')
        self.assertEqual(pages[0]['display_missing_line_count'],8)
        self.assertIsNone(pages[0]['http_status'])

    def test_single_failed_pending_task_returns_on_next_full_rotation(self):
        value=ledger.empty_ledger();ledger.merge_observations(value,[observation()],'synthetic')
        task=ledger.review_queue(value)[0]
        ex._execution_state(value)['capture_cursor_by_role']['opportunity_verifier:']=ex.review_task_key(task)
        for _ in range(4):
            queued=ex.rotated_review_queue(value, cursor_name='capture_cursor_by_role',wrap=False)
            self.assertEqual([t['candidate_id'] for t in queued],[task['candidate_id']])

    def test_cross_run_native_interruption_recovers_original_attempt(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);lp,sp,a,sub=self.fixture(root)
            with patch.object(ex,'_merge_saved_result',side_effect=RuntimeError('synthetic crash')):
                with self.assertRaisesRegex(RuntimeError,'synthetic crash'):
                    native.import_reviews(lp,sp,root/'results',a,[sub],'later-import-run')
            saved=ledger.load_ledger(lp)
            self.assertEqual(ex.recover_saved_results(saved,root/'results','third-recovery-run'),1)
            self.assertEqual(ex.recover_saved_results(saved,root/'results','third-recovery-run'),0)

    def test_funnel_trace_includes_all_carryover_review_queue_tasks(self):
        import terrafar_pipeline_funnel as funnel

        value = ledger.empty_ledger()
        ledger.merge_observations(value, [observation('old-job-1', 'old-run'),
                                           observation('old-job-2', 'old-run')], 'old-run')
        carryover_ids = set(value['tasks'])
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            run_dir = root / 'run'; run_dir.mkdir()
            (run_dir / 'manifest.json').write_text(json.dumps({
                'run_id': 'current-run', 'planned_source_ids': ['source-1'], 'registry_sha256': 'a' * 64}),
                encoding='utf-8')
            source_row = {'source_id': 'source-1', 'outcome': 'checked_unchanged', 'attempted': True,
                          'endpoints': [{'endpoint_id': 'source-1:jobs', 'outcome': 'checked_unchanged',
                                         'content_complete': True, 'candidate_rows': []}]}
            (run_dir / 'source_checks.jsonl').write_text(json.dumps(source_row) + '\n', encoding='utf-8')
            ledger_path = root / 'candidate_ledger.json'
            ledger.save_ledger(ledger_path, value)

            funnel.build_funnel(run_dir, ledger_path, output_dir=root / 'private-funnel')
            trace = [json.loads(line) for line in
                     (root / 'private-funnel' / 'candidate_trace.jsonl').read_text(encoding='utf-8').splitlines()]

        self.assertEqual({row['candidate_id'] for row in trace}, carryover_ids)
        self.assertTrue(all(row['carried_pending_task'] for row in trace))
        self.assertTrue(all(row['candidate_status'] == 'pending' for row in trace))
        self.assertTrue(all(row['ledger_observed_this_run'] is False for row in trace))

    def test_private_store_rejects_rewriting_completed_model_attempt_audit_fields(self):
        import test_terrafar_private_store as store_fixtures

        store_fixtures.VaultTests.setUpClass()
        fixture = store_fixtures.VaultTests()
        try:
            fixture.setUp()
            try:
                path = fixture.source / 'candidate_ledger.json'
                value = ledger.load_ledger(path, require_existing=True)
                candidate_id = next(iter(value['tasks']))
                task_id = 'mtask-synthetic-completed'
                value['model_execution'] = {
                    'schema_version': 1, 'executor_version': 1, 'events': [],
                    'claim_cursor_by_role': {}, 'capture_cursor_by_role': {},
                    'tasks': {task_id: {
                        'task_id': task_id, 'candidate_id': candidate_id,
                        'candidate_fingerprint': 'f' * 64, 'review_task_kind': 'content_review',
                        'status': 'completed', 'lease': None,
                        'attempts': [{
                            'attempt_id': 'synthetic-attempt-1', 'attempt_number': 1,
                            'claimed_at': '2026-10-25T00:00:00Z', 'owner': 'synthetic-reviewer',
                            'run_id': 'synthetic-run', 'outcome': 'merged',
                            'provider_call_invocations': 0, 'provider_responses_received': 0,
                            'native_results_received': 1, 'result_sha256': 'a' * 64,
                            'provider': 'native_codex_session',
                            'provider_response_received_at': '2026-10-25T00:00:01Z',
                            'completed_at': '2026-10-25T00:00:02Z'}]}}
                }
                ledger.save_ledger(path, value)
                fixture.bootstrap()

                mutations = {
                    'outcome': 'failed',
                    'result_sha256': 'b' * 64,
                    'provider': 'unrelated-provider',
                    'provider_response_received_at': '2026-10-26T00:00:01Z',
                    'completed_at': '2026-10-26T00:00:02Z',
                }
                for field, replacement in mutations.items():
                    restored, receipt = fixture.restore('mutated-' + field)
                    restored_ledger = ledger.load_ledger(restored / 'candidate_ledger.json', require_existing=True)
                    attempt = restored_ledger['model_execution']['tasks'][task_id]['attempts'][0]
                    attempt[field] = replacement
                    ledger.save_ledger(restored / 'candidate_ledger.json', restored_ledger)
                    with self.subTest(field=field):
                        with self.assertRaisesRegex(store_fixtures.s.StoreError,
                                                    'private_state_terminal_model_attempt_rewritten'):
                            fixture.vault.save(restored, receipt)
                self.assertEqual(fixture.vault.head()[0]['sequence'], 1)
            finally:
                fixture.doCleanups()
        finally:
            store_fixtures.VaultTests.tearDownClass()


if __name__ == '__main__': unittest.main()
