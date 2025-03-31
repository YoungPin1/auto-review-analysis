import asyncio
import logging
import re
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


from create_infografics import generate_charts
from filter_symbols import clean_review_file
from label_reviews import label_reviews
from parser.parse import parse_reviews
from threshold import filter_labeled_reviews

API_TOKEN = "7540257200:AAHEg889upnDEjL_qTGhp8Y4y6VUsmltTmM"

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

processing_state = {}  # user_id -> bool


@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📩 Поддержка", url="https://t.me/aabattalov")]
        ]
    )

    await message.answer(
        "👋 <b>Привет!</b>\n\n"
        "Я — <b>бот, который умеет анализировать отзывы</b> 🧠\n\n"
        "Могу собрать с Яндекс.Карт отзывы о заведении и показать, что именно пишут гости — что им нравится, а что не очень.\n\n"
        "📊 В конце я пришлю PDF-отчёт с готовой аналитикой.",
        reply_markup=keyboard
    )

    await message.answer(
        "📍 Пришлите ссылку на <b>ресторан, кафе, кофейню или любое другое заведение общественного питания</b> на Яндекс.Картах.\n"
        "⚠️ Нужна ссылка в формате:\n"
        "<code>https://yandex.ru/maps/org/название/id</code>\n\n"
        ""
        "А я подготовлю для вас 📄 <b>анализ отзывов</b> с визуализациями и понятными выводами."
    )


@dp.message()
async def handle_link(message: Message):
    user_id = message.from_user.id

    if processing_state.get(user_id):
        await message.answer("⏳ Подождите, ваш предыдущий запрос ещё обрабатывается.")
        return

    processing_state[user_id] = True
    text = message.text.strip()

    match = re.search(r"/(\d{5,})/", text)
    if not match:
        await message.answer(
            "❌ Не удалось найти ID заведения в ссылке. Убедитесь, что вы отправили корректную ссылку с Яндекс.Карт.\n\n"
            "⚠️ Нужна ссылка в формате:\n"
            "<code>https://yandex.ru/maps/org/название/id</code>\n\n"
            "📌 Пример:\n"
            "<code>https://yandex.ru/maps/org/bro_n/44460425999/</code>"
        )
        processing_state[user_id] = False
        return

    await message.answer(
        f"✅ Ссылка получена: {text}\n\n"
        "🔍 Начинаю сбор и анализ отзывов. Это может занять от <b>5 до 15 минут</b>, в зависимости от загрузки системы.\n\n"
        "📬 Как только всё будет готово, я пришлю вам уведомление!."
    )

    company_id = int(match.group(1))

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, parse_reviews, company_id)
        await loop.run_in_executor(None, clean_review_file, company_id)
        await loop.run_in_executor(None, label_reviews, company_id)
        await loop.run_in_executor(None, filter_labeled_reviews, company_id)
        await loop.run_in_executor(None, generate_charts, company_id)

        json_path = Path(f"files/{company_id}/filtered_analysis.json")
        if json_path.exists():
            file = FSInputFile(json_path)
            await message.answer_document(file, caption="📎 Вот файл с разметкой отзывов")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
        await message.answer(f"Пожалуйста, попробуйте другую ссылку и повторите запрос")
    finally:
        processing_state[user_id] = False


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
