from asyncio import create_task, gather, run, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from concurrent.futures import as_completed, ThreadPoolExecutor
from decimal import Decimal, ROUND_UP
from io import BytesIO
from time import time
from typing import List, Dict, Tuple

from .parser import HTMLParser
from .interfaces import CreatorInterface, UpdaterInterface, ParserInterface

from servises import *
from persistence import *

from settings import MAIN_URL


class Core:
    """здарова ёпта"""

    def __init__(self,
                 google_worker: GoogleWorkerInterface = GoogleWorker(),
                 db_worker: DbWorkerInterface = DbWorker(),
                 io_loader: IoLoaderInterface = IoLoader(),
                 html_parser: ParserInterface = HTMLParser(),
                 ):
        self.__main_url = MAIN_URL
        self.__google_worker = google_worker
        self.__db_worker = db_worker
        self.__io_loader = io_loader
        self.__html_parser = html_parser
        self.__CATEGORIES = []
        self.__PRODUCTS = []
        self.__PROPERTIES = {}
        self.__VALUES = []
        self.objects_in_db = {}
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    def add_categories_data(self) -> None:
        """Возвращает список с данными(словарями) о категориях"""
        response_obj = self.__io_loader.get_item_response(self.__main_url)
        html_page = BS(response_obj.content, 'html.parser')
        item_0_list = html_page.select('.dropdown__list-item_lev1')

        for item_0 in item_0_list[:8]:  # item_0_list[:8] #####################
            cat_0_name = item_0.select('a > .text')[0].text
            cat_0_slug = item_0.select('a')[0].get('href').split('/')[-2]
            if cat_0_name in ['Фасады', 'Фасади']:
                continue
            else:
                name = cat_0_name
                slug = cat_0_slug
                cat_0_childrens = item_0.select('.li_lev2')
                category = Category(name=name,
                                    slug=slug,
                                    have_childrens=True if len(cat_0_childrens) > 0 else False)
                cat_id_0 = self.__db_worker.add_category_to_db(category)
                category.id = cat_id_0
                self.__CATEGORIES.append(category)

                for item_1 in cat_0_childrens[:]:  # cat_0_childrens[:] #####################
                    links_1 = item_1.find_all('a')
                    name = links_1[0].text.strip()
                    if name in ['Мойки из искусственного камня  Belterno', 'Мийки зі штучного каменю  Belterno']:
                        continue
                    else:
                        href_list_1 = links_1[0]["href"].split("/")
                        href = f'/{href_list_1[-3]}/{href_list_1[-2]}/'
                        url = self.__main_url[:-8] + href
                        slug = href.split('/')[-2]
                        cat_1_childrens = item_1.select('.dropdown__list-item')
                        category = Category(name=name,
                                            slug=slug,
                                            parent_id=cat_id_0,
                                            have_childrens=True if len(cat_1_childrens) > 0 else False,
                                            url=url)
                        cat_id_1 = self.__db_worker.add_category_to_db(category)
                        category.id = cat_id_1
                        self.__CATEGORIES.append(category)

                        if len(cat_1_childrens) > 0:
                            for item_2 in cat_1_childrens[:]:  # cat_1_childrens[:] #####################
                                links_2 = item_2.find_all('a')
                                name = links_2[0].text.strip()
                                href_list_2 = links_2[0]["href"].split("/")
                                href = f'/{href_list_2[-3]}/{href_list_2[-2]}/'
                                url = self.__main_url[:-8] + href
                                slug = href.split('/')[-2]
                                category = Category(name=name,
                                                    slug=slug,
                                                    parent_id=cat_id_1,
                                                    url=url)
                                cat_id_2 = self.__db_worker.add_category_to_db(category)
                                category.id = cat_id_2
                                self.__CATEGORIES.append(category)
        print(f'\nCписок с данными о {len(self.__CATEGORIES)} категориях создан\n')

    def add_products_data(self) -> None:
        """Добавляет к данным о категоряих данные об их товарах и возвращает полученный список с категориями"""
        for category in self.__CATEGORIES:
            if not category.have_childrens:
                category_url = category.url
                if category_url:
                    print(f'  Добавляем список с данными о товарах внутри категории {category.name}')
                    products_data_list, products_properties = self._get_products_data(category_url, category.id)

                    products = []
                    for product in products_properties:
                        products.append(product.get('product_id'))
                    self.objects_in_db[category.id] = products

                    run(self._add_properties_data(products_properties))

    async def _add_properties_data(self, products_properties: List[dict]) -> None:
        count_properties = 0
        count_values = 0
        if products_properties:
            try:
                task_list = []
                for product in products_properties:
                    for name, value in product['properties'].items():
                        prop_id = self.__PROPERTIES.get(name)
                        if not prop_id:
                            prop_id = self.__db_worker.add_property_to_db(name)
                            self.__PROPERTIES[name] = prop_id
                            count_properties += 1
                        task_list.append(create_task(
                            self.__db_worker.add_value_to_db(PropertyValue(product_id=product.get('product_id'),
                                                                           property_id=prop_id,
                                                                           value=value))))
                result_list = list(await gather(*task_list))
            except Exception as ex:
                print(f'Exception in _add_properties_data\n{ex}')
            else:
                for result in result_list:
                    if result:
                        self.__VALUES.append(result)
                        count_values += 1
        print(f'     Добавили {count_properties} свойств, {count_values} значений в базу')

    def _get_products_data(self, category_url: str, cat_id: int) -> tuple:
        """
        Возвращает список с данными о товарах внутри категории.
        category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
        """
        try:
            s = time()
            pages_response_list = self._get_pages_response_list(category_url=category_url)
            print(f'     получили responces {len(pages_response_list)} шт')

            products_url_list = self._get_items_url_list(pages_response_list[:])
            print(f'     получили items_urls товаров {len(products_url_list)} шт')

            products_response_list = self._get_items_responses(products_url_list[:])
            print(f'     получили response_items товаров {len(products_response_list)} шт')

            # getting products data
            products_data_dict, products_data_list = self._get_items_data(products_response_list)
            print(f'     Получили данные о {len(products_data_list)} товарах')

            # getting images in bytes
            count_responses, photos_response_list = self._get_photos_response_list(products_data_dict)
            print(f'     Получили {count_responses} изображений')

            # uploading images to Google drive and getting their Google File IDs
            count_photos, photos_id_list = self._get_photos_id_list(photos_response_list)
            print(f'     Загрузили {count_photos} изображений в гугл')

            # replacing image URLs in products with Google File IDs
            if photos_id_list:
                for photo in photos_id_list:
                    item_id = photo.get('item_id')
                    key = photo.get('key')
                    fileId = photo.get('fileId')
                    if fileId:
                        products_data_dict[item_id]['photos'][key] = fileId
                    else:
                        products_data_dict[item_id]['photos'].pop(key)
            else:
                for photo in photos_id_list:
                    products_data_dict[photo.get('item_id')]['photos'] = {}

            # adding products data to the servises
            products_property_list = run(self._add_items_to_database(products_data_dict, cat_id))
            print(f'     Добавили {len(products_property_list)} товаров в базу')

            return products_data_list, products_property_list
        except Exception as ex:
            print(f'Exception in get_products_data - cat_id: {cat_id}, category_url: {category_url}\n{ex}')
            return [], []

    def _get_pages_response_list(self, category_url: str) -> list:
        """
        Возвращает список response обьектов со страницами пагинатора внутри категории.
        category_url format - 'https://viyar.ua/catalog/ruchki_mebelnye/'
        """
        pages_response_list = []
        try:
            response_page = self.__io_loader.get_item_response(category_url).text
            pages_response_list.append(response_page)
            amount_pages = self.__html_parser.get_amount_pages(response_page)
            if amount_pages == 0:
                return pages_response_list
            else:
                urls = {}
                key = 1
                for number_page in range(2, amount_pages + 1):  # range(2, amount_pages + 1):
                    urls[key] = f'{category_url}page-{number_page}'
                    key += 1
                responses = self.__io_loader.get_html_responses(urls)
                for resp in responses.values():
                    if resp[1]:
                        pages_response_list.append(resp[1])
        except Exception as ex:
            pages_response_list.clear()
            print(f"Exception in _get_pages_response_list - {ex}")
        return pages_response_list

    def _get_photos_response_list(self, items_data: Dict[int, dict]) -> Tuple[int, List[dict]]:
        photos_response_list = []
        counter = 0
        if items_data:
            try:
                urls = {}
                c = 1
                for item_id, item in items_data.items():
                    for key, url in item['photos'].items():
                        photos_response_list.append({'id': c, 'item_id': item_id, 'key': key, 'url': url})
                        urls[c] = url
                        c += 1
                result_dict = self.__io_loader.get_bytes_responses(urls)
            except Exception as ex:
                print(f'Exception in _get_photos_response_list - Error: {ex}')
            else:
                for i in range(len(photos_response_list)):
                    id_ = photos_response_list[i].pop('id')
                    ___, photo = result_dict.get(id_)
                    photos_response_list[i]['photo'] = photo
                    if photo:
                        counter += 1
        return counter, photos_response_list

    def _get_photos_id_list(self, photos_response_list: List[dict]) -> tuple:
        photos_id_list = []
        counter = 0
        if photos_response_list:
            try:
                images = []
                c = 1
                for photo_data in photos_response_list:
                    photos_id_list.append({'id': c,
                                           'item_id': photo_data.get('item_id'),
                                           'key': photo_data.get('key')})
                    if photo_data.get('photo'):
                        image = File(data=BytesIO(photo_data.get('photo')),
                                     name=photo_data.get('url').split('/')[-1][:-4],
                                     mimetype='image/jpg')
                        images.append([c, image])
                    c += 1
                result_dict = {}
                with ThreadPoolExecutor(max_workers=30) as executor:
                    future_list = [executor.submit(self.__google_worker.upload_file,
                                                   image[0],
                                                   image[1]
                                                   ) for image in images]
                    for future in as_completed(future_list):
                        result_dict.update(future.result())
            except Exception as ex:
                for i in range(len(photos_id_list)):
                    photos_id_list[i].pop('id')
                    photos_id_list[i]['fileId'] = None
                print(f'Exception in _get_photos_id_list - Error: {ex}')
            else:
                for i in range(len(photos_id_list)):
                    id_ = photos_id_list[i].pop('id')
                    photo_id = result_dict.get(id_)
                    photos_id_list[i]['fileId'] = photo_id
                    if photo_id:
                        counter += 1

        return counter, photos_id_list

    async def _add_items_to_database(self, items_data: Dict[int, dict], cat_id: int) -> list:
        products_property_list = []
        if items_data:
            try:
                task_list = []
                key = 1
                for item in items_data.values():
                    if len(item.get('photos')) > 0 and item.get('photos').get('photo1'):
                        product = Product(category_id=cat_id,
                                          name=item.get('name'),
                                          slug=item.get('slug'),
                                          description=item.get('description'),
                                          price=Decimal(item.get('price')).quantize(Decimal('.01'),
                                                                                    rounding=ROUND_UP),
                                          photo1=item.get('photos').get('photo1'),
                                          photo2=item.get('photos').get('photo2'),
                                          photo3=item.get('photos').get('photo3'),
                                          photo4=item.get('photos').get('photo4'))
                        products_property_list.append({'key': key,
                                                       'properties': item.get('properties'),
                                                       'product': product})
                        task_list.append(create_task(self.__db_worker.add_product_to_db(key, product)))
                        key += 1
                result_list = list(await gather(*task_list))
            except Exception as ex:
                print(f'Exception in _add_items_to_database - cat_id: {cat_id}\n{ex}')
            else:
                result_data = {}
                for result in result_list:
                    result_data.update(result)
                for i in range(len(products_property_list)):
                    key = products_property_list[i].pop('key')
                    product_id = result_data.get(key)
                    if product_id:
                        products_property_list[i]['product_id'] = product_id
                        products_property_list[i].get('product').id = product_id
                        self.__PRODUCTS.append(products_property_list[i].pop('product'))
                    else:
                        products_property_list.pop(i)
        return products_property_list

    def _get_items_responses(self, products_url_list: List[str]) -> List[list]:
        items_responses = []
        if products_url_list:
            try:
                urls_dict = {}
                for key in range(len(products_url_list)):
                    urls_dict[key] = products_url_list[key]
                result = self.__io_loader.get_bytes_responses(urls_dict)
            except Exception as ex:
                print(f'Exception in _get_items_responses - Error: {ex}')
            else:
                for response in result.values():
                    items_responses.append(response)
        return items_responses

    def _get_items_data(self, items_response_list: List[list]) -> Tuple[Dict[int, dict], List[dict]]:
        items_data = {}
        products_data = []
        if items_response_list:
            id_ = 1
            for response in items_response_list:
                data = self.__html_parser.get_item_data(item_url=response[0], item_response=response[1])
                if data:
                    items_data[id_] = data
                    id_ += 1
                    products_data.append(data)
        return items_data, products_data

    ######################################################################################

    def _get_items_url_list(self, response_page_list: List[str]) -> List[str]:
        """Возвращает список URL адресов всех товаров внутри категории"""
        items_url_list = []
        if response_page_list:
            try:
                for response_page in response_page_list:
                    urls = self.__html_parser.get_items_urls(response_page)
                    if urls:
                        items_url_list += urls
            except Exception as ex:
                items_url_list.clear()
                print(f"Exception in get_items_url_list - {ex}")
        return items_url_list


class Creator(CreatorInterface, Core):

    def create_all_data(self) -> Dict[int, List[int]]:
        self.__db_worker.clear_all_tables()
        self.add_categories_data()
        self.add_products_data()
        return self.objects_in_db


class Updater(UpdaterInterface, Core):

    def update_data_in_category(self, cat_id: int):
        pass

# if __name__ == '__main__':
