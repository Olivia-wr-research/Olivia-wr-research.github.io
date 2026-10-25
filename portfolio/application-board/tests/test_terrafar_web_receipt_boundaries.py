"""Synthetic page-boundary regressions; no real collection is performed."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import terrafar_web_receipts as web


class WebReceiptBoundaryTests(unittest.TestCase):
    def events(self, response):
        return web.index_receipt_events([{'tool': 'web.run', 'captured_at': '2026-10-25T00:00:00Z',
                                         'request_response': response}])

    def test_error_with_one_declared_line_is_not_body(self):
        event = self.events('Internal Error ()\nref turn4view0; Total lines: 1\n')[0]
        self.assertEqual(event['response_kind'], 'tool_error')
        self.assertFalse(event['displayed_text_returned'])
        self.assertEqual(event['displayed_line_count'], 0)
        self.assertIsNone(event['displayed_url'])

    def test_error_diagnostic_target_is_not_final_url_or_http_status(self):
        event = self.events('Internal Error ()\nref turn4view1; Total lines: 1\n'
                            'L0: Failed to fetch https://a.example/job: (500) Internal Server Error')[0]
        self.assertEqual(event['failed_target_url'], 'https://a.example/job')
        self.assertIsNone(event['displayed_url'])
        self.assertIsNone(event['http_status'])
        self.assertFalse(event['displayed_text_returned'])

    def test_empty_display_is_not_page_text(self):
        event = self.events('Title (https://a.example/job)\nref turn4view2; Total lines: 0\nL0 is out of bounds')[0]
        self.assertEqual(event['response_kind'], 'empty_display')
        self.assertFalse(event['displayed_text_returned'])

    def test_search_snippet_is_discovery_not_direct_body(self):
        event = self.events('Search hit (https://a.example/job)\nref turn4search2\nA snippet')[0]
        self.assertEqual(event['response_kind'], 'search_discovery')
        self.assertFalse(event['displayed_text_returned'])

    def test_real_looking_page_keeps_validity_and_completeness_unknown(self):
        event = self.events('Job (https://a.example/job)\nref turn4view3; Total lines: 1\nL0: Postdoc')[0]
        self.assertTrue(event['displayed_text_returned'])
        self.assertEqual(event['opportunity_validity'], 'not_assessed')
        self.assertEqual(event['source_completeness'], 'not_established')

    def test_duplicate_and_unclassified_attempts_are_not_dropped(self):
        response = ('-'*80+'\n').join(['Unknown response','Internal Error ()','Internal Error ()'])
        events = self.events(response)
        self.assertEqual(len(events), 3)
        self.assertEqual([e['response_kind'] for e in events], ['unclassified_response','tool_error','tool_error'])
        self.assertEqual([e['block_number'] for e in events], [0,1,2])

    def test_event_index_requires_provenance(self):
        with self.assertRaisesRegex(ValueError, 'web_receipt_provenance_missing'):
            web.index_receipt_events([{'tool':'web.run','request_response':'Internal Error ()'}])

    def test_zero_line_page_does_not_absorb_next_body(self):
        a = 'Empty (https://a.example/job/1)\nref turn1view0; Total lines: 0\nL0 is out of bounds'
        b = 'Another empty (https://a.example/job/2)\nref turn1view1; Total lines: 0\nL0 is out of bounds'
        c = 'Actual job (https://b.example/job/3)\nref turn1view2; Total lines: 2\nL0: Employer B\nL1: Job B'
        response = ('-'*80+'\n').join([a,b,c])
        pages=web.index_receipts([{'tool':'web.run','captured_at':'2026-10-25T00:00:00Z',
                                  'request_response':response}])
        self.assertEqual(len(pages),3)
        self.assertEqual([p['url'] for p in pages],
                         ['https://a.example/job/1','https://a.example/job/2','https://b.example/job/3'])
        self.assertEqual([p['text'] for p in pages],['','','L0: Employer B\nL1: Job B'])
        self.assertEqual([p['tool_refs'] for p in pages],[['turn1view0'],['turn1view1'],['turn1view2']])
        self.assertTrue(all(p['capture_status']=='partial' for p in pages))

    def test_regular_newlines_and_crlf_remain_supported(self):
        for separator in ['\n'+'-'*80+'\n','\r\n'+'-'*80+'\r\n']:
            self.assertEqual(web.split_response_blocks('first'+separator+'second'),['first','second'])

    def test_error_then_real_page_is_not_a_single_block(self):
        response='Internal Error ()\nFetch denied'+('-'*80)+'\nJob (https://b.example/job)\nL0: Correct employer'
        blocks=web.split_response_blocks(response)
        self.assertEqual(len(blocks),2)
        self.assertNotIn('Correct employer',blocks[0])

    def test_nontext_receipt_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'web_receipt_response_not_text'):
            web.split_response_blocks({'unexpected':'mapping'})

    def test_untitled_pdf_preserves_page_and_cross_page_locators(self):
        response = (' (https://a.example/position.pdf)\nref turn3view0; Total lines: 3\n'
                    'L0@P0: MSc Position\nL1@P0-1: Funding subject to confirmation\n'
                    'L2@P1: Review until filled')
        pages = web.index_receipts([{'tool': 'web.run', 'captured_at': '2026-10-25T00:00:00Z',
                                    'request_response': response}])
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]['url'], 'https://a.example/position.pdf')
        self.assertEqual(pages[0]['lines'][1], 'Funding subject to confirmation')
        self.assertEqual(pages[0]['line_locators'][1], 'L1@P0-1')
        self.assertEqual(pages[0]['display_missing_line_count'], 0)
        self.assertEqual(pages[0]['capture_status'], 'partial')

    def test_untitled_pdf_next_to_html_is_not_lost_or_combined(self):
        response = (' (https://a.example/position.pdf)\nref turn3view0; Total lines: 1\n'
                    'L0@P0: MSc Position' + '-' * 80 + '\n'
                    'Job (https://b.example/job)\nref turn3view1; Total lines: 1\nL0: Postdoc')
        pages = web.index_receipts([{'tool': 'web.run', 'captured_at': '2026-10-25T00:00:00Z',
                                    'request_response': response}])
        self.assertEqual([p['text'] for p in pages], ['L0: MSc Position', 'L0: Postdoc'])


if __name__=='__main__':
    unittest.main()
