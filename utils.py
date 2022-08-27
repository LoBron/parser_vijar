from asyncio import get_event_loop, create_task, gather, new_event_loop, set_event_loop, run
from concurrent.futures import ProcessPoolExecutor, as_completed
from random import choice
from time import time
from typing import List, Dict, Any, Union, Tuple
from requests import get

from aiohttp import ClientSession
from bs4 import BeautifulSoup as BS

from database.views import add_category_to_db, add_product_to_db, add_property_to_db, add_value_to_db, clear_all_tables
from google_api.views import google_auth, create_folder, search_folder, get_photos_id_list
from settings import MAIN_URL, GOOGLE_FOLDER_NAME


class Parser:
    """здарова ёпта"""

    def __init__(self):
        self.__main_url = MAIN_URL
        self.__google_credentials = google_auth()
        self.__folder_id = search_folder(GOOGLE_FOLDER_NAME, self.__google_credentials)
        print(self.__folder_id)
        # нужно доработать вариант когда искомая папка находится в корзине
        if not self.__folder_id:
            self.__folder_id = create_folder(GOOGLE_FOLDER_NAME, self.__google_credentials)
            if not self.__folder_id:
                raise FolderIdError
        self.__PROPERTIES = {}
        self.data = None
        self.objects_in_db = {}

    def replace_category_data(self, cat_id: int):
        pass

    def complete_all_tables(self):
        self._add_categories_data()
        self._add_products_data()
        # self._add_properties_and_values()

    def _add_categories_data(self):
        self.data = add_categories_data(self.__main_url)

    def _add_products_data(self):
        """Добавляет к данным о категоряих данные об их товарах и возвращает полученный список с категориями"""
        # это пиздец нечитаемо, нужно попытаться переработать
        for i in range(len(self.data)):  # range(len(data)):
            print(f'Добавляем данные в раздел {self.data[i]["name"]}\n')
            for j in range(len(self.data[i].get("cats_1"))):
                if len(self.data[i].get("cats_1")[j].get("cats_2")) > 0:
                    for k in range(len(self.data[i].get("cats_1")[j].get("cats_2"))):
                        url = self.__main_url[:-8] + self.data[i].get("cats_1")[j].get("cats_2")[k]['href']
                        cat_id = self.data[i].get("cats_1")[j].get("cats_2")[k]['cat_id']
                        print(f'  Добавляем список с данными о товарах \
внутри категории {self.data[i].get("cats_1")[j].get("cats_2")[k]["name"]}')
                        products_data = self._get_products_data(category_url=url, cat_id=cat_id)
                        self.data[i].get("cats_1")[j].get("cats_2")[k]['products'] = products_data
                else:
                    url = self.__main_url[:-8] + self.data[i].get("cats_1")[j]['href']
                    cat_id = self.data[i].get("cats_1")[j]['cat_id']
                    print(f'  Добавляем список с данными о товарах \
внутри категории {self.data[i].get("cats_1")[j]["name"]}')
                    products_data = self._get_products_data(category_url=url, cat_id=cat_id)
                    self.data[i].get("cats_1")[j]['products'] = products_data

    def _add_properties_and_values(self, products_property_list: list):
        timer = time()
        properties = get_event_loop().run_until_complete(self._add_properties_data(products_property_list))
        print(f'        Добавили {len(properties)} свойств, время выполнения {time() - timer} сек')

    def _get_products_data(self, category_url: str, cat_id: int) -> list:
        """
        Возвращает список с данными о товарах внутри категории.
        category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
        """
        products_data_list, products_properties = get_products_data(category_url,
                                                                    cat_id,
                                                                    self.__folder_id,
                                                                    self.__google_credentials)
        products = []
        for product_id in products_properties:
            products.append(product_id)
        self.objects_in_db[cat_id] = products

        # myloop = new_event_loop()
        # set_event_loop(myloop)
        # myloop.run_until_complete(self._add_properties_data(products_properties))
        run(self._add_properties_data(products_properties))

        return products_data_list

    async def _add_properties_data(self, products_properties: List[dict]):

        if products_properties:
            # try:
            task_list = []
            for product in products_properties:
                for name, value in product['properties'].items():
                    prop_id = self.__PROPERTIES.get(name)
                    if not prop_id:
                        prop_id = add_property_to_db(name)
                        self.__PROPERTIES[name] = prop_id
                    task_list.append(create_task(add_value_to_db(product_id=product['prod_id'],
                                                                 property_id=prop_id,
                                                                 value=value)))
            values_id_list = list(await gather(*task_list))
            print('awaittttttttttttttttttt')
            # except Exception as ex:
            #     print(f'Exception in _add_properties_data\n{ex}')
        else:
            print('Список со свойствами товаров пуст.')


def get_items_data_dict(items_response_list: List[list]) -> Tuple[Dict[int, dict], List[dict]]:
    items_data = {}
    products_data = []
    if items_response_list:
        id_ = 1
        for response in items_response_list:
            data = get_item_data(item_url=response[0], item_response=response[1])
            if data:
                items_data[id_] = data
                id_ += 1
                products_data.append(data)
    return items_data, products_data


async def add_items_to_database(items_data: Dict[int, dict], cat_id: int) -> list:
    products_property_list = []
    if items_data:
        try:
            task_list = [create_task(add_product_to_db(data, cat_id))
                         for item_id, data in items_data.items() if len(data.get('photos')) > 0]
            result_list = list(await gather(*task_list))
        except Exception as ex:
            print(f'Exception - {ex}')
        else:
            for result in result_list:
                if result:
                    products_property_list.append(result)
    return products_property_list


def get_products_data(category_url: str, cat_id: int, folder_id: str, google_credentials: google_auth) -> tuple:
    """
    Возвращает список с данными о товарах внутри категории.
    category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
    """
    loop = new_event_loop()
    set_event_loop(loop)
    try:
        s = time()
        pages_response_list = loop.run_until_complete(
            get_pages_response_list(category_url=category_url))
        # pages_response_list = get_event_loop().run_until_complete(
        #     get_pages_response_list(category_url=category_url))
        print(f'     получили responces {len(pages_response_list)} шт')

        items_url_list = get_items_url_list(pages_response_list[:1])
        print(f'     получили items_urls товаров {len(items_url_list)} шт')

        items_response_list = loop.run_until_complete(get_items_response_list(items_url_list[:2]))
        print(f'     получили response_items товаров {len(items_response_list)} шт')

        # getting products data
        items_data_dict, products_data_list = get_items_data_dict(items_response_list)
        print(f'     Получили данные о {len(products_data_list)} товарах')

        # getting images in bytes
        photos_response_list = loop.run_until_complete(get_photos_response_list(items_data_dict))
        print(f'     Получили {len(photos_response_list)} изображений')

        # uploading images to Google drive and getting their Google File IDs
        count_photos, photos_id_list = get_photos_id_list(photos_response_list, folder_id, google_credentials)
        print(f'     Загрузили {count_photos} изображений в гугл')

        # replacing image URLs in products with Google File IDs
        if photos_id_list:
            for photo in photos_id_list:
                item_id = photo.get('item_id')
                key = photo.get('key')
                fileId = photo.get('fileId')
                if fileId:
                    items_data_dict[item_id]['photos'][key] = fileId
                else:
                    items_data_dict[item_id]['photos'].pop(key)
        else:
            for photo in photos_id_list:
                items_data_dict[photo.get('item_id')]['photos'] = {}

        # adding products data to the database
        products_property_list = loop.run_until_complete(add_items_to_database(items_data_dict, cat_id))
        print(f'     Добавили {len(products_property_list)} товаров в базу')

        return products_data_list, products_property_list
    except Exception as ex:
        print(f'Exception in get_products_data - cat_id: {cat_id}, category_url: {category_url}\n{ex}')
        return [], []
    finally:
        loop.close()


async def get_photos_response_list(items_data: Dict[int, dict]) -> List[dict]:
    photos_response_list = []
    if items_data:
        try:
            async with ClientSession() as session:
                task_list = []
                for item_id, item in items_data.items():
                    for key, url in item['photos'].items():
                        task_list.append(create_task(get_photo(item_id, key, url, session)))
                result_list = list(await gather(*task_list))
        except Exception as ex:
            print(f'Exception - {ex}')
        else:
            photos_response_list += result_list
    return photos_response_list


def add_categories_data(main_url: str) -> List[dict]:
    """Возвращает список с данными(словарями) о категориях"""
    categories_info = []
    category_id_list = []
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


# def _add_products_data(data: List[dict], main_url: str) -> List[dict]:
#     """Добавляет к данным о категоряих данные об их товарах и возвращает полученный список с категориями"""
#     for i in range(len(data)):  # range(len(data)):
#         print(f'Добавляем данные в раздел {data[i]["name"]}\n')
#         for j in range(len(data[i].get("cats_1"))):
#             if len(data[i].get("cats_1")[j].get("cats_2")) > 0:
#                 for k in range(len(data[i].get("cats_1")[j].get("cats_2"))):
#                     url = main_url[:-8] + data[i].get("cats_1")[j].get("cats_2")[k]['href']
#                     cat_id = data[i].get("cats_1")[j].get("cats_2")[k]['cat_id']
#                     print(f'  Добавляем список с данными о товарах \
#                     внутри категории {data[i].get("cats_1")[j].get("cats_2")[k]["name"]}')
#                     data[i].get("cats_1")[j].get("cats_2")[k]['products'] = get_products_data(
#                         category_url=url,
#                         cat_id=cat_id)
#             else:
#                 url = main_url[:-8] + data[i].get("cats_1")[j]['href']
#                 cat_id = data[i].get("cats_1")[j]['cat_id']
#                 print(f'  Добавляем список с данными о товарах \
#                 внутри категории {data[i].get("cats_1")[j]["name"]}')
#                 data[i].get("cats_1")[j]['products'] = get_products_data(category_url=url, cat_id=cat_id)
#     return data


# def _get_products_data(category_url: str, cat_id: int, folder_id: str) -> List[dict]:
#     """
#     Возвращает список с данными о товарах внутри категории.
#     category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
#     """
#     try:
#         s = time()
#         pages_response_list = get_event_loop().run_until_complete(get_pages_response_list(category_url=category_url))
#         print(f'     получили responces {len(pages_response_list)} шт')
#
#         items_url_list = get_items_url_list(pages_response_list[:])
#         print(f'     получили items_urls товаров {len(items_url_list)} шт')
#
#         if items_url_list:
#             items_response_list = get_event_loop().run_until_complete(get_items_response_list(items_url_list[:]))
#             print(f'     получили response_items товаров {len(items_response_list)} шт')
#
#             if items_response_list:
#                 products_data_list = get_event_loop().run_until_complete(
#                     get_items_data(items_response_list, cat_id, folder_id)
#                 )
#                 print(f'     получили products_data {len(products_data_list)} шт, время выполнения {time() - s} сек\n')
#                 return products_data_list
#         return []
#     except Exception as ex:
#         print(f'Exception in get_products_data - cat_id: {cat_id}, category_url: {category_url}\n{ex}')


#######################################################################################

async def get_response_page(url: str, session: ClientSession) -> Union[Any, None]:
    n = 1
    while n <= 5:
        try:
            async with session.get(url) as response:
                result = await response.text()
        except Exception as ex:
            n += 1
            if n > 5:
                print(f'Exception in get_response_page - page_url: {url}\n{ex}')
                return None
        else:
            return result


async def get_pages_response_list(category_url: str) -> list:
    """
    Возвращает список response обьектов со страницами пагинатора внутри категории.
    category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
    """
    pages_response_list = []
    try:
        response_page = get(category_url)
        pages_response_list.append(response_page.text)
        item_html = BS(pages_response_list[0], 'html.parser')
        pagination_list = item_html.select('a.pagination__item')
        if len(pagination_list) == 0:
            return pages_response_list
        else:
            try:
                amount_pages = int(pagination_list[-1].text)
                async with ClientSession() as session:
                    task_list = [create_task(get_response_page(f'{category_url}page-{number_page}',
                                                               session)) for number_page in
                                 range(2, amount_pages + 1)]  ############### range(2, amount_pages + 1)
                    result_list = await gather(*task_list)
            except Exception as ex:
                print(f"Exception - {ex}")
            else:
                for result in result_list:
                    if result:
                        pages_response_list.append(result)
    except Exception as ex:
        pages_response_list.clear()
        print(f"Exception - {ex}")
    return pages_response_list


#######################################################################################


def get_urls(response_page: str) -> Union[List[str], None]:
    try:
        url_list = []
        html = BS(response_page, 'html.parser')
        items = html.select('a.product-card__media')
        if len(items):
            for item in items:
                product = item.get('href')
                url = f"https://viyar.ua{product[:-1]}"
                url_list.append(url)
    except Exception as ex:
        print(f"Exception in get_urls - {ex}")
        return None
    else:
        return url_list


def get_items_url_list(response_page_list: List[str]) -> List[str]:
    """Возвращает список URL адресов всех товаров внутри категории"""
    items_url_list = []
    if response_page_list:
        try:
            with ProcessPoolExecutor() as executor:
                future_list = [executor.submit(get_urls, response_page) for response_page in response_page_list]
                for future in as_completed(future_list):
                    result = future.result()
                    if result:
                        items_url_list += result
        except Exception as ex:
            items_url_list.clear()
            print(f"Exception - {ex}")
    return items_url_list


#######################################################################################


async def get_item_response(item_url: str, session: ClientSession) -> Union[Any, None]:
    """Возвращает response обьект на product_detail"""
    n = 1
    while n <= 5:
        try:
            async with session.get(item_url) as response:
                result = await response.text()
        except Exception as ex:
            n += 1
            if n > 5:
                print(f'Exception in get_item_response - item_url: {item_url}\n{ex}')
                return None
        else:
            break
    return [item_url, result]


async def get_items_response_list(items_url_list: list) -> list:
    """Возвращает список response обьектов на все товары внутри категории"""
    items_response_list = []
    if items_url_list:
        try:
            async with ClientSession() as session:
                task_list = [get_item_response(item_url, session) for item_url in items_url_list]
                result_list = list(await gather(*task_list))
        except Exception as ex:
            print(f'Exception - {ex}')
        else:
            for result in result_list:
                if result:
                    items_response_list.append(result)
    return items_response_list


#######################################################################################


def get_item_data(item_url: str, item_response: str) -> Union[Dict[str, Any], None]:
    """Возвращает данные о товаре"""
    item_data = {}
    try:
        item_html = BS(item_response, 'html.parser')
        item_data['name'] = get_name(item_html)
        item_data['slug'] = get_slug(item_url)
        item_data['description'] = get_description(item_html)
        item_data['price'] = get_price(item_html)
        item_data['properties'] = get_properties(item_html)
        item_data['photos'] = get_photos_urls(item_data['name'], item_html)
    except Exception as ex:
        print(f'Exception - {ex}')
        return None
    else:
        return item_data


# async def get_items_data(items_response_list: list,
#                          cat_id: int,
#                          folder_id: str,
#                          google_credentials: google_auth) -> tuple:
#     """___"""
#
#     # getting products data
#     timer = time()
#     products_data_list = []
#     products_properties = []
#     if items_response_list:
#         items_data = {}
#         try:
#             with ProcessPoolExecutor() as executor:
#                 future_list = [executor.submit(get_item_data,
#                                                item_url=item[0],
#                                                item_response=item[1],
#                                                ) for item in items_response_list]
#                 id_ = 1
#                 for future in as_completed(future_list):
#                     result = future.result()
#                     if result:
#                         items_data[id_] = result
#                         products_data_list.append(result)
#                         id_ += 1
#         except Exception as ex:
#             items_data.clear()
#             print(f'Exception - {ex}')
#         print(f'        Получили данные о {len(items_data)} товарах, время выполнения {time() - timer} сек')
#
#         # getting images in bytes
#         timer = time()
#         photos_response_list = []
#         try:
#             async with ClientSession() as session:
#                 task_list = []
#                 for item_id, item in items_data.items():
#                     for key, url in item['photos'].items():
#                         task_list.append(create_task(get_photo(item_id, key, url, session)))
#                 result_list = list(await gather(*task_list))
#         except Exception as ex:
#             print(f'Exception - {ex}')
#         else:
#             photos_response_list += result_list
#         print(f'        Получили {len(photos_response_list)} изображений, время выполнения {time() - timer} сек')
#
#         # uploading images to Google drive and getting their Google File IDs
#         timer = time()
#         photos_id_list = get_photos_id_list(photos_response_list, folder_id, google_credentials)
#         print(f'        Загрузили {len(photos_id_list)} фоток в гугл, время выполнения {time() - timer} сек')
#
#         # replacing image URLs in products with Google File IDs
#         if photos_id_list:
#             for photo in photos_id_list:
#                 item_id = photo.get('item_id')
#                 key = photo.get('key')
#                 fileId = photo.get('fileId')
#                 if fileId:
#                     items_data[item_id]['photos'][key] = fileId
#                 else:
#                     items_data[item_id]['photos'].pop(key)
#         else:
#             for photo in photos_id_list:
#                 items_data[photo.get('item_id')]['photos'] = {}
#
#         # adding products data to the database
#         timer = time()
#         try:
#             task_list = [create_task(add_product_to_db(data, cat_id))
#                          for item_id, data in items_data.items() if len(data.get('photos')) > 0]
#             result_list = list(await gather(*task_list))
#         except Exception as ex:
#             print(f'Exception - {ex}')
#         else:
#             for result in result_list:
#                 if result:
#                     products_properties.append(result)
#         print(f'        Добавили {len(products_properties)} товаров в базу, время выполнения {time() - timer} сек')
#
#     return products_data_list, products_properties


#######################################################################################


def get_name(item_html: BS) -> str:
    """Возвращает наименование товара"""
    try:
        name = item_html.select('h1.product__title-text')[0].text.strip()
    except Exception:
        return f'Exception {int(time() * 1000)}'
    else:
        return name


def get_slug(item_url: str) -> str:
    try:
        slug = item_url.split('/')[-1]
    except Exception:
        return f'exception_{int(time() * 1000)}'
    else:
        return slug


def get_description(item_html: BS) -> Union[str, None]:
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


#######################################################################################





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
    data = {'item_id': item_id, 'key': key, "name": url.split('/')[-1], "photo": None}
    n = 1
    while n <= 5:
        try:
            async with session.get(url) as response:
                photo = await response.read()
        except Exception as ex:
            n += 1
            if n > 5:
                print(f'Exception in get_photo - item_id: {item_id}, key: {key}, url: {url}\n{ex}')
                break
        else:
            data['photo'] = photo
            break
    return data


if __name__ == '__main__':
    # url = 'https://viyar.ua/catalog/dvoiarusne_lizhko'
    # resp = get(url).text
    # google_credentials = google_auth()
    # result = get_item_data(item_url=url, item_response=resp, google_credentials=google_credentials)
    # print(result)
    clear_all_tables()
    parser = Parser().complete_all_tables()

    # creds = google_auth()
    # folder_name = f'django_shop.catalog.images {datetime.now()}'
    # # folder_name = 'test_folder'
    # folder_id = search_folder(folder_name, creds)
    # if not folder_id:
    #     folder_id = create_folder(folder_name, creds)
    # PRODUCTS_PROPERTIES = []
    # category_url = 'https://viyar.ua/catalog/petli/'
    #
    # PRODUCTS_PROPERTIES += get_products_data(category_url=category_url, cat_id=1113, folder_id=folder_id)
    # timer = time()
    # properties = get_event_loop().run_until_complete(add_properties_data())
    # print(f'        Добавили {len(properties)} свойств, время выполнения {time() - timer} сек')

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
