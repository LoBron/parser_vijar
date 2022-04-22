from bs4 import BeautifulSoup as BS
from utils import *

data_products = DataProducts('catalog_vijar')
name_category = 'metiznaya_produktsiya'
path = 'products_data'
data = []
page = 1

while True:
    category_list = requests.get(f'https://viyar.ua/catalog/{name_category}/page-' + str(page))
    html = BS(category_list.content, 'html.parser')
    items = html.select('.product_prewiew')
    if len(items):
        for item in items:
            object_data = {}

            product = item.select('a')
            href_product = f"https://viyar.ua{product[0].get('href')}"
            product_detail = requests.get(href_product)
            html_item = BS(product_detail.content, 'html.parser')

            object_data['name'] = get_name(html_item)

            object_data['price'] = get_price(html_item)

            object_data['properties'] = get_properties(html_item)

            object_data['photos'] = get_photos(object_data['name'], html_item)

            download_photos(object_data.get('photos'), path)

            data.append(object_data)
            print(f"object '{object_data['name']}' added")

        print(f"page {page} added\n")
        page += 1
    else:
        break

data_products.add_data(name_category, data)
# print(data_products.get_data())

