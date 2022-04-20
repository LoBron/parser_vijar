import requests
from bs4 import BeautifulSoup as BS
page = 1
while True:
    category_list = requests.get('https://viyar.ua/catalog/metiznaya_produktsiya/page-' + str(page))
    html = BS(category_list.content, 'html.parser')
    items = html.select('.product_prewiew')
    if len(items):
        for item in items:
            data = {}
            product = item.select('a')
            href_product = f"https://viyar.ua{product[0].get('href')}"
            product_detail = requests.get(href_product)
            html_item = BS(product_detail.content, 'html.parser')

            name = html_item.select('.product_name > h1 > b')[0].text.strip()
            data['name'] = name

            price = float(html_item.select('span.price')[0].text.strip())
            data['price'] = price

            prop = html_item.select('div.charakters > ul.properties > li')
            properties = {}
            n = 1
            for property in prop:
                if n <= len(prop)/2:
                    property = property.text.split(': ')
                    properties[property[0]] = property[1]
                    n += 1
                else:
                    break
            data['properties'] = properties

            print(data)







            # product = item.select('a')
            # name_product = product[0].get('title')
            # print(f'Название - {name_product}')
            # href_product = f"https://viyar.ua{product[0].get('href')}"
            # print(f'Ссылка - {href_product}')
            # img_product = f"https://viyar.ua{item.select('img')[0].get('src')}"
            # print(f'Ссылка на изображение - {img_product}')
            # print()
        page += 1
    else:
        break