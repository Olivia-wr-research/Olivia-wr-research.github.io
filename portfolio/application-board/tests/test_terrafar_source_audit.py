import argparse
import contextlib
import io
import json
import socket
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / 'portfolio/application-board/scripts'))
import terrafar_source_registry as registry
import terrafar_source_audit as audit


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

    def test_candidate_review_queue_is_pending_and_not_a_production_write(self):
        source=self.source()
        key=audit.key_for('https://example.test/list','fake')
        state={'snapshots':{key:{'semantic_hash':'b'*64,'semantic_rows':[{'id':'candidate-1','title':'Example PhD'}],'content_hash':'c'*64,'last_success_at':'2026-01-01T00:00:00Z'}}}
        results=[{'source_id':'test-source','endpoints':[{'endpoint_id':'test-source:primary','outcome':'checked_changed','candidate_count':1}]}]
        rows=audit.build_candidate_review_queue('queue-run',[source],state,results)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['source_id'],'test-source')
        self.assertEqual(rows[0]['candidate_decision'],'pending')
        self.assertEqual(rows[0]['business_status'],'unknown')
        self.assertEqual(rows[0]['skill_verification'],'pending_human_or_codex_review')
        self.assertFalse(rows[0]['formal_site_write'])
        stale=audit.build_candidate_review_queue('failed-run',[source],state,[{'source_id':'test-source','endpoints':[{'endpoint_id':'test-source:primary','outcome':'failed','candidate_count':0}]}])
        self.assertEqual(stale,[])

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
