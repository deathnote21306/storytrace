from unittest.mock import patch

from agents.alert_agent import run


def _scored_article(outlet: str, drift_score: int, **kwargs) -> dict:
    return {
        'outlet': outlet,
        'drift_score': drift_score,
        'country': kwargs.get('country', 'UK'),
        'headline': kwargs.get('headline', 'Test headline'),
        'url': kwargs.get('url', 'https://example.com'),
    }


def test_run_fires_alert_above_threshold(monkeypatch):
    monkeypatch.setenv('WEBHOOK_URL', 'https://hooks.example.com/alerts')
    state = {
        'job_id': 'job-001',
        'scored_list': [_scored_article('BBC', 80)],
    }

    with patch('agents.alert_agent.requests.post') as mock_post:
        result = run(state)

    mock_post.assert_called_once()
    assert result['alerts_fired'] == ['BBC']
    assert result['drift_detected'] == ['BBC']


def test_run_skips_below_threshold(monkeypatch):
    monkeypatch.setenv('WEBHOOK_URL', 'https://hooks.example.com/alerts')
    state = {
        'job_id': 'job-002',
        'scored_list': [_scored_article('BBC', 50)],
    }

    with patch('agents.alert_agent.requests.post') as mock_post:
        result = run(state)

    mock_post.assert_not_called()
    assert result['alerts_fired'] == []
    assert result['drift_detected'] == []


def test_run_handles_missing_webhook_url(monkeypatch):
    """When no webhook is configured: drift is detected but no alert is fired."""
    monkeypatch.delenv('WEBHOOK_URL', raising=False)
    state = {
        'job_id': 'job-003',
        'scored_list': [_scored_article('CNN', 90)],
    }

    with patch('agents.alert_agent.requests.post') as mock_post:
        result = run(state)

    mock_post.assert_not_called()
    assert result['alerts_fired'] == []        # no webhook → no POST attempted
    assert result['drift_detected'] == ['CNN'] # still above threshold


def test_run_handles_post_exception(monkeypatch):
    """Webhook is configured but POST fails — outlet still counted in alerts_fired (attempt was made)."""
    monkeypatch.setenv('WEBHOOK_URL', 'https://hooks.example.com/alerts')
    state = {
        'job_id': 'job-004',
        'scored_list': [_scored_article('RT', 75)],
    }

    with patch('agents.alert_agent.requests.post', side_effect=Exception('connection refused')):
        result = run(state)

    assert result['alerts_fired'] == ['RT']
    assert result['drift_detected'] == ['RT']


def test_run_payload_shape(monkeypatch):
    monkeypatch.setenv('WEBHOOK_URL', 'https://hooks.example.com/alerts')
    state = {
        'job_id': 'job-005',
        'scored_list': [_scored_article('Guardian', 85, country='UK', headline='Big story', url='https://guardian.com/1')],
    }

    with patch('agents.alert_agent.requests.post') as mock_post:
        run(state)

    payload = mock_post.call_args.kwargs['json']
    assert set(payload.keys()) == {
        'job_id', 'outlet', 'country', 'drift_score', 'headline', 'url', 'alert',
    }
    assert payload['job_id'] == 'job-005'
    assert payload['outlet'] == 'Guardian'
    assert payload['drift_score'] == 85
    assert 'DRIFT ALERT' in payload['alert']


def test_run_with_empty_scored_list(monkeypatch):
    monkeypatch.setenv('WEBHOOK_URL', 'https://hooks.example.com/alerts')

    with patch('agents.alert_agent.requests.post') as mock_post:
        result = run({'job_id': 'job-006'})

    mock_post.assert_not_called()
    assert result['alerts_fired'] == []
    assert result['drift_detected'] == []
