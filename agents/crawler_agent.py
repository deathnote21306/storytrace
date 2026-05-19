import ipaddress
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus, urlparse

import feedparser
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

_FEATHERLESS_MODEL = 'Qwen/Qwen2.5-7B-Instruct'
_FEATHERLESS_CONTEXT_MODEL = 'Qwen/Qwen2.5-72B-Instruct'

MAX_ENTRIES_PER_FEED = 20
MAX_CANDIDATES_PER_OUTLET = 3
WORD_CAP = 300
FETCH_TIMEOUT_SECS = 5
KEYWORD_LENGTH = 6

# Outlet → site domain. Used to build Google News RSS search queries (keyword + site filter)
# so each fetch is keyword-scoped at the source instead of pulling the full latest feed.
RSS_FEEDS = {
    'BBC':            'bbc.com',
    'Al Jazeera':     'aljazeera.com',
    'Dawn':           'dawn.com',
    'CNN':            'cnn.com',
    'RT':             'rt.com',
    'Times of India': 'timesofindia.indiatimes.com',
    'Guardian':       'theguardian.com',
    'Fox News':       'foxnews.com',
    'DW':             'dw.com',
    'France24':       'france24.com',
    'NDTV':           'ndtv.com',
    'Arab News':      'arabnews.com',
    'Sputnik':        'sputniknews.com',
    'NHK':            'nhk.or.jp',
    'TASS':           'tass.com',
}


def _build_search_url(domain: str, keyword: str) -> str:
    """Google News RSS search URL filtered to one outlet's domain."""
    q = quote_plus(f'{keyword} site:{domain}')
    return f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'

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


def _get_featherless_client() -> OpenAI:
    return OpenAI(
        base_url='https://api.featherless.ai/v1',
        api_key=os.environ.get('FEATHERLESS_API_KEY', ''),
    )


def _build_search_context(root: dict) -> dict:
    """Extract one subject keyword and a story fingerprint from the root article.

    Returns {'keyword': str, 'summary': str}.
    Returns {} on any failure — callers fall back to the first spaCy entity.
    """
    headline = root.get('headline', '')
    text = root.get('text', '')
    if not headline and not text:
        logger.debug('_build_search_context: no root content, skipping LLM call')
        return {}
    prompt = (
        'You are helping a news monitoring system find related articles across outlets.\n\n'
        'Read the text od the news that is relevent to the headline provided below and understand what the story is about.\n\n'
        'Given this root news story, identify:\n'
        f'1. The single most specific and identifying short phrase (mininum {KEYWORD_LENGTH} words) '
        'that uniquely describes what this story is about — the core subject.\n'
        '   Choose something that any outlet covering the SAME event would also use '
        '(e.g. a proper name, number, location, time, or unique event term — NOT a generic word like "attack" or "talks" or unnecesory jargons).\n'
        '2. A one-sentence summary of exactly what happened.\n\n'
        'Return ONLY valid JSON, no markdown:\n'
        f'{{"keyword": "the single subject term should be atleast {KEYWORD_LENGTH} words", "summary": "one sentence"}}\n\n'
        f'HEADLINE: {headline}\n'
        f'TEXT: {text}'
    )
    try:
        logger.info(f'headline: {headline}, text: {text}')
        client = _get_featherless_client()
        resp = client.chat.completions.create(
            model=_FEATHERLESS_CONTEXT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
            max_tokens=120,
        )
        raw = resp.choices[0].message.content.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(raw)
        logger.info('Search context built: keyword="%s" — "%s"',
                    result.get('keyword', ''), result.get('summary', ''))
        return result
    except Exception as exc:
        logger.warning('_build_search_context LLM call failed, falling back to entities: %s', exc)
        return {}


def _candidate_score(entry, keyword: str) -> bool:
    """Return True if the subject keyword appears in headline + RSS summary/description."""
    combined = (
        entry.get('title', '') + ' ' +
        entry.get('summary', '') + ' ' +
        entry.get('description', '')
    ).lower()
    return keyword.lower() in combined


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
        client = _get_featherless_client()
        resp = client.chat.completions.create(
            model=_FEATHERLESS_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        raw = resp.choices[0].message.content.strip().replace('```json', '').replace('```', '').strip()
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
    outlet: str, domain: str, keyword: str, entities: list[str]
) -> list[dict]:
    """Search the outlet's articles for the subject keyword via Google News RSS.

    The keyword is part of the fetch URL (Google News `site:` filter), so results
    are pre-scoped to this outlet AND this story before any local scoring runs.
    A final keyword/entity check guards against weak matches.
    Does NOT fetch full article text — that happens only for LLM-confirmed articles.
    """
    feed_url = _build_search_url(domain, keyword)
    try:
        feed = feedparser.parse(feed_url)
        matches = []
        for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
            kw_hit = _candidate_score(entry, keyword)
            entity_hit = entity_match(entry.get('title', ''), entities)
            if kw_hit or entity_hit:
                # keyword hit scores 1, entity hit adds 1 bonus — entity alone = 1
                score = (1 if kw_hit else 0) + (1 if entity_hit else 0)
                matches.append((score, entry))
        matches.sort(key=lambda x: x[0], reverse=True)
        result = []
        for _, entry in matches[:MAX_CANDIDATES_PER_OUTLET]:
            rss_summary = _strip_html(entry.get('summary', '') or entry.get('description', ''))
            result.append({
                'outlet':      outlet,
                'url':         entry.link,
                'headline':    entry.get('title', ''),
                'rss_summary': rss_summary[:300],
                'language':    'en',
            })
        if result:
            logger.debug('%s: %d candidate(s) for keyword="%s" — top: "%s"',
                         outlet, len(result), keyword, result[0]['headline'][:70])
        else:
            logger.debug('%s: no results for keyword="%s"', outlet, keyword)
        return result
    except Exception as exc:
        logger.warning('%s: feed parse failed: %s', outlet, exc)
        return []


def run(state: dict) -> dict:
    root = state.get('root', {})
    entities = state.get('entities', [])
    job_id = state.get('job_id', '?')

    logger.info('[%s]  🕷️ ════════ CRAWLER AGENT STARTED ════════  🕷️  |  entities: %s', job_id, entities)

    # Step 1: LLM-generated search context — single subject keyword + story fingerprint
    search_ctx = _build_search_context(root)
    keyword: str = search_ctx.get('keyword') or (entities[0] if entities else '')
    root_summary: str = search_ctx.get('summary') or root.get('headline', '')

    if not keyword:
        logger.warning('[%s] crawler_agent: no keyword or entities, skipping crawl', job_id)
        state['articles'] = []
        return state

    logger.info('[%s] Searching %d outlets with keyword="%s"', job_id, len(RSS_FEEDS), keyword)
    # Step 2: Parallel keyword-scoped fetch (one Google News search per outlet, no full-text yet)
    all_candidates: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_outlet_candidates, outlet, domain, keyword, entities): outlet
            for outlet, domain in RSS_FEEDS.items()
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
