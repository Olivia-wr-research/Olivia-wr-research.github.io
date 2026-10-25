"""Offline wrapper contracts, never evidence of a network run."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import terrafar_isolated_pilot as pilot
import terrafar_candidate_ledger as ledger


class IsolatedPilotTests(unittest.TestCase):
    def test_pilot_cannot_expand_budget_or_detail_scope(self):
        with tempfile.TemporaryDirectory() as d:
            for budgets in ((71,30,10),(70,31,10),(70,30,11),(0,30,10)):
                with self.assertRaisesRegex(ValueError,'budget_out_of_range'):
                    pilot.run(Path(d),'synthetic',*budgets)

    def test_zero_request_guard_failure_is_not_execution(self):
        with tempfile.TemporaryDirectory() as d, patch.object(pilot.audit, 'resolve_public_url', side_effect=ValueError('guard')):
            result=pilot.run(Path(d), 'synthetic-zero')
            self.assertEqual(result['status'], 'blocked_preflight')
            self.assertEqual(result['http_budget_slots_used'], 0)
            self.assertFalse(result['historical_restore'])

    def test_existing_directory_cannot_overwrite_history(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';p.write_text('keep')
            with self.assertRaisesRegex(ValueError, 'no_history_overwrite'):
                pilot.run(Path(d), 'synthetic')
            self.assertEqual(p.read_text(),'keep')

    def test_caps_and_aggregate_do_not_export_candidate_fields(self):
        def fake_audit(args):
            self.assertEqual(args.http_request_budget,70)
            self.assertEqual(args.budget,10)
            state=Path(args.state_dir);state.mkdir()
            ledger.save_ledger(state/'candidate_ledger.json', ledger.empty_ledger())
            report={'http_request_budget':{'used':70},'network_metrics':{
                'sources_with_target_http_request':0, 'total_http_requests_sent':0},
                'status_counts':{'blocked':10},'candidate_secret':'NEVER_PUBLIC'}
            run=pilot.audit.RUNS/args.run_id;run.mkdir(parents=True)
            (run/'daily_report.json').write_text(json.dumps(report))
            print('NEVER_PUBLIC')
        def fake_detail(*args, **kw):
            self.assertEqual(kw['http_budget'],30)
            self.assertEqual(kw['limit'],10)
            args[3].write_text('')
            return {'planned':0,'captured':0,'unchanged':0,'partial':0,'blocked':0,'failed':0,
                    'not_attempted':0,'http_requests_sent':0,'request_budget_slots_used':30}
        with tempfile.TemporaryDirectory() as d, patch.object(pilot.audit,'resolve_public_url'), \
             patch.object(pilot.audit,'run',side_effect=fake_audit), \
             patch.object(pilot.details,'capture_batch',side_effect=fake_detail):
            r=pilot.run(Path(d),'synthetic')
            self.assertEqual(r['http_budget_slots_used'],100)
            self.assertEqual(r['status'],'blocked_no_target_request')
            self.assertNotIn('NEVER_PUBLIC',json.dumps(r))
            self.assertEqual(r['published'],0)


if __name__=='__main__': unittest.main()
