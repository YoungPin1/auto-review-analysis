import asyncio
import logging
import re
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import FSInputFile


from filter_symbols import clean_review_file
from label_reviews import label_reviews
from parser.parse import parse_reviews
from threshold import filter_labeled_reviews
from create_infografics import generate_charts

API_TOKEN = "7540257200:AAHEg889upnDEjL_qTGhp8Y4y6VUsmltTmM"

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Отправь ссылку на заведение с Яндекс.Карт")


@dp.message()
async def handle_link(message: Message):
    text = message.text.strip()
    await message.answer(f"Принял ссылку: {text}\nСкоро начну обработку...")
    match = re.search(r"/(\d{5,})/", text)
    company_id = int(match.group(1))

    loop = asyncio.get_event_loop()

    # await loop.run_in_executor(None, parse_reviews, company_id)  # парсинг
    # await loop.run_in_executor(None, clean_review_file, company_id)  # чистка символов
    # await loop.run_in_executor(None, label_reviews, company_id)  # разметка
    # await loop.run_in_executor(None, filter_labeled_reviews, company_id)  # чистка confidence
    await loop.run_in_executor(None, generate_charts, company_id)

    json_path = Path(f"files/{company_id}/filtered_analysis.json")
    if json_path.exists():
        file = FSInputFile(json_path)
        await message.answer_document(file, caption="📎 Вот файл с разметкой отзывов")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
