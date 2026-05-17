import ipaddress
import re
from urllib.parse import urlparse

import feedparser
import requests

MAX_ENTRIES_PER_FEED = 20
WORD_CAP = 300
FETCH_TIMEOUT_SECS = 5

RSS_FEEDS = {
    'BBC':            'http://feeds.bbci.co.uk/news/rss.xml',
    'Al Jazeera':     'https://www.aljazeera.com/xml/rss/all.xml',
    'Dawn':           'https://www.dawn.com/feed',
    'CNN':            'http://rss.cnn.com/rss/edition.rss',
    'RT':             'https://www.rt.com/rss/news/',
    'Times of India': 'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms',
    'Guardian':       'https://www.theguardian.com/world/rss',
    'Fox News':       'https://moxie.foxnews.com/google-publisher/world.xml',
    'DW':             'https://rss.dw.com/xml/rss-en-all',
    'France24':       'https://www.france24.com/en/rss',
    'NDTV':           'https://feeds.feedburner.com/ndtvnews-world-news',
    'Arab News':      'https://www.arabnews.com/rss.xml',
    'Sputnik':        'https://sputniknews.com/export/rss2/world/index.xml',
    'NHK':            'https://www3.nhk.or.jp/rss/news/cat6.xml',
    'TASS':           'https://tass.com/rss/v2.xml',
}

_TAG_RE = re.compile(r'<[^>]+>')


def _strip_html(text: str) -> str:
    return _TAG_RE.sub(' ', text)


def _is_safe_url(url: str) -> bool:
    """Block non-HTTP schemes and RFC-1918 / loopback / link-local addresses (SSRF guard)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        host = parsed.hostname or ''
        try:
            addr = ipaddress.ip_address(host)
            return addr.is_global and not addr.is_private
        except ValueError:
            return bool(host)  # domain name — assume safe
    except Exception:
        return False


def entity_match(headline: str, entities: list[str]) -> bool:
    h = headline.lower()
    return any(e.lower() in h for e in entities)


def fetch_first_300_words(url: str) -> str | None:
    if not _is_safe_url(url):
        return None
    try:
        r = requests.get(
            url,
            timeout=FETCH_TIMEOUT_SECS,
            headers={'User-Agent': 'StoryTrace/1.0'},
        )
        r.raise_for_status()
        words = _strip_html(r.text).split()[:WORD_CAP]
        return ' '.join(words)
    except Exception:
        return None


def run(state: dict) -> dict:
    entities = state.get('entities', [])
    matched = []

    for outlet, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
                if entity_match(entry.get('title', ''), entities):
                    text = fetch_first_300_words(entry.link)
                    if text:
                        matched.append({
                            'outlet':   outlet,
                            'url':      entry.link,
                            'headline': entry.get('title', ''),
                            'text':     text,
                            'language': 'en',
                        })
                    break
        except Exception:
            continue

    state['articles'] = matched
    return state
