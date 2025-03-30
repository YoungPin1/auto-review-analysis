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
from generate_summary_section import save_summary_and_examples
from render_pdf import render_pdf_from_template
from summarize import summarize_14_clusters
from json_to_txt import export_annotations_to_txt


API_TOKEN = "TELEGRAM TOKEN HERE"

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
        "Я — <b>бот, который умеет анализировать отзывы</b>\n\n"
        "Могу собрать с Яндекс.Карт отзывы о заведении и показать, что именно пишут гости — что им нравится, а что не очень.\n\n"
        "В конце я пришлю PDF-отчёт с готовой аналитикой.",
        reply_markup=keyboard
    )

    await message.answer(
        "📍 Пришлите ссылку на <b>ресторан, кафе, кофейню или любое другое заведение общественного питания</b> на Яндекс.Картах.\n"
        "Нужна ссылка в формате:\n"
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
            "Пример:\n"
            "<code>https://yandex.ru/maps/org/bro_n/44460425999/</code>"
        )
        processing_state[user_id] = False
        return

    await message.answer(
        f"✅ Ссылка получена: {text}\n\n"
        "Начинаю сбор и анализ отзывов. Это может занять от <b>5 до 15 минут</b>, в зависимости от загрузки системы.\n\n"
        "Как только всё будет готово, я пришлю вам уведомление!."
    )

    company_id = int(match.group(1))

    try:
        loop = asyncio.get_event_loop()
        company_info = await loop.run_in_executor(None, parse_reviews, company_id)

        progress_msg = await message.answer("Отзывы собраны. Прогресс: 40%")

        await loop.run_in_executor(None, clean_review_file, company_id)
        await loop.run_in_executor(None, label_reviews, company_id)
        await loop.run_in_executor(None, filter_labeled_reviews, company_id)
        await loop.run_in_executor(None, summarize_14_clusters, company_id)

        await progress_msg.edit_text("Отзывы размечены и проанализированы. Прогресс: 80%")

        await loop.run_in_executor(None, generate_charts, company_id)
        await loop.run_in_executor(None, save_summary_and_examples, company_id)
        await loop.run_in_executor(None, render_pdf_from_template, company_id, company_info["name"])

        await progress_msg.delete()

        report_path = Path(f"files/{company_id}/report/output.pdf")
        txt_path = await loop.run_in_executor(None, export_annotations_to_txt, company_id)
        txt_path = Path(txt_path)

        if report_path.exists():
            await bot.send_document(
                chat_id=message.chat.id,
                document=FSInputFile(report_path),
                caption="Вот готовый PDF-отчёт по отзывам!"
            )
            await bot.send_document(
                chat_id=message.chat.id,
                document=FSInputFile(txt_path),
                caption="Все собранные отзывы с аннотацией в текстовом виде."
            )
        else:
            await message.answer("⚠️ Отчёт не найден. Что-то пошло не так при генерации.")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
        await message.answer(f"Пожалуйста, попробуйте другую ссылку и повторите запрос")
    finally:
        processing_state[user_id] = False


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
