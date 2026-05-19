import logging
import os

from google import genai
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


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
    articles = state.get('articles', [])
    job_id = state.get('job_id', '?')

    logger.info('[%s] translator started — %d article(s) to inspect', job_id, len(articles))

    translated = 0
    for art in articles:
        try:
            lang = detect(art['text'])
        except LangDetectException:
            logger.debug('[%s] %s: language detection failed, skipping', job_id, art['outlet'])
            continue
        if lang != 'en':
            logger.info('[%s] %s: detected language "%s", translating', job_id, art['outlet'], lang)
            art['language'] = lang
            try:
                art['text'] = translate_to_english(art['text'])
                translated += 1
                logger.debug('[%s] %s: translation complete', job_id, art['outlet'])
            except Exception as exc:
                logger.warning('[%s] %s: translation failed, keeping original: %s',
                               job_id, art['outlet'], exc)

    logger.info('[%s] translator done — %d article(s) translated', job_id, translated)
    return state
