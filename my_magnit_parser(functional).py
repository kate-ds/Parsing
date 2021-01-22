import requests
import bs4
import os
from urllib.parse import urljoin
from datetime import datetime
import locale
import pymongo
locale.setlocale(locale.LC_ALL, 'ru_RU')

url = 'https://magnit.ru/promo/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15'
}
params = {
    'geo': 'moskva'
}
cookies = {'mg_geo_id': '2398'}

response = requests.get(url, headers=headers, params=params, cookies=cookies)
soup = bs4.BeautifulSoup(response.text, 'lxml')
catalogue = soup.find('div', attrs= {'class' : 'сatalogue__main'})
products = catalogue.find_all('a', attrs={'class' : 'card-sale'})
data_base_url = os.getenv('DATA_BASE_URL')
data_base = pymongo.MongoClient(data_base_url)["magnit_parse_db"]

def get_price(attr: str) -> float:
    try:
        price = product.find('div', attrs={'class' : attr}).text[1 : -1].split('\n')
        price = float('.'.join(price))
    except:
        price = None
    return price

def get_date(binnary: bin) -> datetime:
    try:
        date = product.find('div', class_='card-sale__date').findChildren()[binnary].text[2:].strip()
        return datetime.strptime(f"{date} {datetime.now().year}", "%d %B %Y")
    except:
        pass

def save(data):
    print(data)
    collection = data_base["magnit_my"]
    collection.insert(data)
    pass

for product in products:
    try:
        data = {
            'url': urljoin(url, product.attrs.get('href')),
            'promo_name': product.find('div', attrs={'class' : 'card-sale__header'}).text,
            'product_name': product.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': get_price('label__price_old'),
            'new_price': get_price('label__price_new'),
            'image_url': urljoin(url, product.find('source').attrs.get('data-srcset')),
            'date_from': get_date(0),
            'date_to': get_date(1)
        }
        save(data)
    except AttributeError:
        pass

#link = urljoin(response.url, product.find('source').attrs.get('data-srcset'))

