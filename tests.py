import pytest
from unittest.mock import patch, MagicMock
from services import translate_character_name, build_url, create_jina_text, load_cache, save_cache, CACHE_FILE
from config import settings
import tempfile
import os
import services
@pytest.mark.parametrize('rus_name, eng_name',
                         (
                             ('Дилюк', 'Diluc'),
                             ('Бай Джу', 'Baizhu'),
                             ('Райден', 'Raiden'),
                         )
)
@patch('services.llm')
def test_translate_character_name(mock_llm, rus_name, eng_name):
    mock_llm.invoke.return_value = MagicMock(content=eng_name)
    assert eng_name == translate_character_name(rus_name)


@pytest.mark.parametrize('en_name, expected_suffix', [
    ('Diluc', 'diluc'),
    ('Raiden', 'raiden'),
    ('Xiangling', 'xiangling'),
])
def test_build_url(en_name, expected_suffix):
    urls = build_url(en_name)
    assert len(urls) == 2

    assert expected_suffix in urls[0]
    assert expected_suffix in urls[1]

    assert urls[0].endswith(f'{expected_suffix}-guide')
    assert urls[1].endswith(f'{expected_suffix}-guide-build')

    assert settings.genshin_url in urls[0]
    assert settings.genshin_url in urls[1]


@patch('services.requests.get')
def test_create_jina_text_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Гайд по Дилюку..."
    mock_get.return_value = mock_response

    result = create_jina_text(["https://example.com/diluc-guide"])

    assert result == "Гайд по Дилюку..."
    mock_get.assert_called_once()


@patch('services.requests.get')
def test_create_jina_text_404_returns_empty(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = create_jina_text(["https://example.com/unknown-guide"])

    assert result == ''


@patch('services.requests.get')
def test_create_jina_text_tries_multiple_urls(mock_get):
    """Если первый URL не сработал, пробует второй"""
    mock_404 = MagicMock(status_code=404)
    mock_200 = MagicMock(status_code=200, text="Успех!")
    mock_get.side_effect = [mock_404, mock_200]

    result = create_jina_text([
        "https://example.com/404",
        "https://example.com/200"
    ])
    assert result == "Успех!"


@patch('services.requests.get')
def test_create_jina_text_uses_jina_prefix(mock_get):
    """Функция добавляет префикс r.jina.ai к URL"""
    mock_response = MagicMock(status_code=200, text="text")
    mock_get.return_value = mock_response

    create_jina_text(["https://example.com/guide"])

    called_url = mock_get.call_args[0][0]
    assert called_url == "https://r.jina.ai/https://example.com/guide"


def test_save_and_load_cache():
    services.CACHE_FILE = tempfile.gettempdir() + "/test_cache.json"

    save_cache({"Дилюк": "огонь"})

    loaded = load_cache()
    assert loaded["Дилюк"] == "огонь"

    os.remove(services.CACHE_FILE)


def test_load_missing_file():
    """Если файла нет, возвращается пустой dict"""
    services.CACHE_FILE = tempfile.gettempdir() + "/no_such_file.json"
    result = load_cache()
    assert result == {}

