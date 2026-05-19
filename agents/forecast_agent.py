import json
import logging
import os

from google import genai

logger = logging.getLogger(__name__)


PROMPT = """You are a geopolitical risk analyst. Analyze this news event and provide a structured impact forecast.

Return ONLY valid JSON in this exact format:
{{
  "event_type": "geopolitical|economic|environmental|conflict|other",
  "countries": [
    {{
      "country":    "country name",
      "dependency": "how this country is connected to the event",
      "impact":     "specific projected impact with timeframe",
      "confidence": "high|medium|low"
    }}
  ],
  "panic_forecasts": ["list any exaggerated or unsupported claims circulating in media"],
  "evidence_assessment": "your evidence-based summary paragraph"
}}

Include the 5 most affected countries. Focus on real, measurable impacts.

NEWS EVENT:
{headline}

ARTICLE TEXT:
{text}
"""


def _get_client() -> genai.Client:
    return genai.Client(api_key=os.environ.get('GEMINI_API_KEY', ''))


def run(story: dict) -> dict:
    root = story.get('root', {})
    job_id = story.get('job_id', '?')
    headline = root.get('headline', '')

    logger.info('[%s] forecast_agent started — headline: "%s"', job_id, headline[:80])

    prompt = PROMPT.format(
        headline=headline,
        text=root.get('text', '')[:1500],
    )
    try:
        client = _get_client()  # keep reference alive for the duration of the request
        r = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
        )
        raw = r.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(raw)
        logger.info('[%s] forecast_agent done — event_type=%s, %d countries',
                    job_id, result.get('event_type'), len(result.get('countries', [])))
        return result
    except Exception as exc:
        logger.error('[%s] forecast_agent failed: %s', job_id, exc)
        return {'error': str(exc)}
