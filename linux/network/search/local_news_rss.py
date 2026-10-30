"""Keyless dated news through the public Google News RSS search feed.

This SearXNG engine makes no paid API call. Publication dates come from each
RSS item's pubDate; retrieval time is never substituted for publication time.
"""
from email.utils import parsedate_to_datetime
import html
import re
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

categories = ['news']
paging = False
time_range_support = True
language_support = False
safesearch = False


def request(query, params):
    period = {'day': '1d', 'month': '30d', 'year': '365d'}.get(params.get('time_range'))
    if period:
        query += ' when:'+period
    params['url'] = 'https://news.google.com/rss/search?'+urlencode(
        {'q': query, 'hl': 'en-CA', 'gl': 'CA', 'ceid': 'CA:en'})
    params['headers']['Accept'] = 'application/rss+xml, application/xml'


def response(resp):
    if len(resp.content) > 1024*1024:
        raise ValueError('News RSS exceeded its response bound')
    root = ET.fromstring(resp.content)
    results = []
    for item in root.findall('.//item')[:50]:
        title, url, date = (item.findtext(key) or '' for key in ['title', 'link', 'pubDate'])
        if not title or not url.startswith('https://news.google.com/'):
            continue
        try:
            published = parsedate_to_datetime(date)
        except (ValueError, TypeError, OverflowError):
            # A dated-search engine must not manufacture missing dates.
            continue
        description = html.unescape(re.sub(r'<[^>]+>', ' ', item.findtext('description') or ''))
        description = re.sub(r'\s+', ' ', description).strip()[:2000]
        publisher = (item.findtext('source') or '')[:200]
        results.append({'url': url, 'title': title[:400], 'publishedDate': published,
                        'content': 'Published '+published.isoformat()+'. '+publisher+'. '+description})
    return results
