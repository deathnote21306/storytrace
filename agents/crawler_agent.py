import ipaddress
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import feedparser
import requests
from google import genai

logger = logging.getLogger(__name__)

MAX_ENTRIES_PER_FEED = 20
MAX_CANDIDATES_PER_OUTLET = 3
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


def _get_gemini_client() -> genai.Client:
    return genai.Client(api_key=os.environ.get('GEMINI_API_KEY', ''))


def _build_search_context(root: dict) -> dict:
    """Extract search keywords and a story fingerprint from the root article via Gemini Flash.

    Returns {'keywords': [...], 'summary': '...'}.
    Returns {} on any failure — callers fall back to spaCy entities.
    """
    headline = root.get('headline', '')
    text = root.get('text', '')
    if not headline and not text:
        logger.debug('_build_search_context: no root content, skipping LLM call')
        return {}
    prompt = (
        'You are helping a news monitoring system find related articles across outlets.\n\n'
        'Given this root news story, extract:\n'
        '1. 8-12 specific keywords/phrases that identify articles covering the SAME event\n'
        '   (include key names, places, organizations, and unique event descriptors;\n'
        '    include common alternative phrasings — e.g. "Washington" for "United States")\n'
        '2. A one-sentence summary of exactly what happened\n\n'
        'Return ONLY valid JSON, no markdown:\n'
        '{"keywords": ["keyword1", "keyword2", ...], "summary": "one sentence"}\n\n'
        f'HEADLINE: {headline}\n'
        f'TEXT: {text[:600]}'
    )
    try:
        client = _get_gemini_client()
        r = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        raw = r.text.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(raw)
        logger.info('Search context built: %d keywords — "%s"',
                    len(result.get('keywords', [])), result.get('summary', '')[:80])
        return result
    except Exception as exc:
        logger.warning('_build_search_context LLM call failed, falling back to entities: %s', exc)
        return {}


def _candidate_score(entry, keywords: list[str]) -> int:
    """Count keyword hits across headline + RSS summary/description."""
    combined = (
        entry.get('title', '') + ' ' +
        entry.get('summary', '') + ' ' +
        entry.get('description', '')
    ).lower()
    return sum(1 for kw in keywords if kw.lower() in combined)


def _score_relevance_batch(root_summary: str, candidates: list[dict]) -> list[bool]:
    """Single Gemini Flash call: return True for each candidate that covers the same event.

    Falls back to [True, True, ...] on any failure so downstream DNA/drift agents
    still get articles to process — they will surface the real signal.
    """
    if not candidates:
        return []
    logger.info('Scoring relevance for %d candidates against: "%s"',
                len(candidates), root_summary[:80])
    items_text = '\n'.join(
        f"{i + 1}. [{c['outlet']}] {c['headline']} — {c.get('rss_summary', '')[:150]}"
        for i, c in enumerate(candidates)
    )
    prompt = (
        'You are a news relevance judge.\n\n'
        'Determine which candidate articles cover the SAME specific news event as the root story.\n'
        'An article is relevant if it reports on the SAME incident/development, not just the same topic.\n\n'
        f'ROOT STORY: {root_summary}\n\n'
        f'CANDIDATE ARTICLES:\n{items_text}\n\n'
        'Return ONLY a JSON array of booleans, one per candidate in order (true = same event):\n'
        '[true, false, ...]'
    )
    try:
        client = _get_gemini_client()
        r = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        raw = r.text.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(raw)
        if isinstance(result, list) and len(result) == len(candidates):
            relevant_count = sum(result)
            logger.info('Relevance filter: %d/%d candidates passed', relevant_count, len(candidates))
            return [bool(x) for x in result]
        logger.warning('Relevance response length mismatch (%d vs %d), keeping all',
                       len(result) if isinstance(result, list) else -1, len(candidates))
    except Exception as exc:
        logger.warning('_score_relevance_batch LLM call failed, keeping all candidates: %s', exc)
    return [True] * len(candidates)


def _fetch_outlet_candidates(
    outlet: str, feed_url: str, keywords: list[str], entities: list[str]
) -> list[dict]:
    """Return up to MAX_CANDIDATES_PER_OUTLET best-scoring entries for one RSS feed.

    Scores entries by keyword hits in headline + RSS description.
    Entity hits get a +2 bonus to preserve backward-compatible matching.
    Does NOT fetch full article text — that happens only for LLM-confirmed articles.
    """
    try:
        feed = feedparser.parse(feed_url)
        scored: list[tuple[int, object]] = []
        for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
            kw_score = _candidate_score(entry, keywords)
            entity_hit = entity_match(entry.get('title', ''), entities)
            if kw_score > 0 or entity_hit:
                scored.append((kw_score + (2 if entity_hit else 0), entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for _, entry in scored[:MAX_CANDIDATES_PER_OUTLET]:
            rss_summary = _strip_html(entry.get('summary', '') or entry.get('description', ''))
            result.append({
                'outlet':      outlet,
                'url':         entry.link,
                'headline':    entry.get('title', ''),
                'rss_summary': rss_summary[:300],
                'language':    'en',
            })
        if result:
            logger.debug('%s: %d candidate(s) — top: "%s"',
                         outlet, len(result), result[0]['headline'][:70])
        else:
            logger.debug('%s: no matching entries in feed', outlet)
        return result
    except Exception as exc:
        logger.warning('%s: feed parse failed: %s', outlet, exc)
        return []


def run(state: dict) -> dict:
    root = state.get('root', {})
    entities = state.get('entities', [])
    job_id = state.get('job_id', '?')

    logger.info('[%s] crawler_agent started — entities: %s', job_id, entities)

    # Step 1: LLM-generated search context — richer keywords + story fingerprint
    search_ctx = _build_search_context(root)
    keywords: list[str] = search_ctx.get('keywords') or entities
    root_summary: str = search_ctx.get('summary') or root.get('headline', '')

    if not keywords and not entities:
        logger.warning('[%s] crawler_agent: no keywords or entities, skipping crawl', job_id)
        state['articles'] = []
        return state

    logger.info('[%s] Crawling %d feeds with %d keyword(s)',
                job_id, len(RSS_FEEDS), len(keywords))

    # Step 2: Parallel RSS fetch — collect top candidates per outlet, no full-text yet
    all_candidates: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_outlet_candidates, outlet, url, keywords, entities): outlet
            for outlet, url in RSS_FEEDS.items()
        }
        for future in as_completed(futures):
            try:
                all_candidates.extend(future.result())
            except Exception as exc:
                logger.warning('[%s] Unexpected error collecting candidates: %s', job_id, exc)

    logger.info('[%s] %d total candidate(s) collected across all feeds', job_id, len(all_candidates))

    # Step 3: One batched LLM call to filter false positives
    relevant_flags = _score_relevance_batch(root_summary, all_candidates)

    # Step 4: Fetch full article text only for relevant articles, one per outlet
    seen_outlets: set[str] = set()
    to_fetch: list[dict] = []
    for candidate, is_relevant in zip(all_candidates, relevant_flags):
        if is_relevant and candidate['outlet'] not in seen_outlets:
            seen_outlets.add(candidate['outlet'])
            to_fetch.append(candidate)

    logger.info('[%s] Fetching full text for %d relevant article(s)', job_id, len(to_fetch))

    articles: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_art = {
            executor.submit(fetch_first_300_words, art['url']): art
            for art in to_fetch
        }
        for future in as_completed(future_to_art):
            art = future_to_art[future]
            try:
                text = future.result()
                if text:
                    articles.append({
                        'outlet':   art['outlet'],
                        'url':      art['url'],
                        'headline': art['headline'],
                        'text':     text,
                        'language': 'en',
                    })
                else:
                    logger.debug('[%s] %s: full-text fetch returned nothing', job_id, art['outlet'])
            except Exception as exc:
                logger.warning('[%s] %s: full-text fetch error: %s', job_id, art['outlet'], exc)

    logger.info('[%s] crawler_agent done — %d article(s) collected', job_id, len(articles))
    state['articles'] = articles
    return state
