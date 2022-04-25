import random
from utils import *
import time

categories = {'nozhki_roliki_opory': 27} #'metiznaya_produktsiya': 4,
path = 'products_data/'

class ParserVijar:

    def __init__(self):
        self.data = {}
        self.path = path
        self.categories = categories

    def add_data(self):
        for name_category, pages in categories.items():
            response_page_list = get_category_pages(name_category, pages)
            print('получили страницы')
            items_list = get_items_hrefs(response_page_list)
            print('получили urls обьектов')
            response_items = get_items_pages(items_list)
            print('получили страницы обьектов')
            self.data[name_category] = add_items_data(response_items, path)
            print('добавили данные')

    def get_data(self, category=None):
        if category:
            return self.data.get(category)
        else:
            return self.data

data = ParserVijar(categories, path)
data.add_data()
print(data.get_data('nozhki_roliki_opory'))
