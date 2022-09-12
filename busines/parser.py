from random import choice
from typing import Optional, Dict, Any, List, Union
from time import time

from bs4 import BeautifulSoup as BS

from .interfaces import ParserInterface


class HTMLParser(ParserInterface):

    @classmethod
    def get_item_data(cls, item_url: str, item_response: str) -> Optional[Dict[str, Any]]:
        """Возвращает данные о товаре"""
        item_data = {}
        try:
            soup_item = BS(item_response, 'html.parser')
            item_data['name'] = cls._get_name(soup_item)
            item_data['slug'] = cls._get_slug(item_url)
            item_data['description'] = cls._get_description(soup_item)
            item_data['price'] = cls._get_price(soup_item)
            item_data['properties'] = cls._get_properties(soup_item)
            item_data['photos'] = cls._get_photos_urls(item_data['name'], soup_item)
        except Exception as ex:
            print(f'Exception in HTMLParser.get_item_data - {ex}')
            return None
        else:
            return item_data

    @staticmethod
    def get_categories_data(response: bytes, main_url: str) -> List[Dict[str, Union[str, list]]]:

        categories_data = []
        html_page = BS(response, 'html.parser')
        item_0_list = html_page.select('.dropdown__list-item_lev1')

        for item_0 in item_0_list[:8]:  # item_0_list[:8] #####################
            cat_0_name = item_0.select('a > .text')[0].text
            cat_0_slug = item_0.select('a')[0].get('href').split('/')[-2]
            if cat_0_name in ['Фасады', 'Фасади']:
                continue
            else:
                cat_0 = {'name': cat_0_name,
                         'slug': cat_0_slug}

                cat_0_childrens = item_0.select('.li_lev2')
                for item_1 in cat_0_childrens[:]:  # cat_0_childrens[:] #####################
                    links_1 = item_1.find_all('a')
                    cat_1_name = links_1[0].text.strip()
                    if cat_1_name in ['Мойки из искусственного камня  Belterno', 'Мийки зі штучного каменю  Belterno']:
                        continue
                    else:
                        href_list_1 = links_1[0]["href"].split("/")
                        href = f'/{href_list_1[-3]}/{href_list_1[-2]}/'
                        cat_1 = {'name': cat_1_name,
                                 'slug': href.split('/')[-2],
                                 'url': main_url[:-8] + href}

                        cat_1_childrens = item_1.select('.dropdown__list-item')
                        if len(cat_1_childrens) > 0:
                            for item_2 in cat_1_childrens[:]:  # cat_1_childrens[:] #####################
                                links_2 = item_2.find_all('a')
                                cat_2_name = links_2[0].text.strip()
                                href_list_2 = links_2[0]["href"].split("/")
                                href = f'/{href_list_2[-3]}/{href_list_2[-2]}/'
                                cat_2 = {'name': cat_2_name,
                                         'slug': href.split('/')[-2],
                                         'url': main_url[:-8] + href}
                                if cat_1.get('childrens'):
                                    cat_1['childrens'].append(cat_2)
                                else:
                                    cat_1['childrens'] = [cat_2]
                        if cat_0.get('childrens'):
                            cat_0['childrens'].append(cat_1)
                        else:
                            cat_0['childrens'] = [cat_1]
                categories_data.append(cat_0)
        return categories_data

    @staticmethod
    def get_amount_pages(response_page: str) -> int:
        try:
            soup_item = BS(response_page, 'html.parser')
            pagination_list = soup_item.select('a.pagination__item')
            if len(pagination_list) == 0:
                return 0
            else:
                return int(pagination_list[-1].text)
        except Exception as ex:
            print(f'Exception in HTMLParser.get_amount_pages - {ex}')
            return 0

    @staticmethod
    def get_items_urls(response_page: str) -> Optional[List[str]]:
        try:
            url_list = []
            soup_item = BS(response_page, 'html.parser')
            items = soup_item.select('a.product-card__media')
            if len(items):
                for item in items:
                    product = item.get('href')
                    url = f"https://viyar.ua{product[:-1]}"
                    url_list.append(url)
        except Exception as ex:
            print(f'Exception in HTMLParser.get_items_urls - {ex}')
            return None
        else:
            return url_list

    @staticmethod
    def _get_name(soup_item: BS) -> str:
        """Возвращает наименование товара"""
        try:
            name = soup_item.select('h1.product__title-text')[0].text.strip()
        except Exception:
            return f'Exception {int(time() * 1000)}'
        else:
            return name

    @staticmethod
    def _get_slug(item_url: str) -> str:
        try:
            slug = item_url.split('/')[-1]
        except Exception:
            return f'exception_{int(time() * 1000)}'
        else:
            return slug

    @staticmethod
    def _get_description(soup_item: BS) -> Optional[str]:
        try:
            info = soup_item.select(
                'div.product-info__content--description > .product-info__content-section > .text > p')
            if info:
                description = ''
                for paragraph in info:
                    description += paragraph.text.strip() + ' '
                return description
            else:
                return None
        except Exception:
            return None

    @staticmethod
    def _get_price(soup_item: BS) -> float:
        """Возвращает стоимость товара за единицу"""
        try:
            try:
                price = float(soup_item.select('span.product-price__price')[0].text.strip())
            except ValueError:
                price = ''
                list_p = soup_item.select('span.product-price__price')[0].text.strip().split()
                for i in list_p:
                    price += i
                price = float(price)
        except Exception as ex:
            print(f'Exception in get_price - {ex}')
            return float(choice(range(1700, 2500, 3)))
        else:
            return price

    @staticmethod
    def _get_properties(soup_item: BS) -> Dict[str, str]:
        """Возвращает характеристики товара"""
        properties = {}
        prop_list = soup_item.select('div.product-info__content-substatus')
        try:
            for property in prop_list:
                property_name = property.select('div.product-info__content-substatus-name')[0].text.strip(':')
                property_value = property.select('div.text')[0].text.strip()
                properties[property_name] = property_value
        except Exception as ex:
            properties[f'Exception - {ex}'] = 'свойства не добавлены'
        return properties

    @staticmethod
    def _get_photos_urls(name: str, soup_item: BS) -> Dict[str, str]:
        """Возвращает список url адресов фотографий товара"""
        photos_url_dict = {}
        try:
            list_ = soup_item.select('div.product-demo__body > ul > li')
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
