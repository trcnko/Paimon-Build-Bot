import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from agent import run_agent
from config import settings

bot = Bot(token=settings.bot_token.get_secret_value())
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "🎮 *Привет! Я AI-помощник по Genshin Impact*\n\n"
        "Я могу:\n"
        "🔥 Собрать актуальный билд для любого персонажа\n"
        "❓ Ответить на вопросы о механиках, реакциях и лоре игры\n\n"
    )
    await message.answer(welcome_text, parse_mode="Markdown")


@dp.message()
async def handle_message(message: Message):
    """Обработчик обычных сообщений"""
    await message.chat.do("typing")
    await message.answer("⏳Подожди секундочку...")

    try:
        response = await asyncio.to_thread(run_agent, message.text)
        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await message.answer(
            "😔 Извини, произошла техническая ошибка. "
            "Попробуй задать вопрос чуть позже."
        )


async def main():
    """Запуск бота"""
    print("🚀 Бот запущен! Ожидаю сообщения...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")