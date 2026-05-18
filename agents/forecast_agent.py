import json
import os

from google import genai


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
    prompt = PROMPT.format(
        headline=root.get('headline', ''),
        text=root.get('text', '')[:1500],
    )
    try:
        r = _get_client().models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt,
        )
        raw = r.text.strip().replace('```json', '').replace('```', '')
        return json.loads(raw)
    except Exception as e:
        return {'error': str(e)}
