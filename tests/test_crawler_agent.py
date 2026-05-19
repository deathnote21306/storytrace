from unittest.mock import MagicMock, patch

from agents.crawler_agent import (
    WORD_CAP,
    _build_search_context,
    _candidate_score,
    _fetch_outlet_candidates,
    _is_safe_url,
    _score_relevance_batch,
    _strip_html,
    entity_match,
    fetch_first_300_words,
    run,
)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def test_entity_match_case_insensitive():
    assert entity_match('Iran Signs Nuclear Deal', ['iran', 'nuclear']) is True
    assert entity_match('Local Weather Update', ['iran']) is False


def test_strip_html_removes_tags():
    assert 'script' not in _strip_html('<script>alert(1)</script>Iran deal')
    assert 'Iran deal' in _strip_html('<p>Iran deal</p>')


def test_is_safe_url_allows_public_domains():
    assert _is_safe_url('https://bbc.co.uk/news') is True
    assert _is_safe_url('http://example.com/page') is True


def test_is_safe_url_blocks_private_ips():
    assert _is_safe_url('http://192.168.1.1/secret') is False
    assert _is_safe_url('http://10.0.0.1/internal') is False
    assert _is_safe_url('http://127.0.0.1/admin') is False


def test_is_safe_url_blocks_non_http_schemes():
    assert _is_safe_url('file:///etc/passwd') is False
    assert _is_safe_url('ftp://example.com/file') is False


def test_fetch_first_300_words_caps_at_300():
    long_text = ' '.join(['word'] * 500)
    mock_resp = MagicMock()
    mock_resp.text = long_text
    mock_resp.raise_for_status = MagicMock()
    with patch('agents.crawler_agent.requests.get', return_value=mock_resp):
        result = fetch_first_300_words('https://example.com/article')
    assert result is not None
    assert len(result.split()) <= WORD_CAP


def test_fetch_first_300_words_strips_html():
    mock_resp = MagicMock()
    mock_resp.text = '<html><body><p>Iran nuclear deal</p></body></html>'
    mock_resp.raise_for_status = MagicMock()
    with patch('agents.crawler_agent.requests.get', return_value=mock_resp):
        result = fetch_first_300_words('https://example.com/article')
    assert result is not None
    assert '<' not in result
    assert 'Iran nuclear deal' in result


def test_fetch_first_300_words_returns_none_on_exception():
    with patch('agents.crawler_agent.requests.get', side_effect=Exception('timeout')):
        result = fetch_first_300_words('https://example.com/article')
    assert result is None


def test_fetch_first_300_words_blocks_ssrf():
    result = fetch_first_300_words('http://169.254.169.254/latest/meta-data/')
    assert result is None


# ---------------------------------------------------------------------------
# _candidate_score
# ---------------------------------------------------------------------------

def _make_entry(title='', summary='', description='', link='https://example.com'):
    entry = MagicMock()
    data = {'title': title, 'summary': summary, 'description': description}
    entry.get = lambda key, default='': data.get(key, default)
    entry.link = link
    return entry


def test_candidate_score_counts_keyword_hits_in_headline():
    entry = _make_entry(title='Iran nuclear deal signed')
    assert _candidate_score(entry, ['Iran', 'nuclear', 'deal']) == 3


def test_candidate_score_hits_in_summary_too():
    entry = _make_entry(title='Major breakthrough', summary='Iran and US reach agreement')
    assert _candidate_score(entry, ['Iran', 'agreement']) == 2


def test_candidate_score_zero_when_no_match():
    entry = _make_entry(title='Weather forecast for London')
    assert _candidate_score(entry, ['Iran', 'nuclear']) == 0


# ---------------------------------------------------------------------------
# _build_search_context
# ---------------------------------------------------------------------------

def test_build_search_context_returns_empty_when_no_content():
    result = _build_search_context({})
    assert result == {}


def test_build_search_context_parses_llm_response():
    mock_response = MagicMock()
    mock_response.text = '{"keywords": ["Iran", "nuclear deal", "Geneva"], "summary": "Iran signs nuclear accord"}'
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    with patch('agents.crawler_agent._get_gemini_client', return_value=mock_client):
        result = _build_search_context({'headline': 'Iran signs deal', 'text': 'Full article text'})
    assert result['keywords'] == ['Iran', 'nuclear deal', 'Geneva']
    assert 'Iran' in result['summary']


def test_build_search_context_falls_back_on_llm_error():
    with patch('agents.crawler_agent._get_gemini_client', side_effect=Exception('API error')):
        result = _build_search_context({'headline': 'Iran deal', 'text': 'text'})
    assert result == {}


# ---------------------------------------------------------------------------
# _score_relevance_batch
# ---------------------------------------------------------------------------

def test_score_relevance_batch_empty_candidates():
    assert _score_relevance_batch('root story', []) == []


def test_score_relevance_batch_parses_llm_booleans():
    mock_response = MagicMock()
    mock_response.text = '[true, false, true]'
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    candidates = [
        {'outlet': 'BBC', 'headline': 'A', 'rss_summary': ''},
        {'outlet': 'CNN', 'headline': 'B', 'rss_summary': ''},
        {'outlet': 'RT',  'headline': 'C', 'rss_summary': ''},
    ]
    with patch('agents.crawler_agent._get_gemini_client', return_value=mock_client):
        result = _score_relevance_batch('Iran signs nuclear deal', candidates)
    assert result == [True, False, True]


def test_score_relevance_batch_falls_back_to_true_on_error():
    candidates = [
        {'outlet': 'BBC', 'headline': 'A', 'rss_summary': ''},
        {'outlet': 'CNN', 'headline': 'B', 'rss_summary': ''},
    ]
    with patch('agents.crawler_agent._get_gemini_client', side_effect=Exception('API error')):
        result = _score_relevance_batch('root story', candidates)
    assert result == [True, True]


def test_score_relevance_batch_falls_back_when_length_mismatch():
    mock_response = MagicMock()
    mock_response.text = '[true]'  # only 1 bool for 2 candidates
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    candidates = [
        {'outlet': 'BBC', 'headline': 'A', 'rss_summary': ''},
        {'outlet': 'CNN', 'headline': 'B', 'rss_summary': ''},
    ]
    with patch('agents.crawler_agent._get_gemini_client', return_value=mock_client):
        result = _score_relevance_batch('root story', candidates)
    assert result == [True, True]


# ---------------------------------------------------------------------------
# _fetch_outlet_candidates
# ---------------------------------------------------------------------------

def test_fetch_outlet_candidates_returns_top_scored():
    entries = [
        _make_entry('Iran nuclear deal signed', 'IAEA confirms agreement', link='https://bbc.com/1'),
        _make_entry('Iran talks resume', '', link='https://bbc.com/2'),
        _make_entry('Weather in London', '', link='https://bbc.com/3'),
    ]
    feed = MagicMock()
    feed.entries = entries
    with patch('agents.crawler_agent.feedparser.parse', return_value=feed):
        result = _fetch_outlet_candidates('BBC', 'http://fake', ['Iran', 'nuclear', 'IAEA'], ['Iran'])
    urls = [r['url'] for r in result]
    assert 'https://bbc.com/1' in urls
    assert 'https://bbc.com/3' not in urls


def test_fetch_outlet_candidates_returns_empty_on_parse_error():
    with patch('agents.crawler_agent.feedparser.parse', side_effect=Exception('feed down')):
        result = _fetch_outlet_candidates('BBC', 'http://fake', ['Iran'], ['Iran'])
    assert result == []


# ---------------------------------------------------------------------------
# run() integration
# ---------------------------------------------------------------------------

def _make_feed_entry(title: str, link: str):
    entry = MagicMock()
    entry.get = lambda key, default='': title if key == 'title' else default
    entry.link = link
    entry.title = title
    return entry


def _make_feed(entries):
    feed = MagicMock()
    feed.entries = entries
    return feed


def test_run_returns_articles_for_matched_headlines():
    entry = _make_feed_entry('Iran nuclear talks resume', 'https://bbc.com/iran')
    feed = _make_feed([entry])

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch('agents.crawler_agent.fetch_first_300_words', return_value='article body text'),
        patch('agents.crawler_agent._build_search_context',
              return_value={'keywords': ['Iran', 'nuclear'], 'summary': 'Iran resumes nuclear talks'}),
        patch('agents.crawler_agent._score_relevance_batch', return_value=[True]),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran', 'nuclear'], 'root': {'headline': 'Iran deal', 'text': ''}})

    assert len(state['articles']) == 1
    art = state['articles'][0]
    assert art['outlet'] == 'BBC'
    assert art['url'] == 'https://bbc.com/iran'
    assert art['headline'] == 'Iran nuclear talks resume'
    assert art['text'] == 'article body text'
    assert art['language'] == 'en'


def test_run_skips_feed_when_parser_raises():
    with (
        patch('agents.crawler_agent.feedparser.parse', side_effect=Exception('feed down')),
        patch('agents.crawler_agent._build_search_context',
              return_value={'keywords': ['Iran'], 'summary': 'Iran story'}),
        patch('agents.crawler_agent._score_relevance_batch', return_value=[]),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran'], 'root': {'headline': 'Iran deal', 'text': ''}})

    assert state['articles'] == []


def test_run_one_article_per_outlet():
    entries = [
        _make_feed_entry('Iran deal update 1', 'https://bbc.com/1'),
        _make_feed_entry('Iran deal update 2', 'https://bbc.com/2'),
        _make_feed_entry('Iran deal update 3', 'https://bbc.com/3'),
    ]
    feed = _make_feed(entries)

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch('agents.crawler_agent.fetch_first_300_words', return_value='body'),
        patch('agents.crawler_agent._build_search_context',
              return_value={'keywords': ['Iran'], 'summary': 'Iran story'}),
        patch('agents.crawler_agent._score_relevance_batch', return_value=[True, True, True]),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran'], 'root': {'headline': 'Iran deal', 'text': ''}})

    assert len(state['articles']) == 1


def test_run_skips_when_fetch_returns_none():
    entry = _make_feed_entry('Iran nuclear talks', 'https://bbc.com/iran')
    feed = _make_feed([entry])

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch('agents.crawler_agent.fetch_first_300_words', return_value=None),
        patch('agents.crawler_agent._build_search_context',
              return_value={'keywords': ['Iran', 'nuclear'], 'summary': 'Iran story'}),
        patch('agents.crawler_agent._score_relevance_batch', return_value=[True]),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran'], 'root': {'headline': 'Iran deal', 'text': ''}})

    assert state['articles'] == []


def test_run_with_no_entities():
    entry = _make_feed_entry('Iran nuclear talks', 'https://bbc.com/iran')
    feed = _make_feed([entry])

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch('agents.crawler_agent._build_search_context', return_value={}),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': []})

    assert state['articles'] == []


def test_run_llm_filters_irrelevant_articles():
    """LLM marks one of two outlets as irrelevant — only the relevant one is returned."""
    bbc_entry = _make_feed_entry('Iran nuclear talks resume', 'https://bbc.com/iran')
    cnn_entry = _make_feed_entry('Iran sanctions lifted', 'https://cnn.com/iran')
    bbc_feed = _make_feed([bbc_entry])
    cnn_feed = _make_feed([cnn_entry])

    def fake_parse(url):
        if 'bbc' in url:
            return bbc_feed
        return cnn_feed

    with (
        patch('agents.crawler_agent.feedparser.parse', side_effect=fake_parse),
        patch('agents.crawler_agent.fetch_first_300_words', return_value='article text'),
        patch('agents.crawler_agent._build_search_context',
              return_value={'keywords': ['Iran', 'nuclear'], 'summary': 'Iran resumes nuclear talks'}),
        # BBC is relevant, CNN is not
        patch('agents.crawler_agent._score_relevance_batch', return_value=[True, False]),
        patch.dict('agents.crawler_agent.RSS_FEEDS',
                   {'BBC': 'http://bbc-feed', 'CNN': 'http://cnn-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran'], 'root': {'headline': 'Iran nuclear talks', 'text': ''}})

    assert len(state['articles']) == 1
    assert state['articles'][0]['outlet'] == 'BBC'
