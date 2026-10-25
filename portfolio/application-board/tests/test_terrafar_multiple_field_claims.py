"""Synthetic contract regressions; these do not assess real content accuracy."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from test_terrafar_ai_pipeline import observation, snapshot_for, supported_model_result
import terrafar_candidate_ledger as ledger
import terrafar_model_executor as executor


class MultipleFieldClaimTests(unittest.TestCase):
    def fixture(self):
        state = ledger.empty_ledger()
        ledger.merge_observations(state, [observation()], 'synthetic-source')
        task = executor.claim_batch(state, 'synthetic-worker', run_id='synthetic-run')['tasks'][0]
        snapshot = snapshot_for(task)
        clauses = ['A relevant master degree is required.', 'English C1 is required.', 'Driving experience is preferred.']
        snapshot['text'] += ' ' + ' '.join(clauses)
        snapshot['text_sha256'] = hashlib.sha256(snapshot['text'].encode()).hexdigest()
        model = supported_model_result(task['candidate_url'])
        for index, clause in enumerate(clauses):
            model['fields'].append({'field': 'eligibility', 'status': 'supported', 'raw_value': clause,
                'normalized_value': clause, 'evidence_index': len(model['evidence']), 'reason': None})
            model['evidence'].append({'field': 'eligibility', 'url': snapshot['url'], 'quote': clause,
                'claim': clause, 'locator': f'Qualification {index + 1}'})
        result = executor.validate_model_result(model, task, snapshot, {'provider': 'offline_test'},
                                                '2026-10-25T01:00:00Z')
        return state, task, snapshot, model, result, clauses

    def test_all_clauses_survive_projection_and_ledger_merge(self):
        state, _, _, _, result, clauses = self.fixture()
        self.assertEqual(result['eligibility']['status'], 'multiple_supported_claims')
        self.assertIsNone(result['eligibility']['value'])
        self.assertEqual([c['value'] for c in result['eligibility']['claims']], clauses)
        ledger.apply_reviews(state, [result], 'synthetic-review')
        saved = state['tasks'][result['candidate_id']]['review_history'][-1]['finding']['eligibility']
        self.assertEqual(saved, result['eligibility'])

    def test_every_clause_requires_its_own_bound_evidence(self):
        state, _, _, _, result, _ = self.fixture()
        result['eligibility']['claims'][1]['locator'] = 'Invented section'
        with self.assertRaisesRegex(ValueError, 'verified_candidate_missing_field_evidence'):
            ledger.apply_reviews(state, [result], 'synthetic-review')

    def test_missing_later_clause_is_not_hidden_by_first_supported_clause(self):
        state, _, _, _, result, _ = self.fixture()
        result['content_verification']['evidence'] = [e for e in result['evidence'] if e['locator'] != 'Qualification 3']
        with self.assertRaisesRegex(ValueError, 'verified_candidate_missing_field_evidence'):
            ledger.apply_reviews(state, [result], 'synthetic-review')

    def test_identical_field_rows_do_not_create_false_multiplicity(self):
        _, task, snapshot, model, _, _ = self.fixture()
        model['fields'] = model['fields'][:3]
        model['fields'].append(copy.deepcopy(model['fields'][-1]))
        result = executor.validate_model_result(model, task, snapshot, {'provider': 'offline_test'})
        self.assertEqual(result['eligibility']['status'], 'supported')
        self.assertNotIn('claims', result['eligibility'])

    def test_malformed_multiple_claims_fail_closed(self):
        for claims in ([], [{}], [{'status': 'supported', 'value': ''}] * 2):
            with self.subTest(claims=claims):
                state, _, _, _, result, _ = self.fixture()
                result['eligibility']['claims'] = claims
                with self.assertRaisesRegex(ValueError, 'invalid_multiple_supported_claims'):
                    ledger.apply_reviews(state, [result], 'synthetic-review')

    def test_single_value_readers_cannot_publish_a_fragment(self):
        _, _, _, _, result, _ = self.fixture()
        self.assertNotIn('eligibility', ledger._supported_content_fields(result))
        self.assertEqual(len([x for x in ledger._supported_content_claims(result) if x[0] == 'eligibility']), 3)

    def test_mixed_single_and_multiple_shapes_are_rejected_by_both_readers(self):
        result = {'eligibility': {'status': 'supported', 'value': 'MSc',
                                  'claims': [{'status': 'supported', 'value': 'English C1'}]}}
        for reader in [ledger._supported_content_fields, ledger._supported_content_claims]:
            with self.assertRaisesRegex(ValueError, 'mixed_single_and_multiple_claims'):
                reader(result)

    def test_multiple_dates_keep_near_term_status_recheck(self):
        state, _, _, _, result, _ = self.fixture()
        ledger.apply_reviews(state, [result], 'synthetic-review')
        task = state['tasks'][result['candidate_id']]
        task['current_open_status'] = 'open'
        task['current_open_status_checked_at'] = '2026-10-25T01:00:00Z'
        finding = task['review_history'][-1]['finding']
        for dates in (['2026-10-29', '2026-11-10'], ['2026-11-10', '2026-10-29'],
                      ['October 29, 2026', '10 November 2026'], ['Nov 10, 2026', '29 Oct 2026']):
            finding['deadline'] = {'status': 'multiple_supported_claims', 'value': None,
                'claims': [{'status': 'supported', 'value': date} for date in dates]}
            self.assertEqual(len(ledger.open_status_tasks(state, today='2026-10-26')), 1)
        self.assertIsNone(finding['deadline']['value'])

    def test_schedule_date_does_not_guess_locale_or_invalid_calendar(self):
        for value in ('08-11-2026', '31 February 2026', '2026-99-99', 'October 2026', 'open until filled'):
            self.assertIsNone(ledger._date_for_recheck(value))

    def test_paraphrases_are_explicitly_not_semantically_verified(self):
        _, _, _, _, result, _ = self.fixture()
        fields = result['finding']['model_field_findings']
        self.assertTrue(all('normalization_status' in f for f in fields))
        self.assertTrue(any(f['normalization_status'] == 'model_proposal_requires_semantic_review' for f in fields))

    def test_optional_qualification_cannot_be_normalized_as_mandatory(self):
        _, task, snapshot, model, _, _ = self.fixture()
        quote = 'German language skills are a plus (but not required).'
        snapshot['text'] += ' ' + quote
        snapshot['text_sha256'] = hashlib.sha256(snapshot['text'].encode()).hexdigest()
        model['evidence'].append({'field': 'eligibility', 'url': snapshot['url'],
            'quote': quote, 'claim': quote, 'locator': 'Language preference'})
        model['fields'].append({'field': 'eligibility', 'status': 'supported', 'raw_value': quote,
            'normalized_value': 'German is required', 'evidence_index': len(model['evidence']) - 1, 'reason': None})
        with self.assertRaisesRegex(executor.ModelExecutionError, 'strengthens_optional_condition'):
            executor.validate_model_result(model, task, snapshot, {'provider': 'offline_test'})
        model['fields'][-1]['normalized_value'] = '德语为加分项，不要求必须具备。'
        result = executor.validate_model_result(model, task, snapshot, {'provider': 'offline_test'})
        self.assertEqual(result['finding']['model_field_findings'][-1]['normalization_status'],
                         'model_proposal_requires_semantic_review')

    def test_two_clauses_can_share_one_exact_quote_without_overwrite(self):
        state, task, snapshot, model, _, _ = self.fixture()
        model['fields'] = model['fields'][:3]
        model['fields'][-1]['raw_value'] = 'master degree'
        model['fields'].append({**model['fields'][-1], 'raw_value': 'is required'})
        result = executor.validate_model_result(model, task, snapshot, {'provider': 'offline_test'})
        ledger.apply_reviews(state, [result], 'synthetic-review')
        self.assertEqual([c['value'] for c in result['eligibility']['claims']], ['master degree', 'is required'])

    def test_saved_ledger_and_idempotent_review_preserve_all_clauses(self):
        state, _, _, _, result, _ = self.fixture()
        ledger.apply_reviews(state, [result], 'synthetic-review')
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'candidate_ledger.json'
            ledger.save_ledger(path, state)
            loaded = ledger.load_ledger(path, require_existing=True)
            before = ledger.digest(loaded)
            ledger.apply_reviews(loaded, [result], 'synthetic-review')
            self.assertEqual(before, ledger.digest(loaded))


if __name__ == '__main__':
    unittest.main()
