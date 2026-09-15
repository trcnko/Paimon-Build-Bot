import json
import os.path
import requests
from langchain_core.messages import SystemMessage
from typing import List
from langchain_openai import ChatOpenAI
from config import settings

llm = ChatOpenAI(base_url=settings.base_url, api_key=settings.api_key.get_secret_value(), model=settings.model_name)

def translate_character_name(rus_name: str) -> str:
    '''Переводит имя персонажа с русского на английский'''
    response = llm.invoke([
        SystemMessage(content='''Переведи имя персонажа Genshin Impact с русского на английский так, 
        как оно пишется в официальной английской версии игры. Если такого имени нет в списке персонажей, просто переведи имя на английский.
        Верни ТОЛЬКО английское имя, без пояснений и кавычек'''),
        {'role': 'user', 'content': rus_name}
    ])
    return response.content.strip().strip('"\'`')

def build_url(en_name: str) -> List[str]:
    '''Формирует 2 варианта url гайда персонажа'''
    url_type_1 = f'{settings.genshin_url}{en_name.lower()}-guide'
    url_type_2 = f'{settings.genshin_url}{en_name.lower()}-guide-build'
    return [url_type_1, url_type_2]

def create_jina_text(urls: List[str]) -> str:
    for url in urls:
        jina_url = f'https://r.jina.ai/{url}'
        try:
            response = requests.get(jina_url, timeout=15)
            if response.status_code == 200:
                return response.text
        except requests.RequestException:
            continue

    return ''

CACHE_FILE = 'cache.json'
def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_cache(data: dict):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=3)