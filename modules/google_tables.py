import asyncio
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from gspread import service_account, Client, Spreadsheet, exceptions
from gspread.utils import rowcol_to_a1
from loguru import logger
import pandas as pd
import os
from modules.vk_ads import get_targeting_stats

load_dotenv()
TABLE_LINK = os.environ.get("table_link")
SHEET_NAME_STATS = os.environ.get("sheet_name_stats")
SHEET_NAME_CITIES = os.environ.get("sheet_name_cities")

def client_init_json() -> Client:
    """Создание клиента для работы с Google Sheets."""
    return service_account(filename='./data/loader_test.json')

def get_table_by_url(client: Client, table_url):
    """Получение таблицы из Google Sheets по ссылке."""
    return client.open_by_url(table_url)

def get_table_by_id(client: Client, table_url):
    """Получение таблицы из Google Sheets по ID таблицы."""
    return client.open_by_key(table_url)

def test_get_table(table_url: str, table_key: str):
    """Тестирование получения таблицы из Google Sheets."""
    client = client_init_json()
    table = get_table_by_url(client, table_url)
    print('Инфо по таблице по ссылке: ', table)
    table = get_table_by_id(client, table_key)
    print('Инфо по таблице по id: ', table)

def add_data_to_worksheet(table: Spreadsheet, title: str, data: List[Dict], start_row: int = 2) -> None:
    """
    Добавляет данные на рабочий лист в Google Sheets.

    :param table: Объект таблицы (Spreadsheet).
    :param title: Название рабочего листа.
    :param data: Список словарей с данными.
    :param start_row: Номер строки, с которой начнется добавление данных.
    """
    try:
        worksheet = table.worksheet(title)
    except exceptions.WorksheetNotFound as e:
        # worksheet = create_worksheet(table, title, rows=100, cols=20)
        logger.exception(e)
        return

    headers = data[0].keys()
    end_row = start_row + len(data) - 1
    end_col = chr(ord('A') + len(headers) - 1)

    cell_range = f'A{start_row}:{end_col}{end_row}'
    cell_list = worksheet.range(cell_range)

    flat_data = []
    for row in data:
        for header in headers:
            flat_data.append(row[header])

    for i, cell in enumerate(cell_list):
        cell.value = flat_data[i]

    worksheet.update_cells(cell_list)

def extract_data_from_sheet(table: Spreadsheet, sheet_name: str) -> List[Dict]:
    """
    Извлекает данные из указанного листа таблицы Google Sheets и возвращает список словарей.

    :param table: Объект таблицы Google Sheets (Spreadsheet).
    :param sheet_name: Название листа в таблице.
    :return: Список словарей, представляющих данные из таблицы.
    """
    worksheet = table.worksheet(sheet_name)
    # headers = worksheet.row_values()  # Первая строка считается заголовками

    data = []
    rows = worksheet.get_all_values()  # Начинаем считывать с второй строки

    return rows
    # for row in rows:
    #     row_dict = {headers[i]: value for i, value in enumerate(row)}
    #     data.append(row_dict)

    # return data

async def test_get_data(table_link = TABLE_LINK, sheet_name_cities= SHEET_NAME_CITIES):
    client = client_init_json()
    table = get_table_by_url(client, table_link)

    data = extract_data_from_sheet(table, 'Стата артисты')
    # print(data)
    df = pd.DataFrame(data)
    df = df.iloc[:, :4]
    result_df = df[(df.iloc[:, 2] == "") | (df.iloc[:, 3] == "")] # выбор строк, в которых 2 или 3 столбец = ""
    result_df = result_df[~(result_df == '').all(axis=1)]
    result = df.loc[df.iloc[:, 0] != '', df.columns[1]]

    arr = []
    for index_city, city_row in result_df.iterrows():
        for index_artist, artist_row in result.items():
            if index_city < index_artist:
                arr.append({"index": index_city+1, "city": city_row[1].strip(), "artist": last_artist})
                break
            last_artist = artist_row

    worksheet = table.worksheet('Стата артисты')
    logger.info(arr)
    await update_worksheet(worksheet, arr)
    # for i in arr:
    #     stats = await get_targeting_stats(i["city"], i["artist"])
        
    #     worksheet.update([stats["listeners"], stats["group_followers"]], f"C{i["index"]}")

    # print(result_df)
    # print(result)

    # worksheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
    # data = extract_data_from_sheet(table, 'Лист1')
    # "ссылка Вк группа"
    # "Лайки яндекс"
    # "Статистика прослушиваний вк в мск"

    # for i in data:
    #     for j in i:
    #         print(j, i[j])

async def update_worksheet(worksheet, arr):
    cells_to_update = []
    for i in arr:
        stats = await get_targeting_stats(i["city"], i["artist"])
        row_index = i["index"]
        cells_to_update.append({
            "range": f"C{row_index}",  # Ячейка для слушателей
            "values": [[stats["listeners"]]]  # Слушатели
        })
        cells_to_update.append({
            "range": f"D{row_index}",  # Ячейка для подписчиков
            "values": [[stats["group_followers"]]]  # Подписчики
        })
        await asyncio.sleep(2.4)
    logger.info(f"Cells {cells_to_update}")
    worksheet.batch_update(cells_to_update)

async def update_table(table_link = TABLE_LINK, sheet_name_stats = SHEET_NAME_STATS):
    # группа, datetime.now(), лайки_янд, слушатели_мск, подписчики_мск

    client = client_init_json()
    table = get_table_by_url(client, table_link)

    worksheet = table.worksheet(sheet_name_stats)
    # 2. Получение данных всех строк
    all_values = worksheet.get_all_values()

    # 3. Определение столбцов для проверки (нумерация начинается с 1)
    # cols_to_check = [4, 5, 6, 8, 9]  # D, E, F, H, I
    cols_to_check = [4, 5, 8, 9]  # D, E, F, H, I
    # 4. Определение строк для обновления (индекс начинается с 0)
    rows_to_update = []
    for row_index, row in enumerate(all_values):
        if row_index == 0 or row_index == 1:  # Пропускаем заголовки (если есть)
            continue
        if any(not row[col_index - 1] for col_index in cols_to_check):  # Проверяем, есть ли пустые ячейки в указанных столбцах
            rows_to_update.append(row_index + 1)  # +1, т.к. в gspread нумерация строк начинается с 1

    # 5. Обновление данных (если есть строки для обновления)
    if rows_to_update:
        # Создаем словарь с обновлениями для каждого столбца в строке
        updates = []

        for row_index in rows_to_update:
            # Предполагаем, что у вас есть all_values и row_index
            artist = all_values[row_index - 1][0]
            city = "Москва"
            logger.info(artist)
            # data_yand = await get_stats(artist)
            try:
                data_vk = await get_targeting_stats(city, artist)
                data = [
                    data_vk["group"]["group_link"], 
                    datetime.now().strftime("%d.%m.%y"),
                    data_vk["listeners"],
                    data_vk["group_followers"]
                ]
            except:
                data = ["", datetime.now().strftime("%d.%m.%y"), "", ""]
            for i, col_index in enumerate(cols_to_check):  # Перебираем столбцы D, E, F, H, I
                #Проверяем ячейку, чтобы не перезаписывать данные в заполненных ячейках
                cell_value = all_values[row_index - 1][col_index - 1]
                if not cell_value:
                    updates.append({
                        'range': f'{rowcol_to_a1(row_index, col_index)}',
                        'values': [[data[i]]]  # Берем значение из массива
                    })

            if row_index % 6 == 0:
                if updates:
                    worksheet.batch_update(updates)
                    updates = []
            await asyncio.sleep(2.4)

        # Выполняем массовое обновление
        if updates:
            worksheet.batch_update(updates)

        print(f"Обновлено {len(rows_to_update)} строк.")
    else:
        print("Нет строк для обновления.")
    # worksheet.batch_update(cells_to_update)

if __name__ == '__main__':
    test_get_data()