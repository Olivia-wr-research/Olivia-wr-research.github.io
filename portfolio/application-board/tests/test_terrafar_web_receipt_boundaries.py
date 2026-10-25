"""Synthetic page-boundary regressions; no real collection is performed."""
import unittest
import terrafar_web_receipts as web


class WebReceiptBoundaryTests(unittest.TestCase):
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
