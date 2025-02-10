import os 

from dotenv import load_dotenv

from loguru import logger
import aiohttp

load_dotenv()
sec = os.environ.get("google_secret")
cx = os.environ.get("google_search_engine_id")

async def google_search(artist_name: str):
    """
    Асинхронно выполняет поиск в OpenAI с использованием Custom Search API.
    """
    url = f"https://www.googleapis.com/customsearch/v1?key={sec}&cx={cx}"
    params = {"q": "яндекс музыка " + artist_name,
              "start": "1"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as r:
                r.raise_for_status()
                data = await r.json()
                if "items" in data and data["items"]:
                    return data["items"][0]
                else:
                    logger.warning(f"No search results found for {artist_name}")
                    return {}  # Возвращаем пустой словарь, если нет результатов
    except aiohttp.ClientError as e:
        logger.error(f"Error during OpenAI search for {artist_name}: {e}")
        return {}  # Возвращаем пустой словарь в случае ошибки
    except Exception as e:
        logger.exception(f"An unexpected error occurred during OpenAI search: {e}")
        return {}  # Возвращаем пустой словарь в случае ошибки

async def get_artist_link(artist_name: str) -> str:
    """
    Асинхронно получает ссылку на артиста, выполняя поиск в OpenAI.
    """
    result = await google_search(artist_name=artist_name)
    if result and "link" in result:
        link = result["link"]
        logger.info(f"Found link: {link}")
        return link
    else:
        logger.warning(f"Could not find artist link for {artist_name}")
        return ""  # Возвращаем пустую строку, если ссылка не найдена

async def get_like(artist_id: str = "5880813"):
    """
    Асинхронно получает информацию о лайках артиста.
    Использует aiohttp для асинхронных HTTP-запросов.
    """
    url = f"https://music.yandex.ru/handlers/artist.jsx?artist={artist_id}&what=&sort=&dir=&period=month&trackPage=0&trackPageSize=1&lang=ru&external-domain=music.yandex.ru&overembed=false&ncrnd=0.4035522368585789"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                r.raise_for_status()  # Поднимает исключение для кодов ошибок 4xx/5xx
                data = await r.json()

        month_stats = data["stats"]
        return {"lastMonthListeners": month_stats["lastMonthListeners"],
                "lastMonthListenersDelta": month_stats["lastMonthListenersDelta"],
                "likesCount": data["likesCount"]}
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching data from {url}: {e}")
        # Обработайте ошибку соответствующим образом.  Например, верните словарь по умолчанию.
        return {"lastMonthListeners": 0, "lastMonthListenersDelta": 0, "likesCount": 0}
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        # Обработайте другие исключения.
        return {"lastMonthListeners": 0, "lastMonthListenersDelta": 0, "likesCount": 0}


class YandexData:
    """
    musician_name: str = musician_name
    ya_music_id: str = ya_music_id
    last_month_listeners: str = last_month_listeners
    last_month_delta: str = last_month_delta
    link: str = link
    likes: str = likes
    """
    def __init__(
            self, musician_name: str, ya_music_id: str, 
            last_month_listeners: str, last_month_delta: str, link: str, likes: str
            ) -> None:

        self.musician_name: str = musician_name
        self.ya_music_id: str = ya_music_id
        self.last_month_listeners: str = last_month_listeners
        self.last_month_delta: str = last_month_delta
        self.link: str = link
        self.likes: str = likes


async def get_stats(musician_name: str) -> 'YandexData':  # Укажите фактический класс YandexData
    """
    Асинхронно получает статистику по музыканту.
    """
    try:
        link = await get_artist_link(artist_name=musician_name)  # await здесь
        link = link.removesuffix("/info")
        artist_id = link.split("/")[-1]
        stats = await get_like(artist_id=artist_id)  # await здесь
        likes = str(stats["likesCount"])

        try:
            last_month_listeners = str(stats["lastMonthListeners"])
            last_month_delta = str(stats["lastMonthListenersDelta"])

            data = YandexData(musician_name, artist_id, last_month_listeners,
                              last_month_delta, link, likes)
        except Exception as e:
            logger.exception(f"{e}")
            data = YandexData(musician_name, artist_id, "",
                              "", link, likes)  # Fallback case внутри try

    except Exception as e:  # Обработка ошибок на более высоком уровне.
        logger.exception(f"Error getting stats for {musician_name}: {e}")
        # Возвращаем дефолтное значение или возбуждаем исключение, в зависимости от требований.
        data = YandexData(musician_name, "", "", "", "", "")  # Или raise

    return data


async def beautify_yandex_stats(stats: YandexData) -> YandexData:
    if stats.likes.isdigit():
        stats.likes = '{:,}'.format(int(stats.likes))
    if stats.last_month_listeners.isdigit():
        stats.last_month_listeners = '{:,}'.format(int(stats.last_month_listeners))
    try:
        if stats.last_month_delta.isdigit():
            stats.last_month_delta = '{:,}'.format(int(stats.last_month_delta))
    except:
        pass

    return stats


if __name__ == "__main__":
    art_name = input("Введите артиста: ")
    link = get_artist_link(artist_name=art_name)
    artist_id = link.split("/")[-1]
    print(get_like(artist_id=artist_id))

