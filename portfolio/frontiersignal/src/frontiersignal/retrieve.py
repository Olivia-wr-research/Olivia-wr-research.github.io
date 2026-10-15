"""Bounded OpenAlex retrieval with explicit errors and credentials in headers only."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .privacy import minimized_snapshot

FIELDS = 'id,doi,display_name,publication_year,authorships,cited_by_count,type,is_retracted,is_authors_truncated,primary_location'


class RetrievalError(RuntimeError):
    pass


def parameters(topic, start_year, end_year, limit):
    if not isinstance(topic,str) or not 3 <= len(topic.strip()) <= 300:
        raise ValueError('Use a public topic of 3–300 characters.')
    if not isinstance(limit,int) or not 5 <= limit <= 200:
        raise ValueError('Limit must be an integer between 5 and 200.')
    if not 1900 <= start_year <= end_year <= datetime.now(timezone.utc).year:
        raise ValueError('Choose a valid year range ending no later than the current year.')
    clean = re.sub(r'[?*]', ' ', topic)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if len(clean) < 3:
        raise ValueError('Topic is empty after removing wildcard punctuation.')
    return {'search':clean,'filter':f'publication_year:{start_year}-{end_year},is_retracted:false','per_page':str(limit),'select':FIELDS}


def tls_context():
    for candidate in [os.getenv('SSL_CERT_FILE'),'/etc/ssl/cert.pem','/etc/ssl/certs/ca-certificates.crt']:
        if candidate and os.path.isfile(candidate):
            return ssl.create_default_context(cafile=candidate)
    return ssl.create_default_context()


def fetch(topic, start_year, end_year, limit=100):
    params = parameters(topic,start_year,end_year,limit)
    url = 'https://api.openalex.org/works?'+urlencode(params)
    headers = {'Accept':'application/json','User-Agent':'FrontierSignal/0.2 research-map'}
    key = os.environ.get('OPENALEX_API_KEY','').strip()
    if key:
        headers['Authorization'] = 'Bearer '+key
    try:
        with urlopen(Request(url,headers=headers),timeout=30,context=tls_context()) as response:
            payload = json.loads(response.read(20_000_001))
    except HTTPError as exc:
        guidance = 'Set OPENALEX_API_KEY for authenticated access.' if exc.code in (401,403) else 'Wait before retrying.' if exc.code == 429 else 'Check the public topic and try again.'
        raise RetrievalError(f'OpenAlex HTTP {exc.code}. {guidance}') from None
    except (URLError,TimeoutError,OSError):
        raise RetrievalError('OpenAlex connection failed; no replacement records were generated.') from None
    except (json.JSONDecodeError,UnicodeDecodeError):
        raise RetrievalError('OpenAlex returned an invalid JSON response.') from None
    if not isinstance(payload,dict) or not isinstance(payload.get('results'),list):
        raise RetrievalError('OpenAlex returned an unexpected response schema.')
    total = payload.get('meta',{}).get('count') if isinstance(payload.get('meta'),dict) else None
    return minimized_snapshot({'schema_version':1,'topic':topic.strip(),'search_terms':params['search'],'start_year':start_year,'end_year':end_year,'retrieved_at':datetime.now(timezone.utc).isoformat(),'provider':'OpenAlex','request_url':url,'reported_total':total,'requested_limit':limit,'records':payload['results']})
