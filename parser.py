
import requests
from bs4 import BeautifulSoup as BS
from utils import DataProducts, download_img

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

            name = html_item.select('.product_name > h1 > b')[0].text.strip()
            object_data['name'] = name

            price = float(html_item.select('span.price')[0].text.strip())
            object_data['price'] = price

            properties = {}
            prop = html_item.select('div.charakters > ul.properties > li')
            n = 1
            for property in prop:
                if n <= len(prop)/2:
                    property = property.text.split(': ')
                    properties[property[0]] = property[1]
                    n += 1
                else:
                    break
            object_data['properties'] = properties

            def get_photo(name, n, html_item, path):

                if n == 1:
                    photo = html_item.find_all('img', alt=name)
                else:
                    photo = html_item.find_all('img', alt=name+' — фото'+str(n))
                photo_url = f"https://viyar.ua{photo[0].get('src')}"

                photos[f"photo{n}"] = photo_url
                root = f"{path}\{photo_url.split('/')[-1]}"
                download_img(photo_url, root)
                print(f'фото №{n} загружено')
                return

            photos = {}
            for n in range(1, 5):
                try:
                    get_photo(name, n, html_item, path)
                except IndexError:
                    break
                # try:
                #     if n == 1:
                #         photo = html_item.find_all('img', alt=name)
                #     else:
                #         photo = html_item.find_all('img', alt=name+' — фото'+str(n))
                #     photo_url = f"https://viyar.ua{photo[0].get('src')}"
                # except IndexError:
                #     break
                # photos[f"photo{n}"] = photo_url
                # root = f"{path}\{photo_url.split('/')[-1]}"
                # download_img(photo_url, root)

            object_data['photos'] = photos

            data.append(object_data)
            print(object_data)
            print(f"object '{name}' added")

        print(f"page {page} added\n")
        page += 1
    else:
        break

data_products.add_data(name_category, data)
print(data_products.get_data())

