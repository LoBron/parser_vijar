import concurrent.futures

import requests
from bs4 import BeautifulSoup as BS
import asyncio
import aiohttp
import time

import random

from utils import get_name, get_slug, get_price, get_properties, get_photos_urls, download_photos


async def get_response_page(category_url, number_page, session):
    # try:
    async with session.get(f'{category_url}page-{number_page}') as response:
        return await response.text()
    # except Exception as ex:
    #     print(ex)


async def get_response_pages(category_url):
    """Возвращает список response обьектов со страницами пагинатора внутри категории"""
    response_page_list = []
    response_page = requests.get(f'{category_url}')
    response_page_list.append(response_page.text)
    item_html = BS(response_page_list[0], 'html.parser')
    paggination_list = item_html.select('.paggination > li')
    if 0 <= len(paggination_list) <= 2:
        return response_page_list
    else:
        n = int(paggination_list[-2].text)
        s = time.time()
        async with aiohttp.ClientSession() as session:
            task_list = [asyncio.create_task(get_response_page(category_url, i, session)) for i in range(2, n + 1)]  # (2, n + 1)]
            for future in asyncio.as_completed(task_list):
                response_page_list.append(await future)
        print(time.time()-s)
        # time.sleep(0.1)
        await asyncio.sleep(0.1)
    return response_page_list


#######################################################################################
def get_urls(response_page):
    url_list = []
    # try:
    html = BS(response_page, 'html.parser')
    items = html.select('.product_prewiew')
    if len(items):
        for item in items:
            product = item.select('a')
            # url = product[0].get('href')
            url = f"https://viyar.ua{product[0].get('href')}"
            url_list.append(url[:-1])
    # except Exception as ex:
    #     print(f'!------------------{ex}------------------!')
    return url_list


def get_items_urls(response_page_list):
    """Возвращает список URL адресов всех товаров внутри категории"""
    items_url_list = []
    if len(response_page_list) > 0:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_list = [executor.submit(get_urls, response_page) for response_page in response_page_list]
            for future in concurrent.futures.as_completed(future_list):
                items_url_list += future.result()
    return items_url_list


#######################################################################################
async def get_item_response(item_url, session):
    """Возвращает response обьект на product_detail"""
    # try:
    async with session.get(item_url) as response:
        return await response.text()
    # except Exception as ex:
    #     print(ex)


async def get_items_responses(items_url_list):
    """Возвращает список response обьектов на все товары внутри категории"""
    items_response_list = []
    # try:
    async with aiohttp.ClientSession() as session:
        task_list = [asyncio.create_task(get_item_response(item_url, session)) for item_url in items_url_list]
        for future in asyncio.as_completed(task_list):
            items_response_list.append(await future)

    # except Exception as ex:
    #     print(ex)
    await asyncio.sleep(0.1)
    return items_response_list


#######################################################################################
def get_item_data(item_response, path_to_download):
    """Возвращает данные о товаре и загружает его фотографии в path_to_download"""
    item_data = {}
    item_html = BS(item_response, 'html.parser')
    code = ''
    for i in range(5, random.choice([j for j in range(6, 11)])):
        code += random.choice([str(k) for k in range(0, 10)])
    item_data['name'] = get_name(item_html, code)
    # print(f"object '{item_data['name']}' added")
    item_data['slug'] = get_slug(item_response, code)
    item_data['price'] = get_price(item_html)
    item_data['properties'] = get_properties(item_html)
    item_data['photos'] = get_photos_urls(item_data['name'], item_html)
    download_photos(item_data.get('photos'), path_to_download)
    # print(f"object '{item_data['name']}' added")
    return item_data


def get_items_data(items_response_list, path_to_download):
    """Возврашает список данных о товарах и загружает их фотографии в path_to_download"""
    items_data = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_list = [executor.submit(get_item_data, item_response, path_to_download) for item_response in
                       items_response_list]
        for future in concurrent.futures.as_completed(future_list):
            items_data.append(future.result())
    return items_data

# async def main():
#     async with aiohttp.ClientSession() as session:
#         start = time.time()
#         response_page_list = await get_response_pages('https://viyar.ua/catalog/yashchiki_mullerbox', session)
#
#         print(time.time() - start)
#         start = time.time()
#         items_url_list = get_items_urls(response_page_list)
#         # print(items_url_list[1])
#         # time.sleep(5)
#         print(time.time() - start)
#         time.sleep(5)
#
#         start = time.time()
#         items_response_list = await get_items_responses(items_url_list, session)
#         print(f'amount of responses {len(items_response_list)}')
#         print(time.time() - start)
#
#         start = time.time()
#         items_response_list = get_items_responses1(items_url_list)
#         print(f'amount of responses {len(items_response_list)}')
#         print(time.time() - start)
#     await asyncio.sleep(0.1)

if __name__ == '__main__':
    # asyncio.run(main())
    path = 'products_data/'

    start = time.time()
    response_page_list = asyncio.run(get_response_pages('https://viyar.ua/catalog/yashchiki_mullerbox/'))
    print(f'amount of responses {len(response_page_list)}')
    print(time.time() - start)

    start = time.time()
    items_url_list = get_items_urls(response_page_list)
    print(f'amount of urls {len(items_url_list)}')
    print(time.time() - start)
    time.sleep(5)

    start = time.time()
    items_response_list = asyncio.run(get_items_responses(items_url_list))
    print(f'amount of responses {len(items_response_list)}')
    print(time.time() - start)

    start = time.time()
    items_data = get_items_data(items_response_list, path)
    print(f'amount of items {len(items_data)}')
    print(time.time() - start)
    print(items_data)