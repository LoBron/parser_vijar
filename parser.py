import random
import multiprocessing
from utils import *
# import time
#
# categories = {'nozhki_roliki_opory': 3} #'metiznaya_produktsiya': 4,
# path = 'products_data/'
#
# class ParserVijar:
#
#     def __init__(self, categories, path):
#         self.__data = {}
#         self.categories = categories
#         self.path = path
#
#     def set_data(self):
#         for name_category, pages in self.categories.items():
#             response_page_list = get_category_pages(name_category, pages)
#             print('получили страницы')
#             items_list = get_items_hrefs(response_page_list)
#             print('получили urls обьектов')
#             response_items = get_items_pages(items_list)
#             print('получили страницы обьектов')
#             self.data[name_category] = add_items_data(response_items, self.path)
#             print('добавили данные')
#
#     def get_data(self, category=None):
#         if category:
#             return self.__data.get(category)
#         else:
#             return self.__data

# data = ParserVijar(categories, path)
# data.set_data()
# print(data.get_data('nozhki_roliki_opory'))


# path = 'products_data/'
# a = requests.get('https://viyar.ua/catalog/kronospan_0301_su_kapuchino_2800kh2070kh18_mm/')
# print(add_item_data(a, path))


main_url = 'https://viyar.ua'
path = 'products_data/'

data = get_categories_info(main_url)
print(add_products_data(data, main_url, path))


# def add_items_data(response_items, path):
#     """https://docs.python.org/3.8/library/concurrent.futures.html#threadpoolexecutor"""
#     items_data = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
#         future_list = [executor.submit(add_item_data, response_item, path) for response_item in response_items]
#         for future in concurrent.futures.as_completed(future_list):
#             items_data.append(future.result())
#     return items_data

# def azaza(asd):
#     l = []
#     for i in range(1, asd):
#         for j in range(1, asd):
#             l.append(i*j)
#     return sum(l)
#
# items_data = [random.choice(range(100,300,10)) for i in range(10)]
# if __name__ == '__main__':
#     start = time.time()
#     items_data = [random.choice(range(100,300,10)) for i in range(100)]
#     with multiprocessing.Pool(processes=4) as pool:
#         print(pool.map(azaza, items_data))
#     print(time.time()-start)

# start = time.time()
# l = []
# for item in items_data:
#     l.append(azaza(item))
# print(l)
# print(time.time()-start)