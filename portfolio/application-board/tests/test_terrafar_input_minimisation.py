import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from terrafar_model_executor import _clean_public_text


class InputMinimisationTests(unittest.TestCase):
    def test_calendar_and_funding_intervals_remain_field_evidence(self):
        text = 'Deadline 2026-11-13. Project funded 2026-2030. Starts 2027-01-01.'
        self.assertEqual(_clean_public_text(text), text)

    def test_actual_contacts_remain_redacted(self):
        text = 'Contact person@example.edu or +358 2941 911. Tel: 2026-2030.'
        clean = _clean_public_text(text)
        self.assertNotIn('person@example.edu', clean)
        self.assertNotIn('+358 2941 911', clean)
        self.assertNotIn('2026-2030', clean)
        self.assertEqual(clean.count('[phone omitted]'), 2)

    def test_deadline_with_clock_time_remains_evidence(self):
        text = 'Deadline 2026-11-13 23:59, timezone not stated.'
        self.assertEqual(_clean_public_text(text), text)
        self.assertIn('[phone omitted]', _clean_public_text('Tel: 2026-11-13 23:59'))

    def test_invalid_calendar_does_not_bypass_contact_redaction(self):
        self.assertEqual(_clean_public_text('2026-99-99'), '[phone omitted]')
        self.assertEqual(_clean_public_text('9999-1234'), '[phone omitted]')

    def test_minimisation_preserves_unknown_and_length_limit(self):
        self.assertIsNone(_clean_public_text(None))
        self.assertIsNone(_clean_public_text({'private': 'unstructured'}))
        self.assertEqual(_clean_public_text('Deadline 2026-11-13', 8), 'Deadline')


if __name__ == '__main__':
    unittest.main()
