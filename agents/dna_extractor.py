import copy
import json
import os

from openai import OpenAI

MODEL = 'mistralai/Mistral-7B-Instruct-v0.3'

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
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                'role':    'user',
                'content': PROMPT.format(
                    root_text=root_text[:500],
                    article_text=article_text[:800],
                ),
            }],
            temperature=0.1,
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except Exception:
        return copy.deepcopy(_FALLBACK_DNA)


def run(state: dict) -> dict:
    root = state.get('root', {})
    root_text = root.get('text') or root.get('headline', '')
    dna_list = []
    for art in state.get('articles', []):
        dna = extract_dna(art['text'], root_text)
        dna_list.append({**art, 'dna': dna})
    state['dna_list'] = dna_list
    return state
