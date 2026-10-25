"""Checkout-local Skill references must resolve without machine-specific paths."""
import hashlib
from pathlib import Path
import unittest

import terrafar_candidate_ledger as ledger
import terrafar_model_executor as executor


class SkillPinPathTests(unittest.TestCase):
    def test_pin_resolves_to_the_exact_read_content(self):
        pin = ledger.skill_pin()
        relative = Path(pin['path'])
        self.assertFalse(relative.is_absolute())
        self.assertNotIn('..', relative.parts)
        resolved = ledger._REPO_ROOT / relative
        self.assertTrue(resolved.is_file())
        self.assertEqual(resolved, ledger.SKILL_PATH)
        self.assertEqual(hashlib.sha256(resolved.read_bytes()).hexdigest(), pin['sha256'])

    def test_legacy_export_uses_the_resolvable_pin(self):
        batch = ledger.export_agent_batch(ledger.empty_ledger(), limit=1)
        self.assertEqual(batch['skill'], ledger.skill_pin())

    def test_model_assignment_uses_the_same_pin(self):
        batch = executor.claim_batch(ledger.empty_ledger(), owner='offline-test',
                                     limit=1, run_id='offline-skill-path-test')
        self.assertEqual(batch['skill'], ledger.skill_pin())

    def test_historical_logical_path_remains_valid_with_unchanged_content(self):
        old = {**ledger.skill_pin(), 'path': '.agents/skills/terrafar-source-audit/SKILL.md'}
        self.assertTrue(ledger.skill_pin_matches(old))

    def test_changed_hash_name_or_arbitrary_path_never_matches(self):
        pin = ledger.skill_pin()
        for change in ({'sha256': '0' * 64}, {'name': 'another-skill'},
                       {'path': '../SKILL.md'}, {'path': '/private/tmp/SKILL.md'},
                       {'untrusted_extra': True}):
            with self.subTest(change=change):
                self.assertFalse(ledger.skill_pin_matches({**pin, **change}))


if __name__ == '__main__':
    unittest.main()
