"""
E2E integration test — PR-13 (H10 Pipeline Check).
Requires all API keys in .env: FEATHERLESS_API_KEY, GEMINI_API_KEY, NEWSAPI_KEY.
Run: pytest tests/test_pipeline.py -v -s
"""
from dotenv import load_dotenv
load_dotenv()

from backend.orchestrator import run_pipeline


def test_full_pipeline():
    result = run_pipeline('test-job-001', 'Russia Ukraine war')

    assert result.get('root') is not None, 'root story not found'
    assert isinstance(result.get('scored_list'), list), 'scored_list missing'
    assert len(result['scored_list']) >= 3, 'fewer than 3 outlets matched'
    assert isinstance(result.get('tree'), dict), 'tree not built'
    assert 'children' in result['tree'], 'tree has no children'
    assert len(result['tree']['children']) >= 2, 'fewer than 2 country branches'

    print(f"\nOutlets found: {len(result['scored_list'])}")
    print(f"Tree branches: {len(result['tree']['children'])}")
    print(f"Root: {result['root'].get('outlet')} — {result['root'].get('headline', '')[:60]}")

    for art in result['scored_list']:
        assert art.get('country') not in (None, 'Unknown'), \
            f"Missing country for outlet {art['outlet']}"
        assert 0 <= art['drift_score'] <= 100, \
            f"drift_score out of range for {art['outlet']}"
