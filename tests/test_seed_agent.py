from unittest.mock import patch, MagicMock
import pytest
from agents.seed_agent import run, query_gdelt, query_newsapi, _outlet_from_url, _is_url


# --- Unit tests for helpers ---

def test_is_url():
    assert _is_url('https://reuters.com/article') is True
    assert _is_url('http://bbc.co.uk/news') is True
    assert _is_url('Iran nuclear deal') is False


def test_outlet_from_url():
    assert _outlet_from_url('https://www.reuters.com/world/article') == 'Reuters'
    assert _outlet_from_url('https://bbc.co.uk/news') == 'Bbc'


# --- query_gdelt ---

def test_query_gdelt_returns_first_article():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        'articles': [
            {'url': 'https://example.com/1', 'title': 'Test', 'domain': 'example.com', 'seendate': '20240315T120000Z'},
            {'url': 'https://example.com/2', 'title': 'Test 2'},
        ]
    }
    with patch('agents.seed_agent.requests.get', return_value=mock_resp):
        result = query_gdelt('Iran')
    assert result['url'] == 'https://example.com/1'


def test_query_gdelt_returns_none_on_empty():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {'articles': []}
    with patch('agents.seed_agent.requests.get', return_value=mock_resp):
        result = query_gdelt('Iran')
    assert result is None


def test_query_gdelt_returns_none_on_exception():
    with patch('agents.seed_agent.requests.get', side_effect=Exception('timeout')):
        result = query_gdelt('Iran')
    assert result is None


# --- query_newsapi ---

def test_query_newsapi_returns_none_without_key(monkeypatch):
    monkeypatch.delenv('NEWSAPI_KEY', raising=False)
    result = query_newsapi('Iran')
    assert result is None


def test_query_newsapi_returns_article(monkeypatch):
    monkeypatch.setenv('NEWSAPI_KEY', 'test-key')
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        'articles': [{'title': 'Iran deal', 'url': 'https://cnn.com/1', 'source': {'name': 'CNN'}}]
    }
    with patch('agents.seed_agent.requests.get', return_value=mock_resp):
        result = query_newsapi('Iran')
    assert result['title'] == 'Iran deal'


# --- run() integration ---

def test_run_with_topic_uses_gdelt():
    gdelt_article = {
        'url':       'https://reuters.com/article',
        'title':     'Iran Signs Nuclear Deal',
        'domain':    'reuters.com',
        'seendate':  '20240315T120000Z',
    }
    with patch('agents.seed_agent.query_gdelt', return_value=gdelt_article), \
         patch('agents.seed_agent._fetch_text', return_value='article body text'):
        state = run({'input': 'Iran nuclear deal'})

    assert state.get('error') is None
    assert state['root']['outlet'] == 'Reuters'
    assert state['root']['headline'] == 'Iran Signs Nuclear Deal'
    assert state['root']['text'] == 'article body text'
    assert 'entities' in state


def test_run_falls_back_to_newsapi_when_gdelt_empty(monkeypatch):
    monkeypatch.setenv('NEWSAPI_KEY', 'test-key')
    newsapi_article = {
        'url':         'https://cnn.com/article',
        'title':       'Iran Deal Update',
        'source':      {'name': 'CNN'},
        'publishedAt': '2024-03-15T12:00:00Z',
        'description': 'Breaking news about Iran',
    }
    with patch('agents.seed_agent.query_gdelt', return_value=None), \
         patch('agents.seed_agent.query_newsapi', return_value=newsapi_article):
        state = run({'input': 'Iran nuclear deal'})

    assert state.get('error') is None
    assert state['root']['outlet'] == 'CNN'
    assert state['root']['text'] == 'Breaking news about Iran'


def test_run_sets_error_when_both_sources_empty(monkeypatch):
    monkeypatch.delenv('NEWSAPI_KEY', raising=False)
    with patch('agents.seed_agent.query_gdelt', return_value=None), \
         patch('agents.seed_agent.query_newsapi', return_value=None):
        state = run({'input': 'obscure topic nobody covers'})

    assert 'error' in state
    assert 'root' not in state


def test_run_with_url_input():
    with patch('agents.seed_agent._fetch_text', return_value='Some article words about Iran nuclear'):
        state = run({'input': 'https://reuters.com/world/iran-nuclear-2024'})

    assert state.get('error') is None
    assert state['root']['url'] == 'https://reuters.com/world/iran-nuclear-2024'
    assert state['root']['outlet'] == 'Reuters'
    assert 'entities' in state
