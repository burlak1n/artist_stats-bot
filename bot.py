from enum import Enum
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.filters import Command

from dotenv import load_dotenv

from modules.logger import logger
from modules import yamusic
from modules.vk_ads import get_targeting_stats
from modules.google_tables import test_get_data, fill_table_artist

load_dotenv()
bot_token = os.environ.get("bot_token")
PASSWORD = os.environ.get("PASSWORD")

loyalty_percent_static = 6.2
attendance_percent_static = 1.8

bot = Bot(bot_token)
dp = Dispatcher()

ALLOWED_USERS = set()

class CallEnum(Enum):
    TOUR = "тур"
    TABLE = "таблица"

kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Таблица артистов", callback_data=CallEnum.TABLE.value),
            InlineKeyboardButton(text="Стата артисты", callback_data=CallEnum.TOUR.value)
        ]
    ]
)

async def get_vk_data_about_musician(musician: str, city: str):
    vk_data = await get_targeting_stats(city, musician)

    logger.info(vk_data)

    group_followers = vk_data["group_followers"]
    listeners = vk_data["listeners"]
    if not group_followers or not listeners:
        return "Не вышло определить число подписчиков или слушателей"
    if listeners != 0:
        loyalty_percent = (group_followers/listeners)*100
    else:
        loyalty_percent = 0

    max_attendance = attendance_percent_static*(loyalty_percent/loyalty_percent_static)
    avg_attendance = (max_attendance+1)/2

    return f"""
{vk_data["musician_name"]}, г.{city}
<a href="{vk_data["group"]["group_link"]}">VK</a> Подписчики:
    кол-во: {group_followers}
    активные: {vk_data["active_group_followers"]}
    слушатели: {listeners}

Проценты:
    преданности: {loyalty_percent:.2f}%
    прихода максимум: {max_attendance:.2f}%
    прихода средний: {avg_attendance:.2f}%

Прогнозы:
    1%: {int(listeners/100)}
    средний: {int(listeners*avg_attendance/100)}
    максимум: {int(listeners*max_attendance/100)}
"""

async def get_yand_data_about_musician(musician: str):
    yandex_data = await yamusic.get_stats(musician)
    artist_id = yandex_data.ya_music_id
    yandex_data = await yamusic.beautify_yandex_stats(yandex_data)

    return f"""
<a href="{yandex_data.link}">Я.Музыка</a>
❤️: {yandex_data.likes} 
🎶: {yandex_data.last_month_listeners} (мес)
+-: {yandex_data.last_month_delta}
    """, artist_id

async def get_data_about_musician(musician: str, city: str) -> str:
    vk = await get_vk_data_about_musician(musician, city)
    yand, artist_id = await get_yand_data_about_musician(musician)
    return f"{vk}{yand}", artist_id

@dp.message(Command("reset"), F.from_user.id.in_(ALLOWED_USERS))
async def table_handler(message: Message):
    logger.debug(f"Введена команда /reset пользователем {message.from_user.id}")
    await message.answer("Бот перезагружен")
    python = sys.executable  # Получаем путь к текущему интерпретатору Python
    os.execl(python, python, *sys.argv)

@dp.message(F.text, F.from_user.id.in_(ALLOWED_USERS))
async def artist_data_handler(message: Message):
    a = message.text.split(",")
    if len(a) != 2:
        await message.answer("Повторите ввод")
        return
    artist = a[0].strip()
    city = a[1].strip()
    await message.answer("Запрос принят. Минуточку!")
    try:
        txt, artist_id = await get_data_about_musician(artist, city)
        await message.answer(txt, disable_web_page_preview=True, parse_mode="html")
        # a = await asyncio.to_thread(get_screenshots, artist_id)
        # await message.answer_photo(photo=a[0])
        # await message.answer_photo(photo=a[1])
    except Exception as e:
        logger.exception(e)
        await message.answer("Произошла ошибка на стороне сервера")

@dp.message(F.text, F.from_user.id.not_in(ALLOWED_USERS))
async def password_handler(message: Message):
    if message.text == PASSWORD:
        ALLOWED_USERS.add(message.from_user.id)
        await message.answer("Введите сообщение в формате 'артист, город', либо воспользуйтесь кнопками", reply_markup=kb)

@dp.callback_query(F.data == CallEnum.TABLE.value, F.from_user.id.in_(ALLOWED_USERS))
async def table_handler(call: CallbackQuery):
    await call.answer()
    await call.message.answer("Бот начал обработку таблицы артистов")
    await fill_table_artist()
    await call.message.answer("Бот закончил обработку таблицы артистов")

@dp.callback_query(F.data == CallEnum.TOUR.value, F.from_user.id.in_(ALLOWED_USERS))
async def tour_handler(call: CallbackQuery):
    await call.answer()
    await call.message.answer("Бот начал обработку городов в таблице")
    await test_get_data()
    await call.message.answer("Бот закончил обработку городов в таблице")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot, skip_updates=True))
