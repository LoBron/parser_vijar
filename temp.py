import concurrent.futures
import random
import threading
import time
import requests
from bs4 import BeautifulSoup as BS
def get_response_pages(category_url):
    """Возвращает список response обьектов со страницами пагинатора внутри категории"""
    response_page_list = []
    n = 1
    while True:
        response_page = requests.get(f'{category_url}page-{n}/')
        if response_page.status_code == 200: #in range(200, 207):   #####################
            response_page_list.append(response_page)
            # print(f'страница {n} добавлена')
            n += 1
        else:
            break
    return response_page_list

def get_response_pages1(category_url):
    """Возвращает список response обьектов со страницами пагинатора внутри категории"""
    response_page_list = []
    r_page = requests.get(f'{category_url}')
    response_page_list.append(r_page)
    item_html = BS(r_page.content, 'html.parser')
    l = item_html.select('.paggination > li')
    if 0 <= len(l) <= 2:
        return response_page_list
    else:
        n = int(l[-2].text)
    for i in range(2, n+1):
        response_page = requests.get(f'{category_url}page-{i}/')
        response_page_list.append(response_page)
    return response_page_list

def get_response_page(category_url, number_page):
    return requests.get(f'{category_url}page-{number_page}/')

def get_response_pages2(category_url):
    """Возвращает список response обьектов со страницами пагинатора внутри категории"""
    response_page_list = []
    response_page = requests.get(f'{category_url}')
    response_page_list.append(response_page)
    item_html = BS(response_page.content, 'html.parser')
    paggination_list = item_html.select('.paggination > li')
    if 0 <= len(paggination_list) <= 2:
        return response_page_list
    else:
        n = int(paggination_list[-2].text)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_list = [executor.submit(get_response_page, category_url, i) for i in range(2, n+1)]
        for future in concurrent.futures.as_completed(future_list):
            response_page_list.append(future.result())
    return response_page_list

def get_items_urls(response_page_list):
    """Возвращает список URL адресов всех товаров внутри категории"""
    items_url_list = []
    if len(response_page_list) > 0:
        for response_page in response_page_list:
            html = BS(response_page.content, 'html.parser')
            items = html.select('.product_prewiew')
            if len(items):
                for item in items:
                    product = item.select('a')
                    items_url_list.append(f"https://viyar.ua{product[0].get('href')}")
    return items_url_list

def get_urls(response_page):
    url_list = []
    html = BS(response_page.content, 'html.parser')
    items = html.select('.product_prewiew')
    if len(items):
        for item in items:
            product = item.select('a')
            url_list.append(f"https://viyar.ua{product[0].get('href')}")
    return url_list

def get_items_urls1(response_page_list):
    """Возвращает список URL адресов всех товаров внутри категории"""
    items_url_list = []
    if len(response_page_list) > 0:
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            future_list = [executor.submit(get_urls, response_page) for response_page in response_page_list]
            for future in concurrent.futures.as_completed(future_list):
                items_url_list += future.result()
    return items_url_list
def get_item_response(item_url):
    """Возвращает response обьект на product_detail"""
    return requests.get(item_url)

def get_items_responses(items_url_list):
    """Возвращает список response обьектов на все товары внутри категории"""
    items_response_list = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_list = [executor.submit(get_item_response, item_url) for item_url in items_url_list]
        for future in concurrent.futures.as_completed(future_list):
            items_response_list.append(future.result())
    return items_response_list
def get_item_data(item_response, path_to_download):
    """Возвращает данные о товаре и загружает его фотографии в path_to_download"""
    item_data = {}
    item_html = BS(item_response.content, 'html.parser')
    code = ''
    for i in range(5, random.choice([j for j in range(6, 11)])):
        code += random.choice([str(k) for k in range(0, 10)])
    item_data['name'] = get_name(item_html, code)
    # print(f"object '{item_data['name']}' added")
    item_data['slug'] = get_slug(item_response, code)
    item_data['price'] = get_price(item_html)
    item_data['properties'] = get_properties(item_html)
    item_data['photos'] = get_photos_urls(item_data['name'], item_html)
    download_photos(item_data.get('photos'), path_to_download)
    # print(f"object '{item_data['name']}' added")
    return item_data

# def add_items_data(response_items, path):
#     """https://docs.python.org/3.8/library/concurrent.futures.html#threadpoolexecutor"""
#     items_data = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
#         future_list = [executor.submit(add_item_data, response_item, path) for response_item in response_items]
#         for future in concurrent.futures.as_completed(future_list):
#             items_data.append(future.result())
#     return items_data
def get_items_data(items_response_list, path_to_download):
    """Возврашает список данных о товарах и загружает их фотографии в path_to_download"""
    items_data = []
    for item_response in items_response_list:
        items_data.append(get_item_data(item_response, path_to_download))
    return items_data

def get_items_data1(items_response_list, path_to_download):
    """Возврашает список данных о товарах и загружает их фотографии в path_to_download"""
    items_data = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        future_list = [executor.submit(get_item_data, item_response, path_to_download) for item_response in items_response_list]
        for future in concurrent.futures.as_completed(future_list):
            items_data.append(future.result())
    return items_data

def get_name(item_html, code):
    """Возвращает наименование товара"""
    try:
        name = item_html.select('.product_name > h1 > b')[0].text.strip()
    except Exception:
        return f'Exeption {code}'
    else:
        return name

def get_slug(item_response, code):
    try:
        url = item_response.url
    except Exception:
        return f'exeption_{code}'
    else:
        return url.split('/')[-2]

def get_price(item_html):
    """Возвращает стоимость товара за единицу"""
    try:
        try:
            price = float(item_html.select('span.price')[0].text.strip())
        except ValueError:
            price = ''
            list_p = item_html.select('span.price')[0].text.strip().split()
            for i in list_p:
                price += i
            price = float(price)
    except Exception:
        return random.choice(range(1700, 2500, 3))
    else:
        return price


def get_properties(item_html):
    """Возвращает характеристики товара"""
    properties = {}
    prop_list = item_html.select('div.charakters > ul.properties > li')
    n = 1
    try:
        for prop in prop_list:
            if n <= len(prop_list) / 2:
                property = prop.text.split(': ')
                properties[property[0]] = property[1].lower()
                n += 1
            else:
                break
    except Exception as ex:
        properties[f'Exception - {ex}'] = 'свойства не добавлены'
    return properties

def get_photos_urls(name, item_html):
    """Возвращает список url адресов фотографий товара"""
    photos_url_list = []
    for n in range(1, 5):
        try:
            if n == 1:
                photo = item_html.find_all('img', alt=name)
            else:
                photo = item_html.find_all('img', alt=name + ' — фото' + str(n))
            photo_url = f"https://viyar.ua{photo[0].get('src')}"
            photos_url_list.append(photo_url)
        except IndexError:
            break
    return photos_url_list
def download_photos(photos_url_list, path):
    """Запускает потоки и загружает в них фотографии товара"""
    if photos_url_list:
        for photo_url in photos_url_list:
            threading.Thread(target=download_photo, args=(photo_url, path)).start()

def download_photo(photo_url, path):
    """Загружает фотографию"""
    root = path + photo_url.split('/')[-1]
    p = requests.get(photo_url)
    img = open(root, "wb")
    img.write(p.content)
    img.close()

if __name__ == '__main__':
    t1 = time.time()
    path_to_download = 'products_data/'
    cat_url = 'https://viyar.ua/catalog/metiznaya_produktsiya/'
    response_page_list = get_response_pages(cat_url)
    print(f'    получили responces в количестве {len(response_page_list)} шт')
    items_url_list = get_items_urls(response_page_list)
    print(f'    получили items_urls товаров в количестве {len(items_url_list)} шт')
    response_items_list = get_items_responses(items_url_list)
    print(f'    получили response_items товаров в количестве {len(response_items_list)} шт')
    products_data_list = get_items_data(response_items_list, path_to_download)
    print(f'    получили products_data в количестве {len(products_data_list)} шт')
    print(time.time() - t1)
