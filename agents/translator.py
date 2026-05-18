import os

from google import genai
from langdetect import detect, LangDetectException


def _get_client() -> genai.Client:
    return genai.Client(api_key=os.environ.get('GEMINI_API_KEY', ''))


def translate_to_english(text: str) -> str:
    client = _get_client()  # keep reference alive for the duration of the request
    r = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=(
            'Translate this news article to English. Preserve the tone and framing exactly. '
            'Do not add commentary. Return only the translated text.\n\n' + text
        ),
    )
    return r.text


def run(state: dict) -> dict:
    for art in state.get('articles', []):
        try:
            lang = detect(art['text'])
        except LangDetectException:
            continue
        if lang != 'en':
            art['language'] = lang
            try:
                art['text'] = translate_to_english(art['text'])
            except Exception:
                pass  # leave in original language if Gemini fails
    return state
