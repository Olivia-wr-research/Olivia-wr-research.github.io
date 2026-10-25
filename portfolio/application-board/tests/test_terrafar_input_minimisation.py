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

    def test_day_month_first_official_dates_preserved_without_reordering(self):
        for text in ('Closing date: 08-11-2026', 'Closing date: 09-11-2026',
                     'Deadline 31-12-2026', 'Deadline 12-31-2026'):
            with self.subTest(text=text):
                self.assertEqual(_clean_public_text(text), text)

    def test_day_month_first_clock_and_contact_label(self):
        text = 'Closing date: 08-11-2026 17:00 UK time'
        self.assertEqual(_clean_public_text(text), text)
        self.assertEqual(_clean_public_text('Tel: 08-11-2026'), 'Tel: [phone omitted]')
        self.assertIn('[phone omitted]', _clean_public_text('Phone: 08-11-2026 17:00'))

    def test_invalid_day_month_calendar_does_not_escape_redaction(self):
        for text in ('31-02-2026', '29-02-2025', '08-11-2026 29:00'):
            with self.subTest(text=text):
                self.assertIn('[phone omitted]', _clean_public_text(text))
        self.assertEqual(_clean_public_text('29-02-2028'), '29-02-2028')

    def test_minimisation_preserves_unknown_and_length_limit(self):
        self.assertIsNone(_clean_public_text(None))
        self.assertIsNone(_clean_public_text({'private': 'unstructured'}))
        self.assertEqual(_clean_public_text('Deadline 2026-11-13', 8), 'Deadline')


if __name__ == '__main__':
    unittest.main()
