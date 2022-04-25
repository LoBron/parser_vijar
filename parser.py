import random

from utils import *
import multiprocessing
import time

# data_products = DataProducts('catalog_vijar')
name_category = 'metiznaya_produktsiya'
path = 'products_data/'
data = []
page = 1
timer = time.time()
pages = 12 #12
amount_processor_cores = 4
#########################################################################################################################

timer_0 = time.time()
response_page_list = get_category_pages(name_category, pages)
print('список страниц добавлен')
print(f"0) время выполнения - {time.time() - timer_0}\n")
########################################################################################################################

# sequence = 6, 8, 10, 12
# d = {f'{i} процессов': [] for i in sequence}
# for i in range(40):
#     timer_1 = time.time()
#     n = random.choice(sequence)
#     with concurrent.futures.ThreadPoolExecutor(max_workers=number_processor_cores*2) as executor:
#         future_list = [executor.submit(get_category_page, name_category, page) for page in range(1, pages+1)]
#         for future in concurrent.futures.as_completed(future_list):
#             response_page_list.append(future.result())
#         d[f'{n} процессов'].append(time.time()-timer_1)
#         print(f"{i} Итерация, время выполнения - {time.time() - timer_1}")
#
# # d = {'sdfdsfsd': [121, 2323, 433, 5445, 45]}
# for j in d.items():
#     print(f'{j[0]} -- вызовов: {len(j[1])} шт -- среднее значение: {sum(j[1])/len(j[1])} сек')

########################################################################################################################

timer_1 = time.time()
items_list = get_items_hrefs(response_page_list)
print(items_list)
print(f"1) время выполнения - {time.time() - timer_1}\n")
########################################################################################################################

timer_2 = time.time()
response_items = get_items_pages(items_list)
print(response_items)
print(f"2) время выполнения - {time.time() - timer_2}\n")

########################################################################################################################

timer_3 = time.time()
data = add_items_data(response_items, path)
print(data)
print(f"3) время выполнения - {time.time() - timer_3}\n")

########################################################################################################################
print(f"время скачивания данных - {time.time() - timer}")