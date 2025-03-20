import re
import asyncio
from iogram import Bot, Dispatcher, F
from iogram.types import Message, FSInputFile
from iogram.dispatcher.rules import Command
from iogram.fsm.storage.memory import MemoryStorage
from iogram.fsm.context import FSMContext
from iogram.fsm.state import State, StatesGroup

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())

YANDEX_URL_REGEX = re.compile(r"https?://yandex\.ru/maps/[\w\d/\-?=&#.%]+")

# Состояние пользователя
class UserState(StatesGroup):
    waiting = State()


@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Отправьте ссылку на заведение из Яндекс.Карт,\n"
        "и я пришлю вам PDF-отчёт с анализом отзывов."
    )


@dp.message(F.text)
async def handle_link(message: Message, state: FSMContext):
    user_data = await state.get_data()

    # Проверка на "ожидание"
    if user_data.get("busy"):
        await message.answer("⏳ Пожалуйста, подождите, пока я не закончу обработку предыдущего запроса.")
        return

    link = message.text.strip()

    if not YANDEX_URL_REGEX.fullmatch(link):
        await message.answer("⚠️ Пожалуйста, отправьте корректную ссылку на заведение в Яндекс.Картах.")
        return

    await message.answer("🔄 Обрабатываю ваш запрос, это может занять немного времени...")
    await state.update_data(busy=True)

    try:
        report_path = await generate_report(link)

        await message.answer_document(FSInputFile(report_path))
        await message.answer("✅ Готово! Можете прислать другую ссылку для анализа.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обработке: {str(e)}")
    finally:
        await state.update_data(busy=False)


async def generate_report(link: str) -> str:
    import shutil
    await asyncio.sleep(5)  # имитируем задержку

    path = "/tmp/sample_report.pdf"
    shutil.copy("example.pdf", path)
    return path


if __name__ == "__main__":
    dp.run_polling(bot)
