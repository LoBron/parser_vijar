from random import choice
from typing import Optional, Dict, Any, List
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
