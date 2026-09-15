from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config import settings
from services import translate_character_name, build_url, create_jina_text, load_cache, save_cache

llm = ChatOpenAI(base_url=settings.base_url, api_key=settings.api_key.get_secret_value(), model=settings.model_name)

@tool
def get_character_build(character_name_ru: str) -> str:
    '''
    Получает полный билд (гайд) для конкретного персонажа Genshin Impact.

    ИСПОЛЬЗУЙ ЭТОТ ИНСТРУМЕНТ, если пользователь спрашивает про:
    - билд, сборку, гайд для конкретного персонажа
    - какие артефакты или оружие взять конкретному персонажу
    - как раскачать таланты конкретному персонажу
    - какие команды подходят персонажу

    Аргумент: character_name_ru (имя персонажа на русском, например "Дилюк" или "Райден")
    :return:
    '''
    try:
        en_name = translate_character_name(character_name_ru)
        cache = load_cache()
        if en_name in cache:
            raw_text = cache[en_name]
        else:
            urls = build_url(en_name)
            raw_text = create_jina_text(urls)

            if not raw_text:
                return f'Не удалось найти гайд, проверь правильность имени персонажа'
            cache[en_name] = raw_text
            save_cache(cache)

        response = llm.invoke(
            [
                SystemMessage(content=(
                    '''Ты эксперт по Genshin Impact. Твоя задача — проанализировать предоставленный текст и извлечь из него ключевую информацию.
                    Если какой-то информации в тексте нет, пиши "Не указано" или оставь пустой список.
                    Отвечай строго на русском языке.'''
                )),
                HumanMessage(content=f'Проанализируй этот текст и верни краткую выжимку в формате JSON с полями: лучшие легендарные и эпические оружия, лучший сет артефактов, статы для артефактов, подстаты для артефактов, порядок прокачки талантов, команды и ротация.Текст гайда для анализа:\n\n{raw_text}')
            ],
            response_format={'type': 'json_object'}
        )
        return response.content
    except Exception as e:
        print(f'Произошла {e} ошибка при сборе билда')

@tool
def answer_general_question(question: str) -> str:
    """
    Отвечает на общие вопросы об игре Genshin Impact.
    ИСПОЛЬЗУЙ ЭТОТ ИНСТРУМЕНТ, если пользователь спрашивает про не про билд, а:
    - игровые механики (реакции элементов, резонанс)
    - лор, сюжет, регионы, персонажей (без привязки к билду)
    - события, валюту, систему молитв
    """
    response = llm.invoke([
        SystemMessage(content=
                      '''Ты дружелюбный и знающий помощник по Genshin Impact. 
                      Отвечай подробно, структурированно и на русском языке. 
                      Используй эмодзи для наглядности.'''
                      ),
        HumanMessage(content=question)
    ])
    return response.content

AGENT_SYSTEM_PROMPT = '''Ты — дружелюбный AI-помощник по игре Genshin Impact 🎮
У тебя есть два инструмента. Твоя задача — выбрать правильный:
1. `get_character_build`: Используй ТОЛЬКО для запросов о билдах, артефактах, оружии или талантах КОНКРЕТНОГО персонажа.
2. `answer_general_question`: Используй для ВСЕХ остальных вопросов (механики, лор, общие советы).
ВАЖНО:
- Если инструмент `get_character_build` вернул тебе JSON, твоя задача — не просто переслать его, а красиво оформить для пользователя, используя жирный шрифт, списки и эмодзи.
- Всегда отвечай на русском языке.
'''

agent = create_react_agent(
    model=llm,
    tools=[get_character_build, answer_general_question],
    prompt=AGENT_SYSTEM_PROMPT,
)

def run_agent(user_query: str) -> str:
    """Запускает агента и возвращает финальный ответ."""
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    return result["messages"][-1].content