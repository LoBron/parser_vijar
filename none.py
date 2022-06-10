import concurrent.futures

import requests
from bs4 import BeautifulSoup as BS
import asyncio
import aiohttp
import time


# def get_response_page1(category_url, number_page):
#     return requests.get(f'{category_url}page-{number_page}/')
#
# def get_response_pages1(category_url):
#     """Возвращает список response обьектов со страницами пагинатора внутри категории"""
#     response_page_list = []
#     response_page = requests.get(f'{category_url}')
#     response_page_list.append(response_page)
#     item_html = BS(response_page.content, 'html.parser')
#     paggination_list = item_html.select('.paggination > li')
#     if 0 <= len(paggination_list) <= 2:
#         return response_page_list
#     else:
#         n = int(paggination_list[-2].text)
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future_list = [executor.submit(get_response_page1, category_url, i) for i in range(2, 3)] #(2, n + 1)]
#         for future in concurrent.futures.as_completed(future_list):
#             response_page_list.append(future.result())
#     return response_page_list


async def get_response_page(category_url, number_page, session):
    async with session.get(f'{category_url}page-{number_page}/') as response:
        return await response.text()


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
        async with aiohttp.ClientSession() as session:
            task_list = [asyncio.create_task(get_response_page(category_url, i, session)) for i in
                         range(2, n + 1)]  # (2, n + 1)]
            for future in asyncio.as_completed(task_list):
                response_page_list.append(await future)
        await asyncio.sleep(0.1)
    return response_page_list


#######################################################################################
def get_urls(response_page):
    url_list = []
    try:
        html = BS(response_page, 'html.parser')
        items = html.select('.product_prewiew')
        if len(items):
            for item in items:
                product = item.select('a')
                url = f"https://viyar.ua{product[0].get('href')}"
                url_list.append(url[:-2])
    except Exception as ex:
        print(f'!------------------{ex}------------------!')
    return url_list


def get_items_urls(response_page_list):
    """Возвращает список URL адресов всех товаров внутри категории"""
    items_url_list = []
    if len(response_page_list) > 0:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_list = [executor.submit(get_urls, response_page) for response_page in response_page_list[:2]]
            for future in concurrent.futures.as_completed(future_list):
                items_url_list += future.result()
    return items_url_list


#######################################################################################
async def get_item_response(item_url, session):
    """Возвращает response обьект на product_detail"""
    async with session.get(item_url) as response:
        return await response.text()


async def get_items_responses(items_url_list):
    """Возвращает список response обьектов на все товары внутри категории"""
    items_response_list = []
    async with aiohttp.ClientSession() as session:
        task_list = [asyncio.create_task(get_response_page(get_item_response, item_url, session)) for item_url in items_url_list]
        for future in asyncio.as_completed(task_list):
            items_response_list.append(await future)
    await asyncio.sleep(0.1)
    return items_response_list


if __name__ == '__main__':
    start = time.time()
    response_page_list = asyncio.run(get_response_pages('https://viyar.ua/catalog/yashchiki_mullerbox/'))
    print(time.time() - start)
    start = time.time()
    items_url_list = get_items_urls(response_page_list)
    print(time.time() - start)

    start = time.time()
    print(f'amount of responses {asyncio.run(get_items_responses(items_url_list))}')
    print(time.time() - start)

    # start = time.time()
    # print(get_response_pages1('https://viyar.ua/catalog/yashchiki_mullerbox/'))
    # print(time.time() - start)
