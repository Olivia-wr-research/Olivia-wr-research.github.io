import argparse
import contextlib
import io
import json
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.parse import urlsplit
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / 'portfolio/application-board/scripts'))
import terrafar_source_registry as registry
import terrafar_source_audit as audit
import terrafar_candidate_ledger as candidate_ledger
import terrafar_restore_run_state as restore_run_state
import terrafar_source_adapters as source_adapters


class RegistryUnionTests(unittest.TestCase):
    def test_frozen_id_sets_and_seed_mappings_are_total(self):
        report = registry.validate_registry_ids(
            registry.load(registry.REGISTRY),
            registry.load(registry.BASELINE)['source_ids'],
            registry.load(registry.PREVIOUS)['source_ids'],
            registry.load(registry.KIT / 'data/registry_baseline.json')['source_ids'],
            [x['seed_source_id'] for x in registry.load(registry.MAINT / 'registry/seed_mapping.json')['mappings']],
            registry.load(registry.PREMERGE)['source_ids'],
        )
        self.assertTrue(report['valid'])
        self.assertEqual(report['seed_ids_accounted_for'], 133)
        self.assertEqual(report['premerge_ids_preserved'], 264)

    def test_premerge_snapshot_matches_legacy_repository_sources(self):
        rows = registry.load(registry.REGISTRY)['sources']
        ids = registry.premerge_source_ids(rows)
        self.assertEqual(ids, registry.load(registry.PREMERGE)['source_ids'])

    def test_same_count_replacement_is_rejected(self):
        rows = [{'source_id': 'kept', 'canonical_url': 'https://a.test/'}]
        with self.assertRaises(SystemExit):
            registry.validate_registry_ids({'sources': rows}, ['removed'], ['kept'], [], [])

    def test_normalization_preserves_paths_queries_hosts_and_functional_ids(self):
        a = registry.canonical_url('https://jobs.example/a?id=17&utm_source=x')
        self.assertEqual(a, 'https://jobs.example/a?id=17')
        self.assertNotEqual(a, registry.canonical_url('https://jobs.example/b?id=17'))
        self.assertNotEqual(a, registry.canonical_url('https://www.jobs.example/a?id=17'))
        self.assertNotEqual(a, registry.canonical_url('http://jobs.example/a?id=17'))

    def test_seed_occurrence_ledger_has_no_dropped_links(self):
        d = registry.load(registry.MAINT / 'registry/occurrence_disposition.json')
        self.assertEqual(d['source_seed_occurrences'], 161)
        self.assertEqual(d['dispositions']['retained_or_mapped_source'], 147)
        self.assertEqual(d['dispositions']['excluded_asset'], 14)
        self.assertEqual(len(d['occurrences']), 161)

    def test_same_url_logical_scopes_keep_distinct_ids(self):
        rows = registry.load(registry.REGISTRY)['sources']
        by_url = {}
        for row in rows:
            by_url.setdefault(row['canonical_url'], []).append(row['source_id'])
        duplicate_groups = [ids for ids in by_url.values() if len(ids) > 1]
        self.assertTrue(duplicate_groups)
        self.assertTrue(all(len(ids) == len(set(ids)) for ids in duplicate_groups))
        sfu = [x for x in rows if x['source_id'] in {'geo-intake-sfu-ma-2027', 'geo-intake-sfu-phd-2027'}]
        self.assertEqual(len(sfu), 2)
        self.assertEqual(sfu[0]['canonical_url'], sfu[1]['canonical_url'])

    def test_bootstrap_builder_refuses_to_overwrite_frozen_registry(self):
        before = registry.REGISTRY.read_bytes()
        with self.assertRaises(SystemExit):
            registry.build()
        self.assertEqual(before, registry.REGISTRY.read_bytes())

    def test_candidate_facts_remain_unknown_on_import(self):
        rows = registry.load(registry.REGISTRY)['sources']
        seed = next(x for x in rows if x.get('unverified_seed'))
        self.assertEqual(seed['verified_metadata'], {'status': 'unknown', 'fields': {}})
        self.assertIsNone(seed['last_verified_at'])


class StatusAndNetworkTests(unittest.TestCase):
    def source(self, adapter='fake'):
        return {'source_id': 'test-source', 'canonical_url': 'https://example.test/list', 'adapter': adapter,
                'monitor_endpoints': [{'endpoint_id': 'test-source:primary', 'url': 'https://example.test/list', 'adapter': adapter, 'required': True}]}

    def fake_response(self, status=200, body=b'page'):
        return {'outcome': 'response', 'attempts': [{'attempt_id': 'attempt-1', 'started_at': '2026-01-01T00:00:00Z'}],
                'http_status': status, 'reason': None, 'robots': {'allowed': True, 'status': 404},
                'body': body, 'response_url': 'https://example.test/list', 'response_hash': 'a'*64,
                'etag': None, 'last_modified': None, 'content_complete': True}

    def test_first_observation_is_partial_then_known_empty(self):
        state = {'snapshots': {}}
        with patch.object(audit, 'fetch_endpoint', return_value=self.fake_response()), \
             patch.object(audit, 'semantic_result', return_value=([], {'items': 0})):
            first = audit.check_one(self.source(), 'run1', state, 1, 0, 0)
        self.assertEqual(first['outcome'], 'partial')
        self.assertTrue(first['first_observed'])
        self.assertIn('no_prior_comparison', first['reason'])
        with patch.object(audit, 'fetch_endpoint', return_value=self.fake_response()), \
             patch.object(audit, 'semantic_result', return_value=([], {'items': 0})):
            second = audit.check_one(self.source(), 'run2', state, 1, 0, 0)
        self.assertEqual(second['outcome'], 'checked_empty')
        self.assertTrue(second['baseline_available'])

    def test_semantic_change_and_unchanged_use_persisted_snapshot(self):
        state = {'snapshots': {}}
        with patch.object(audit, 'fetch_endpoint', return_value=self.fake_response()), patch.object(audit, 'semantic_result', return_value=([{'id': 'a'}], {})):
            audit.check_one(self.source(), 'r1', state, 1, 0, 0)
        with patch.object(audit, 'fetch_endpoint', return_value=self.fake_response()), patch.object(audit, 'semantic_result', return_value=([{'id': 'a'}], {})):
            same = audit.check_one(self.source(), 'r2', state, 1, 0, 0)
        self.assertEqual(same['outcome'], 'checked_unchanged')
        with patch.object(audit, 'fetch_endpoint', return_value=self.fake_response()), patch.object(audit, 'semantic_result', return_value=([{'id': 'b'}], {})):
            changed = audit.check_one(self.source(), 'r3', state, 1, 0, 0)
        self.assertEqual(changed['outcome'], 'checked_changed')

    def test_304_without_baseline_is_not_success(self):
        response = self.fake_response(status=304, body=b'')
        response['response_hash'] = None
        with patch.object(audit, 'fetch_endpoint', return_value=response):
            result = audit.check_one(self.source(), 'r1', {'snapshots': {}}, 1, 0, 0)
        self.assertEqual(result['outcome'], 'partial')
        self.assertFalse(result['baseline_available'])

    def test_304_with_successful_baseline_is_unchanged(self):
        state = {'snapshots': {audit.key_for('https://example.test/list', 'fake'):
            {'semantic_hash': 'x', 'semantic_rows': [{'id': 1}], 'scope': {}, 'content_hash': 'a'*64}}}
        with patch.object(audit, 'fetch_endpoint', return_value=self.fake_response(status=304, body=b'')):
            result = audit.check_one(self.source(), 'r1', state, 1, 0, 0)
        self.assertEqual(result['outcome'], 'checked_unchanged')

    def test_incomplete_pagination_remains_partial(self):
        state = {'snapshots': {}}
        with patch.object(audit, 'fetch_endpoint', return_value=self.fake_response()), \
             patch.object(audit, 'semantic_result', return_value=([{'id': 'page1'}], {'_complete': False, 'pagination_detected': True})):
            result = audit.check_one(self.source(), 'r1', state, 1, 0, 0)
        self.assertEqual(result['outcome'], 'partial')
        self.assertIn('pagination', result['reason'])
        self.assertTrue(state['snapshots'])  # transport observation is retained
        self.assertFalse(any('semantic_hash' in value for value in state['snapshots'].values()))

    def test_login_captcha_and_soft_404_are_not_empty(self):
        self.assertEqual(audit.sniff_block(b'<title>Login</title>', 200), 'login_or_challenge_page')
        self.assertEqual(audit.sniff_block(b'<title>404 Not Found</title>', 200), 'soft_404')
        self.assertEqual(audit.sniff_block(b'Forbidden', 403), 'http_access_restricted')
        self.assertIsNone(audit.sniff_block(b'<title>List</title><h1>No positions</h1>', 200))

    def test_transient_failure_is_retried_and_attempt_ids_are_distinct(self):
        success = {'status': 200, 'url': 'https://example.test/list', 'headers': {}, 'body': b'x', 'complete': True}
        with patch.object(audit, 'robots_gate', return_value={'allowed': True, 'status': 404}), \
             patch.object(audit, 'http_get', side_effect=[RuntimeError('timeout'), success]):
            result = audit.fetch_endpoint('https://example.test/list', 1, 0, 1, True, None)
        self.assertEqual(len(result['attempts']), 2)
        self.assertNotEqual(result['attempts'][0]['attempt_id'], result['attempts'][1]['attempt_id'])
        self.assertEqual(result['http_status'], 200)

    def test_robot_disallow_is_blocked_without_page_request(self):
        with patch.object(audit, 'robots_gate', return_value={'allowed': False, 'status': 200, 'reason': 'robots_disallow'}):
            result = audit.fetch_endpoint('https://example.test/list', 1, 0, 0, True, None)
        self.assertEqual(result['outcome'], 'blocked')
        self.assertFalse(result['attempts'])

    def test_robots_cache_rechecks_rules_for_each_path(self):
        audit.robots_cache.clear()
        robots = {'status': 200, 'url': 'https://example.test/robots.txt', 'headers': {},
                  'body': b'User-agent: *\nDisallow: /private\n', 'complete': True}
        try:
            with patch.object(audit, 'http_get', return_value=robots) as fetch:
                public = audit.robots_gate('https://example.test/public/jobs', 1, 0, retries=0)
                private = audit.robots_gate('https://example.test/private/jobs', 1, 0, retries=0)
            self.assertTrue(public['allowed'])
            self.assertFalse(private['allowed'])
            self.assertEqual(fetch.call_count, 2)
        finally:
            audit.robots_cache.clear()

    def test_robots_cache_does_not_cross_scheme_or_port(self):
        audit.robots_cache.clear()
        robots = {'status': 404, 'url': 'https://example.test/robots.txt', 'headers': {}, 'body': b'', 'complete': True}
        try:
            with patch.object(audit, 'http_get', return_value=robots) as fetch:
                audit.robots_gate('https://example.test/list', 1, 0, retries=0)
                audit.robots_gate('http://example.test/list', 1, 0, retries=0)
                audit.robots_gate('https://example.test:8443/list', 1, 0, retries=0)
            self.assertEqual(fetch.call_count, 3)
        finally:
            audit.robots_cache.clear()

    def test_preflight_redirects_cannot_expand_the_hostname_scope(self):
        audit.configure_request_host_scope({'sample.example'})
        try:
            with self.assertRaisesRegex(ValueError, 'request_host_outside_preflight_scope'):
                audit.safe_public_url('https://redirect.example/robots.txt')
            with patch.object(audit.socket, 'getaddrinfo', return_value=[(2, 1, 6, '', ('93.184.216.34', 443))]):
                self.assertEqual(audit.safe_public_url('https://sample.example/robots.txt').hostname, 'sample.example')
        finally:
            audit.configure_request_host_scope(None)

    def test_live_redirect_is_rejected_before_connecting_outside_preflight_scope(self):
        first_url = 'https://sample.example/list'
        source_parts = urlsplit(first_url)
        response = Mock()
        response.status = 302
        response.getheaders.return_value = [('Location', 'https://extra.example/robots.txt')]
        response.read.return_value = b''
        connection = Mock()
        connection.getresponse.return_value = response
        audit.configure_request_host_scope({'sample.example'})
        audit.configure_request_budget(3)
        try:
            with patch.object(audit, 'resolve_public_url', side_effect=[(source_parts, ['93.184.216.34']), ValueError('request_host_outside_preflight_scope')]), \
                 patch.object(audit, 'paced'), patch.object(audit, 'pinned_connection', return_value=connection):
                with self.assertRaisesRegex(ValueError, 'request_host_outside_preflight_scope'):
                    audit.http_get(first_url, 1, 0)
            connection.request.assert_called_once()
            self.assertEqual(audit.http_request_budget_stats(), {'used': 1, 'limit': 3})
        finally:
            audit.configure_request_host_scope(None)
            audit.configure_request_budget(None)

    def test_rejected_redirect_keeps_first_http_status_and_chain_in_attempt_log(self):
        first_url = 'https://sample.example/list'
        source_parts = urlsplit(first_url)
        response = Mock()
        response.status = 302
        response.getheaders.return_value = [('Location', 'https://extra.example/jobs')]
        response.read.return_value = b''
        connection = Mock()
        connection.getresponse.return_value = response
        audit.configure_request_host_scope({'sample.example'})
        audit.robots_cache.clear()
        try:
            with patch.object(audit, 'resolve_public_url', side_effect=[
                    (source_parts, ['93.184.216.34']),
                    ValueError('request_host_outside_preflight_scope')]), \
                 patch.object(audit, 'paced'), patch.object(audit, 'pinned_connection', return_value=connection):
                with self.assertRaisesRegex(ValueError, 'request_host_outside_preflight_scope') as caught:
                    audit.http_get(first_url, 1, 0)
            error = caught.exception
            self.assertTrue(audit.request_sent_for_error(error))
            self.assertTrue(audit.transport_attempted_for_error(error))
            self.assertEqual(audit.http_status_for_error(error), 302)
            self.assertEqual(audit.redirect_chain_for_error(error), [
                {'from': first_url, 'status': 302, 'to': 'https://extra.example/jobs'}])
            connection.request.assert_called_once()
            audit.robots_cache.clear()
            with patch.object(audit, 'http_get', side_effect=error):
                robots = audit.robots_gate(first_url, 1, 0, retries=0)
            logged = robots['attempts'][0]
            self.assertTrue(logged['transport_attempted'])
            self.assertTrue(logged['http_request_started'])
            self.assertTrue(logged['request_sent'])
            self.assertEqual(logged['http_status'], 302)
            self.assertEqual(logged['redirect_chain'], audit.redirect_chain_for_error(error))
            self.assertEqual(robots['status'], 302)
        finally:
            audit.configure_request_host_scope(None)
            audit.robots_cache.clear()

    def test_tcp_connection_failure_is_not_logged_as_http_request_sent(self):
        audit.robots_cache.clear()
        audit.configure_request_budget(None)
        connection = Mock()
        with patch.object(audit, 'robots_gate', return_value={
                'allowed': True, 'status': 404, 'reason': 'robots_not_found', 'attempts': []}), \
             patch.object(audit, 'resolve_public_url', return_value=(urlsplit('https://example.test/list'), ['93.184.216.34'])), \
             patch.object(audit, 'paced'), \
             patch.object(audit, 'getproxies', return_value={}), \
             patch.object(audit.http.client, 'HTTPSConnection', return_value=connection), \
             patch.object(audit.socket, 'create_connection', side_effect=OSError('synthetic TCP connect failure')):
            result = audit.fetch_endpoint('https://example.test/list', 1, 0, 0, True, None)
        self.assertEqual(result['outcome'], 'error')
        attempt = result['attempts'][-1]
        self.assertTrue(attempt['transport_attempted'])
        self.assertFalse(attempt['http_request_started'])
        self.assertFalse(attempt['request_sent'])
        self.assertIsNone(attempt['http_status'])

    def test_tls_connection_uses_the_validated_ip_and_original_hostname(self):
        parsed = urlsplit('https://example.test/jobs')
        raw_socket = Mock()
        wrapped_socket = Mock()
        connection = Mock()
        connection._context = Mock()
        connection._context.wrap_socket.return_value = wrapped_socket
        with patch.object(audit, 'getproxies', return_value={}), \
             patch.object(audit.http.client, 'HTTPSConnection', return_value=connection) as make_connection, \
             patch.object(audit.socket, 'create_connection', return_value=raw_socket) as connect:
            result = audit.pinned_connection(parsed, ['93.184.216.34'], 3)
        self.assertIs(result, connection)
        self.assertEqual(make_connection.call_args.args[:2], ('example.test', 443))
        self.assertEqual(connect.call_args.args[0], ('93.184.216.34', 443))
        connection._context.wrap_socket.assert_called_once_with(raw_socket, server_hostname='example.test')

    def test_request_budget_exhaustion_is_not_misclassified_as_failure_or_block(self):
        robots_attempt = {'attempt_id': 'robots-budget', 'request_sent': False, 'endpoint': 'robots.txt'}
        with patch.object(audit, 'robots_gate', return_value={'allowed': False, 'status': None,
                'reason': 'runner_request_budget_exhausted', 'attempts': [robots_attempt]}):
            before_robots = audit.fetch_endpoint('https://example.test/list', 1, 0, 0, True, None)
        self.assertEqual(before_robots['outcome'], 'not_attempted')
        self.assertEqual(before_robots['reason'], 'runner_request_budget_exhausted')

        with patch.object(audit, 'robots_gate', return_value={'allowed': True, 'status': 404,
                'reason': 'robots_not_found', 'attempts': []}), \
             patch.object(audit, 'http_get', side_effect=audit.RequestBudgetExceeded('http_request_budget_exhausted')):
            after_robots = audit.fetch_endpoint('https://example.test/list', 1, 0, 0, True, None)
        self.assertEqual(after_robots['outcome'], 'partial')
        self.assertEqual(after_robots['reason'], 'runner_request_budget_exhausted')
        self.assertFalse(after_robots['attempts'][-1]['request_sent'])
        with patch.object(audit, 'fetch_endpoint', return_value=after_robots):
            source_result = audit.check_one(self.source(), 'budget-run', {'snapshots': {}}, 1, 0, 0)
        self.assertEqual(source_result['outcome'], 'partial')
        self.assertEqual(source_result['endpoints'][0]['reason'], 'runner_request_budget_exhausted')

    def test_non_global_dns_guard_is_reported_as_runner_block(self):
        audit.robots_cache.clear()
        with patch.object(audit, 'http_get', side_effect=ValueError('private_or_non_global_address')):
            result = audit.robots_gate('https://example.test/list', 1, 0, retries=0)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'runner_safety_guard_block')
        self.assertEqual(result['error_detail'], 'private_or_non_global_address')

    def test_dns_failure_and_empty_resolution_fail_closed_before_http(self):
        with patch.object(audit.socket, 'getaddrinfo', side_effect=socket.gaierror('temporary resolver failure')):
            with self.assertRaisesRegex(ValueError, 'destination_dns_resolution_failed'):
                audit.http_get('https://example.test/list', 1, 0)
        with patch.object(audit.socket, 'getaddrinfo', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'destination_dns_resolution_failed'):
                audit.http_get('https://example.test/list', 1, 0)

    def test_http_request_budget_stops_before_an_over_budget_request(self):
        fake_connection = Mock()
        fake_connection.request.side_effect = OSError('synthetic transport error')
        audit.configure_request_budget(1)
        try:
            with patch.object(audit, 'resolve_public_url', return_value=(urlsplit('https://example.test/list'), ['93.184.216.34'])), \
                 patch.object(audit, 'paced'), patch.object(audit, 'pinned_connection', return_value=fake_connection) as connect:
                with self.assertRaisesRegex(OSError, 'synthetic transport error'):
                    audit.http_get('https://example.test/list', 1, 0)
                with self.assertRaises(audit.RequestBudgetExceeded):
                    audit.http_get('https://example.test/list', 1, 0)
            self.assertEqual(connect.call_count, 1)
            self.assertEqual(audit.http_request_budget_stats(), {'used': 1, 'limit': 1})
        finally:
            audit.configure_request_budget(None)

    def test_http_request_connects_only_to_the_validated_numeric_address(self):
        audit.configure_request_host_scope(None)
        audit.configure_request_budget(None)
        with patch.object(audit.socket, 'getaddrinfo', return_value=[(2, 1, 6, '', ('93.184.216.34', 443))]) as lookup, \
             patch.object(audit, 'pinned_connection', side_effect=OSError('synthetic connect failure')) as connect:
            with self.assertRaisesRegex(OSError, 'synthetic connect failure'):
                audit.http_get('https://example.test/list', 1, 0)
        lookup.assert_called_once_with('example.test', 443, type=audit.socket.SOCK_STREAM)
        connect.assert_called_once()
        self.assertEqual(connect.call_args.args[1], ['93.184.216.34'])

    def test_required_state_restore_reads_disk_and_rejects_missing_or_corrupt_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / 'restored-state'
            state_dir.mkdir()
            payload = {'schema_version': 1, 'snapshots': {'https://example.test/list\nfake': {'semantic_hash': 'a' * 64}}, 'last_run_id': 'first'}
            (state_dir / 'state.json').write_text(json.dumps(payload), encoding='utf-8')
            command = (
                "import json,sys;sys.path.insert(0,sys.argv[1]);import terrafar_source_audit as a;"
                "s=a.load_state(__import__('pathlib').Path(sys.argv[2]),require_existing=True);"
                "print(s['last_run_id'],next(iter(s['snapshots'].values()))['semantic_hash'])"
            )
            completed = subprocess.run(
                [sys.executable, '-c', command, str(ROOT / 'portfolio/application-board/scripts'), str(state_dir)],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(completed.stdout.strip(), 'first ' + 'a' * 64)
            missing = Path(tmp) / 'missing-state'
            with self.assertRaisesRegex(FileNotFoundError, 'required_state_file_missing'):
                audit.load_state(missing, require_existing=True)
            (state_dir / 'state.json').write_text('{broken', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'state_file_unreadable'):
                audit.load_state(state_dir, require_existing=True)

    def test_fixture_state_restores_in_a_new_process_and_checks_unchanged_and_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir=Path(tmp)/'first-run-state'; state_dir.mkdir()
            source=self.source()
            state={'schema_version':1,'snapshots':{}}
            response=self.fake_response(body=b'fixture page')
            with patch.object(audit,'fetch_endpoint',return_value=response), patch.object(audit,'semantic_result',return_value=([{'id':'fixture-a'}],{})):
                first=audit.check_one(source,'fixture-first',state,1,0,0)
            self.assertEqual(first['outcome'],'partial')
            audit.writej(state_dir/'state.json',state)
            command='''
import json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
import terrafar_source_audit as a
state=a.load_state(Path(sys.argv[2]),require_existing=True)
source={'source_id':'test-source','canonical_url':'https://example.test/list','adapter':'fake','monitor_endpoints':[{'endpoint_id':'test-source:primary','url':'https://example.test/list','adapter':'fake','required':True}]}
body=b'fixture page'
response={'outcome':'response','attempts':[{'attempt_id':'fixture-attempt','started_at':'2026-01-01T00:00:00Z'}],'http_status':200,'reason':None,'robots':{'allowed':True,'status':404},'body':body,'response_url':'https://example.test/list','response_hash':a.sha(body),'etag':None,'last_modified':None,'content_complete':True}
rows=[{'id':sys.argv[3]}]
with patch.object(a,'fetch_endpoint',return_value=response),patch.object(a,'semantic_result',return_value=(rows,{})):
 result=a.check_one(source,'fixture-second',state,1,0,0)
print(json.dumps({'outcome':result['outcome'],'baseline_available':result['baseline_available'],'restored_snapshot_count':len(state['snapshots'])}))
'''
            outcomes=[]
            for candidate_id in ('fixture-a','fixture-b'):
                completed=subprocess.run([sys.executable,'-c',command,str(ROOT/'portfolio/application-board/scripts'),str(state_dir),candidate_id],check=True,capture_output=True,text=True)
                outcomes.append(json.loads(completed.stdout))
            self.assertEqual(outcomes[0]['outcome'],'checked_unchanged')
            self.assertEqual(outcomes[1]['outcome'],'checked_changed')
            self.assertTrue(all(x['baseline_available'] and x['restored_snapshot_count']>=1 for x in outcomes))

    def test_candidate_ledger_keeps_pending_tasks_on_unchanged_runs_and_is_idempotent(self):
        source=self.source()
        key=audit.key_for('https://example.test/list','fake')
        state={'snapshots':{key:{'semantic_hash':'b'*64,'semantic_rows':[{'id':'candidate-1','title':'Example PhD'}],'content_hash':'c'*64,'last_success_at':'2026-01-01T00:00:00Z'}}}
        result=[{'source_id':'test-source','endpoints':[{'endpoint_id':'test-source:primary','adapter':'fake','outcome':'checked_changed','candidate_count':1}]}]
        observations=audit.build_candidate_observations([source],state,result)
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,observations,'run-a')
        candidate_id=next(iter(ledger['tasks']))
        candidate_ledger.merge_observations(ledger,observations,'run-a')
        candidate_ledger.merge_observations(ledger,observations,'run-b')
        unchanged=[{'source_id':'test-source','endpoints':[{'endpoint_id':'test-source:primary','adapter':'fake','outcome':'checked_unchanged','candidate_count':1}]}]
        candidate_ledger.merge_observations(ledger,audit.build_candidate_observations([source],state,unchanged),'run-c')
        self.assertEqual(len(ledger['tasks']),1)
        self.assertEqual(candidate_ledger.open_tasks(ledger)[0]['candidate_id'],candidate_id)
        self.assertEqual(ledger['tasks'][candidate_id]['status'],'pending')
        self.assertFalse(ledger['tasks'][candidate_id]['formal_site_write'])
        self.assertEqual(ledger['tasks'][candidate_id]['observed_runs'],['run-a','run-b','run-c'])

    def test_candidate_ledger_migrates_legacy_rows_deduplicates_and_retains_provenance(self):
        source=self.source()
        rows=[{'task_id':f'old-run:test-source:{n}','run_id':'old-run','source_id':'test-source','candidate_key':f'https://example.test/jobs/{n}','candidate_url':f'https://example.test/jobs/{n}','source_url':'https://example.test/list','candidate':{'id':f'job-{n}'},'retrieved_at':'2026-01-01T00:00:00Z','content_sha256':'a'*64} for n in range(60)]
        rows += [dict(rows[0])]
        ledger=candidate_ledger.migrate_legacy_queue(candidate_ledger.empty_ledger(),rows,{'test-source':source},'migration-run')
        self.assertEqual(len(ledger['tasks']),60)
        self.assertEqual(len(candidate_ledger.open_tasks(ledger)),60)
        self.assertIn(rows[0]['task_id'],ledger['tasks'][next(iter(ledger['tasks']))]['legacy_task_ids'])
        candidate_ledger.migrate_legacy_queue(ledger,rows,{'test-source':source},'migration-run')
        self.assertEqual(len(ledger['tasks']),60)

    def test_restore_policy_reaudit_demotes_unsupported_old_terminal_review_without_erasing_history(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-old','candidate_url':'https://jobs.example/job-old','source_url':'https://jobs.example/list','candidate':{'id':'job-old'},'retrieved_at':'2026-01-01T00:00:00Z'}
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,[observation],'run-1')
        candidate_id=next(iter(ledger['tasks']))
        bad_evidence=[{'url':'https://jobs.example/job-old','claim':'detail page identifies job-old','locator':'Title field'}]
        ledger['tasks'][candidate_id]['status']='verified'
        ledger['tasks'][candidate_id]['review_history']=[{'event_id':'old-event','status':'verified','run_id':'old-run','reviewer':'legacy-reviewer','reviewed_at':'2026-01-02T00:00:00Z','evidence':bad_evidence,'finding':{'decision_scope':'page_content','content_verification':{'status':'verified','evidence':bad_evidence},'current_open_status':'unknown'}}]
        ledger.pop('evidence_policy_version')
        candidate_ledger.revalidate_terminal_reviews(ledger,'restore-run-2')
        self.assertEqual(ledger['tasks'][candidate_id]['status'],'insufficient_evidence')
        self.assertEqual(len(ledger['tasks'][candidate_id]['review_history']),2)
        self.assertEqual(ledger['tasks'][candidate_id]['review_history'][0]['status'],'verified')
        self.assertEqual(ledger['tasks'][candidate_id]['review_history'][1]['status'],'insufficient_evidence')
        self.assertEqual(ledger['evidence_policy_version'],candidate_ledger.EVIDENCE_POLICY_VERSION)

    def test_restore_policy_reaudits_exclusions_and_duplicate_targets(self):
        observations=[{'source_id':'s','endpoint_id':'s:list','candidate_key':key,'candidate_url':f'https://jobs.example/{key}','source_url':'https://jobs.example/list','candidate':{'id':key},'retrieved_at':'2026-01-01T00:00:00Z'} for key in ('excluded','duplicate')]
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,observations,'run-1')
        ids={task['candidate_key']:candidate_id for candidate_id,task in ledger['tasks'].items()}
        ledger['tasks'][ids['excluded']]['status']='excluded'
        ledger['tasks'][ids['excluded']]['review_history']=[{'status':'excluded','reviewer':'legacy-reviewer','reviewed_at':'2026-01-02T00:00:00Z','evidence':[],'finding':{'decision_scope':'excluded'}}]
        ledger['tasks'][ids['duplicate']]['status']='duplicate'
        ledger['tasks'][ids['duplicate']]['review_history']=[{'status':'duplicate','reviewer':'legacy-reviewer','reviewed_at':'2026-01-02T00:00:00Z','duplicate_of':'missing-target','evidence':[{'url':'https://jobs.example/duplicate','claim':'Duplicate notice','locator':'Duplicate field'}],'finding':{'decision_scope':'duplicate'}}]
        ledger.pop('evidence_policy_version')
        candidate_ledger.revalidate_terminal_reviews(ledger,'restore-run-2')
        self.assertEqual(ledger['tasks'][ids['excluded']]['status'],'insufficient_evidence')
        self.assertEqual(ledger['tasks'][ids['duplicate']]['status'],'insufficient_evidence')
        self.assertEqual(len(ledger['tasks'][ids['excluded']]['review_history']),2)
        self.assertEqual(len(ledger['tasks'][ids['duplicate']]['review_history']),2)

    def test_candidate_review_requires_evidence_and_terminal_conclusions_keep_history(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-1','candidate_url':'https://jobs.example/job-1','source_url':'https://jobs.example/list','candidate':{'id':'job-1'},'retrieved_at':'2026-01-01T00:00:00Z'}
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,[observation],'run-1')
        candidate_id=next(iter(ledger['tasks']))
        candidate_fingerprint=ledger['tasks'][candidate_id]['content_fingerprint']
        with self.assertRaisesRegex(ValueError,'requires_evidence'):
            candidate_ledger.apply_reviews(ledger,[{'candidate_id':candidate_id,'candidate_fingerprint':candidate_fingerprint,'status':'verified','reviewer':'audit_reviewer','reviewed_at':'2026-01-02T00:00:00Z','evidence':[]}],'review-1')
        insufficient={'candidate_id':candidate_id,'candidate_fingerprint':candidate_fingerprint,'status':'insufficient_evidence','reviewer':'audit_reviewer','reviewed_at':'2026-01-02T00:00:00Z','evidence':[]}
        candidate_ledger.apply_reviews(ledger,[insufficient],'review-1')
        missing_failure_identity={**insufficient}
        missing_failure_identity.pop('reviewer')
        with self.assertRaisesRegex(ValueError,'requires_reviewer_and_time'):
            candidate_ledger.apply_reviews(ledger,[missing_failure_identity],'review-missing-failure-identity')
        self.assertEqual(candidate_ledger.open_tasks(ledger)[0]['status'],'insufficient_evidence')
        evidence=[
            {'field':'application_route','url':'https://jobs.example/job-1','claim':'application_route is stated as Online application portal','locator':'Application route'},
            {'field':'deadline','url':'https://jobs.example/job-1','claim':'deadline is stated as 2026-02-01','locator':'Deadline field'},
            {'field':'funding','url':'https://jobs.example/job-1','claim':'funding is stated as salaried doctoral position','locator':'Funding field'},
            {'field':'eligibility','url':'https://jobs.example/job-1','claim':'eligibility is stated as relevant masters degree','locator':'Requirements field'},
        ]
        verified={'candidate_id':candidate_id,'candidate_fingerprint':candidate_fingerprint,'status':'verified','decision_scope':'page_content','content_verification':{'status':'verified','evidence':evidence},'reviewer':'opportunity_verifier','reviewed_at':'2026-01-03T00:00:00Z','evidence':evidence,'current_open_status':'unknown',
                  'application_route':{'status':'verified_as_stated','value':'Online application portal','evidence_url':'https://jobs.example/job-1','locator':'Application route'},
                  'deadline':{'status':'supported','value':'2026-02-01','evidence_url':'https://jobs.example/job-1','locator':'Deadline field'},
                  'funding':{'status':'supported','value':'salaried doctoral position','evidence_url':'https://jobs.example/job-1','locator':'Funding field'},
                  'eligibility':{'status':'supported','value':'relevant masters degree','evidence_url':'https://jobs.example/job-1','locator':'Requirements field'}}
        sparse={**verified,'content_verification':{'status':'verified','evidence':[{'url':'https://jobs.example/job-1','claim':'detail page identifies job-1','locator':'Title field'}]},'evidence':[{'url':'https://jobs.example/job-1','claim':'detail page identifies job-1','locator':'Title field'}]}
        with self.assertRaisesRegex(ValueError,'missing_field_evidence'):
            candidate_ledger.apply_reviews(ledger,[sparse],'review-sparse')
        wrong_value={**verified,'deadline':{**verified['deadline'],'value':'2099-12-31'}}
        with self.assertRaisesRegex(ValueError,'missing_field_evidence:.*deadline'):
            candidate_ledger.apply_reviews(ledger,[wrong_value],'review-wrong-value')
        wrong_reviewer={**verified,'reviewer':42}
        with self.assertRaisesRegex(ValueError,'requires_reviewer_and_time'):
            candidate_ledger.apply_reviews(ledger,[wrong_reviewer],'review-wrong-reviewer')
        wrong_time={**verified,'reviewed_at':'not-a-timestamp'}
        with self.assertRaisesRegex(ValueError,'timestamp_invalid'):
            candidate_ledger.apply_reviews(ledger,[wrong_time],'review-wrong-time')
        candidate_ledger.apply_reviews(ledger,[verified],'review-2')
        candidate_ledger.apply_reviews(ledger,[verified],'review-2-replayed-in-another-run')
        self.assertEqual(ledger['tasks'][candidate_id]['status'],'verified')
        self.assertEqual(ledger['tasks'][candidate_id]['review_history'][-1]['finding']['current_open_status'],'unknown')
        self.assertEqual(len(ledger['events']),3)
        changed={**observation,'candidate':{'id':'job-1','title':'Updated title'},'retrieved_at':'2026-01-04T00:00:00Z'}
        candidate_ledger.merge_observations(ledger,[changed],'run-3')
        self.assertEqual(ledger['tasks'][candidate_id]['status'],'pending')
        self.assertEqual(len(ledger['tasks'][candidate_id]['content_versions']),2)
        self.assertEqual(len(ledger['tasks'][candidate_id]['review_history']),2)
        with self.assertRaisesRegex(ValueError,'content_fingerprint_mismatch'):
            candidate_ledger.apply_reviews(ledger,[verified],'stale-review-after-change')
        self.assertEqual(ledger['tasks'][candidate_id]['status'],'pending')

    def test_duplicate_conclusion_requires_existing_stable_target(self):
        observations=[{'source_id':'s','endpoint_id':'s:list','candidate_key':key,'candidate_url':f'https://jobs.example/{key}','source_url':'https://jobs.example/list','candidate':{'id':key},'retrieved_at':'2026-01-01T00:00:00Z'} for key in ('job-1','job-2')]
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,observations,'run-1')
        first,second=ledger['tasks'].values()
        result={'candidate_id':first['candidate_id'],'candidate_fingerprint':first['content_fingerprint'],'status':'duplicate','decision_scope':'duplicate','duplicate_of':'missing-stable-id','reviewer':'audit_reviewer','reviewed_at':'2026-01-02T00:00:00Z','evidence':[{'url':first['candidate_url'],'claim':'Same role identifier as another record','locator':'Role identifier'}]}
        with self.assertRaisesRegex(ValueError,'duplicate_candidate_review_missing_or_invalid_target'):
            candidate_ledger.apply_reviews(ledger,[result],'review-duplicate-invalid')
        result['duplicate_of']=second['candidate_id']
        candidate_ledger.apply_reviews(ledger,[result],'review-duplicate-valid')
        self.assertEqual(ledger['tasks'][first['candidate_id']]['status'],'duplicate')

    def test_candidate_ledger_survives_restart_interruption_and_disjoint_review_merges(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path=Path(tmp)/'candidate_ledger.json'
            observation=lambda n:{'source_id':'s','endpoint_id':'s:list','candidate_key':f'job-{n}','candidate_url':f'https://jobs.example/{n}','source_url':'https://jobs.example/list','candidate':{'id':n},'retrieved_at':'2026-01-01T00:00:00Z'}
            ledger=candidate_ledger.empty_ledger()
            candidate_ledger.merge_observations(ledger,[observation(1),observation(2)],'run-1')
            candidate_ledger.save_ledger(ledger_path,ledger)
            batch=candidate_ledger.export_agent_batch(ledger,limit=10,agent='opportunity_verifier')
            self.assertEqual(batch['candidate_count'],2)
            self.assertLessEqual(batch['candidate_count'],10)
            before_interrupted_write=candidate_ledger.load_ledger(ledger_path,require_existing=True)
            candidate_id=batch['candidate_ids'][0]
            candidate_fingerprint=before_interrupted_write['tasks'][candidate_id]['content_fingerprint']
            evidence=[{'field':'deadline','url':'https://jobs.example/1','claim':'deadline is stated as 2026-02-01','locator':'Deadline field'}]
            result={'candidate_id':candidate_id,'candidate_fingerprint':candidate_fingerprint,'status':'verified','decision_scope':'page_content','content_verification':{'status':'verified','evidence':evidence},'reviewer':'agent','reviewed_at':'2026-01-02T00:00:00Z','evidence':evidence,'deadline':{'status':'supported','value':'2026-02-01','evidence_url':'https://jobs.example/1','locator':'Deadline field'}}
            candidate_ledger.apply_reviews(before_interrupted_write,[result],'review-1')
            restored_after_interrupt=candidate_ledger.load_ledger(ledger_path,require_existing=True)
            self.assertEqual(len(candidate_ledger.open_tasks(restored_after_interrupt)),2)
            candidate_ledger.apply_reviews(restored_after_interrupt,[result],'review-1')
            candidate_ledger.save_ledger(ledger_path,restored_after_interrupt)
            retry=candidate_ledger.load_ledger(ledger_path,require_existing=True)
            self.assertEqual(len(candidate_ledger.open_tasks(retry)),1)
            self.assertEqual(len(retry['tasks'][candidate_id]['review_history']),1)
            with self.assertRaisesRegex(ValueError,'duplicate_candidate_review'):
                candidate_ledger.apply_reviews(retry,[result,result],'review-2')

    def test_parallel_review_merges_serialize_without_lost_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path=Path(tmp)/'candidate_ledger.json'
            observations=[{'source_id':'s','endpoint_id':'s:list','candidate_key':f'job-{n}','candidate_url':f'https://jobs.example/{n}','source_url':'https://jobs.example/list','candidate':{'id':n},'retrieved_at':'2026-01-01T00:00:00Z'} for n in (1,2)]
            ledger=candidate_ledger.empty_ledger()
            candidate_ledger.merge_observations(ledger,observations,'run-1')
            candidate_ledger.save_ledger(ledger_path,ledger)
            ids=list(ledger['tasks'])
            barrier=threading.Barrier(2)
            errors=[]
            def merge_one(candidate_id):
                try:
                    candidate_url=ledger['tasks'][candidate_id]['candidate_url']
                    candidate_fingerprint=ledger['tasks'][candidate_id]['content_fingerprint']
                    evidence=[{'field':'deadline','url':candidate_url,'claim':'deadline is stated as 2026-02-01','locator':'Deadline field'}]
                    result={'candidate_id':candidate_id,'candidate_fingerprint':candidate_fingerprint,'status':'verified','decision_scope':'page_content','content_verification':{'status':'verified','evidence':evidence},'reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z','evidence':evidence,'deadline':{'status':'supported','value':'2026-02-01','evidence_url':candidate_url,'locator':'Deadline field'}}
                    barrier.wait()
                    with candidate_ledger.ledger_lock(ledger_path):
                        current=candidate_ledger.load_ledger(ledger_path,require_existing=True)
                        candidate_ledger.apply_reviews(current,[result],'run-2')
                        candidate_ledger.save_ledger(ledger_path,current)
                except Exception as error:
                    errors.append(error)
            workers=[threading.Thread(target=merge_one,args=(candidate_id,)) for candidate_id in ids]
            for worker in workers: worker.start()
            for worker in workers: worker.join()
            self.assertEqual(errors,[])
            final=candidate_ledger.load_ledger(ledger_path,require_existing=True)
            self.assertEqual(len(final['tasks']),2)
            self.assertTrue(all(final['tasks'][candidate_id]['status']=='verified' for candidate_id in ids))
            self.assertEqual(sum(len(task['review_history']) for task in final['tasks'].values()),2)

    def test_cross_actions_run_restore_migrates_legacy_then_restores_candidate_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); legacy=base/'legacy-artifact'; (legacy/'state').mkdir(parents=True); (legacy/'run').mkdir()
            destination1=base/'restored-1'; destination2=base/'restored-2'
            registry_bytes=registry.REGISTRY.read_bytes(); registry_sha=audit.sha(registry_bytes)
            state={'schema_version':1,'snapshots':{'https://jobs.ethz.ch/\neth_listing':{'semantic_hash':'a'*64,'semantic_rows':[],'adapter':'eth_listing'}},'last_run_id':'old-program-run','last_registry_sha256':registry_sha,'last_plan_sha256':'b'*64}
            state_bytes=(json.dumps(state,indent=2)+'\n').encode()
            (legacy/'state/state.json').write_bytes(state_bytes)
            manifest={'run_id':'old-program-run','registry_sha256':registry_sha,'plan_sha256':'b'*64}
            (legacy/'run/manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            source=next(x for x in registry.load(registry.REGISTRY)['sources'] if x['source_id']=='eth-doctoral-listing')
            row={'task_id':'old-program-run:eth-doctoral-listing:abc','run_id':'old-program-run','source_id':'eth-doctoral-listing','candidate_key':'https://jobs.ethz.ch/job/view/J1','candidate_url':'https://jobs.ethz.ch/job/view/J1','source_url':source['canonical_url'],'candidate':{'url':'https://jobs.ethz.ch/job/view/J1','titleEn':'Example PhD'},'retrieved_at':'2026-10-23T00:00:00Z','content_sha256':'c'*64}
            (legacy/'run/candidate_review_queue.jsonl').write_text(json.dumps(row)+'\n',encoding='utf-8')
            provenance={'origin_run_id':'old-program-run','state_sha256':audit.sha(state_bytes),'state_schema_version':1,'registry_sha256':registry_sha,'parser_sha256':{'eth_listing':audit.sha((audit.APP/'scripts/import_eth.py').read_bytes()),'jobbnorge_rss':audit.sha((audit.APP/'scripts/import_jobbnorge.py').read_bytes())}}
            (legacy/'state/provenance.json').write_text(json.dumps(provenance),encoding='utf-8')
            candidate_id=candidate_ledger.stable_candidate_id('eth-doctoral-listing','eth-doctoral-listing:primary',row['candidate_key'])
            evidence=[{'url':row['candidate_url'],'claim':'detail page identifies Example PhD','locator':'Title field'}]
            review_file=base/'agent-review.json'
            review_file.write_text(json.dumps([{'candidate_id':candidate_id,'source_id':'eth-doctoral-listing','endpoint_id':'eth-doctoral-listing:primary','candidate_key':row['candidate_key'],'candidate_url':row['candidate_url'],'ledger_review_status':'insufficient_evidence','content_verification':{'status':'insufficient_evidence','evidence':evidence},'application_route':{'status':'unknown'},'current_open_status':'unknown','verifier':'opportunity_verifier','verified_at':'2026-10-23T00:30:00Z'}]),encoding='utf-8')
            first=restore_run_state.restore(legacy,destination1,'1001','1002',registry.REGISTRY,allow_legacy=True,review_results_path=review_file)
            self.assertTrue(first['candidate_ledger_migrated_from_legacy_queue'])
            self.assertEqual(first['candidate_task_count'],1)
            restored_ledger=candidate_ledger.load_ledger(destination1/'candidate_ledger.json',require_existing=True)
            self.assertEqual(restored_ledger['tasks'][candidate_id]['status'],'insufficient_evidence')
            self.assertEqual(restored_ledger['tasks'][candidate_id]['review_history'][0]['finding']['current_open_status'],'unknown')
            wrong_identity=json.loads(review_file.read_text())
            wrong_identity[0]['source_id']='another-source'
            wrong_file=base/'wrong-agent-review.json'
            wrong_file.write_text(json.dumps(wrong_identity),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'identity_mismatch'):
                restore_run_state.restore(legacy,base/'wrong-review','1001','1005',registry.REGISTRY,allow_legacy=True,review_results_path=wrong_file)
            with self.assertRaisesRegex(ValueError,'distinct'):
                restore_run_state.restore(legacy,base/'invalid','1001','1001',registry.REGISTRY,allow_legacy=True)
            missing_reviewer=json.loads(review_file.read_text())
            del missing_reviewer[0]['verifier']
            missing_reviewer_file=base/'missing-reviewer.json'
            missing_reviewer_file.write_text(json.dumps(missing_reviewer),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'reviewer_missing'):
                restore_run_state.restore(legacy,base/'missing-reviewer','1001','1006',registry.REGISTRY,allow_legacy=True,review_results_path=missing_reviewer_file)
            new_artifact=base/'new-artifact'; (new_artifact/'state').mkdir(parents=True)
            state2=(destination1/'state.json').read_bytes(); ledger2=(destination1/'candidate_ledger.json').read_bytes()
            (new_artifact/'state/state.json').write_bytes(state2)
            (new_artifact/'state/candidate_ledger.json').write_bytes(ledger2)
            provenance2={'format':'terrafar-maintenance-state-v1','origin_actions_run_id':'1002','origin_program_run_id':json.loads(state2)['last_run_id'],'state_compatibility_version':1,'state_sha256':audit.sha(state2),'state_schema_version':1,'candidate_ledger_schema_version':1,'candidate_task_count':1,'candidate_ledger_sha256':audit.sha(ledger2),'registry_sha256':registry_sha,'adapter_catalog_sha256':audit.sha(source_adapters.CATALOG_PATH.read_bytes())}
            (new_artifact/'state/provenance.json').write_text(json.dumps(provenance2),encoding='utf-8')
            second=restore_run_state.restore(new_artifact,destination2,'1002','1003',registry.REGISTRY)
            self.assertFalse(second['candidate_ledger_migrated_from_legacy_queue'])
            self.assertEqual(second['origin_actions_run_id'],'1002')
            self.assertEqual(second['current_actions_run_id'],'1003')
            self.assertEqual(second['candidate_task_count'],1)
            provenance2['candidate_ledger_sha256']='d'*64
            (new_artifact/'state/provenance.json').write_text(json.dumps(provenance2),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'candidate_ledger_hash_mismatch'):
                restore_run_state.restore(new_artifact,base/'corrupt','1002','1004',registry.REGISTRY)

    def test_current_open_status_requires_current_portal_acceptance_not_a_deadline(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-1','candidate_url':'https://jobs.example/job-1','source_url':'https://jobs.example/list','candidate':{'id':'job-1'},'retrieved_at':'2026-01-01T00:00:00Z'}
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,[observation],'run-1')
        candidate_id=next(iter(ledger['tasks']))
        candidate_fingerprint=ledger['tasks'][candidate_id]['content_fingerprint']
        evidence=[{'url':'https://jobs.example/job-1','claim':'detail page identifies job-1','locator':'Title field'}]
        result={'candidate_id':candidate_id,'candidate_fingerprint':candidate_fingerprint,'status':'insufficient_evidence','reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z','evidence':evidence,'current_open_status':'open_per_page'}
        with self.assertRaisesRegex(ValueError,'current_status_value_not_allowed'):
            candidate_ledger.apply_reviews(ledger,[result],'review-1')
        result['current_open_status']='open'
        result['current_status_evidence']={'status':'open','scope':'application_portal','url':'https://jobs.example/job-1','claim':'Applications will be accepted until 22 November 2026.','locator':'Deadline field'}
        with self.assertRaisesRegex(ValueError,'explicit_portal_acceptance_evidence'):
            candidate_ledger.apply_reviews(ledger,[result],'review-deadline')
        result['current_status_evidence']['claim']=candidate_ledger.CURRENT_STATUS_CLAIMS['open']
        with self.assertRaisesRegex(ValueError,'explicit_portal_acceptance_evidence'):
            candidate_ledger.apply_reviews(ledger,[result],'review-unlinked-status')
        result['current_status_evidence']['locator']='Application portal status'
        result['evidence'].append({'field':'current_open_status','url':'https://jobs.example/job-1','claim':candidate_ledger.CURRENT_STATUS_CLAIMS['open'],'locator':'Application portal status'})
        candidate_ledger.apply_reviews(ledger,[result],'review-live-portal')

    def test_sample_adapter_catalog_is_additive_and_completeness_fails_closed(self):
        registry_before=registry.REGISTRY.read_bytes()
        ids=json.loads((audit.MAINT/'round_002/sample_manifest.json').read_text())['source_ids']
        rows=registry.load(registry.REGISTRY)['sources']
        sample=[row for row in rows if row['source_id'] in set(ids)]
        adapted=source_adapters.apply_catalog(sample)
        self.assertEqual(len(sample),10)
        self.assertEqual(len(adapted),10)
        self.assertTrue(all(item.get('monitor_endpoints') for item in adapted))
        self.assertEqual(registry.REGISTRY.read_bytes(),registry_before)
        incomplete=b'<html><head><title>Jobs</title></head><body><h1>Teaching and research</h1><p>Official recruitment opportunities from the University of Helsinki.</p><a href="/job/1">PhD role</a></body></html>'
        list_rows,scope=source_adapters.semantic_result('helsinki_successfactors','https://jobs.helsinki.fi/search',incomplete)
        self.assertFalse(scope['_complete'])
        self.assertEqual(len(list_rows),1)
        expanded=b'<html><head><title>Max Planck Jobboard</title></head><body><h1>Jobboard</h1><p>5 results. Show more for Young Researchers.</p></body></html>'
        _,scope=source_adapters.semantic_result('mpg_jobboard','https://www.mpg.de/jobboard',expanded)
        self.assertFalse(scope['_complete'])
        ubc=b'<html><head><title>Geography Graduate Admissions</title></head><body><h1>Geography</h1><p>MA MSc PhD Funding application</p></body></html>'
        _,scope=source_adapters.semantic_result('ubc_geography_admissions','https://geog.ubc.ca/graduate/admissions/',ubc)
        self.assertTrue(scope['_complete'])

    def test_eth_list_needs_explicit_total_and_terminal_page_evidence(self):
        card='<a class=\"job-ad__item__link\" href=\"/job/view/J1\"><h3>Doctoral position in geography</h3></a>'
        no_total=f'<html><body>{card}</body></html>'.encode()
        rows,scope=audit.semantic_result('eth_listing','https://jobs.ethz.ch/',no_total)
        self.assertEqual(len(rows),1)
        self.assertFalse(scope['_complete'])
        proven=f'<html><body><p>1 open position</p>{card}</body></html>'.encode()
        _,scope=audit.semantic_result('eth_listing','https://jobs.ethz.ch/',proven)
        self.assertTrue(scope['_complete'])
        another_page=f'<html><body><p>2 open positions</p>{card}<a href=\"/?page=2\">2</a></body></html>'.encode()
        _,scope=audit.semantic_result('eth_listing','https://jobs.ethz.ch/',another_page)
        self.assertFalse(scope['_complete'])

    def test_missing_agent_result_is_not_attempted_and_duplicate_is_rejected(self):
        rows = audit.reconcile_task_results(['a', 'b'], [{'source_id': 'a', 'outcome': 'partial'}])
        self.assertEqual([x['outcome'] for x in rows], ['partial', 'not_attempted'])
        with self.assertRaises(ValueError):
            audit.reconcile_task_results(['a'], [{'source_id': 'a'}, {'source_id': 'a'}])

    def test_zero_denominator_is_unknown_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); regp=base/'registry.json'; runs=base/'runs'
            regp.write_text(json.dumps({'sources': []}), encoding='utf-8')
            args=argparse.Namespace(run_id='empty-run',live=True,state_dir=str(base/'state'),budget=1,concurrency=1,timeout=1,retries=0,per_host_delay=0)
            with patch.object(audit,'REGISTRY',regp), patch.object(audit,'RUNS',runs), contextlib.redirect_stdout(io.StringIO()):
                audit.run(args)
            report=json.loads((runs/'empty-run/daily_report.json').read_text())
            self.assertIsNone(report['coverage'])
            self.assertTrue(report['result_conservation'])
            self.assertEqual(report['planned_sources'],0)

    def test_manifest_budget_and_resume_keep_one_result_per_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); regp=base/'registry.json'; runs=base/'runs'; state=base/'state'
            source_rows=[{'source_id':f's{i}','active':True,'enabled_for_daily_audit':True,'canonical_url':f'https://e.test/{i}','monitor_endpoints':[]} for i in range(3)]
            regp.write_text(json.dumps({'sources':source_rows}), encoding='utf-8')
            args=argparse.Namespace(run_id='fixed-run',live=True,state_dir=str(state),budget=1,concurrency=1,timeout=1,retries=0,per_host_delay=0)
            def fake_check(source,*unused):
                return {'run_id':'fixed-run','task_id':'fixed-run:'+source['source_id'],'source_id':source['source_id'],'outcome':'needs_endpoint','attempted':True,'started_at':None,'completed_at':'2026-01-01T00:00:00Z','scope':'test','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':200,'first_observed':False,'evidence':[],'reason':'test_no_adapter','candidate_count':0,'endpoints':[]}
            with patch.object(audit,'REGISTRY',regp), patch.object(audit,'RUNS',runs), patch.object(audit,'check_one',side_effect=fake_check), contextlib.redirect_stdout(io.StringIO()):
                audit.run(args)
            args.budget=3
            with patch.object(audit,'REGISTRY',regp), patch.object(audit,'RUNS',runs), patch.object(audit,'check_one',side_effect=fake_check), contextlib.redirect_stdout(io.StringIO()):
                audit.run(args)
            rows=[json.loads(x) for x in (runs/'fixed-run/source_checks.jsonl').read_text().splitlines()]
            self.assertEqual(len(rows),3)
            self.assertEqual(len({x['source_id'] for x in rows}),3)
            self.assertEqual(CounterForTest(x['outcome'] for x in rows), {'needs_endpoint':3})
            report=json.loads((runs/'fixed-run/daily_report.json').read_text())
            self.assertTrue(report['result_conservation'])
            self.assertEqual(report['planned_sources'],3)
            self.assertFalse(report['candidate_data_written_to_formal_site'])
            state_snapshot=json.loads((state/'state.json').read_text())
            self.assertEqual(state_snapshot['last_run_id'],'fixed-run')
            self.assertTrue(state_snapshot['last_run_completed_at'])

    def test_explicit_source_id_manifest_limits_run_and_records_full_registry_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); regp=base/'registry.json'; runs=base/'runs'; state=base/'state'; idsfile=base/'sample.json'
            source_rows=[{'source_id':f's{i}','active':True,'enabled_for_daily_audit':True,'canonical_url':f'https://e.test/{i}','monitor_endpoints':[]} for i in range(3)]
            regp.write_text(json.dumps({'sources':source_rows}), encoding='utf-8')
            idsfile.write_text(json.dumps({'source_ids':['s2','s0']}), encoding='utf-8')
            args=argparse.Namespace(run_id='subset-run',live=True,state_dir=str(state),require_state=False,source_ids_file=str(idsfile),http_request_budget=7,budget=2,concurrency=1,timeout=1,retries=0,per_host_delay=0)
            def fake_check(source,*unused):
                return {'run_id':'subset-run','task_id':'subset-run:'+source['source_id'],'source_id':source['source_id'],'outcome':'needs_endpoint','attempted':True,'started_at':None,'completed_at':'2026-01-01T00:00:00Z','scope':'test','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':200,'first_observed':False,'evidence':[],'reason':'test_no_adapter','candidate_count':0,'endpoints':[]}
            with patch.object(audit,'REGISTRY',regp), patch.object(audit,'RUNS',runs), patch.object(audit,'check_one',side_effect=fake_check), contextlib.redirect_stdout(io.StringIO()):
                audit.run(args)
            manifest=json.loads((runs/'subset-run/manifest.json').read_text())
            report=json.loads((runs/'subset-run/daily_report.json').read_text())
            rows=[json.loads(x) for x in (runs/'subset-run/source_checks.jsonl').read_text().splitlines()]
            self.assertEqual(manifest['planned_source_ids'],['s2','s0'])
            self.assertEqual(manifest['active_registry_source_count'],3)
            self.assertEqual(manifest['scope_mode'],'explicit_source_subset')
            self.assertEqual(report['planned_sources'],2)
            self.assertEqual([x['source_id'] for x in rows],['s2','s0'])


def CounterForTest(values):
    out={}
    for value in values: out[value]=out.get(value,0)+1
    return out


if __name__=='__main__':
    unittest.main()
