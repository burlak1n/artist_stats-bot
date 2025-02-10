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


async def get_brief_info(artist_id: str|int = 10886466):
    url = f'{base_url}/artists/{artist_id}/brief-info'
    result = await client._request.get(url)
    result = result["stats"]    
    # info = await client.artists_brief_info(artist_id)
    logger.info(result)
    return result

async def main():
    
    await client.init()
    await get_brief_info()

if __name__ == "__main__":
    asyncio.run(main())