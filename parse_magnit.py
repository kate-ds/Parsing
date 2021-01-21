import os
import time
import requests
import bs4
from urllib.parse import urljoin
import pymongo
from dotenv import load_dotenv
from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, 'ru_RU')


class ParseError(Exception):
    def __init__(self, text):
        self.text = text


class MagnitParser:
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15'
    }
    _params = {
        'geo': 'moskva'
    }
    _cookies = {'mg_geo_id': '2398'}

    def __init__(self, start_url, data_client):
        self.start_url = start_url
        self.data_client = data_client
        self.data_base = self.data_client["magnit_parse_db"]

    @staticmethod
    def _get_response(url, *args, **kwargs):
        while True:
            try:
                response = requests.get(url, *args, **kwargs)
                if response.status_code > 399:
                    raise ParseError(response.status_code)
                time.sleep(0.1)
                return response
            except (requests.RequestException, ParseError):
                time.sleep(0.5)
                continue

    @staticmethod
    def _get_soup(response):
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        for product in self.parse(self.start_url):
            self.save(product)

    def parse(self, url) -> dict:
        resp = self._get_response(url, params=self._params, headers=self._headers, cookies=self._cookies)
        print(resp)
        soup = self._get_soup(resp)
        # print(soup)
        catalog_main = soup.find('div', attrs={'class': 'сatalogue__main'})
        # print(catalog_main)
        for product_tag in catalog_main.find_all('a', attrs={'class': 'card-sale'}):
            yield self._get_product_data(product_tag)

    @staticmethod
    def get_price(product_tag, attr: str) -> float or None:
       try:
           price: list = (product_tag.find('div', attrs={'class' : attr}).text)[1 : -1].split('\n')
           return float('.'.join(price))
       except:
           return None

    @staticmethod
    def get_date(product_tag, binary: bin) -> datetime:
        try:
            date = product_tag.find('div', class_='card-sale__date').findChildren()[binary].text[2:].strip()
            return datetime.strptime(f"{date} {datetime.now().year}", "%d %B %Y")
        except:
            pass

    @property
    def data_template(self) -> dict:
        return {
            'url': lambda tag: urljoin(self.start_url, tag.attrs.get('href')),
            'promo_name':lambda tag: tag.find('div', attrs={'class' : 'card-sale__header'}).text,
            'product_name': lambda tag: tag.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': lambda tag: self.get_price(tag, 'label__price_old'),
            'new_price': lambda tag: self.get_price(tag, 'label__price_new'),
            'image_url': lambda tag: urljoin(self.start_url, tag.find('source').attrs.get('data-srcset')),
            'date_from': lambda tag: self.get_date(tag, 0),
            'date_to': lambda tag: self.get_date(tag, 1)
        }

    def _get_product_data(self, product_tag: bs4.Tag) -> dict:
        data = {}
        for key, pattern in self.data_template.items():
            try:
                data[key] = pattern(product_tag)
            except AttributeError:
                pass
        return data


    def save(self, data):
        print(data)
        collection = self.data_base["magnit"]
        collection.insert_one(data)
        pass


if __name__ == '__main__':
    load_dotenv(".env")
    data_base_url = os.getenv('DATA_BASE_URL')
    data_client = pymongo.MongoClient(data_base_url)
    url = 'https://magnit.ru/promo/'
    parser = MagnitParser(url, data_client)
    parser.run()
