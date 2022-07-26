from __future__ import print_function
from asyncio import get_event_loop, create_task, gather
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from random import choice
from time import time
from typing import List, Dict, Tuple, Any, Optional, Union
from os.path import exists
from io import BytesIO
from requests import get

from aiohttp import ClientSession, ClientError
from bs4 import BeautifulSoup as BS

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, Session

from my_sqlalchemy_mptt import mptt_sessionmaker
from models import Cat

# DATABASE_URL = 'postgresql+asyncpg://postgres:1@localhost:5432/test'
DATABASE_URL = 'postgresql+psycopg2://postgres:1@localhost:5432/test'
engine = create_engine(DATABASE_URL, echo=True)
Session = mptt_sessionmaker(sessionmaker(bind=engine))

# session = sessionmaker(bind=engine)


def add_cat_to_database(cat_data: dict, parent_id: Union[int, None] = None):
    session = Session()
    cat = Cat()
    cat.name = cat_data.get('name')
    cat.slug = cat_data.get('slug')
    cat.parent_id = parent_id
    session.add(cat)
    session.commit()
    return cat.id


def get_categories_info(main_url: str) -> List[dict]:
    """Возвращает список с данными(словарями) о категориях"""
    categories_info = []
    response_obj = get(main_url)
    html_page = BS(response_obj.content, 'html.parser')
    items0_list = html_page.select('.main-menu > .top_level > li')
    print(items0_list)

    for item0 in items0_list[:]:  # items0_list: #####################
        cat0_name = item0.find_all('span')[0].text.strip()
        if cat0_name in ['Фасады', 'Фасади']:
            continue
        else:
            cats_0 = {}
            cats_0["name"] = cat0_name
            cats_0["slug"] = 'надо доработать'
            cats_0["cats_1"] = []
            print(cats_0)
            parent_id_0 = add_cat_to_database(cats_0)
            print(parent_id_0)

            items1_list = item0.select('.hidden-label > div')
            for item1 in items1_list[:]:  # items1_list: #####################
                if len(item1) > 0:
                    links = item1.find_all('a')
                    cat1_name = links[0].text.strip()
                    if cat1_name in ['Мойки из искусственного камня  Belterno', 'Мийки зі штучного каменю  Belterno']:
                        continue
                    else:
                        cats_1 = {}
                        cats_1["name"] = cat1_name
                        href_list_1 = links[0]["href"].split("/")
                        cats_1["href"] = f'/{href_list_1[-3]}/{href_list_1[-2]}/'
                        cats_1["slug"] = cats_1["href"].split('/')[-2]
                        cats_1["cats_2"] = []
                        parent_id_1 = add_cat_to_database(cats_1, parent_id_0)
                        print(parent_id_1)
                        if len(links) > 1:
                            for n in range(1, len(links)):  # range(1, len(links)):  #####################
                                cats_2 = {}
                                cats_2["name"] = links[n].text.strip()
                                href_list_2 = links[n]["href"].split("/")
                                cats_2["href"] = f'/{href_list_2[-3]}/{href_list_2[-2]}/'
                                cats_2["slug"] = cats_2["href"].split('/')[-2]
                                parent_id_2 = add_cat_to_database(cats_2, parent_id_1)
                                print(parent_id_2)

                                cats_1["cats_2"].append(cats_2)
                        cats_0["cats_1"].append(cats_1)
            categories_info.append(cats_0)
    print('Cписок с данными о разделах создан\n')
    return categories_info


def add_products_data(data: List[dict], main_url: str) -> List[dict]:
    """Добавляет к данным о категоряих данные об их товарах и возвращает полученный список с категориями"""
    for i in range(len(data)):  # range(len(data)):
        print(f'Добавляем данные в раздел {data[i]["name"]}\n')
        for j in range(len(data[i].get("categories_level_1"))):
            if len(data[i].get("categories_level_1")[j].get("categories_level_2")) > 0:
                for k in range(len(data[i].get("categories_level_1")[j].get("categories_level_2"))):
                    url = main_url[:-8] + data[i].get("categories_level_1")[j].get("categories_level_2")[k]['href']
                    print(f'  Добавляем список с данными о товарах \
                    внутри категории {data[i].get("categories_level_1")[j].get("categories_level_2")[k]["name"]}')
                    data[i].get("categories_level_1")[j].get("categories_level_2")[k]['products'] = get_products_data(
                        category_url=url)
            else:
                url = main_url[:-8] + data[i].get("categories_level_1")[j]['href']
                print(f'  Добавляем список с данными о товарах \
                внутри категории {data[i].get("categories_level_1")[j]["name"]}')
                data[i].get("categories_level_1")[j]['products'] = get_products_data(category_url=url)
    return data


def get_products_data(category_url: str) -> List[dict]:
    """Возвращает список с данными о товарах внутри категории"""
    s = time()
    response_pages_list = get_event_loop().run_until_complete(get_response_pages(category_url=category_url))
    print(f'     получили responces в количестве {len(response_pages_list)} шт')

    items_url_list = get_items_urls(response_pages_list)
    print(f'     получили items_urls товаров в количестве {len(items_url_list)} шт')

    if len(items_url_list) > 0:
        items_response_list = get_event_loop().run_until_complete(get_items_responses(items_url_list))
        print(f'     получили response_items товаров в количестве {len(items_response_list)} шт')

        products_data_list = get_items_data(items_response_list)
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
    """Возвращает список response обьектов со страницами пагинатора внутри категории"""
    response_page_list = []
    response_page = get(f'{category_url}')
    response_page_list.append(response_page.text)
    item_html = BS(response_page_list[0], 'html.parser')
    paggination_list = item_html.select('.paggination > li')
    if 0 <= len(paggination_list) <= 2:
        return response_page_list
    else:
        n = int(paggination_list[-2].text)
        async with ClientSession() as session:
            task_list = [create_task(get_response_page(f'{category_url}page-{number_page}',
                                                       session)) for number_page in range(2, n + 1)]
            response_page_list += await gather(*task_list)
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


async def get_items_responses(items_url_list: list):
    """Возвращает список response обьектов на все товары внутри категории"""
    try:
        try:
            async with ClientSession() as session:
                task_list = [get_item_response(item_url, session) for item_url in items_url_list]
                items_response_list = await gather(*task_list)
        except ClientError as e:
            print(e)
    except BaseException as ex:
        print(ex)
    return items_response_list


#######################################################################################
def google_auth():
    """Shows basic usage of the Drive v3 API.
      Prints the names and ids of the first 10 files the user has access to.
      """
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/drive']
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def get_item_data(item_url: str, item_response: str, google_credentials: Credentials) -> Dict[str, Any]:
    """Возвращает данные о товаре и загружает его фотографии в path_to_download"""
    item_data = {}
    item_html = BS(item_response, 'html.parser')
    item_data['name'] = get_name(item_html)
    item_data['slug'] = get_slug(item_url)
    item_data['price'] = get_price(item_html)
    item_data['properties'] = get_properties(item_html)
    photos_url_dict = get_photos_urls(item_data['name'], item_html)
    item_data['photos'] = get_event_loop().run_until_complete(download_photos(photos_url_dict, google_credentials))
    return item_data


def get_items_data(items_response_list: list) -> List[dict]:
    """Возврашает список данных о товарах и загружает их фотографии в path_to_download"""
    items_data = []
    google_credentials = google_auth()

    with ProcessPoolExecutor() as executor:
        future_list = [executor.submit(get_item_data,
                                       item_url=item[0],
                                       item_response=item[1],
                                       creds=google_credentials) for item in items_response_list]
        for future in as_completed(future_list):
            items_data.append(future.result())
    return items_data


#######################################################################################


def get_name(item_html: BS) -> str:
    """Возвращает наименование товара"""
    try:
        name = item_html.select('.product_name > h1 > b')[0].text.strip()
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
        return float(choice(range(1700, 2500, 3)))
    else:
        return price


def get_properties(item_html: BS) -> Dict[str, str]:
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


def get_photos_urls(name: str, item_html: BS) -> Dict[str, str]:
    """Возвращает список url адресов фотографий товара"""
    photos_url_dict = {}
    for n in range(1, 5):
        try:
            if n == 1:
                photo = item_html.find_all('img', alt=name)
            else:
                photo = item_html.find_all('img', alt=name + ' — фото' + str(n))
            photo_url = f"https://viyar.ua{photo[0].get('src')}"
            photos_url_dict[f'photo{n}'] = photo_url
        except IndexError:
            break
    return photos_url_dict


async def download_photos(photos_url_dict: Dict[str, str], google_credentials: Credentials) -> Dict[str, str]:
    """Запускает потоки и загружает в них фотографии товара"""
    photos_id_dict = {}
    if photos_url_dict:
        async with ClientSession() as session:
            task_list = [create_task(get_photo(key, url, session)) for key, url in photos_url_dict.items()]
            photo_list = await gather(*task_list)

        user_permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
        with ThreadPoolExecutor() as executor:
            future_list = [executor.submit(google_upload_image,
                                           key=photo.get('key'),
                                           image=BytesIO(photo.get('photo')),
                                           google_credentials=google_credentials,
                                           file_metadata={'name': photo.get('name')},
                                           user_permission=user_permission
                                           ) for photo in photo_list]
            for future in as_completed(future_list):
                result = future.result()
                if result:
                    photos_id_dict[result[0]] = result[1]

    return photos_id_dict


async def get_photo(key: str, url: str, session: ClientSession):
    """Загружает фотографию"""
    async with session.get(url) as response:
        return {'key': key, "name": url.split('/')[-1], "photo": await response.read()}


def google_upload_image(key: str,
                        image: BytesIO,
                        google_credentials: Credentials,
                        file_metadata: Dict[str, str],
                        user_permission: Dict[str, str]) -> Optional[Tuple[str, Any]]:
    try:
        # create gmail api client
        service = build('drive', 'v3', credentials=google_credentials)
        media = MediaIoBaseUpload(image, mimetype='image/jpg')
        file = service.files().create(body=file_metadata, media_body=media).execute()
        fileId = file.get("id")
        service.permissions().create(fileId=fileId, body=user_permission).execute()
        return key, fileId

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None


if __name__ == '__main__':
    # url = 'https://viyar.ua/catalog/neon_lenta_smd_2835_9_6vt_12v_ip20_4kh10_mm_kholodnyy_svet'
    # resp = get(url).text
    # google_credentials = google_auth()
    # result = get_item_data(item_url=url, item_response=resp, google_credentials=google_credentials)
    # # print(get_event_loop().run_until_complete(download_photos(
    # #     photos_url_list=["https://viyar.ua/upload/resize_cache/photos/300_300_1/ph97262.jpg",
    # #                      'https://viyar.ua/upload/resize_cache/photos/300_300_1/ph66441.jpg',
    # #                      'https://viyar.ua/upload/resize_cache/photos/300_300_1/ph84038.jpg',
    # #                      'https://viyar.ua/upload/resize_cache/photos/300_300_1/ph90731.jpg'],
    # #     google_credentials=google_auth()
    # # )))
    # print(result)

    get_categories_info('https://viyar.ua/catalog')

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
