import random
import threading
import time
import concurrent.futures
import requests
from bs4 import BeautifulSoup as BS



def get_categories_info(main_url):
    categories_info = []
    response_obj = requests.get(main_url)
    html_page = BS(response_obj.content, 'html.parser')
    items0_list = html_page.select('.main-menu > .top_level > li')
    for item0 in items0_list:
        cat0_name = item0.find_all('span')[0].text.strip()
        if cat0_name in ['Фасады', 'Фасади']:
            continue
        else:
            cat_level_0 = {}
            cat_level_0["name"] = cat0_name
            cat_level_0["slug"] = 'надо доработать'
            cat_level_0["categories_level_1"] = []
            items1_list = item0.select('.hidden-label > div')
            for item1 in items1_list:
                if len(item1) > 0:
                    links = item1.find_all('a')
                    cat1_name = links[0].text.strip()
                    if cat1_name in ['Мойки из искусственного камня  Belterno', 'Мийки зі штучного каменю  Belterno']:
                        continue
                    else:
                        cat_level_1 = {}
                        cat_level_1["name"] = cat1_name  #links[0]["title"]
                        cat_level_1["href"] = links[0]["href"]
                        cat_level_1["slug"] = cat_level_1["href"].split('/')[-2]
                        cat_level_1["categories_level_2"] = []
                        if len(links) > 1:
                            for n in range(1, len(links)):
                                cat_level_2 = {}
                                cat_level_2["name"] = links[n].text.strip()
                                cat_level_2["href"] = links[n]["href"]
                                cat_level_2["slug"] = cat_level_2["href"].split('/')[-2]
                                cat_level_1["categories_level_2"].append(cat_level_2)
                        cat_level_0["categories_level_1"].append(cat_level_1)
            categories_info.append(cat_level_0)
    return categories_info


def add_products_data(data, main_url, path):
    for i in range(1): #range(len(data)):
        print(data[i])
        for j in range(len(data[i].get("categories_level_1"))):
            print(data[i].get("categories_level_1"))
            if len(data[i].get("categories_level_1")[j].get("categories_level_2")) > 0:
                for k in range(len(data[i].get("categories_level_1")[j].get("categories_level_2"))):
                    url = main_url + data[i].get("categories_level_1")[j].get("categories_level_2")[k]['href']
                    data[i].get("categories_level_1")[j].get("categories_level_2")[k]['products'] = get_category_data(url=url, path=path)
            else:
                url = main_url + data[i].get("categories_level_1")[j]['href']
                data[i].get("categories_level_1")[j]['products'] = get_category_data(url=url, path=path)



def get_category_data(url, path):
    response_page_list = get_category_pages(url=url)
    print('получили страницы')
    print(response_page_list)
    items_list = get_items_hrefs(response_page_list)
    print('получили urls обьектов')
    print(items_list)
    response_items = get_items_pages(items_list)
    print('получили страницы обьектов')
    # print(response_items)
    return add_items_data(response_items, path)



def get_category_pages(url):
    response_page_list = []
    n = 1
    while True:
        response_page = requests.get(f'{url}page-{n}/')
        if response_page.status_code == 200: #in range(200, 207):
            response_page_list.append(response_page)
            print(f'страница {n} добавлена')
            n += 1
        else:
            break
    return response_page_list


# def get_category_pages(name_category, pages):
#     response_page_list = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=pages) as executor:
#         timer_0 = time.time()
#         future_list = [executor.submit(get_category_page, name_category, page) for page in range(1, pages + 1)]
#         for future in concurrent.futures.as_completed(future_list):
#             response_page_list.append(future.result())
#             print(f"1) время выполнения - {time.time() - timer_0}")
#         print(f"1) время выполнения ФУНКЦИИ - {time.time() - timer_0}\n")
#     return response_page_list

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

def get_item_page(item_href):
    return requests.get(item_href)

def get_items_pages(items_list):
    items_pages = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_list = [executor.submit(get_item_page, item) for item in items_list]
        for future in concurrent.futures.as_completed(future_list):
            items_pages.append(future.result())
    return items_pages

def add_item_data(response_item, path):
    """Возвращает данные о товаре и загружает его фотографии"""
    item_data = {}
    item = BS(response_item.content, 'html.parser')
    item_data['name'] = get_name(item)
    print(f"object '{item_data['name']}' added")
    item_data['slug'] = get_slug(response_item)
    item_data['price'] = get_price(item)
    item_data['properties'] = get_properties(item)
    item_data['photos'] = get_photos(item_data['name'], item)
    download_photos(item_data.get('photos'), path)
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
def add_items_data(response_items, path):
    items_data = []
    for response_item in response_items:
        items_data.append(add_item_data(response_item, path))
    return items_data


def get_name(html_item):
    """Возвращает наименование товара"""
    name = html_item.select('.product_name > h1 > b')[0].text.strip()
    return name

def get_slug(response_item):
    url = response_item.url
    return url.split('/')[-2]


def get_price(html_item):
    """Возвращает стоимость товара за единицу"""
    try:
        # print(html_item.select('span.price'))
        price = float(html_item.select('span.price')[0].text.strip())
    except IndexError:
        return random.choice(range(1700, 2500, 3))
    except ValueError:
        price_l = html_item.select('span.price')[0].text.strip().split()
        return float(price_l[0]+price_l[1])
    else:
        return price







def get_properties(html_item):
    """Возвращает характеристики товара"""
    properties = {}
    prop_list = html_item.select('div.charakters > ul.properties > li')
    n = 1
    for prop in prop_list:
        if n <= len(prop_list) / 2:
            property = prop.text.split(': ')
            properties[property[0]] = property[1].lower()
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