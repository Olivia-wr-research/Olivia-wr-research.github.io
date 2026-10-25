#!/usr/bin/env python3
"""Index saved web-tool receipts without inventing transport or completeness.

No network IO. The returned display is a partial representation of a page;
missing display lines and missing job URLs remain explicit downstream work.
"""
import hashlib
import re


def split_response_blocks(response):
    """Split tool delimiters even when an error omitted its final newline.

    In particular, ``L0 is out of bounds`` may touch the next delimiter.
    Requiring a leading newline would attach the next page's body to the
    empty page's URL. Keep each result isolated before interpreting its lines.
    """
    if not isinstance(response, str):
        raise ValueError('web_receipt_response_not_text')
    return [block.strip('\r\n') for block in re.split(r'(?:\r?\n)?-{20,}\r?\n', response)
            if block.strip()]


def index_receipt_events(receipts):
    """Keep one outcome per returned block, including errors without a URL.

    A displayed text fragment is not a validated opportunity or a complete page.
    The URL in a fetch diagnostic is a failed target, never a successful final URL.
    Repeated blocks remain distinct attempts; this function makes no network calls.
    """
    events = []
    for receipt_number, receipt in enumerate(receipts):
        if receipt.get('tool') != 'web.run' or not receipt.get('captured_at'):
            raise ValueError('web_receipt_provenance_missing')
        for block_number, block in enumerate(split_response_blocks(receipt['request_response'])):
            heading = re.search(r'^(.*?)\s*\((https?://.+)\)\r?\n', block)
            title, url = heading.groups() if heading else (block.splitlines()[0], None)
            lines = re.findall(r'^L(\d+)(@P\d+(?:-\d+)?)?: ?(.*)$', block, re.M)
            count = re.search(r'Total lines: (\d+)', block)
            refs = re.findall(r'turn\d+(?:view|search)\d+', block[:700])
            # Error wrappers can include an L0 diagnostic or falsely declare one
            # line while returning no L0. Neither is a source-page body.
            explicit_error = (block.startswith('Internal Error ()') or
                              (heading is None and block.startswith('Error fetching ')))
            diagnostic = re.search(r'Failed to fetch (https?://\S+?)(?::\s|\s|$)', block)
            if explicit_error:
                kind = 'tool_error'
            elif any('search' in ref for ref in refs) and not lines:
                kind = 'search_discovery'
            elif heading and lines:
                kind = 'displayed_text'
            elif heading:
                kind = 'empty_display'
            else:
                kind = 'unclassified_response'
            events.append({
                'receipt_number': receipt_number, 'block_number': block_number,
                'observed_at': receipt['captured_at'],
                'capture_time_precision': receipt.get('capture_time_precision', 'as_recorded'),
                'title': title, 'displayed_url': url if not explicit_error else None,
                'failed_target_url': diagnostic.group(1) if explicit_error and diagnostic else None,
                'tool_refs': list(dict.fromkeys(refs)), 'response_kind': kind,
                'displayed_text_returned': kind == 'displayed_text',
                'displayed_line_count': len(lines),
                'declared_total_lines': int(count[1]) if count else None,
                'response_block_sha256': hashlib.sha256(block.encode('utf-8')).hexdigest(),
                'http_status': None, 'underlying_http_requests': None,
                'opportunity_validity': 'not_assessed', 'source_completeness': 'not_established',
            })
    return events


def index_receipts(receipts):
    pages = {}
    for receipt in receipts:
        if receipt.get('tool') != 'web.run' or not receipt.get('captured_at'):
            raise ValueError('web_receipt_provenance_missing')
        for block in split_response_blocks(receipt['request_response']):
            # PDF responses can have an empty title before their URL.
            heading = re.search(r'^(.*?)\s*\((https?://.+)\)\r?\n', block)
            if not heading:
                continue
            title, url = heading.groups()
            page = pages.setdefault(url, {'title': title, 'url': url, 'lines': {},
                'observed_at': receipt['captured_at'], 'tool_refs': [],
                'collection_method': 'authorized_web_tool', 'http_status': None,
                'underlying_http_requests': None, 'capture_status': 'partial'})
            # Preserve PDF page locators while retaining global display-line
            # identity. PDF text is evidence too, not an empty HTTP response.
            for n, page_marker, text in re.findall(r'^L(\d+)(@P\d+(?:-\d+)?)?: ?(.*)$', block, re.M):
                page['lines'][int(n)] = text
                page.setdefault('line_locators', {})[int(n)] = f'L{n}{page_marker}'
            count = re.search(r'Total lines: (\d+)', block)
            if count:
                page['display_total_lines'] = int(count[1])
            page['tool_refs'] += re.findall(r'turn\d+view\d+', block[:700])[:1]
    for page in pages.values():
        page['display_missing_line_count'] = max(0, page.get('display_total_lines', 0) - len(page['lines']))
        page['text'] = '\n'.join('L' + str(n) + ': ' + t for n, t in sorted(page['lines'].items()))
    return list(pages.values())
