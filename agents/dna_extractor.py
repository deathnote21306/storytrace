import copy
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

logger = logging.getLogger(__name__)

MODELS = [
    'Qwen/Qwen2.5-7B-Instruct',
    'Qwen/Qwen2.5-3B-Instruct',
    'microsoft/Phi-3-mini-4k-instruct',
]

PROMPT = """You are a journalism analyst. Extract the following from the article below.
Return ONLY valid JSON — no explanation, no markdown, just the JSON object.

{{
  "summary":       "2-3 sentence factual summary of this article",
  "facts_kept":    ["list every key factual claim present in the article"],
  "facts_dropped": ["key facts from the ROOT STORY that are MISSING from this article"],
  "tone":          "neutral|alarming|dismissive|supportive",
  "framing":       "one sentence describing the narrative angle of this article",
  "political_lean":"left|center|right|unknown"
}}

ROOT STORY (ground truth):
{root_text}

THIS ARTICLE TO ANALYZE:
{article_text}
"""

_FALLBACK_DNA = {
    'facts_kept':    [],
    'facts_dropped': [],
    'tone':          'unknown',
    'framing':       'Could not extract',
    'summary':       '',
    'political_lean': 'unknown',
}


def _get_client() -> OpenAI:
    return OpenAI(
        base_url='https://api.featherless.ai/v1',
        api_key=os.environ.get('FEATHERLESS_API_KEY', ''),
    )


def extract_dna(article_text: str, root_text: str) -> dict:
    client = _get_client()
    content = PROMPT.format(root_text=root_text[:500], article_text=article_text[:800])
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': content}],
                temperature=0.1,
                max_tokens=400,
                timeout=15,
            )
            raw = response.choices[0].message.content.strip()
            raw = raw.replace('```json', '').replace('```', '').strip()
            result = json.loads(raw)
            # Leave summary as '' if the LLM didn't produce one; the frontend
            # falls back to headline rather than showing a placeholder string.
            result['summary'] = str(result.get('summary', '')).strip()
            logger.debug('DNA extracted via %s: %d facts, tone=%s',
                         model, len(result.get('facts_kept', [])), result.get('tone'))
            return result
        except Exception as exc:
            logger.debug('Model %s failed, trying next: %s', model, exc)
            continue
    logger.warning('All models failed for DNA extraction, using fallback')
    return copy.deepcopy(_FALLBACK_DNA)


def run(state: dict) -> dict:
    root = state.get('root', {})
    root_text = root.get('text') or root.get('headline', '')
    articles = state.get('articles', [])
    job_id = state.get('job_id', '?')

    logger.info('[%s]  🧬 ════════ DNA EXTRACTOR STARTED ════════  🧬  |  %d article(s) + root', job_id, len(articles))

    # Extract root DNA so drift_scorer has facts to compare against
    if root_text and not root.get('dna', {}).get('facts_kept'):
        logger.info('[%s] Extracting root DNA', job_id)
        root['dna'] = extract_dna(root_text, root_text)
        state['root'] = root
        logger.info('[%s] Root DNA: %d facts, tone=%s',
                    job_id, len(root['dna'].get('facts_kept', [])), root['dna'].get('tone'))

    results = [None] * len(articles)
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(extract_dna, art['text'], root_text): i
            for i, art in enumerate(articles)
        }
        for future in as_completed(futures):
            i = futures[future]
            try:
                dna = future.result()
                results[i] = {
                    **articles[i],
                    'dna': dna,
                    'summary': dna.get('summary', ''),
                }
                logger.debug('[%s] %s DNA: %d facts kept, %d dropped, tone=%s',
                             job_id, articles[i]['outlet'],
                             len(dna.get('facts_kept', [])),
                             len(dna.get('facts_dropped', [])),
                             dna.get('tone'))
            except Exception as exc:
                logger.warning('[%s] %s: DNA extraction raised unexpectedly: %s',
                               job_id, articles[i]['outlet'], exc)
                results[i] = {
                    **articles[i],
                    'dna': copy.deepcopy(_FALLBACK_DNA),
                    'summary': '',
                }

    logger.info('[%s] dna_extractor done — %d result(s)', job_id, len(results))
    state['dna_list'] = results
    return state
