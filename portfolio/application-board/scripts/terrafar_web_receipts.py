#!/usr/bin/env python3
"""Index saved web-tool receipts without inventing transport or completeness.

No network IO. The returned display is a partial representation of a page;
missing display lines and missing job URLs remain explicit downstream work.
"""
import re


def index_receipts(receipts):
    pages = {}
    for receipt in receipts:
        if receipt.get('tool') != 'web.run' or not receipt.get('captured_at'):
            raise ValueError('web_receipt_provenance_missing')
        for block in re.split(r'\n-{20,}\n', receipt['request_response']):
            heading = re.search(r'^(.+?) \((https?://.+)\)\n', block)
            if not heading:
                continue
            title, url = heading.groups()
            page = pages.setdefault(url, {'title': title, 'url': url, 'lines': {},
                'observed_at': receipt['captured_at'], 'tool_refs': [],
                'collection_method': 'authorized_web_tool', 'http_status': None,
                'underlying_http_requests': None, 'capture_status': 'partial'})
            page['lines'].update({int(n): t for n, t in re.findall(r'^L(\d+): ?(.*)$', block, re.M)})
            count = re.search(r'Total lines: (\d+)', block)
            if count:
                page['display_total_lines'] = int(count[1])
            page['tool_refs'] += re.findall(r'turn\d+view\d+', block[:700])[:1]
    for page in pages.values():
        page['display_missing_line_count'] = max(0, page.get('display_total_lines', 0) - len(page['lines']))
        page['text'] = '\n'.join('L' + str(n) + ': ' + t for n, t in sorted(page['lines'].items()))
    return list(pages.values())
