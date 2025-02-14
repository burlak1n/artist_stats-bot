import json
import os
import sys
from loguru import logger
from vkbottle import API
import asyncio
from dotenv import load_dotenv
import requests
from modules.utils import get_artist_link, find_closest_match
from modules.test import get_artist_group
# from modules.utils import find_city_coordinates

logger.remove()
logger.add(sys.stderr, level="INFO")

load_dotenv()
ACCESS_TOKEN = os.environ.get("vk_user_token")
api = API(ACCESS_TOKEN)
criteria_sample = {
    "sex": 0,
    "age_from": 0,
    "age_to": 0,
}
data_sample = {
    "access_token": ACCESS_TOKEN,
    "v": "5.199",
}

headers = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded',
    'dnt': '1',
    'origin': 'https://dev.vk.com',
    'priority': 'u=1, i',
    'referer': 'https://dev.vk.com/',
    'sec-ch-ua': '"Chromium";v="133", "Not(A:Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
}

async def search_groups(artist: str):
    # group_link = await get_artist_link(artist, vk=True)
    # if not group_link:
        # Выбирается первая группа по релевантности

        # groups = await api.groups.search(q=artist, sort=0, count=1)
    
    r = await get_artist_group(artist)
    r = r["response"]["items"]
    logger.info(r)
    if r:
        return {
            "group_id": r[0]["id"],
            "group_link": f"https://vk.com/{r[0]["screen_name"]}"
        }
        # logger.info(f'{groups}, {artist}')
        # logger.info([group["name"] for group in groups.to_dict()["items"]])
        # d = groups.to_dict()["items"]
        # names_low = [group["name"].lower() for group in d]
        # if artist.lower() == names_low[0]:
        #     group = d[0]
        #     logger.info(group)
        # else:
        #     group = await find_closest_match(artist, [group["name"] for group in d])
        #     group = d[group]
        group = groups.items[0]
        return {
            "group_id": group.id,
            "group_link": "https://vk.com/" + group.screen_name
        }
    # screen_name = group_link.split("/")[-1]
    # group_id = await api.utils.resolve_screen_name(screen_name)
    # #TODO: Улучшить поиск
    # logger.info(group_link, group_id)
    # return {
    #     "group_id": group_id,
    #     "group_link": group_link
    # }

async def get_musicians(artist_name: str):
    artists = await api.ads.get_musicians(artist_name)
    for artist in artists.items:
        if artist.avatar: # Если у исполнителя есть аватарка, то кайф
            return artist
    a = artists.items
    if a:
        logger.info(f"Исполнитель без аватарки: {a[0]}")
        return a[0]
    logger.info(f"Не найден исполнитель {artist_name}")

# ts - targeting_stats
async def get_ts_by_group_followers_city(city_coordinate: str, group):
    criteria = {
        **criteria_sample, # надеюсь, это работает правильно
        "groups": group['group_id'],
    }

    if city_coordinate:
        criteria["cities"] = city_coordinate

    data = {
        **data_sample,
        "link_url": group['group_link'],
        "criteria": json.dumps(criteria),
    }
    a = requests.post("https://api.vk.com/method/ads.getTargetingStats", data=data).json()
    try:
        a = a["response"]["audience_count"]
        return a
    except Exception as e:
        logger.exception(e)
        return None

async def get_ts_by_active_group_followers_city(city_coordinate: str, group):
    criteria = {
        **criteria_sample,
        "groups_active_formula": group['group_id'],
        # Для 40км
        # "geo_near": city_coordinate,
        # "geo_point_type": "regular"
    }
    if city_coordinate:
        criteria["cities"] = city_coordinate

    data = {
        **data_sample,
        "link_url": group['group_link'],
        "criteria": json.dumps(criteria),
    }
    a = requests.post("https://api.vk.com/method/ads.getTargetingStats", data=data).json()
    try:
        a = a["response"]["audience_count"]
        return a
    except Exception as e:
        logger.exception(e)
        return None

async def get_ts_by_musician_listener_city(city_coordinate, musician_id: str, group_link):
    criteria = {
        **criteria_sample,
        "music_artists_formula": musician_id,
    }
    # Случай РФ, Россия
    if city_coordinate:
        criteria["cities"] = city_coordinate

    data = {
        **data_sample,
        "link_url": group_link,
        "criteria": json.dumps(criteria),
    }

    a = requests.post("https://api.vk.com/method/ads.getTargetingStats", data=data).json()
    try:
        a = a["response"]["audience_count"]
        return a
    except Exception as e:
        logger.exception(e)
        return None

async def get_targeting_stats(city: str | int, artist: str):
    # city_coord = await find_city_coordinates(city_name=city)
    city_coord = city
    if city not in ["Россия", "РФ", 1]:
        city_coord = await api.database.get_cities(q=city, count=1)
        if not city_coord.items:
             city_coord = 1
        else:
            city_coord = city_coord.items[0].id
    # group = {"group_link": "", "group_id": ""}
    # musician = ""

    if not artist or artist == "None":
        logger.info("Нет артиста")
        return None
    group = await search_groups(artist)
    musician = await get_musicians(artist)
    if musician:
        response = {
            "group": group,
            "city": city_coord,
            "musician_name": musician.name,
            "active_group_followers": await get_ts_by_active_group_followers_city(city_coord, group),
            "group_followers": await get_ts_by_group_followers_city(city_coord, group),
            "listeners": await get_ts_by_musician_listener_city(city_coord, musician.id, group["group_link"]),
        }
    # logger.info(city_coord, artist, response)
        return response
    return group
async def main():
    await get_targeting_stats("Москва", "Baby Cute")

if __name__ == "__main__":
    asyncio.run(main())