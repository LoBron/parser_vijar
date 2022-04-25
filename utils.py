import threading
import concurrent.futures


import requests
from bs4 import BeautifulSoup as BS

def get_items_hrefs(response_page_list):
    items_hrefs = []
    for response_page in response_page_list:
        html = BS(response_page.content, 'html.parser')
        items = html.select('.product_prewiew')
        if len(items):
            for item in items:
                product = item.select('a')
                items_hrefs.append(f"https://viyar.ua{product[0].get('href')}")
    return items_hrefs

def add_items_data(response_items, path):
    """https://docs.python.org/3.8/library/concurrent.futures.html#threadpoolexecutor"""
    items_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_list = [executor.submit(add_item_data, response_item, path) for response_item in response_items]
        for future in concurrent.futures.as_completed(future_list):
            items_data.append(future.result())
    return items_data

def add_item_data(response_item, path):
    """Возвращает данные о товаре и загружает его фотографии"""
    item_data = {}
    item = BS(response_item.content, 'html.parser')
    item_data['name'] = get_name(item)
    item_data['price'] = get_price(item)
    item_data['properties'] = get_properties(item)
    item_data['photos'] = get_photos(item_data['name'], item)
    download_photos(item_data.get('photos'), path)
    # print(f"object '{object_data['name']}' added")
    return item_data


def get_item_page(item_href):
    return requests.get(item_href)

def get_items_pages(items_list, amount_processor_cores):
    items_pages = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=amount_processor_cores*2) as executor:
        future_list = [executor.submit(get_item_page, item) for item in items_list]
        for future in concurrent.futures.as_completed(future_list):
            items_pages.append(future.result())
    return items_pages



# class DataProducts:
#     def __init__(self, name):
#         self.name = name
#         self.data = {}
#
#     def add_data(self, name_category, data):
#         self.data[name_category] = data
#
#     def get_data(self, name_category=None):
#         if name_category:
#             return self.data.get(name_category)
#         else:
#             return self.data

# def add_page_data(items, path):
#     """https://docs.python.org/3.8/library/concurrent.futures.html#threadpoolexecutor"""
#     page = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#         future_to_item = [executor.submit(add_item_data, item, path) for item in items]
#         for future in concurrent.futures.as_completed(future_to_item):
#             page.append(future.result())
#     return page

# def add_item_data(item, path):
#     """Возвращает данные о товаре и загружает его фотографии"""
#     object_data = {}
#
#     product = item.select('a')
#     href_product = f"https://viyar.ua{product[0].get('href')}"
#     product_detail = requests.get(href_product)
#     html_item = BS(product_detail.content, 'html.parser')
#     object_data['name'] = get_name(html_item)
#     object_data['price'] = get_price(html_item)
#     object_data['properties'] = get_properties(html_item)
#     object_data['photos'] = get_photos(object_data['name'], html_item)
#     download_photos(object_data.get('photos'), path)
#     # print(f"object '{object_data['name']}' added")
#     return object_data

def get_name(html_item):
    """Возвращает наименование товара"""
    name = html_item.select('.product_name > h1 > b')[0].text.strip()
    return name

def get_price(html_item):
    """Возвращает стоимость товара за единицу"""
    price = float(html_item.select('span.price')[0].text.strip())
    return price

def get_properties(html_item):
    """Возвращает характеристики товара"""
    properties = {}
    prop_list = html_item.select('div.charakters > ul.properties > li')
    n = 1
    for prop in prop_list:
        if n <= len(prop_list) / 2:
            property = prop.text.split(': ')
            properties[property[0]] = property[1]
            n += 1
        else:
            break
    return properties

def get_photos(name, html_item):
    """Возвращает url адреса фотографий"""
    photos = []
    for n in range(1, 5):
        try:
            if n == 1:
                photo = html_item.find_all('img', alt=name)
            else:
                photo = html_item.find_all('img', alt=name + ' — фото' + str(n))
            photo_url = f"https://viyar.ua{photo[0].get('src')}"
            photos.append(photo_url)
        except IndexError:
            break
    return photos

def download_photos(kwargs, path):
    """Запускает потоки и загружает в них фотографии"""
    if kwargs:
        # n = 1
        for img_url in kwargs:
            threading.Thread(target=download_img, args=(img_url, path)).start()
            # threading.Thread(target=download_img, args=(img_url, path, n), name=f'thr-{n}').start()
            # n += 1

def download_img(url, path):
    """Загружает фотографию"""
    root = path + url.split('/')[-1]
    p = requests.get(url)
    img = open(root, "wb")
    img.write(p.content)
    img.close()
    # print(f"Загружено фото {n}")