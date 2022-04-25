from utils import *
import time

# data_products = DataProducts('catalog_vijar')
name_category = 'metiznaya_produktsiya'
path = 'products_data/'
data = []
page = 1
timer = time.time()
while page <= 12:
    category_list = requests.get(f'https://viyar.ua/catalog/{name_category}/page-' + str(page))
    html = BS(category_list.content, 'html.parser')
    items = html.select('.product_prewiew')
    if len(items):
        start = time.time()

        data += add_page_data(items, path)
        print(data)

        print(f"page {page} added\n")
        page += 1
        print(f"Время выполнения - {time.time()-start}")
    else:
        break

print(f"Время выполнения - {time.time()-timer}")

# data_products.add_data(name_category, data)
# print(data_products.get_data())

