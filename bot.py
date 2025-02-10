import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

# from aiogram.filters import CommandStart, StateFilter
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup

from dotenv import load_dotenv

from modules.logger import logger
from modules import yamusic
from modules.vk_ads import get_targeting_stats
# from modules.utils import get_top_50_cities, get_screenshots
from modules.google_tables import test_get_data, update_table

load_dotenv()
bot_token = os.environ.get("bot_token")
PASSWORD = os.environ.get("PASSWORD")

bot = Bot(bot_token)
dp = Dispatcher()

ALLOWED_USERS = set()
# class Form(StatesGroup):
#     city = State()
#     artist = State()

# logger.debug(f"start https://t.me/{bot.get_me().username}")

async def get_vk_data_about_musician(musician: str, city: str):
    vk_data = await get_targeting_stats(city, musician)

    logger.info(vk_data)

    group_followers = vk_data["group_followers"]
    listeners = vk_data["listeners"]

    if listeners != 0:
        loyalty_percent = (group_followers/listeners)*100
    else:
        loyalty_percent = 0
    loyalty_percent_static = 6.2
    attendance_percent_static = 1.8

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


# @dp.message(CommandStart, StateFilter(None))
# async def start_message_handler(message: Message, state: FSMContext):
#     await state.set_state(Form.city)
#     await message.answer("Введите город")

# @dp.message(F.text, Form.city)
# async def city_handler(message: Message, state: FSMContext):
#     city = message.text
#     city_coord = await city_finder.find_city_coordinates(city)
#     if city_coord:
#         await state.update_data(city=city)
#         await message.answer("Введите артиста")
#         await state.set_state(Form.artist)
#     else:
#         await message.answer("Город не найден!\nВведите город ещё раз")

# @dp.message(F.text, Form.artist)
# async def artist_handler(message: Message, state: FSMContext):
#     artist = message.text
#     data = await state.get_data()
#     city = data["city"]
#     await message.answer(f"Выполняется поиск по:\nг. {city}\n{artist}\nожидайте")
#     try:
#         txt = await get_data_about_musician(artist, city)
#         await message.answer(txt, disable_web_page_preview=True)
#         await state.clear()
#     except Exception as e:
#         logger.exception(e)
#         await message.answer("Возникла ошибка, попробуйте ещё раз позднее")

@dp.message(F.text, F.from_user.id.in_(ALLOWED_USERS))
async def artist_data_handler(message: Message):
    a = message.text.split(",")
    if len(a) != 2:
        await message.answer("Повторите ввод")
        return
    artist = a[0].strip()
    second = a[1].strip()
    if second == "тур":
        await message.answer("Бот начал обработку городов в таблице")
        await test_get_data()
        await message.answer("Бот закончил обработку городов в таблице")

        # top_50_cities = await get_top_50_cities()
        # for city in top_50_cities[:3]:
        #     try:
        #         txt = await get_vk_data_about_musician(artist, city)
        #         await message.answer(txt, disable_web_page_preview=True, parse_mode="html")
        #     except Exception as e:
        #         logger.exception(e)
        #         await message.answer(f"Произошла ошибка на стороне сервера при обработке города {city}")
        #         continue
        #     await asyncio.sleep(1.5)  # Задержка в 1.5 секунды между итерациями. Чтобы ВК выжил
    if second == "таблица":
        await message.answer("Бот начал обработку таблицы")
        await update_table()
        await message.answer("Бот закончил обработку таблицы")
    else: #обработка города
        city = second
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
        await message.answer("Пароль принят. Введите сообщение в формате 'артист, город'")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot, skip_updates=True))
