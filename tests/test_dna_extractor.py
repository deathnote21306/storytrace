import json
from unittest.mock import MagicMock, patch

from agents.dna_extractor import extract_dna, run

DNA_KEYS = {'facts_kept', 'facts_dropped', 'tone', 'framing', 'political_lean'}

VALID_DNA = {
    'facts_kept':    ['Iran agreed to pause enrichment'],
    'facts_dropped': ['IAEA inspection rejected'],
    'tone':          'neutral',
    'framing':       'Diplomatic de-escalation framing',
    'political_lean': 'center',
}


def _mock_completion(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_extract_dna_returns_valid_structure(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = (
            _mock_completion(json.dumps(VALID_DNA))
        )
        result = extract_dna('article text', 'root text')

    assert set(result.keys()) == DNA_KEYS
    assert result['tone'] == 'neutral'
    assert result['political_lean'] == 'center'


def test_extract_dna_strips_markdown_fences(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    wrapped = f'```json\n{json.dumps(VALID_DNA)}\n```'
    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = (
            _mock_completion(wrapped)
        )
        result = extract_dna('article text', 'root text')

    assert set(result.keys()) == DNA_KEYS
    assert result['tone'] == 'neutral'


def test_extract_dna_falls_back_on_invalid_json(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = (
            _mock_completion('this is not json at all')
        )
        result = extract_dna('article text', 'root text')

    assert set(result.keys()) == DNA_KEYS
    assert result['tone'] == 'unknown'
    assert result['facts_kept'] == []


def test_extract_dna_falls_back_on_api_exception(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.side_effect = Exception('API down')
        result = extract_dna('article text', 'root text')

    assert set(result.keys()) == DNA_KEYS
    assert result['framing'] == 'Could not extract'


def test_extract_dna_fallbacks_are_independent():
    """Each fallback dict is a fresh copy — mutating one doesn't affect others."""
    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.side_effect = Exception('fail')
        r1 = extract_dna('text', 'root')
        r2 = extract_dna('text', 'root')

    r1['facts_kept'].append('mutated')
    assert r2['facts_kept'] == []


def test_run_attaches_dna_to_each_article(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    state = {
        'root': {'text': 'Root story about Iran nuclear deal'},
        'articles': [
            {'outlet': 'BBC', 'url': 'https://bbc.com/1', 'headline': 'Iran deal',
             'text': 'BBC article text', 'language': 'en'},
            {'outlet': 'RT',  'url': 'https://rt.com/1',  'headline': 'Western pressure',
             'text': 'RT article text',  'language': 'en'},
        ],
    }

    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = (
            _mock_completion(json.dumps(VALID_DNA))
        )
        result = run(state)

    assert len(result['dna_list']) == 2
    for entry in result['dna_list']:
        assert 'dna' in entry
        assert set(entry['dna'].keys()) == DNA_KEYS
        assert 'outlet' in entry
        assert 'url' in entry


def test_run_preserves_original_article_fields(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    article = {
        'outlet': 'Guardian', 'url': 'https://guardian.com/1',
        'headline': 'Iran steps back', 'text': 'article body', 'language': 'en',
    }
    state = {'root': {'headline': 'Iran nuclear talks'}, 'articles': [article]}

    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = (
            _mock_completion(json.dumps(VALID_DNA))
        )
        result = run(state)

    entry = result['dna_list'][0]
    assert entry['outlet'] == 'Guardian'
    assert entry['url'] == 'https://guardian.com/1'
    assert entry['headline'] == 'Iran steps back'
    assert entry['language'] == 'en'


def test_run_uses_root_headline_when_text_missing(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    state = {
        'root': {'headline': 'Iran nuclear deal signed'},
        'articles': [{'outlet': 'BBC', 'url': 'u', 'headline': 'h', 'text': 't', 'language': 'en'}],
    }

    with patch('agents.dna_extractor._get_client') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = (
            _mock_completion(json.dumps(VALID_DNA))
        )
        run(state)

    call_args = mock_client.return_value.chat.completions.create.call_args
    prompt_content = call_args.kwargs['messages'][0]['content']
    assert 'Iran nuclear deal signed' in prompt_content


def test_run_with_empty_articles(monkeypatch):
    monkeypatch.setenv('FEATHERLESS_API_KEY', 'test-key')
    state = {'root': {'text': 'root'}, 'articles': []}

    result = run(state)

    assert result['dna_list'] == []
