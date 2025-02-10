import json
import os
from loguru import logger
from vkbottle import API
import asyncio
from dotenv import load_dotenv
import requests

# from modules.utils import find_city_coordinates

# logger.remove()
# logger.add(sys.stderr, level="INFO")

load_dotenv()
ACCESS_TOKEN = os.environ.get("vk_user_token")
api = API(ACCESS_TOKEN)

# ACCOUNT_ID: int = int(os.environ.get("cabinet_account_id"))
# CLIENT_ID = os.environ.get("client_id")

async def search_groups(artist: str):
    groups = await api.groups.search(q=artist, sort=0, count=1)
    # Выбирается первая группа по релевантности
    group = groups.items[0]
    # logger.info(group)
    if group:
        # exit()
        return {
            "group_id": group.id,
            "group_link": "https://vk.com/" + group.screen_name
        }
    logger.error(f"Группа не найдена")

async def get_musicians(artist_name: str):
    artists = await api.ads.get_musicians(artist_name)
    for artist in artists.items:
        if artist.avatar: # Если у исполнителя есть аватарка, то кайф
            return artist
    logger.info(f"Исполнитель без аватарки: {artist}")
    return artist[0]

# ts - targeting_stats
async def get_ts_by_group_followers_city(city_coordinate: str, group):
    criteria = {
        "sex": 0,
        "age_from": 0,
        "age_to": 0,
        "groups": group['group_id'],
    }

    if city_coordinate:
        criteria["cities"] = city_coordinate

    data = {
        "access_token": ACCESS_TOKEN,
        "link_url": group['group_link'],
        "criteria": json.dumps(criteria),
        "v": "5.199",
    }
    a = requests.post("https://api.vk.com/method/ads.getTargetingStats", data=data)
    try:
        a = a.json()["response"]["audience_count"]
    except Exception as e:
        logger.exception(e)
        a = a.json()
    logger.info(a)
    return a

async def get_ts_by_active_group_followers_city(city_coordinate: str, group):
    criteria = {
        "sex": 0,
        "age_from": 0,
        "age_to": 0,
        "groups_active_formula": group['group_id'],
        # "geo_near": city_coordinate,
        # "geo_point_type": "regular"
    }
    if city_coordinate:
        criteria["cities"] = city_coordinate

    data = {
        "access_token": ACCESS_TOKEN,
        "link_url": group['group_link'],
        "criteria": json.dumps(criteria),
        "v": "5.199",
    }
    a = requests.post("https://api.vk.com/method/ads.getTargetingStats", data=data)
    try:
        a = a.json()["response"]["audience_count"]
    except Exception as e:
        logger.exception(e)
        a = a.json()
    logger.info(a)
    return a

async def get_ts_by_musician_listener_city(city_coordinate, musician_id: str, group_link):
    criteria = {
        "sex": 0,
        "age_from": 0,
        "age_to": 0,
        "music_artists_formula": musician_id,
    }

    if city_coordinate:
        criteria["cities"] = city_coordinate

    data = {
        "access_token": ACCESS_TOKEN,
        "link_url": group_link,
        "criteria": json.dumps(criteria),
        "v": "5.199",
    }

    a = requests.post("https://api.vk.com/method/ads.getTargetingStats", data=data)
    try:
        a = a.json()["response"]["audience_count"]
    except Exception as e:
        logger.exception(e)
        a = a.json()

    logger.info(a)
    return a

async def get_targeting_stats(city: str, artist: str):
    # city_coord = await find_city_coordinates(city_name=city)
    city_coord = None
    if city not in ["Россия", "РФ"]:
        city_coord = await api.database.get_cities(q=city, count=1)
        city_coord = city_coord.items[0].id
    group = await search_groups(artist)
    musician = await get_musicians(artist)
    # musician_id = musician.id
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

async def main():
    await get_targeting_stats("Москва", "Baby Cute")

if __name__ == "__main__":
    asyncio.run(main())