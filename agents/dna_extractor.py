import copy
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

MODELS = [
    'Qwen/Qwen2.5-7B-Instruct',
    'Qwen/Qwen2.5-3B-Instruct',
    'microsoft/Phi-3-mini-4k-instruct',
]

PROMPT = """You are a journalism analyst. Extract the following from the article below.
Return ONLY valid JSON — no explanation, no markdown, just the JSON object.

{{
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
            return json.loads(raw)
        except Exception:
            continue
    return copy.deepcopy(_FALLBACK_DNA)


def run(state: dict) -> dict:
    root = state.get('root', {})
    root_text = root.get('text') or root.get('headline', '')
    articles = state.get('articles', [])

    # Extract root DNA so drift_scorer has facts to compare against
    if root_text and not root.get('dna', {}).get('facts_kept'):
        root['dna'] = extract_dna(root_text, root_text)
        state['root'] = root

    results = [None] * len(articles)
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(extract_dna, art['text'], root_text): i
            for i, art in enumerate(articles)
        }
        for future in as_completed(futures):
            i = futures[future]
            try:
                results[i] = {**articles[i], 'dna': future.result()}
            except Exception:
                results[i] = {**articles[i], 'dna': copy.deepcopy(_FALLBACK_DNA)}

    state['dna_list'] = results
    return state
