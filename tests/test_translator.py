from unittest.mock import MagicMock, patch

from agents.translator import run


def _article(text: str, language: str = 'en') -> dict:
    return {'outlet': 'BBC', 'url': 'https://example.com', 'headline': 'Test', 'text': text, 'language': language}


def _mock_translation(translated: str) -> MagicMock:
    resp = MagicMock()
    resp.text = translated
    return resp


def test_english_articles_are_untouched(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    state = {'articles': [_article('Iran nuclear talks resumed today.')]}

    with patch('agents.translator._get_client') as mock_get:
        result = run(state)

    mock_get.return_value.models.generate_content.assert_not_called()
    assert result['articles'][0]['text'] == 'Iran nuclear talks resumed today.'
    assert result['articles'][0]['language'] == 'en'


def test_non_english_article_is_translated(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    state = {'articles': [_article('Les pourparlers nucléaires iraniens ont repris.')]}

    with patch('agents.translator._get_client') as mock_get:
        mock_get.return_value.models.generate_content.return_value = _mock_translation('Iranian nuclear talks resumed.')
        with patch('agents.translator.detect', return_value='fr'):
            result = run(state)

    assert result['articles'][0]['text'] == 'Iranian nuclear talks resumed.'
    assert result['articles'][0]['language'] == 'fr'


def test_translation_called_once_per_non_english_article(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    state = {'articles': [
        _article('English article text'),
        _article('Texto en español sobre Irán'),
        _article('Another English article'),
    ]}

    with patch('agents.translator._get_client') as mock_get:
        mock_get.return_value.models.generate_content.return_value = _mock_translation('Translated text')
        with patch('agents.translator.detect', side_effect=['en', 'es', 'en']):
            run(state)

    assert mock_get.return_value.models.generate_content.call_count == 1


def test_lang_detect_exception_is_silently_ignored(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    state = {'articles': [_article('???')]}

    from langdetect import LangDetectException
    with patch('agents.translator._get_client') as mock_get:
        with patch('agents.translator.detect', side_effect=LangDetectException(0, '???')):
            result = run(state)

    mock_get.return_value.models.generate_content.assert_not_called()
    assert result['articles'][0]['text'] == '???'


def test_run_with_empty_articles(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    state = {'articles': []}

    with patch('agents.translator._get_client') as mock_get:
        result = run(state)

    mock_get.return_value.models.generate_content.assert_not_called()
    assert result['articles'] == []


def test_run_mutates_articles_in_place(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    article = _article('Texto en español')
    state = {'articles': [article]}

    with patch('agents.translator._get_client') as mock_get:
        mock_get.return_value.models.generate_content.return_value = _mock_translation('Spanish text')
        with patch('agents.translator.detect', return_value='es'):
            run(state)

    assert article['text'] == 'Spanish text'
    assert article['language'] == 'es'
