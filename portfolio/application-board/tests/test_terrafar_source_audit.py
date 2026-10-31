import argparse
import contextlib
from concurrent.futures import ThreadPoolExecutor
import io
import json
import socket
import subprocess
import sys
import tempfile
import time
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
import terrafar_prepare_data_review as prepare_data_review


def assignment_manifest(rows):
    provenance_fields = ("source_actions_run_id", "source_program_run_id", "source_capture_id")
    tasks = []
    all_source_ids = set()
    for row in rows:
        provenance = {field: row.get(field) for field in provenance_fields}
        source_run_ids = sorted(f"{field}:{provenance[field]}" for field in provenance_fields
                                if provenance[field] is not None)
        all_source_ids.update(source_run_ids)
        tasks.append({field: row.get(field) for field in (
            "candidate_id", "candidate_fingerprint", "source_id", "endpoint_id", "candidate_key", "candidate_url")}
            | {"review_task_kind": row.get("review_task_kind", "content_review"),
               "assigned_agent": row.get("reviewer"), "source_provenance": provenance,
               "source_run_ids": source_run_ids})
    return {"format": "terrafar-review-assignment-v1", "skill": candidate_ledger.skill_pin(),
            "source_run_ids": sorted(all_source_ids), "tasks": tasks}


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


class WorkflowRecoveryGuardTests(unittest.TestCase):
    def test_bootstrap_selectors_only_apply_on_first_attempt(self):
        workflow=(ROOT/'.github/workflows/terrafar-source-maintenance.yml').read_text(encoding='utf-8')
        self.assertIn('if [[ "${GITHUB_RUN_ATTEMPT:-1}" == 1 ]]',workflow)
        self.assertIn('&& "${GITHUB_RUN_ATTEMPT:-1}" == 1',workflow)
        self.assertIn('No prior successful maintenance run with an unexpired state artifact was found',workflow)

    def test_restore_selection_is_versioned_and_rejects_legacy_replay(self):
        workflow=(ROOT/'.github/workflows/terrafar-source-maintenance.yml').read_text(encoding='utf-8')
        self.assertIn("      - 'main'",workflow)
        self.assertIn('startswith("terrafar-source-maintenance-state-v3-")',workflow)
        self.assertIn('startswith("terrafar-source-maintenance-state-")',workflow)
        self.assertIn('name: terrafar-source-maintenance-state-v3-${{ github.run_id }}-${{ github.run_attempt }}',workflow)
        self.assertIn('Legacy bootstrap is one-time only; a version 3 state artifact already exists in this repository.',workflow)
        self.assertIn('Refusing stale explicit restore run',workflow)
        self.assertIn('selected="$(find_valid_run \'*\' || true)"',workflow)
        self.assertIn('latest_compatible="$(find_valid_run \'*\' || true)"',workflow)


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

    def test_v1_candidate_ledger_migration_preserves_stable_ids_and_review_history(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-v1','candidate_url':'https://jobs.example/job-v1','source_url':'https://jobs.example/list','candidate':{'id':'job-v1'},'retrieved_at':'2026-01-01T00:00:00Z'}
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,[observation],'run-old')
        candidate_id=next(iter(ledger['tasks']))
        ledger['tasks'][candidate_id]['review_history']=[{'status':'insufficient_evidence','reviewer':'verifier','run_id':'old','finding':{'reason':'missing evidence'}}]
        ledger['schema_version']=1
        migrated=candidate_ledger.migrate_ledger_payload(ledger)
        self.assertEqual(migrated['schema_version'],2)
        self.assertIn(candidate_id,migrated['tasks'])
        self.assertEqual(migrated['tasks'][candidate_id]['status'],'pending')
        self.assertEqual(migrated['tasks'][candidate_id]['review_history'],ledger['tasks'][candidate_id]['review_history'])
        self.assertEqual(migrated['tasks'][candidate_id]['current_open_status'],'unknown')
        self.assertEqual(migrated['migration_history'][-1]['preserved_task_count'],1)

    def test_unknown_application_status_is_queued_separately_from_verified_content(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-status','candidate_url':'https://jobs.example/job-status','source_url':'https://jobs.example/list','candidate':{'id':'job-status'},'retrieved_at':'2026-01-01T00:00:00Z'}
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,[observation],'run-1')
        task=next(iter(ledger['tasks'].values()))
        task['status']='verified'
        self.assertEqual(candidate_ledger.open_tasks(ledger),[])
        status_queue=candidate_ledger.open_status_tasks(ledger,today='2026-01-03')
        self.assertEqual(len(status_queue),1)
        self.assertEqual(status_queue[0]['review_task_kind'],'current_open_status_review')
        item={'url':task['candidate_url'],'claim':'The application page could not be loaded for status confirmation.','locator':'Application route response','page_content_sha256':'a'*64}
        result={'candidate_id':task['candidate_id'],'candidate_fingerprint':task['content_fingerprint'],'current_open_status':'unknown','evidence':[item],'reviewer':'opportunity_verifier','reviewed_at':'2026-01-03T00:00:00Z','reason':'portal state not confirmed'}
        candidate_ledger.apply_open_status_reviews(ledger,[result],'status-run-1')
        candidate_ledger.apply_open_status_reviews(ledger,[result],'status-run-2')
        self.assertEqual(len(task['open_status_history']),1)
        self.assertEqual(task['status'],'verified')
        self.assertEqual(len(candidate_ledger.open_status_tasks(ledger,today='2026-01-04')),1)

    def test_verified_open_status_near_deadline_is_rechecked_more_frequently(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-near-deadline','candidate_url':'https://jobs.example/job-near-deadline','source_url':'https://jobs.example/list','candidate':{'id':'job-near-deadline'},'retrieved_at':'2026-01-01T00:00:00Z'}
        ledger=candidate_ledger.empty_ledger(); candidate_ledger.merge_observations(ledger,[observation],'run-1')
        task=next(iter(ledger['tasks'].values())); task['status']='verified'
        task['current_open_status']='open'; task['current_open_status_checked_at']='2026-01-01T00:00:00Z'
        task['review_history']=[{'status':'verified','finding':{'deadline':{'value':'2026-01-05'}}}]
        self.assertEqual(len(candidate_ledger.open_status_tasks(ledger,today='2026-01-02')),1)
        task['current_open_status_checked_at']='2026-01-01T00:00:00Z'
        task['review_history']=[{'status':'verified','finding':{'deadline':{'value':'2026-03-01'}}}]
        self.assertEqual(candidate_ledger.open_status_tasks(ledger,today='2026-01-02'),[])

    def test_open_status_review_requires_portal_page_hash(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-status-hash','candidate_url':'https://jobs.example/job-status-hash','source_url':'https://jobs.example/list','candidate':{'id':'job-status-hash'},'retrieved_at':'2026-01-01T00:00:00Z'}
        ledger=candidate_ledger.empty_ledger(); candidate_ledger.merge_observations(ledger,[observation],'run-1')
        task=next(iter(ledger['tasks'].values())); task['status']='verified'
        evidence=[{'field':'current_open_status','url':task['candidate_url'],'claim':candidate_ledger.CURRENT_STATUS_CLAIMS['open'],'locator':'Apply button'}]
        result={'candidate_id':task['candidate_id'],'candidate_fingerprint':task['content_fingerprint'],'current_open_status':'open','current_status_evidence':{'status':'open','scope':'application_portal','claim':candidate_ledger.CURRENT_STATUS_CLAIMS['open'],'url':task['candidate_url'],'locator':'Apply button'},'evidence':evidence,'reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z'}
        with self.assertRaisesRegex(ValueError,'explicit_portal_acceptance_evidence'):
            candidate_ledger.apply_open_status_reviews(ledger,[result],'run-2')

    def test_incomplete_partial_candidate_rows_are_not_merged(self):
        source=self.source()
        state={'snapshots':{}}
        result=[{'source_id':'test-source','endpoints':[{'endpoint_id':'test-source:primary','adapter':'fake','outcome':'partial','content_complete':False,'candidate_rows':[{'id':'partial-only'}]}]}]
        self.assertEqual(audit.build_candidate_observations([source],state,result),[])
        result[0]['endpoints'][0]['content_complete']=True
        self.assertEqual(len(audit.build_candidate_observations([source],state,result)),1)

    def test_incomplete_sources_stay_in_retry_queue_until_complete_success(self):
        state={'maintenance_retry_ids':['old','retry-me']}
        plan=['retry-me','new']
        audit.update_maintenance_retry_queue(state,plan,{'retry-me':{'outcome':'failed'},'new':{'outcome':'not_attempted'}})
        self.assertEqual(state['maintenance_retry_ids'],['old','retry-me'])
        audit.update_maintenance_retry_queue(state,plan,{'retry-me':{'outcome':'partial'},'new':{'outcome':'blocked'}})
        self.assertEqual(state['maintenance_retry_ids'],['old','retry-me','new'])
        audit.update_maintenance_retry_queue(state,plan,{'retry-me':{'outcome':'checked_unchanged'},'new':{'outcome':'checked_empty'}})
        self.assertEqual(state['maintenance_retry_ids'],['old'])

    def test_persistent_retries_cannot_starve_rotating_sources_across_many_rounds(self):
        sources=[{'source_id':f'source-{index:02d}'} for index in range(36)]
        persistent={'source-00','source-01','source-02'}
        state={'maintenance_retry_ids':sorted(persistent),'maintenance_cursor':0,'maintenance_retry_cursor':0}
        visited=[]; retry_visit_counts={sid:0 for sid in persistent}
        for round_number in range(1,9):
            chosen=audit.select_maintenance_batch(sources,state['maintenance_retry_ids'],state,6)
            selected=[row['source_id'] for row in chosen]
            self.assertEqual(len(selected),6)
            self.assertEqual(len(selected),len(set(selected)))
            self.assertGreaterEqual(len(set(selected)-persistent),4)
            visited.extend(set(selected)-persistent)
            retry_visit_counts.update({sid:retry_visit_counts.get(sid,0)+1 for sid in selected if sid in persistent})
            outcomes={sid:{'outcome':'failed'} for sid in selected if sid in persistent}
            outcomes.update({sid:{'outcome':'checked_unchanged'} for sid in selected if sid not in persistent})
            audit.update_maintenance_retry_queue(state,[row['source_id'] for row in sources],outcomes)
            self.assertTrue(persistent.issubset(state['maintenance_retry_ids']))
        self.assertEqual(set(visited),{row['source_id'] for row in sources}-persistent)
        self.assertTrue(all(count>0 for count in retry_visit_counts.values()))

    def test_single_source_budget_alternates_persistent_retries_and_rotation(self):
        sources=[{'source_id':sid} for sid in ('failed','healthy-1','healthy-2')]
        state={'maintenance_retry_ids':['failed'],'maintenance_retry_turn':True}
        selected=[]
        for _ in range(6):
            selected.append(audit.select_maintenance_batch(sources,state['maintenance_retry_ids'],state,1)[0]['source_id'])
        self.assertEqual(selected[::2],['failed','failed','failed'])
        self.assertEqual(set(selected[1::2]),{'healthy-1','healthy-2'})

    def test_same_run_resume_retries_partial_but_reuses_settled_checks(self):
        sources=[{'source_id':sid} for sid in ('complete','partial','blocked')]
        completed={'complete':{'outcome':'checked_empty'},'partial':{'outcome':'partial'},'blocked':{'outcome':'blocked'}}
        self.assertEqual([row['source_id'] for row in audit.resumable_sources(sources,completed)],['partial','blocked'])

    def test_data_review_patch_is_idempotent_evidence_bound_and_rollback_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ledger_path=root/'candidate_ledger.json'
            formal=root/'positions.mjs'
            output=root/'pending-data'
            active_catalog=root/'active.mjs'
            original='export const positions=[{"id":"formal-1","url":"https://jobs.example/job-review","salary":"unknown salary","funding":"unknown funding"}];\n'
            formal.write_text(original,encoding='utf-8')
            active_catalog.write_text("export const geographyCatalog=[{id:'active-1',url:'https://jobs.example/job-review',salary:'unknown salary',funding:'unknown funding'}];\n",encoding='utf-8')
            ledger=candidate_ledger.empty_ledger()
            observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-review','candidate_url':'https://jobs.example/job-review','source_url':'https://jobs.example/list','candidate':{'id':'job-review'},'retrieved_at':'2026-01-01T00:00:00Z'}
            candidate_ledger.merge_observations(ledger,[observation],'source-run')
            candidate_id=next(iter(ledger['tasks']))
            candidate_ledger.save_ledger(ledger_path,ledger)
            claim={'field':'funding','url':'https://jobs.example/job-review','claim':'funding: CHF 1000 annual salary','locator':'Salary section'}
            result={'candidate_id':candidate_id,'candidate_fingerprint':ledger['tasks'][candidate_id]['content_fingerprint'],'source_id':'s','endpoint_id':'s:list','candidate_key':'job-review','source_url':'https://jobs.example/list','candidate_url':'https://jobs.example/job-review','formal_record_id':'formal-1','status':'verified','decision_scope':'page_content','reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z','source_capture_id':'test-capture-1','evidence':[claim],'content_verification':{'status':'verified','evidence':[dict(claim)]},'funding':{'status':'verified_as_stated','value':'CHF 1000 annual salary','evidence_url':'https://jobs.example/job-review','locator':'Salary section'},'formal_patch':{'salary':'CHF 1000 annual salary'}}
            result_path=root/'review.json'; result_path.write_text(json.dumps(result),encoding='utf-8')
            first=prepare_data_review.prepare(ledger_path,result_path,formal,output,'data-review-run',active_catalog)
            wrong_target=dict(result); wrong_target['active_catalog_record_id']='active-wrong'
            wrong_target_path=root/'wrong-target-review.json'
            wrong_target_path.write_text(json.dumps(wrong_target),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'active_catalog_target_identity_mismatch'):
                prepare_data_review.prepare(ledger_path,wrong_target_path,formal,output,'wrong-target-run',active_catalog)
            unsupported_text=dict(result); unsupported_text['formal_patch']={'salary':'Guaranteed CHF 1000 annual salary'}
            unsupported_text_path=root/'unsupported-claim.json'
            unsupported_text_path.write_text(json.dumps(unsupported_text),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'formal_patch_field_not_supported_by_verified_finding:salary'):
                prepare_data_review.prepare(ledger_path,unsupported_text_path,formal,output,'unsupported-claim-run',active_catalog)
            stale=json.loads(Path(first['patch_path']).read_text(encoding='utf-8'))
            stale.pop('target_record_id'); stale.pop('target_identity_source'); stale.pop('target_identity_verified')
            Path(first['patch_path']).write_text(json.dumps(stale,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            preview=Path(first['preview_path'])
            stale_preview=json.loads(preview.read_text(encoding='utf-8'))
            stale_preview.pop('target_record_id'); stale_preview.pop('target_identity_source')
            preview.write_text(json.dumps(stale_preview,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            second=prepare_data_review.prepare(ledger_path,result_path,formal,output,'data-review-run-retry',active_catalog)
            before_patch=Path(first['patch_path']).read_text(encoding='utf-8')
            unrelated=candidate_ledger.load_ledger(ledger_path,require_existing=True)
            unrelated['revision']+=1
            candidate_ledger.save_ledger(ledger_path,unrelated)
            third=prepare_data_review.prepare(ledger_path,result_path,formal,output,'data-review-run-after-unrelated-review',active_catalog)
            restored=candidate_ledger.load_ledger(ledger_path,require_existing=True)
            patch=json.loads(Path(first['patch_path']).read_text())
            self.assertEqual(first['ledger_revision'],second['ledger_revision'])
            self.assertEqual(Path(third['patch_path']).read_text(encoding='utf-8'),before_patch)
            self.assertEqual(len(restored['tasks'][candidate_id]['review_history']),1)
            self.assertEqual(patch['changes']['salary']['before'],'unknown salary')
            self.assertEqual(patch['rollback']['salary'],'unknown salary')
            self.assertTrue(first['rollback_roundtrip_verified'])
            self.assertFalse(patch['formal_data_written'])
            self.assertFalse(patch['published'])
            self.assertEqual(formal.read_text(encoding='utf-8'),original)
            self.assertEqual(patch['target_record_id'],'active-1')
            self.assertEqual(patch['target_identity_source'],'active_catalog_exact_url')
            self.assertTrue(patch['target_identity_verified'])
            self.assertTrue(list((output/'history').glob('*.json')))

    def test_data_review_patch_write_failure_does_not_advance_ledger_and_retry_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); ledger_path=root/'candidate_ledger.json'; formal=root/'positions.mjs'; output=root/'pending-data'
            formal.write_text('export const positions=[{"id":"formal-1","url":"https://jobs.example/job-review","salary":"unknown salary"}];\n',encoding='utf-8')
            ledger=candidate_ledger.empty_ledger()
            observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-review','candidate_url':'https://jobs.example/job-review','source_url':'https://jobs.example/list','candidate':{'id':'job-review'},'retrieved_at':'2026-01-01T00:00:00Z'}
            candidate_ledger.merge_observations(ledger,[observation],'source-run')
            candidate_id=next(iter(ledger['tasks']))
            candidate_ledger.save_ledger(ledger_path,ledger)
            claim={'field':'funding','url':'https://jobs.example/job-review','claim':'funding: CHF 1000 annual salary','locator':'Salary section'}
            result={'candidate_id':candidate_id,'candidate_fingerprint':ledger['tasks'][candidate_id]['content_fingerprint'],'source_id':'s','endpoint_id':'s:list','candidate_key':'job-review','source_url':'https://jobs.example/list','candidate_url':'https://jobs.example/job-review','formal_record_id':'formal-1','status':'verified','decision_scope':'page_content','reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z','source_capture_id':'test-capture-1','evidence':[claim],'content_verification':{'status':'verified','evidence':[dict(claim)]},'funding':{'status':'verified_as_stated','value':'CHF 1000 annual salary','evidence_url':'https://jobs.example/job-review','locator':'Salary section'},'formal_patch':{'salary':'CHF 1000 annual salary'}}
            result_path=root/'review.json'; result_path.write_text(json.dumps(result),encoding='utf-8')
            original_ledger=ledger_path.read_bytes()
            original_writer=prepare_data_review.write_idempotent_json
            calls={'count':0}
            def fail_preview(path,value,identity_keys):
                calls['count']+=1
                if calls['count']==2:
                    raise OSError('simulated interruption during preview write')
                original_writer(path,value,identity_keys)
            with patch.object(prepare_data_review,'write_idempotent_json',side_effect=fail_preview):
                with self.assertRaisesRegex(OSError,'simulated interruption'):
                    prepare_data_review.prepare(ledger_path,result_path,formal,output,'interrupted-run')
            self.assertEqual(ledger_path.read_bytes(),original_ledger)
            self.assertTrue(list(output.glob('*.json')))
            recovered=prepare_data_review.prepare(ledger_path,result_path,formal,output,'retry-run')
            self.assertEqual(recovered['ledger_status'],'verified')
            self.assertTrue(Path(recovered['preview_path']).exists())
            self.assertEqual(len(candidate_ledger.load_ledger(ledger_path,True)['tasks'][candidate_id]['review_history']),1)

    def test_concurrent_data_review_preparations_retain_both_ledger_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); ledger_path=root/'candidate_ledger.json'; formal=root/'positions.mjs'; output=root/'pending-data'
            formal.write_text('export const positions=[{"id":"formal-1","url":"https://jobs.example/job-1","salary":"unknown"},{"id":"formal-2","url":"https://jobs.example/job-2","salary":"unknown"}];\n',encoding='utf-8')
            ledger=candidate_ledger.empty_ledger(); results=[]
            for n in (1,2):
                observation={'source_id':'s','endpoint_id':'s:list','candidate_key':f'job-{n}','candidate_url':f'https://jobs.example/job-{n}','source_url':'https://jobs.example/list','candidate':{'id':f'job-{n}'},'retrieved_at':'2026-01-01T00:00:00Z'}
                candidate_ledger.merge_observations(ledger,[observation],f'source-run-{n}')
                candidate_id=candidate_ledger.stable_candidate_id('s','s:list',f'job-{n}')
                finding={'status':'verified_as_stated','value':f'CHF {n}000 annual salary','evidence_url':observation['candidate_url'],'locator':'Salary section'}
                claim={'field':'funding','url':observation['candidate_url'],'claim':f"funding: {finding['value']}",'locator':'Salary section'}
                results.append({'candidate_id':candidate_id,'candidate_fingerprint':ledger['tasks'][candidate_id]['content_fingerprint'],'source_id':'s','endpoint_id':'s:list','candidate_key':f'job-{n}','source_url':'https://jobs.example/list','candidate_url':observation['candidate_url'],'formal_record_id':f'formal-{n}','status':'verified','decision_scope':'page_content','reviewer':'opportunity_verifier','reviewed_at':f'2026-01-0{n+2}T00:00:00Z','source_capture_id':f'capture-{n}','evidence':[claim],'content_verification':{'status':'verified','evidence':[dict(claim)]},'funding':finding,'formal_patch':{'salary':finding['value']}})
            candidate_ledger.save_ledger(ledger_path,ledger)
            paths=[]
            for n,result in enumerate(results,1):
                path=root/f'review-{n}.json'; path.write_text(json.dumps(result),encoding='utf-8'); paths.append(path)
            original_load=candidate_ledger.load_ledger
            def delayed_load(*args,**kwargs):
                value=original_load(*args,**kwargs)
                time.sleep(0.03)
                return value
            def execute(pair):
                result_path,run_id=pair
                return prepare_data_review.prepare(ledger_path,result_path,formal,output,run_id)
            with patch.object(candidate_ledger,'load_ledger',side_effect=delayed_load):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    list(pool.map(execute,[(paths[0],'parallel-1'),(paths[1],'parallel-2')]))
            saved=candidate_ledger.load_ledger(ledger_path,require_existing=True)
            self.assertEqual({task['status'] for task in saved['tasks'].values()},{'verified'})
            self.assertEqual(sum(len(task['review_history']) for task in saved['tasks'].values()),2)

    def test_data_review_rejects_formal_record_url_mismatch_before_any_ledger_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); ledger_path=root/'candidate_ledger.json'; formal=root/'positions.mjs'; output=root/'pending-data'
            formal.write_text('export const positions=[{"id":"formal-1","url":"https://jobs.example/different","salary":"unknown salary"}];\n',encoding='utf-8')
            ledger=candidate_ledger.empty_ledger()
            observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-review','candidate_url':'https://jobs.example/job-review','source_url':'https://jobs.example/list','candidate':{'id':'job-review'},'retrieved_at':'2026-01-01T00:00:00Z'}
            candidate_ledger.merge_observations(ledger,[observation],'source-run'); candidate_ledger.save_ledger(ledger_path,ledger)
            candidate_id=next(iter(ledger['tasks']))
            result={'candidate_id':candidate_id,'candidate_fingerprint':ledger['tasks'][candidate_id]['content_fingerprint'],'source_id':'s','endpoint_id':'s:list','candidate_key':'job-review','source_url':'https://jobs.example/list','candidate_url':'https://jobs.example/job-review','formal_record_id':'formal-1','status':'verified','decision_scope':'page_content','reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z','source_capture_id':'test-capture-1','evidence':[],'content_verification':{'status':'verified','evidence':[]},'funding':{'status':'verified_as_stated','value':'CHF 1000','evidence_url':'https://jobs.example/job-review','locator':'Salary'},'formal_patch':{'salary':'CHF 1000'}}
            result_path=root/'review.json'; result_path.write_text(json.dumps(result),encoding='utf-8')
            before=ledger_path.read_bytes()
            with self.assertRaisesRegex(ValueError,'formal_record_url_identity_mismatch'):
                prepare_data_review.prepare(ledger_path,result_path,formal,output,'wrong-url-run')
            self.assertEqual(ledger_path.read_bytes(),before)

    def test_imports_launch_readiness_reviews_with_identity_and_assignment_checks(self):
        results_dir=Path(__file__).parents[1]/'maintenance/terrafar-source-audit/agent-results'
        rows=[json.loads((results_dir/name).read_text(encoding='utf-8')) for name in (
            'launch-readiness-eth-ai-12136.json','launch-readiness-eth-atmospheric-chemistry.json',
            'launch-readiness-vienna-6233.json')]
        assignment=json.loads((results_dir/'launch-readiness-import-assignment.json').read_text(encoding='utf-8'))
        ledger=candidate_ledger.empty_ledger()
        # The first two records represent tasks recovered from the prior Actions artifact.
        for result in rows[:2]:
            cid=result['candidate_id']; source_id=result['source_id']; endpoint_id=result['endpoint_id']; key=result['candidate_key']
            ledger['tasks'][cid]={'candidate_id':cid,'source_id':source_id,'endpoint_id':endpoint_id,'candidate_key':key,
                'candidate_url':result['candidate_url'],'source_url':result['candidate_url'],'candidate':{},
                'content_fingerprint':result['candidate_fingerprint'],'status':'pending','review_history':[],
                'current_open_status':'unknown','open_status_history':[],'formal_site_write':False}
        candidate_ledger.merge_review_results(ledger,rows,'actions-run-1',assignment)
        self.assertEqual(len(ledger['tasks']),3)
        self.assertTrue(all(ledger['tasks'][row['candidate_id']]['status']=='verified' for row in rows))
        self.assertTrue(all(ledger['tasks'][row['candidate_id']]['current_open_status']=='unknown' for row in rows))
        self.assertEqual(sum(len(ledger['tasks'][row['candidate_id']]['review_history']) for row in rows),3)
        revision=ledger['revision']
        candidate_ledger.merge_review_results(ledger,rows,'actions-run-1',assignment)
        self.assertEqual(ledger['revision'],revision)
        self.assertEqual(sum(len(ledger['tasks'][row['candidate_id']]['review_history']) for row in rows),3)
        wrong=json.loads(json.dumps(assignment)); wrong['tasks'][0]['source_id']='wrong-source'
        with self.assertRaisesRegex(ValueError,'review_result_assignment_identity_mismatch'):
            candidate_ledger.merge_review_results(ledger,rows,'actions-run-2',wrong)
        incomplete=json.loads(json.dumps(assignment)); incomplete['tasks'][0].pop('candidate_fingerprint')
        with self.assertRaisesRegex(ValueError,'review_assignment_task_identity_incomplete'):
            candidate_ledger.merge_review_results(ledger,rows,'actions-run-3',incomplete)
        wrong_run=json.loads(json.dumps(rows)); wrong_run[0]['source_actions_run_id']='99999999999'
        with self.assertRaisesRegex(ValueError,'review_result_source_provenance_not_assigned'):
            candidate_ledger.merge_review_results(ledger,wrong_run,'actions-run-4',assignment)

    def test_review_import_merges_embedded_candidate_observation_before_review_idempotently(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-captured','candidate_url':'https://jobs.example/captured','source_url':'https://jobs.example/list','candidate':{'id':'captured','title':'Captured from source'},'retrieved_at':'2026-01-01T00:00:00Z','parser':'agent_page_capture'}
        candidate_id=candidate_ledger.stable_candidate_id('s','s:list','job-captured')
        candidate_fingerprint=candidate_ledger.digest(observation['candidate'])
        review={'review_task_kind':'content_review','candidate_id':candidate_id,'candidate_fingerprint':candidate_fingerprint,'source_id':'s','endpoint_id':'s:list','candidate_key':'job-captured','candidate_url':'https://jobs.example/captured','candidate_observation':observation,'source_capture_id':'capture-1','status':'insufficient_evidence','reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z','evidence':[],'reason':'Captured page fields do not support a formal update.'}
        second_observation={**observation,'candidate_key':'job-captured-2','candidate_url':'https://jobs.example/captured-2','candidate':{'id':'captured-2','title':'Second captured record'}}
        second_id=candidate_ledger.stable_candidate_id('s','s:list','job-captured-2')
        second_review={**review,'candidate_id':second_id,'candidate_fingerprint':candidate_ledger.digest(second_observation['candidate']),'candidate_key':'job-captured-2','candidate_url':second_observation['candidate_url'],'candidate_observation':second_observation}
        second_review['source_capture_id']='capture-2'
        assignment=assignment_manifest([review,second_review])
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_review_results(ledger,[review,second_review],'actions-run-1',assignment)
        candidate_ledger.merge_review_results(ledger,[review,second_review],'actions-run-1',assignment)
        task=ledger['tasks'][candidate_id]
        self.assertEqual(len(ledger['tasks']),2)
        self.assertEqual(task['status'],'insufficient_evidence')
        self.assertEqual(task['parser'],'agent_page_capture')
        self.assertEqual(task['current_open_status'],'unknown')
        self.assertEqual(len(task['review_history']),1)
        self.assertEqual(sum(event['event_type']=='observed' for event in ledger['events']),2)
        candidate_ledger.merge_review_results(ledger,[review,second_review],'actions-run-2',assignment)
        self.assertEqual(len(ledger['tasks']),2)
        self.assertEqual(len(task['review_history']),1)
        self.assertEqual(task['observed_runs'],['actions-run-1','actions-run-2'])
        unassigned=assignment_manifest([review]); unassigned['tasks']=[]; unassigned['source_run_ids']=[]
        with self.assertRaisesRegex(ValueError,'review_result_not_assigned'):
            candidate_ledger.merge_review_results(ledger,[review], 'actions-run-3', unassigned)
        stale_assignment=assignment_manifest([review]); stale_assignment['tasks'][0]['candidate_fingerprint']='stale-fingerprint'
        with self.assertRaisesRegex(ValueError,'review_result_fingerprint_not_assigned'):
            candidate_ledger.merge_review_results(ledger,[review],'actions-run-4',stale_assignment)

    def test_review_import_rejects_candidate_observation_with_wrong_stable_identity(self):
        observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-captured','candidate_url':'https://jobs.example/captured','source_url':'https://jobs.example/list','candidate':{'id':'captured'},'retrieved_at':'2026-01-01T00:00:00Z'}
        review={'review_task_kind':'content_review','candidate_id':'tcand-wrong','candidate_fingerprint':candidate_ledger.digest(observation['candidate']),'source_id':'s','endpoint_id':'s:list','candidate_key':'job-captured','candidate_url':observation['candidate_url'],'candidate_observation':observation,'source_capture_id':'capture-1','status':'insufficient_evidence','reviewer':'opportunity_verifier','reviewed_at':'2026-01-02T00:00:00Z','evidence':[]}
        assignment=assignment_manifest([review])
        with self.assertRaisesRegex(ValueError,'review_result_stable_identity_mismatch'):
            candidate_ledger.merge_review_results(candidate_ledger.empty_ledger(),[review],'actions-run-1',assignment)

    def test_reviewed_candidate_maps_to_exactly_one_active_catalog_record(self):
        candidate_url='https://jobs.ethz.ch/job/view/JOPG_ethz_UtuGzrXTpseTskgjY9'
        active_catalog=Path(__file__).parents[3]/'docs/apps/application-board/geography-opportunities.mjs'
        self.assertEqual(prepare_data_review.find_active_catalog_match(active_catalog,candidate_url),'geo-eth-atmosphere')
        with tempfile.TemporaryDirectory() as tmp:
            repeated=Path(tmp)/'ambiguous.mjs'
            block="record({\n    id:'duplicate',\n    url:'https://example.test/job',\n  }),\n"
            repeated.write_text(block+block,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'active_catalog_url_match_not_unique'):
                prepare_data_review.find_active_catalog_match(repeated,'https://example.test/job')

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
        non_utc_time={**verified,'reviewed_at':'2026-01-03T08:00:00+08:00'}
        with self.assertRaisesRegex(ValueError,'must_be_utc'):
            candidate_ledger.apply_reviews(ledger,[non_utc_time],'review-non-utc-time')
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
        observations=[{'source_id':'s','endpoint_id':'s:list','candidate_key':key,'candidate_url':f'https://jobs.example/{key}','source_url':'https://jobs.example/list','candidate':{'id':key,'title':'Same exact role'},'retrieved_at':'2026-01-01T00:00:00Z'} for key in ('job-1','job-2')]
        ledger=candidate_ledger.empty_ledger()
        candidate_ledger.merge_observations(ledger,observations,'run-1')
        first,second=ledger['tasks'].values()
        result={'candidate_id':first['candidate_id'],'candidate_fingerprint':first['content_fingerprint'],'status':'duplicate','decision_scope':'duplicate','duplicate_of':'missing-stable-id','reviewer':'audit_reviewer','reviewed_at':'2026-01-02T00:00:00Z','evidence':[{'url':first['candidate_url'],'claim':'Same role identifier as another record','locator':'Role identifier'}]}
        with self.assertRaisesRegex(ValueError,'duplicate_candidate_review_missing_or_invalid_target'):
            candidate_ledger.apply_reviews(ledger,[result],'review-duplicate-invalid')
        result['duplicate_of']=second['candidate_id']
        result['duplicate_match']={'source_fingerprint':first['content_fingerprint'],'target_fingerprint':second['content_fingerprint'],'matching_fields':['title'],'identity_claim':'Both official pages identify the same position'}
        result['evidence'].append({'url':second['candidate_url'],'claim':'Same exact role title as the first page','locator':'Title field'})
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
            review_file.write_text(json.dumps([{'candidate_id':candidate_id,'source_id':'eth-doctoral-listing','endpoint_id':'eth-doctoral-listing:primary','candidate_key':row['candidate_key'],'candidate_url':row['candidate_url'],'ledger_review_status':'verified','content_verification':{'status':'verified','evidence':evidence},'application_route':{'status':'unknown'},'current_open_status':'unknown','verifier':'opportunity_verifier','verified_at':'2026-10-23T00:30:00Z'}]),encoding='utf-8')
            first=restore_run_state.restore(legacy,destination1,'1001','1002',registry.REGISTRY,allow_legacy=True,review_results_path=review_file)
            self.assertTrue(first['candidate_ledger_migrated_from_legacy_queue'])
            self.assertEqual(first['candidate_task_count'],1)
            restored_ledger=candidate_ledger.load_ledger(destination1/'candidate_ledger.json',require_existing=True)
            self.assertEqual(restored_ledger['tasks'][candidate_id]['status'],'insufficient_evidence')
            self.assertEqual(restored_ledger['tasks'][candidate_id]['review_history'][0]['finding']['current_open_status'],'unknown')
            self.assertIn('no candidate_fingerprint',restored_ledger['tasks'][candidate_id]['review_history'][0]['reason'])
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
            provenance2={'format':'terrafar-maintenance-state-v1','origin_actions_run_id':'1002','origin_program_run_id':json.loads(state2)['last_run_id'],'state_compatibility_version':1,'state_sha256':audit.sha(state2),'state_schema_version':1,'candidate_ledger_schema_version':json.loads(ledger2)['schema_version'],'candidate_task_count':1,'candidate_ledger_sha256':audit.sha(ledger2),'registry_sha256':registry_sha,'adapter_catalog_sha256':audit.sha(source_adapters.CATALOG_PATH.read_bytes())}
            (new_artifact/'state/provenance.json').write_text(json.dumps(provenance2),encoding='utf-8')
            second=restore_run_state.restore(new_artifact,destination2,'1002','1003',registry.REGISTRY)
            self.assertFalse(second['candidate_ledger_migrated_from_legacy_queue'])
            self.assertEqual(second['origin_actions_run_id'],'1002')
            self.assertEqual(second['current_actions_run_id'],'1003')
            self.assertEqual(second['candidate_task_count'],1)
            self.assertFalse(second['candidate_ledger_schema_migrated'])
            provenance2['candidate_ledger_sha256']='d'*64
            (new_artifact/'state/provenance.json').write_text(json.dumps(provenance2),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'candidate_ledger_hash_mismatch'):
                restore_run_state.restore(new_artifact,base/'corrupt','1002','1004',registry.REGISTRY)

    def test_cross_actions_run_restore_migrates_hashed_v1_ledger_without_losing_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); artifact=base/'artifact'; (artifact/'state').mkdir(parents=True)
            registry_sha=audit.sha(registry.REGISTRY.read_bytes())
            state={'schema_version':1,'snapshots':{'https://jobs.example/list\nfake':{'semantic_hash':'a'*64,'semantic_rows':[{'id':'job-1'}],'adapter':'fake'}},'last_run_id':'program-2001','last_registry_sha256':registry_sha}
            state_bytes=json.dumps(state).encode(); (artifact/'state/state.json').write_bytes(state_bytes)
            ledger=candidate_ledger.empty_ledger()
            observation={'source_id':'s','endpoint_id':'s:list','candidate_key':'job-1','candidate_url':'https://jobs.example/job-1','source_url':'https://jobs.example/list','candidate':{'id':'job-1'},'retrieved_at':'2026-01-01T00:00:00Z'}
            candidate_ledger.merge_observations(ledger,[observation],'program-2001')
            candidate_id=next(iter(ledger['tasks']))
            ledger['schema_version']=1
            for name in ('current_open_status','current_status_evidence','current_open_status_checked_at','open_status_history'):
                ledger['tasks'][candidate_id].pop(name,None)
            ledger_bytes=json.dumps(ledger,ensure_ascii=False).encode()
            (artifact/'state/candidate_ledger.json').write_bytes(ledger_bytes)
            provenance={'format':'terrafar-maintenance-state-v1','origin_actions_run_id':'2001','origin_program_run_id':'program-2001','state_compatibility_version':1,'state_sha256':audit.sha(state_bytes),'state_schema_version':1,'candidate_ledger_schema_version':1,'candidate_task_count':1,'candidate_ledger_sha256':audit.sha(ledger_bytes),'registry_sha256':registry_sha,'adapter_catalog_sha256':audit.sha(source_adapters.CATALOG_PATH.read_bytes())}
            (artifact/'state/provenance.json').write_text(json.dumps(provenance),encoding='utf-8')
            restored=restore_run_state.restore(artifact,base/'restored','2001','2002',registry.REGISTRY)
            migrated=json.loads((base/'restored/candidate_ledger.json').read_text())
            self.assertTrue(restored['candidate_ledger_schema_migrated'])
            self.assertEqual(migrated['schema_version'],2)
            self.assertEqual(set(migrated['tasks']),{candidate_id})
            self.assertEqual(migrated['tasks'][candidate_id]['current_open_status'],'unknown')
            self.assertEqual(restored['candidate_task_count'],1)

    def test_cross_actions_run_restore_checks_v3_runner_adapter_and_ledger_implementation_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); artifact=base/'artifact'; (artifact/'state').mkdir(parents=True)
            registry_sha=audit.sha(registry.REGISTRY.read_bytes())
            state={'schema_version':1,'snapshots':{},'last_run_id':'program-7001','last_registry_sha256':registry_sha}
            state_bytes=json.dumps(state,sort_keys=True).encode(); (artifact/'state/state.json').write_bytes(state_bytes)
            ledger=candidate_ledger.empty_ledger(); ledger_bytes=json.dumps(ledger,sort_keys=True).encode()
            (artifact/'state/candidate_ledger.json').write_bytes(ledger_bytes)
            provenance={'format':'terrafar-maintenance-state-v1','origin_actions_run_id':'7001','origin_program_run_id':'program-7001',
                'state_compatibility_version':3,'state_sha256':audit.sha(state_bytes),'state_schema_version':1,
                'candidate_ledger_schema_version':ledger['schema_version'],'candidate_task_count':0,
                'candidate_ledger_sha256':audit.sha(ledger_bytes),'registry_sha256':registry_sha,
                'adapter_catalog_sha256':audit.sha(source_adapters.CATALOG_PATH.read_bytes()),
                'runner_sha256':restore_run_state.runner_sha(),
                'adapter_implementation_sha256':restore_run_state.adapter_implementation_sha(),
                'candidate_ledger_implementation_sha256':restore_run_state.candidate_ledger_implementation_sha()}
            provenance_path=artifact/'state/provenance.json'
            provenance_path.write_text(json.dumps(provenance),encoding='utf-8')
            restored=restore_run_state.restore(artifact,base/'restored','7001','7002',registry.REGISTRY)
            self.assertEqual(restored['origin_actions_run_id'],'7001')
            self.assertEqual(restored['state_compatibility_migrated_from'],None)
            wrong_runner=dict(provenance); wrong_runner['runner_sha256']='0'*64
            provenance_path.write_text(json.dumps(wrong_runner),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'restored_runner_version_mismatch'):
                restore_run_state.restore(artifact,base/'wrong-runner','7001','7003',registry.REGISTRY)
            wrong_adapter=dict(provenance); wrong_adapter['adapter_implementation_sha256']='1'*64
            provenance_path.write_text(json.dumps(wrong_adapter),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'restored_adapter_implementation_version_mismatch'):
                restore_run_state.restore(artifact,base/'wrong-adapter','7001','7004',registry.REGISTRY)
            wrong_ledger=dict(provenance); wrong_ledger['candidate_ledger_implementation_sha256']='2'*64
            provenance_path.write_text(json.dumps(wrong_ledger),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'restored_candidate_ledger_implementation_version_mismatch'):
                restore_run_state.restore(artifact,base/'wrong-ledger','7001','7005',registry.REGISTRY)
            unsupported_compat=dict(provenance); unsupported_compat['state_compatibility_version']=2
            provenance_path.write_text(json.dumps(unsupported_compat),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'restored_state_compatibility_version_unsupported'):
                restore_run_state.restore(artifact,base/'unsupported-compat','7001','7006',registry.REGISTRY)

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
        result['evidence'].append({'field':'current_open_status','url':'https://jobs.example/job-1','claim':candidate_ledger.CURRENT_STATUS_CLAIMS['open'],'locator':'Application portal status','page_content_sha256':'a'*64})
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
