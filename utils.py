from __future__ import print_function

from datetime import datetime
from asyncio import get_event_loop, create_task, gather
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from random import choice
from time import time
from typing import List, Dict, Tuple, Any, Optional, Union
from io import BytesIO

from requests import get

from aiohttp import ClientSession, ClientError
from bs4 import BeautifulSoup as BS

from database.views import add_category_to_db, add_product_to_db, add_property_to_db, add_value_to_db
from google_api.views import google_auth, google_upload_image, google_create_folder, google_search_folder


def get_categories_info(main_url: str) -> List[dict]:
    """Возвращает список с данными(словарями) о категориях"""
    categories_info = []
    response_obj = get(main_url)
    html_page = BS(response_obj.content, 'html.parser')
    item_0_list = html_page.select('.dropdown__list-item_lev1')

    for item_0 in item_0_list[:8]:  # item_0_list[:8] #####################
        cat_0_name = item_0.select('a > .text')[0].text
        cat_0_slug = item_0.select('a')[0].get('href').split('/')[-2]
        if cat_0_name in ['Фасады', 'Фасади']:
            continue
        else:
            cat_0 = {}
            cat_0["name"] = cat_0_name
            cat_0["slug"] = cat_0_slug
            cat_0["cats_1"] = []
            cat_id_0 = add_category_to_db(cat_0)
            cat_0['cat_id'] = cat_id_0

            item_1_list = item_0.select('.li_lev2')
            for item_1 in item_1_list[:]:  # item_1_list[:] #####################
                links_1 = item_1.find_all('a')
                cat_1_name = links_1[0].text.strip()
                if cat_1_name in ['Мойки из искусственного камня  Belterno', 'Мийки зі штучного каменю  Belterno']:
                    continue
                else:
                    cat_1 = {}
                    cat_1["name"] = cat_1_name
                    href_list_1 = links_1[0]["href"].split("/")
                    cat_1["href"] = f'/{href_list_1[-3]}/{href_list_1[-2]}/'
                    cat_1["slug"] = cat_1["href"].split('/')[-2]
                    cat_1["cats_2"] = []
                    cat_id_1 = add_category_to_db(cat_1, cat_id_0)
                    cat_1['cat_id'] = cat_id_1

                    item_2_list = item_1.select('.dropdown__list-item')
                    if len(item_2_list) > 0:
                        for item_2 in item_2_list[:]:  # item_2_list[:] #####################
                            links_2 = item_2.find_all('a')
                            cat_2 = {}
                            cat_2["name"] = links_2[0].text.strip()
                            href_list_2 = links_2[0]["href"].split("/")
                            cat_2["href"] = f'/{href_list_2[-3]}/{href_list_2[-2]}/'
                            cat_2["slug"] = cat_2["href"].split('/')[-2]
                            cat_id_2 = add_category_to_db(cat_2, cat_id_1)
                            cat_2['cat_id'] = cat_id_2

                            cat_1["cats_2"].append(cat_2)
                    cat_0["cats_1"].append(cat_1)
            categories_info.append(cat_0)
    print('\nCписок с данными о категориях создан\n')
    return categories_info


def add_products_data(data: List[dict], main_url: str) -> List[dict]:
    """Добавляет к данным о категоряих данные об их товарах и возвращает полученный список с категориями"""
    for i in range(len(data)):  # range(len(data)):
        print(f'Добавляем данные в раздел {data[i]["name"]}\n')
        for j in range(len(data[i].get("cats_1"))):
            if len(data[i].get("cats_1")[j].get("cats_2")) > 0:
                for k in range(len(data[i].get("cats_1")[j].get("cats_2"))):
                    url = main_url[:-8] + data[i].get("cats_1")[j].get("cats_2")[k]['href']
                    cat_id = data[i].get("cats_1")[j].get("cats_2")[k]['cat_id']
                    print(f'  Добавляем список с данными о товарах \
                    внутри категории {data[i].get("cats_1")[j].get("cats_2")[k]["name"]}')
                    data[i].get("cats_1")[j].get("cats_2")[k]['products'] = get_products_data(
                        category_url=url,
                        cat_id=cat_id)
            else:
                url = main_url[:-8] + data[i].get("cats_1")[j]['href']
                cat_id = data[i].get("cats_1")[j]['cat_id']
                print(f'  Добавляем список с данными о товарах \
                внутри категории {data[i].get("cats_1")[j]["name"]}')
                data[i].get("cats_1")[j]['products'] = get_products_data(category_url=url, cat_id=cat_id)
    return data


def get_products_data(category_url: str, cat_id: int, folder_id: str) -> List[dict]:
    """
    Возвращает список с данными о товарах внутри категории.
    category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
    """
    s = time()
    response_pages_list = get_event_loop().run_until_complete(get_response_pages(category_url=category_url))
    print(f'     получили responces в количестве {len(response_pages_list)} шт')

    items_url_list = get_items_urls(response_pages_list[:1])
    print(f'     получили items_urls товаров в количестве {len(items_url_list)} шт')

    if len(items_url_list) > 0:
        items_response_list = get_event_loop().run_until_complete(get_items_responses(items_url_list[:12]))
        print(f'     получили response_items товаров в количестве {len(items_response_list)} шт')

        products_data_list = get_event_loop().run_until_complete(get_items_data(items_response_list, cat_id, folder_id))
        print(f'     получили products_data \
в количестве {len(products_data_list)} шт, время выполнения {time() - s} сек')
        print('')
        return products_data_list
    print('')
    return []


#######################################################################################

async def get_response_page(url: str, session: ClientSession):
    async with session.get(url) as response:
        return await response.text()


async def get_response_pages(category_url: str):
    """
    Возвращает список response обьектов со страницами пагинатора внутри категории.
    category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
    """
    response_page_list = []
    response_page = get(category_url)
    response_page_list.append(response_page.text)
    item_html = BS(response_page_list[0], 'html.parser')
    pagination_list = item_html.select('a.pagination__item')
    if len(pagination_list) == 0:
        return response_page_list
    else:
        amount_pages = int(pagination_list[-1].text)
        async with ClientSession() as session:
            task_list = [create_task(get_response_page(f'{category_url}page-{number_page}',
                                                       session)) for number_page in
                         range(2, amount_pages + 1)]  ############### range(2, amount_pages + 1)
            response_page_list += await gather(*task_list)
    return response_page_list


#######################################################################################


def get_urls(response_page: str) -> List[str]:
    url_list = []
    html = BS(response_page, 'html.parser')
    items = html.select('a.product-card__media')
    if len(items):
        for item in items:
            product = item.get('href')
            url = f"https://viyar.ua{product[:-1]}"
            url_list.append(url)
    return url_list


def get_items_urls(response_page_list: List[str]) -> List[str]:
    """Возвращает список URL адресов всех товаров внутри категории"""
    items_url_list = []
    if len(response_page_list) > 0:
        with ProcessPoolExecutor() as executor:
            future_list = [executor.submit(get_urls, response_page) for response_page in response_page_list]
            for future in as_completed(future_list):
                items_url_list += future.result()
    return items_url_list


#######################################################################################


async def get_item_response(item_url: str, session: ClientSession):
    """Возвращает response обьект на product_detail"""
    async with session.get(item_url) as response:
        return [item_url, await response.text()]


async def get_items_responses(items_url_list: list) -> list:
    """Возвращает список response обьектов на все товары внутри категории"""
    items_response_list = []
    try:
        try:
            async with ClientSession() as session:
                task_list = [get_item_response(item_url, session) for item_url in items_url_list]
                items_response_list += list(await gather(*task_list))
        except ClientError as e:
            print(e)
    except BaseException as ex:
        print(ex)
    return items_response_list


#######################################################################################


def get_item_data(item_url: str, item_response: str) -> Dict[str, Any]:
    """Возвращает данные о товаре и загружает его фотографии в path_to_download"""
    item_data = {}
    item_html = BS(item_response, 'html.parser')
    item_data['name'] = get_name(item_html)
    item_data['slug'] = get_slug(item_url)
    item_data['description'] = get_description(item_html)
    item_data['price'] = get_price(item_html)
    item_data['properties'] = get_properties(item_html)
    item_data['photos'] = get_photos_urls(item_data['name'], item_html)
    print(item_data['photos'])
    return item_data


async def get_items_data(items_response_list: list, cat_id: int, folder_id: str) -> tuple:
    """Возврашает список данных о товарах и загружает их фотографии в path_to_download"""
    items_data = {}
    google_credentials = google_auth()

    timer = time()
    with ProcessPoolExecutor() as executor:
        future_list = [executor.submit(get_item_data,
                                       item_url=item[0],
                                       item_response=item[1],
                                       ) for item in items_response_list]
        id_ = 1
        for future in as_completed(future_list):
            items_data[id_] = future.result()
            id_ += 1
    print(f'        Получили данные о {len(items_data)} товарах, время выполнения {time() - timer} сек')

    timer = time()
    async with ClientSession() as session:
        task_list = []
        for item_id, item in items_data.items():
            for key, url in item['photos'].items():
                task_list.append(create_task(get_photo(item_id, key, url, session)))
        response_list = await gather(*task_list)
    print(f'        Получили {len(response_list)} изображений, время выполнения {time() - timer} сек')

    timer = time()
    with ThreadPoolExecutor() as executor:
        photos_data = []
        user_permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
        future_list = [executor.submit(google_upload_image,
                                       item_id=response.get('item_id'),
                                       key=response.get('key'),
                                       image=BytesIO(response.get('photo')),
                                       google_credentials=google_credentials,
                                       file_metadata={'name': response.get('name'), 'parents': [folder_id]},
                                       user_permission=user_permission
                                       ) for response in response_list]
        for future in as_completed(future_list):
            result = future.result()
            if result:
                photos_data.append(result)
    print(f'        Загрузили {len(photos_data)} фоток в гугл, время выполнения {time() - timer} сек')

    for photo in photos_data:
        item_id = photo.get('item_id')
        key = photo.get('key')
        fileId = photo.get('fileId')
        items_data[item_id]['photos'][key] = fileId

    timer = time()
    task_list = [create_task(add_product_to_db(data, cat_id)) for item_id, data in items_data.items()]
    items_id_list = await gather(*task_list)
    print(f'        Добавили {len(items_id_list)} товаров в базу, время выполнения {time() - timer} сек')

    return items_id_list


#######################################################################################


def get_name(item_html: BS) -> str:
    """Возвращает наименование товара"""
    try:
        name = item_html.select('h1.product__title-text')[0].text.strip()
    except Exception:
        return f'Exeption {int(time() * 1000)}'
    else:
        return name


def get_slug(item_url: str) -> str:
    try:
        slug = item_url.split('/')[-1]
    except Exception:
        return f'exeption_{int(time() * 1000)}'
    else:
        return slug


def get_description(item_html: BS) -> str:
    try:
        info = item_html.select('div.product-info__content--description > .product-info__content-section > .text > p')
        if info:
            description = ''
            for paragraph in info:
                description += paragraph.text.strip() + ' '
            return description
        else:
            return None
    except Exception:
        return None


def get_price(item_html: BS) -> float:
    """Возвращает стоимость товара за единицу"""
    try:
        try:
            price = float(item_html.select('span.product-price__price')[0].text.strip())
        except ValueError:
            price = ''
            list_p = item_html.select('span.product-price__price')[0].text.strip().split()
            for i in list_p:
                price += i
            price = float(price)
    except Exception:
        return float(choice(range(1700, 2500, 3)))
    else:
        return price


def get_properties(item_html: BS) -> Dict[str, str]:
    """Возвращает характеристики товара"""
    properties = {}
    prop_list = item_html.select('div.product-info__content-substatus')
    try:
        for property in prop_list:
            property_name = property.select('div.product-info__content-substatus-name')[0].text.strip(':')
            property_value = property.select('div.text')[0].text.strip()
            properties[property_name] = property_value
    except Exception as ex:
        properties[f'Exception - {ex}'] = 'свойства не добавлены'
    return properties


def get_photos_urls(name: str, item_html: BS) -> Dict[str, str]:
    """Возвращает список url адресов фотографий товара"""
    photos_url_dict = {}
    try:
        list_ = item_html.select('div.product-demo__body > ul > li')
        if len(list_) > 0:
            n = 1
            for l in list_:
                if n <= 4:
                    src = l.select('img')[0].get('src')
                    photo_url = f"https://viyar.ua{src}"
                    photos_url_dict[f'photo{n}'] = photo_url
                    n += 1
    except Exception as ex:
        print(f'Ошибка добавления ссылок на изображения товара ---{name}---{ex}')
    return photos_url_dict


# async def download_photos(photos_url_dict: Dict[str, str], google_credentials: Credentials) -> Dict[str, str]:
#     """Запускает потоки и загружает в них фотографии товара"""
#     photos_id_dict = {}
#     if photos_url_dict:
#         async with ClientSession() as session:
#             task_list = [create_task(get_photo(key, url, session)) for key, url in photos_url_dict.items()]
#             photo_list = await gather(*task_list)
#
#         user_permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
#         with ThreadPoolExecutor() as executor:
#             future_list = [executor.submit(google_upload_image,
#                                            item_id=
#                                            key=photo.get('key'),
#                                            image=BytesIO(photo.get('photo')),
#                                            google_credentials=google_credentials,
#                                            file_metadata={'name': photo.get('name')},
#                                            user_permission=user_permission
#                                            ) for photo in photo_list]
#             for future in as_completed(future_list):
#                 result = future.result()
#                 if result:
#                     photos_id_dict[result[0]] = result[1]
#     return photos_id_dict


async def get_photo(item_id: int, key: str, url: str, session: ClientSession):
    """Загружает фотографию"""
    async with session.get(url) as response:
        return {'item_id': item_id, 'key': key, "name": url.split('/')[-1], "photo": await response.read()}


async def add_properties_data():
    prop_dict = {}
    for product in PRODUCTS_PROPERTIES:
        for name, value in product['properties'].items():
            prop_id = prop_dict.get(name)
            if not prop_id:
                prop_id = add_property_to_db(name)
                prop_dict[name] = prop_id
            await add_value_to_db(product_id=product['prod_id'],
                                  property_id=prop_id,
                                  value=value)


if __name__ == '__main__':
    # url = 'https://viyar.ua/catalog/dvoiarusne_lizhko'
    # resp = get(url).text
    # google_credentials = google_auth()
    # result = get_item_data(item_url=url, item_response=resp, google_credentials=google_credentials)
    # print(result)

    creds = google_auth()
    folder_name = f'django_shop.catalog.images {datetime.now()}'
    # folder_name = 'test_folder'
    folder_id = google_search_folder(folder_name, creds)
    if not folder_id:
        folder_id = google_create_folder(folder_name, creds)
    PRODUCTS_PROPERTIES = []
    category_url = 'https://viyar.ua/kv/catalog/moyki_franke/'

    PRODUCTS_PROPERTIES += get_products_data(category_url=category_url, cat_id=1113, folder_id=folder_id)
    for prop in PRODUCTS_PROPERTIES:
        print(prop)
    get_event_loop().run_until_complete(add_properties_data())

    # main_url = 'https://viyar.ua/catalog'
    # data = get_categories_info(main_url)
    # add_products_data(data, main_url)

    # item_url = 'https://viyar.ua/catalog/dsp_cleaf_duna_fiocco_seta_fc08_baragan_tolshchina_18_18_5mm'
    # item_response = get(item_url).text
    # google_credentials = google_auth()
    # item_data = get_item_data(item_url, item_response, google_credentials)
    # print(item_data)

    # item_data = {}
    # item_html = BS(item_response, 'html.parser')
    # item_data['name'] = get_name(item_html)
    # item_data['slug'] = get_slug(item_url)
    # item_data['price'] = get_price(item_html)
    # item_data['properties'] = get_properties(item_html)
    # photos_url_dict = get_photos_urls(item_data['name'], item_html)
    # print(item_data)
    # print(photos_url_dict)

# def write_photo(root: str, photo: bytes) -> None:
#     """Записывает фотографию на диск"""
#     with open(root, "wb") as img:
#         img.write(photo)


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
