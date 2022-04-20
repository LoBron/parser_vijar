import requests
from bs4 import BeautifulSoup as BS

r = requests.get('https://viyar.ua/catalog/metiznaya_produktsiya/page-1/')
html = BS(r.content, 'html.parser')
for el in html.select('.product_prewiew'):
    product = el.select('a')
    name_product = product[0].get('title')
    print(f'Название - {name_product}')
    href_product = f"https://viyar.ua{product[0].get('href')}"
    print(f'Ссылка - {href_product}')
    img_product = f"https://viyar.ua{el.select('img')[0].get('src')}"
    print(f'Ссылка на изображение - {img_product}')
    print()



