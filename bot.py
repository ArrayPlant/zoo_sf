import logging
import aiohttp

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, BOT_USERNAME, ADMIN_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())


class QuizStates(StatesGroup):
    Q1 = State()
    Q2 = State()
    Q3 = State()
    Q4 = State()
    Q5 = State()
    FEEDBACK = State()

#-----------------алгоритм выбора животного-----------------#
quiz = [
    {
        "question": "1️⃣ Где вы предпочитаете жить?",
        "answers": [
            ("В горах",         {"porcupine": 2}),
            ("В джунглях",      {"tiger": 2, "monkey": 1}),
            ("На берегу моря",  {"pinguin": 2}),
            ("В тихом лесу",    {"sloth": 2}),
        ]
    },
    {
        "question": "2️⃣ Какая у вас любимая еда?",
        "answers": [
            ("Фрукты и орехи",    {"monkey": 2, "sloth": 1}),
            ("Мясо",              {"tiger": 2}),
            ("Рыба и морепродукты", {"pinguin": 2}),
            ("Корнеплоды",        {"porcupine": 2}),
        ]
    },
    {
        "question": "3️⃣ Как вы любите проводить выходные?",
        "answers": [
            ("В активных походах", {"tiger": 1, "monkey": 1}),
            ("Лениво читая книгу", {"sloth": 2}),
            ("Фотографируя природу", {"pinguin": 1, "porcupine": 1}),
            ("В компании друзей",  {"monkey": 2}),
        ]
    },
    {
        "question": "4️⃣ Вы — жаворонок или сова?",
        "answers": [
            ("Жаворонок",           {"tiger": 1, "porcupine": 1}),
            ("Сова",                {"sloth": 2}),
            ("Прокрастинатор(-ка)", {"monkey": 1, "pinguin": 1}),
            ("Засыпаю где попало",  {"porcupine": 1, "sloth": 1}),
        ]
    },
    {
        "question": "5️⃣ Что для вас важнее всего?",
        "answers": [
            ("Свобода",      {"monkey": 2, "sloth": 1}),
            ("Безопасность", {"porcupine": 2}),
            ("Скорость",     {"tiger": 2}),
            ("Сплочённость", {"pinguin": 2}),
        ]
    },
]

#-----------------словарь для результ-----------------#
result_media = {
    "porcupine": {
        "photo":   "https://i.ibb.co/kgj1LVtn/image.webp",
        "caption": "<b>Ваше тотемное животное — Дикобраз!</b>\n\nУютный, но бодрый колючий друг."
    },
    "tiger": {
        "photo":   "https://i.ibb.co/wTxm6Wf/image.jpg",
        "caption": "<b>Ваше тотемное животное — Тигр!</b>\n\nСильный, отважный и независимый."
    },
    "monkey": {
        "photo":   "https://i.ibb.co/MkSCMtYc/image.jpg",
        "caption": "<b>Ваше тотемное животное — Обезьяна!</b>\n\nОзорной, любознательный и общительный."
    },
    "pinguin": {
        "photo":   "https://i.ibb.co/QBq19WL/image.jpg",
        "caption": "<b>Ваше тотемное животное — Пингвин!</b>\n\nСтильный, дружелюбный и преданный."
    },
    "sloth": {
        "photo":   "https://i.ibb.co/0pqnVPfh/image.jpg",
        "caption": "<b>Ваше тотемное животное — Ленивец!</b>\n\nСпокойный, размеренный и безмятежный."
    },
}

#-----------------фолбек на url-----------------#
async def send_photo_from_url(chat_id: int, url: str, caption: str, reply_markup):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.read()
        file = BufferedInputFile(data, filename="photo.jpg")
        return await bot.send_photo(chat_id, file, caption=caption, reply_markup=reply_markup)
    except Exception as e:
        logging.warning(f"Не удалось скачать {url}: {e}, отправляю URL")
        return await bot.send_photo(chat_id, url, caption=caption, reply_markup=reply_markup)

#-----------------вопросы с кнопками инлайн-----------------#
async def send_question(state: FSMContext, chat_id: int, data: dict, q_idx: int, state_to: State):
    kb = InlineKeyboardBuilder()
    for a_idx, (text, _) in enumerate(data["answers"]):
        kb.button(text=text, callback_data=f"{q_idx}:{a_idx}")
    kb.adjust(2)
    await bot.send_message(chat_id, data["question"], reply_markup=kb.as_markup())
    await state.set_state(state_to)

#-----------------deep link для поделиться-----------------#
@dp.message(CommandStart(deep_link=True))
async def cmd_start_payload(message: types.Message, state: FSMContext, command: CommandObject):
    print("pizda")
    payload = command.args
    if "_" in payload:
        uid_str, animal = payload.split("_", 1)
        if uid_str.isdigit() and animal in result_media:
            orig_id = int(uid_str)
            chat = await bot.get_chat(orig_id)
            if chat.username:
                name = f"@{chat.username}"
            else:
                name = f'<a href="tg://user?id={orig_id}">{chat.full_name}</a>'
            media = result_media[animal]
            caption = (
                f"Пользователь {name} считает своим тотемным животным — "
                f"<b>{media['caption'].split(' — ')[1].split('!</b>')[0]}</b>!"
            )
            kb = InlineKeyboardBuilder()
            kb.button(text="Пройти викторину", callback_data="restart")
            kb.adjust(1)
            await send_photo_from_url(message.chat.id, media["photo"], caption, kb.as_markup())
            return
    await cmd_start(message, state)

#-----------------обработчик старта-----------------#
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(scores={})
    await message.answer(
        "👋 Привет! Давай узнаем твоё тотемное животное.\n"
        "Я задам 5 вопросов — отвечай на них.",
        reply_markup=ReplyKeyboardRemove()
    )
    await send_question(state, message.chat.id, quiz[0], 0, QuizStates.Q1)

#-----------------обработчик ответов-----------------#
@dp.callback_query(F.data.regexp(r'^\d+:\d+$'))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    q_idx, a_idx = map(int, callback.data.split(":"))
    data = await state.get_data()
    scores = data.get("scores", {})
    for animal, pts in quiz[q_idx]["answers"][a_idx][1].items():
        scores[animal] = scores.get(animal, 0) + pts
    await state.update_data(scores=scores)
    await callback.answer()
    if q_idx + 1 < len(quiz):
        nxt = list(QuizStates)[q_idx + 1]
        await send_question(state, callback.message.chat.id, quiz[q_idx + 1], q_idx + 1, nxt)
    else:
        best = max(scores.items(), key=lambda x: x[1])[0]
        media = result_media[best]
        share_cd = f"share:{callback.from_user.id}:{best}"
        kb = InlineKeyboardBuilder()
        kb.button(text="Узнать больше об опеке", callback_data="learn_more")
        kb.button(text="Поделиться результатом", callback_data=share_cd)
        kb.button(text="Связаться с зоопарком", callback_data="contact")
        kb.button(text="Попробовать ещё раз?", callback_data="restart")
        kb.adjust(2)
        await send_photo_from_url(
            callback.message.chat.id,
            media["photo"],
            f"{media['caption']}",
            kb.as_markup()
        )
        fb = InlineKeyboardBuilder()
        fb.button(text="Оставить отзыв", callback_data="feedback")
        await bot.send_message(callback.message.chat.id,
            "Если хочешь оставить отзыв — нажми ниже:",
            reply_markup=fb.as_markup()
        )
        await state.clear()

#-----------------поделиться результатом-----------------#
@dp.callback_query(F.data.startswith("share:"))
async def share_result(callback: types.CallbackQuery):
    _, uid_str, animal = callback.data.split(":", 2)
    if uid_str.isdigit() and animal in result_media:
        url = f"https://t.me/{BOT_USERNAME}?start={uid_str}_{animal}"
        await callback.answer()
        await bot.send_message(callback.message.chat.id,
            f"🔗 Скопируй ссылку и поделись:\n{url}"
        )

#-----------------узнать больше об опеке-----------------#
@dp.callback_query(F.data == "learn_more")
async def learn_more(callback: types.CallbackQuery):
    await callback.answer()
    await bot.send_message(callback.message.chat.id,
        "<b>Программа опеки Московского зоопарка</b>\n\n"
        "Став опекуном, вы получаете:\n"
        "• Фотокарточки\n"
        "• Новости о жизни\n"
        "• Скидки на билеты\n\n"
        "Пиши: <i>zoofriends@moscowzoo.ru</i>\n"
        "Звони: <i>+7 (962) 971-38-75</i>"
    )

#-----------------контакт зоопарка-----------------#
@dp.callback_query(F.data == "contact")
async def contact(callback: types.CallbackQuery):
    await callback.answer()
    await bot.send_contact(callback.message.chat.id,
        phone_number="+7 499 252-29-51",
        first_name="Московский Зоопарк"
    )
    await bot.send_message(callback.message.chat.id,
        text="Почта зоопарка: zoopark@culture.mos.ru")

#-----------------рестарт викторины-----------------#
@dp.callback_query(F.data == "restart")
async def restart(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Начинаем заново!")
    await state.clear()
    await state.update_data(scores={})
    await send_question(state, callback.message.chat.id, quiz[0], 0, QuizStates.Q1)

#-----------------отызвы-----------------#
@dp.callback_query(F.data == "feedback")
async def ask_feedback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await bot.send_message(callback.message.chat.id, "Напишите ваш отзыв:")
    await state.set_state(QuizStates.FEEDBACK)

@dp.message(QuizStates.FEEDBACK)
async def receive_feedback(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID,
        f"📢 Отзыв от @{message.from_user.username or message.from_user.id}:\n\n{message.text}"
    )
    await message.answer("Спасибо! ❤️")
    await state.clear()


@dp.message()
async def fallback(message: types.Message):
    await message.reply("Нажми /start, чтобы начать викторину.")


if __name__ == "__main__":
    dp.run_polling(bot)
