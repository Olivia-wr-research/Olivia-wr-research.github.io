import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('import_jobbnorge', Path(__file__).parents[1] / 'scripts/import_jobbnorge.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def item(title, job_id='123', deadline='fredag 30. oktober 2026'):
    return f'<item><title>{title}</title><link>https://www.jobbnorge.no/ledige-stillinger/stilling/{job_id}/test</link><jn:jobtype>1017 Stipendiat</jn:jobtype><jn:deadline>{deadline}</jn:deadline></item>'


def feed(content):
    return ('<rss xmlns:jn="https://export.jobbnorge.no/xml/"><channel>' + content + '</channel></rss>').encode()


class ImportTests(unittest.TestCase):
    def test_postdoc_excluded_and_repeated_id_deduplicated(self):
        result = module.parse_feed(feed(item('PhD in ecology') * 2 + item('Postdoctoral researcher', '124')), '2026-10-15')
        self.assertEqual(len(result['doctoral_records']), 1)

    def test_deadline_unknown_not_invented_and_expired_kept_as_expired(self):
        rows = module.parse_feed(feed(item('PhD', deadline='as soon as possible') + item('PhD', '124', 'onsdag 14. oktober 2026')), '2026-10-15')['doctoral_records']
        self.assertIsNone(rows[0]['deadline'])
        self.assertFalse(rows[0]['detail_verified'])
        self.assertEqual(rows[1]['status'], 'past_deadline')

    def test_host_injection_rejected(self):
        raw = feed(item('PhD')).replace(b'www.jobbnorge.no', b'evil.example')
        self.assertEqual(module.parse_feed(raw, '2026-10-15')['doctoral_records'], [])

    def test_entities_and_non_feed_rejected(self):
        for raw in (b'<!DOCTYPE rss><rss/>', b'<html/>'):
            with self.assertRaises(ValueError):
                module.parse_feed(raw, '2026-10-15')

    def test_invalid_calendar_date(self):
        self.assertIsNone(module.deadline_date('31. februar 2026'))


if __name__ == '__main__':
    unittest.main()
