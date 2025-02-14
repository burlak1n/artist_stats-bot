import asyncio
import os
from yandex_music import ClientAsync
from loguru import logger
from dotenv import load_dotenv

# без авторизации недоступен список треков альбома
load_dotenv()
TOKEN = os.environ.get("yandex_token")
client = ClientAsync(TOKEN)
base_url = 'https://api.music.yandex.net'


async def get_artist_info(artist_id: str|int = 10886466):
    url = f'{base_url}/artists/{artist_id}/brief-info'
    result = await client._request.get(url)
    result = result["stats"]
    artist = await client.artists(artist_id)
    artist = artist[0]
    logger.info(artist)
    client.artists_brief_info
    return {
        #TODO
        # "lastMonthListeners": month_stats["lastMonthListeners"],
        # "lastMonthListenersDelta": month_stats["lastMonthListenersDelta"],
        "likesCount": artist.likes_count
        }

async def main():
    # return {"lastMonthListeners": month_stats["lastMonthListeners"],
    #     "lastMonthListenersDelta": month_stats["lastMonthListenersDelta"],
    #     "likesCount": data["likesCount"]}
    # Получить эти данные
    await client.init()
    await get_artist_info()

if __name__ == "__main__":
    asyncio.run(main())