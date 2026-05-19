import logging
import os
import re
import requests
import spacy
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

nlp = spacy.load('en_core_web_sm')

GDELT_URL   = 'https://api.gdeltproject.org/api/v2/doc/doc'
NEWSAPI_URL = 'https://newsapi.org/v2/everything'

_ENTITY_LABELS = {'PERSON', 'ORG', 'GPE', 'EVENT', 'NORP'}


def _is_url(text: str) -> bool:
    return text.startswith('http://') or text.startswith('https://')


def _outlet_from_url(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    domain = re.sub(r'^www\.', '', domain)
    return domain.split('.')[0].capitalize()


def _fetch_text(url: str) -> str:
    """Fetch raw page text (first 300 words). Returns '' on any error."""
    try:
        r = requests.get(url, timeout=8, headers={'User-Agent': 'StoryTrace/1.0'})
        r.raise_for_status()
        words = r.text.split()[:300]
        return ' '.join(words)
    except Exception:
        return ''


def query_gdelt(query: str) -> dict | None:
    """Return the earliest matching article from GDELT, or None."""
    try:
        r = requests.get(GDELT_URL, params={
            'query':      query,
            'mode':       'artlist',
            'maxrecords': 5,
            'sort':       'DateAsc',   # earliest = root story
            'format':     'json',
        }, timeout=10)
        articles = r.json().get('articles', [])
        return articles[0] if articles else None
    except Exception:
        return None


def query_newsapi(query: str) -> dict | None:
    """Fallback if GDELT returns nothing. Requires NEWSAPI_KEY env var."""
    api_key = os.environ.get('NEWSAPI_KEY')
    if not api_key:
        return None
    try:
        r = requests.get(NEWSAPI_URL, params={
            'q':        query,
            'sortBy':   'publishedAt',
            'pageSize': 1,
            'language': 'en',
            'apiKey':   api_key,
        }, timeout=10)
        articles = r.json().get('articles', [])
        return articles[0] if articles else None
    except Exception:
        return None


def _extract_entities(text: str) -> list[str]:
    doc = nlp(text[:1000])  # cap NLP input for speed
    return [e.text for e in doc.ents if e.label_ in _ENTITY_LABELS]


def run(state: dict) -> dict:
    user_input: str = state['input']
    job_id = state.get('job_id', '?')

    logger.info('[%s] seed_agent started — input: "%s"', job_id, user_input[:120])

    # --- Direct URL input: treat the URL itself as the root story ---
    if _is_url(user_input):
        logger.info('[%s] Input is a URL — fetching root story directly', job_id)
        text = _fetch_text(user_input)
        entities = _extract_entities(text) or [_outlet_from_url(user_input)]
        logger.info('[%s] Entities extracted: %s', job_id, entities)
        state['entities'] = entities
        state['root'] = {
            'outlet':    _outlet_from_url(user_input),
            'country':   'US',
            'url':       user_input,
            'headline':  '',
            'text':      text,
            'published': '',
            'dna':       {},
        }
        logger.info('[%s] seed_agent done — root outlet: %s', job_id, state['root']['outlet'])
        return state

    # --- Topic input: extract entities then query GDELT → NewsAPI ---
    logger.info('[%s] Input is a topic — running NER then querying GDELT', job_id)
    entities = _extract_entities(user_input)
    query = ' '.join(entities[:3]) if entities else user_input
    state['entities'] = entities if entities else [user_input]
    logger.info('[%s] Entities: %s | GDELT query: "%s"', job_id, state['entities'], query)

    gdelt_raw = query_gdelt(query)
    if gdelt_raw:
        logger.info('[%s] GDELT found article: "%s"', job_id, gdelt_raw.get('title', '')[:80])
    else:
        logger.info('[%s] GDELT returned nothing, trying NewsAPI', job_id)

    newsapi_raw = None if gdelt_raw else query_newsapi(query)
    if newsapi_raw:
        logger.info('[%s] NewsAPI found article: "%s"', job_id, newsapi_raw.get('title', '')[:80])

    raw = gdelt_raw or newsapi_raw

    if not raw:
        logger.error('[%s] seed_agent: no source story found for "%s"', job_id, user_input)
        state['error'] = f'Could not find source story for: {user_input}'
        return state

    if gdelt_raw:
        url = raw.get('url', '')
        state['root'] = {
            'outlet':    raw.get('domain', 'Unknown').split('.')[0].capitalize(),
            'country':   'US',
            'url':       url,
            'headline':  raw.get('title', ''),
            'text':      _fetch_text(url) if url else '',
            'published': raw.get('seendate', ''),
            'dna':       {},
        }
    else:
        url = raw.get('url', '')
        state['root'] = {
            'outlet':    raw.get('source', {}).get('name', 'Unknown'),
            'country':   'US',
            'url':       url,
            'headline':  raw.get('title', ''),
            'text':      raw.get('description', '') or _fetch_text(url),
            'published': raw.get('publishedAt', ''),
            'dna':       {},
        }

    logger.info('[%s] seed_agent done — root: "%s" @ %s',
                job_id, state['root']['headline'][:80], state['root']['outlet'])
    return state
