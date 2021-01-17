import json
import time
from pathlib import Path
import requests
import os

# ?categories=&ordering=&page=4&price_promo__gte=&price_promo__lte=&records_per_page=12&search=&store="
# -- это параметры с разделителем &, напр 'categories' = None

# with open("5ka_ru.html", "w", encoding="UTF-8") as file:
#     file.write(response.text)
#
# print(1)

class ParseError(Exception):
    def __init__(self, text):
        self.text = text

        #Создаем класс ошибок

class Parse5ka:
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:82.0) Gecko/20100101 Firefox/82.0'
    }
    _params = {
        "records_per_page" : 50
    }
    def __init__(self, start_url:str, result_path:Path):
        self.start_url = start_url
        self.result_path = result_path

        # Создаем основной класс парсера, в нем указываем параметры и заголовки, которые мы задаем по дефолту
        # Например, при запросе мы передаем заголовок с названием клиента - Mozilla
        # инициируем класс, в котором мы говорим, что начальная точка входа у нас будет start_url
        # и в result_path будут храниться наши файлы

    @staticmethod
    def _get_response(url: str, *args, **kwargs) -> requests.Response:
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

        # создаем метод, который получает ответ от сервера, обрабатывает ошибки и повторяет запрос в случае ошибки
        # если ошибка, выполняется класс ошибки и возвращает ее. Предусмотрены ошибки из requests и
        # непридвиденные ParseError

    def run(self):
        for product in self.parse(self.start_url):
            file_path = self.result_path.joinpath(f"{product['id']}.json")
            self.save(product, file_path)

        # метод, который складывает каждый продукт (который вернул метод parse)
        # в файл .json и сохраняет (с помощью метода save)

    def parse(self, url: str) -> dict:
        while url:
            response = self._get_response(url, params=self._params, headers=self._headers)
            data = response.json()
            url = data['next']
            for product in data['results']:
                yield product

        # получает из метода get_response ответ на url (пока в next не появится None)
        # возвращает генратор, состоящий из продуктов на странице

    @staticmethod
    def save(data:dict, file_path:Path):
        with file_path.open('w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False)
            # file.write(json.dumps(data)) --либо так, но так длиннее запись
        # сохраняет данные в отдельный файл

class Categories(Parse5ka):
    def __init__(self, start_url:str, category_url:str, result_path:Path):
        super().__init__(start_url, result_path)
        self.category_url = category_url
        # создаем новый класс категорий, который являкется дочерним от Parse5ka

    def parse_categories(self, url: str) -> list:
        response = self._get_response(url)
        return response.json()
        # определяем метод, который будет возвращать нам генератор сз категорий продуктов

    def run(self):
        for category in self.parse_categories(self.category_url):
            _params = {
                "categories":category['parent_group_code']
            }
            products = self.parse(self.start_url)
            list_of_products = []
            for product in products:
                list_of_products.append(product['id'])

            data = {
                "name": category['parent_group_name'],
                "code": category['parent_group_code'],
                "products": list_of_products # список словарей товаров соответсвующих данной категории
            }
            file_path = self.result_path.joinpath(f"{category['parent_group_code']}.json")
            self.save(data, file_path)

            # переопределяем метод run(), который подставляет в параметр ссылки номер категории,
            # собирает список товаров из этой категории и складывает в словарь заданного вида
            # затем сохраняет это в json, воспользовавшись методом save()

if __name__ == '__main__':
    url = 'https://5ka.ru/api/v2/special_offers/'
    url_cat = 'https://5ka.ru/api/v2/categories/'
    # result_path = Path(__file__).parent.joinpath('products')
    result_path_categories = Path(__file__).parent.joinpath('categories')
    try:
        os.mkdir(result_path_categories)
    except FileExistsError:
        pass

# parser = Parse5ka(url, result_path)
    parser2 = Categories(url, url_cat, result_path_categories)
    parser2.run()