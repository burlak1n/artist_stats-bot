import json
import os

import aiohttp
from dotenv import load_dotenv
from difflib import SequenceMatcher
'''
from io import BytesIO
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from aiogram.types import BufferedInputFile
'''

from loguru import logger
load_dotenv()
sec = os.environ.get("google_secret")
cx = os.environ.get("google_search_engine_id")
# top_50_cities = None

def json_beauty(data:dict) -> str:
    return (json.dumps(data, indent=2))

async def google_search(artist_name: str, vk: bool = False):
    """
    Асинхронно выполняет поиск в Google с использованием Custom Search API.
    """
    url = f"https://www.googleapis.com/customsearch/v1?key={sec}&cx={cx}"
    if vk:
        params = {"q": artist_name + "группа вконтакте",
              "start": 1}
    else:
        params = {"q": "яндекс музыка " + artist_name,
              "start": 1}

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
        logger.error(f"Error during Google search for {artist_name}: {e}")
        return {}  # Возвращаем пустой словарь в случае ошибки
    except Exception as e:
        logger.exception(f"An unexpected error occurred during Google search: {e}")
        return {}  # Возвращаем пустой словарь в случае ошибки

async def get_artist_link(artist_name: str, vk: bool = False) -> str:
    """
    Асинхронно получает ссылку на артиста, выполняя поиск в OpenAI.
    """
    result = await google_search(artist_name=artist_name, vk=vk)
    if result and "link" in result:
        link = result["link"]
        logger.info(f"Found link: {link}")
        return link
    else:
        logger.warning(f"Could not find artist link for {artist_name}")
        return ""  # Возвращаем пустую строку, если ссылка не найдена
def normalize_string(s):
    s = s.lower()
    s = "".join(c for c in s if c.isalnum() or c.isspace())
    return s

async def find_closest_match(query, candidates):
    query = normalize_string(query)
    closest_match = None
    max_similarity = 0
    i = 0
    for candidate in candidates:
        candidate_norm = normalize_string(candidate)
        similarity = SequenceMatcher(None, query, candidate_norm).ratio()
        if similarity > max_similarity:
            max_similarity = similarity
            id = i
            # closest_match = candidate
        i+=1

    return id
'''
def get_screenshots(artist_id):
    screen = []
    options = webdriver.ChromeOptions()
    # options.add_argument("--window-size=1024x768")  # Установите нужное разрешение

    driver = webdriver.Chrome(options=options)
    # Load the webpage
    driver.get(f"https://music.yandex.ru/artist/{artist_id}/info")  # Replace with the actual URL

    try:
        # Явное ожидание: ждем, пока элемент станет кликабельным (до 10 секунд)
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.d-icon.deco-icon.d-icon_cross-big.local-icon-theme-black"))
        )

        # Клик на элемент
        element.click()
        print("Элемент успешно нажат!")

    except Exception as e:
        print(f"Ошибка при нажатии на элемент: {e}")

    try:
        # Находим все элементы div с классом artist-trends__toggle
        elements = driver.find_elements(By.CLASS_NAME, "artist-trends__toggle")
        for element in elements:
            driver.execute_script("arguments[0].scrollIntoView();", element)
            try:
                # Ожидание кликабельности элемента (опционально, но рекомендуется)
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(element)
                )

                element.click()
                time.sleep(0.5)
                screen.append(driver.get_screenshot_as_png())
                # print(f"Скриншот сохранен как: {f"screenshot_{i+1}.png"}")
                element.click()
                time.sleep(0.5)

            except Exception as e:
                print("Ошибка при нажатии на элемент: ", e)
                return

    except Exception as e:
        print("Ошибка при поиске элементов: ", e)
        return
        

    driver.quit()

    image_listeners = Image.open(BytesIO(screen[0]))
    cropped_listeners = image_listeners.crop((59, 55, 775+59, 567+50))

    image_likes = Image.open(BytesIO(screen[1]))
    cropped_likes = image_likes.crop((59, 55, 775+59, 567+100))

    print("Успех")
    return [pil_image_to_buffered_input_file(cropped_listeners, "listeners.png"), pil_image_to_buffered_input_file(cropped_likes, "likes.png")]

def pil_image_to_buffered_input_file(pil_image: Image.Image, filename: str = "image.png") -> BufferedInputFile:
    """
    Преобразует PIL Image в BufferedInputFile для aiogram.

    Args:
        pil_image: Изображение PIL.
        filename: Имя файла для BufferedInputFile.

    Returns:
        BufferedInputFile: BufferedInputFile, содержащий изображение.
    """
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")  # Или другой нужный формат
    buffered.seek(0)  # Важно вернуть указатель в начало буфера

    return BufferedInputFile(
        buffered.getvalue(),
        filename=filename
    )
'''

# Поиск координат (Для 40км)
# async def find_city_coordinates(city_name: str, radius: str = "50000") -> str:
#     """
#     return coordinates = '55.75586,37.61769,50000,-1,Москва'
#     if none = ''
#     """
#     city_string = await search_string_in_csv(city_name)

#     if not city_string:
#         return ""

#     sep_string = city_string.split(",")
#     city_latitude = sep_string[-4]
#     city_longitude = sep_string[-3]
#     return_string = f"{city_latitude},{city_longitude},{radius},{city_name}"
#     logger.debug(return_string)
    
#     return return_string

# async def search_string_in_csv(data: str) -> str:
#     hard_directory = os.path.join("data", "city.csv")
#     directory = hard_directory if os.path.isfile(hard_directory) else "city.csv"

#     if not os.path.isfile(directory):
#         logger.error(f"File not found: {directory}")
#         return

#     try:
#         with open(directory, "r", encoding="utf-8") as csv_file:
#             for line in csv_file:
#                 if data in line:
#                     return line
#     except Exception as e:
#         logger.error(f"Error reading file: {e}")
#     return

# async def get_top_50_cities(path: str = "./modules/city.csv"):
#     global top_50_cities
#     if not top_50_cities:
#         df = pd.read_csv(path)
#         df['population'] = pd.to_numeric(df['population'], errors='coerce')
#         df = df.dropna(subset=['population'])
#         df_sorted = df.sort_values(by='population', ascending=False) # сортировка по убыванию
#         top_50_cities_df = df_sorted.head(50)
#         top_50_cities = top_50_cities_df['address'].to_numpy()
#         top_50_cities = np.array([
#             (s.split(',')[1].strip() if len(s.split(',')) > 1 else s.split(',')[0].strip()).replace('г ', '').replace('Респ ', '').replace('обл', '')
#             for s in top_50_cities
#         ])
#         logger.info(top_50_cities)
    
#     return top_50_cities

# if __name__ == "__main__":
#     asyncio.run(get_top_50_cities())