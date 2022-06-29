import random
import threading
import asyncio
import time
import concurrent.futures
from typing import List, Dict, Any, Coroutine

import requests
from aiohttp import ClientSession, ClientError
from bs4 import BeautifulSoup as BS


def get_categories_info(main_url):
    """Возвращает список с данными(словарями) о категориях"""
    categories_info = []
    response_obj = requests.get(main_url)
    html_page = BS(response_obj.content, 'html.parser')
    items0_list = html_page.select('.main-menu > .top_level > li')

    for item0 in items0_list[1:2]:  # items0_list: #####################
        cat0_name = item0.find_all('span')[0].text.strip()
        if cat0_name in ['Фасады', 'Фасади']:
            continue
        else:
            cat_level_0 = {}
            cat_level_0["name"] = cat0_name
            cat_level_0["slug"] = 'надо доработать'
            cat_level_0["categories_level_1"] = []

            items1_list = item0.select('.hidden-label > div')
            for item1 in items1_list[:]:  # items1_list: #####################
                if len(item1) > 0:
                    links = item1.find_all('a')
                    cat1_name = links[0].text.strip()
                    if cat1_name in ['Мойки из искусственного камня  Belterno', 'Мийки зі штучного каменю  Belterno']:
                        continue
                    else:
                        cat_level_1 = {}
                        cat_level_1["name"] = cat1_name
                        href_list_1 = links[0]["href"].split("/")
                        cat_level_1["href"] = f'/{href_list_1[-3]}/{href_list_1[-2]}/'
                        cat_level_1["slug"] = cat_level_1["href"].split('/')[-2]
                        cat_level_1["categories_level_2"] = []
                        if len(links) > 1:
                            for n in range(1, len(links)):  # range(1, len(links)):  #####################
                                cat_level_2 = {}
                                cat_level_2["name"] = links[n].text.strip()
                                href_list_2 = links[n]["href"].split("/")
                                cat_level_2["href"] = f'/{href_list_2[-3]}/{href_list_2[-2]}/'
                                cat_level_2["slug"] = cat_level_2["href"].split('/')[-2]
                                cat_level_1["categories_level_2"].append(cat_level_2)
                        cat_level_0["categories_level_1"].append(cat_level_1)
            categories_info.append(cat_level_0)
    print('Cписок с данными о разделах создан\n')
    return categories_info


def add_products_data(data, main_url, path_to_download):
    """Добавляет к данным о категоряих данные об их товарах и возвращает полученный список с категориями"""
    for i in range(len(data)):  # range(len(data)):
        print(f'Добавляем данные в раздел {data[i]["name"]}\n')
        for j in range(len(data[i].get("categories_level_1"))):
            if len(data[i].get("categories_level_1")[j].get("categories_level_2")) > 0:
                for k in range(len(data[i].get("categories_level_1")[j].get("categories_level_2"))):
                    url = main_url[:-8] + data[i].get("categories_level_1")[j].get("categories_level_2")[k]['href']
                    print(
                        f'  Добавляем список с данными о товарах внутри категории {data[i].get("categories_level_1")[j].get("categories_level_2")[k]["name"]}')
                    data[i].get("categories_level_1")[j].get("categories_level_2")[k]['products'] = get_products_data(
                        category_url=url, path_to_download=path_to_download)
            else:
                url = main_url[:-8] + data[i].get("categories_level_1")[j]['href']
                print(
                    f'  Добавляем список с данными о товарах внутри категории {data[i].get("categories_level_1")[j]["name"]}')
                data[i].get("categories_level_1")[j]['products'] = get_products_data(category_url=url,
                                                                                     path_to_download=path_to_download)
    return data


def get_products_data(category_url: str, path_to_download: str) -> List[dict]:
    """Возвращает список с данными о товарах внутри категории"""
    s = time.time()
    response_pages_list = asyncio.get_event_loop().run_until_complete(get_response_pages(category_url=category_url))
    print(f'     получили responces в количестве {len(response_pages_list)} шт')

    items_url_list = get_items_urls(response_pages_list)
    print(f'     получили items_urls товаров в количестве {len(items_url_list)} шт')

    if len(items_url_list) > 0:
        items_response_list = asyncio.get_event_loop().run_until_complete(get_items_responses(items_url_list))
        print(f'     получили response_items товаров в количестве {len(items_response_list)} шт')

        products_data_list = get_items_data(items_response_list, path_to_download)
        print(f'     получили products_data в количестве {len(products_data_list)} шт, время выполнения {time.time()-s} сек')
        print('')
        return products_data_list
    print('')
    return []

#######################################################################################

async def get_response_page(url: str, session: BS) -> Any:
    async with session.get(url) as response:
        return await response.text()


async def get_response_pages(category_url: str) -> Any:
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
        async with ClientSession() as session:
            task_list = [asyncio.create_task(get_response_page(f'{category_url}page-{number_page}', session)) for number_page in range(2, n + 1)]
            response_page_list += await asyncio.gather(*task_list)
    return response_page_list

#######################################################################################


def get_urls(response_page: str) -> List[str]:
    url_list = []
    html = BS(response_page, 'html.parser')
    items = html.select('.product_prewiew')
    if len(items):
        for item in items:
            product = item.select('a')
            url = f"https://viyar.ua{product[0].get('href')}"
            url_list.append(url[:-1])
    return url_list


def get_items_urls(response_page_list: List[str]) -> List[str]:
    """Возвращает список URL адресов всех товаров внутри категории"""
    items_url_list = []
    if len(response_page_list) > 0:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_list = [executor.submit(get_urls, response_page) for response_page in response_page_list]
            for future in concurrent.futures.as_completed(future_list):
                items_url_list += future.result()
    return items_url_list

#######################################################################################


async def get_item_response(item_url: str, session: ClientSession) -> List[str, Coroutine[str]]:
    """Возвращает response обьект на product_detail"""
    async with session.get(item_url) as response:
        return [item_url, await response.text()]



async def get_items_responses(items_url_list: list) -> Any:
    """Возвращает список response обьектов на все товары внутри категории"""
    try:
        try:
            async with ClientSession() as session:
                task_list = [get_item_response(item_url, session) for item_url in items_url_list]
                items_response_list = await asyncio.gather(*task_list)
        except ClientError as e:
            print(e)
    except BaseException as ex:
        print(ex)
    return items_response_list

#######################################################################################

def get_item_data(item_url: str, item_response, path_to_download: str) -> Dict[str: Any]:
    """Возвращает данные о товаре и загружает его фотографии в path_to_download"""
    item_data = {}
    item_html = BS(item_response, 'html.parser')
    item_data['name'] = get_name(item_html)
    item_data['slug'] = get_slug(item_url)
    item_data['price'] = get_price(item_html)
    item_data['properties'] = get_properties(item_html)
    item_data['photos'] = get_photos_urls(item_data['name'], item_html)
    asyncio.get_event_loop().run_until_complete(download_photos(item_data.get('photos'), path_to_download))
    return item_data


def get_items_data(items_response_list: list, path_to_download: str) -> List[dict]:
    """Возврашает список данных о товарах и загружает их фотографии в path_to_download"""
    items_data = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_list = [executor.submit(get_item_data,
                                       item_url=l[0],
                                       item_response=l[1],
                                       path_to_download=path_to_download) for l in items_response_list]
        for future in concurrent.futures.as_completed(future_list):
            items_data.append(future.result())
    return items_data

#######################################################################################


def get_name(item_html: BS) -> str:
    """Возвращает наименование товара"""
    try:
        name = item_html.select('.product_name > h1 > b')[0].text.strip()
    except Exception:
        return f'Exeption {int(time.time() * 1000)}'
    else:
        return name


def get_slug(item_url: str) -> str:
    try:
        slug = item_url.split('/')[-1]
    except Exception:
        return f'exeption_{int(time.time() * 1000)}'
    else:
        return slug


def get_price(item_html: BS) -> float:
    """Возвращает стоимость товара за единицу"""
    try:
        try:
            price = float(item_html.select('span.price')[0].text.strip())
        except ValueError:
            price = ''
            list_p = item_html.select('span.price')[0].text.strip().split()
            for i in list_p:
                price += i
            price = float(price)
    except Exception:
        return float(random.choice(range(1700, 2500, 3)))
    else:
        return price


def get_properties(item_html: BS) -> Dict[str: str]:
    """Возвращает характеристики товара"""
    properties = {}
    prop_list = item_html.select('div.charakters > ul.properties > li')
    n = 1
    try:
        for prop in prop_list:
            if n <= len(prop_list) / 2:
                property = prop.text.split(': ')
                properties[property[0]] = property[1].lower()
                n += 1
            else:
                break
    except Exception as ex:
        properties[f'Exception - {ex}'] = 'свойства не добавлены'
    return properties


def get_photos_urls(name: str, item_html: BS) -> List[str]:
    """Возвращает список url адресов фотографий товара"""
    photos_url_list = []
    for n in range(1, 5):
        try:
            if n == 1:
                photo = item_html.find_all('img', alt=name)
            else:
                photo = item_html.find_all('img', alt=name + ' — фото' + str(n))
            photo_url = f"https://viyar.ua{photo[0].get('src')}"
            photos_url_list.append(photo_url)
        except IndexError:
            break
    return photos_url_list


async def download_photos(photos_url_list: List[str], path: str) -> None:
    """Запускает потоки и загружает в них фотографии товара"""
    if photos_url_list:
        async with ClientSession() as session:
            task_list = [asyncio.create_task(get_photo(photo_url, session)) for photo_url in photos_url_list]
            photo_list = await asyncio.gather(*task_list)
        for photo in photo_list:
            root = path + photo[0].split('/')[-1]
            threading.Thread(target=write_photo, args=(root, photo[1])).start()


async def get_photo(photo_url: str, session: ClientSession) -> List[str, Coroutine[bytes]]:
    """Загружает фотографию"""
    async with session.get(photo_url) as response:
        return [photo_url, await response.read()]


def write_photo(root: str, photo: bytes) -> None:
    """Записывает фотографию на диск"""
    with open(root, "wb") as img:
        img.write(photo)


# def download_photo(photo_url, path):
#     """Загружает фотографию"""
#     root = path + photo_url.split('/')[-1]
#     retries = Retry(connect=5, read=2, redirect=5)
#     http = PoolManager(retries=retries)
#     p = requests.get(photo_url)
#     img = open(root, "wb")
#     img.write(p.content)
#     img.close()


# async def download_photos(photos_url_list: list, path: str) -> None:
#     """Запускает потоки и загружает в них фотографии товара"""
#     async with aiohttp.ClientSession() as session:
#         for photo_url in photos_url_list:
#             photo = await download_photo(photo_url, session)
#             write_image(photo, photo_url, path)
#
#
# async def download_photo(photo_url, session):
#     async with session.get(photo_url) as response:
#         return await response.read()
#
# def write_image(photo, photo_url, path):
#     root = path + photo_url.split('/')[-1]
#     with open(root, "wb") as file:
#         file.write(photo)

# async def save_photo(photo, photo_url, path):
#     root = path + photo_url.split('/')[-1]
#     print(root)
#     time.sleep(5)
#     async with aiofiles.open(root, mode='wb') as img:
#         print('здарова ёпта')
#         time.sleep(5)
#         await img.write(photo)



