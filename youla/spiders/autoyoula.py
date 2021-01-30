import scrapy
import os
import pymongo
from dotenv import load_dotenv
from scrapy.http import Response


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']
    css_query = {
        'brand': 'div.ColumnItemList_container__5gTrc a.blackLink',
        'pagination': 'div.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu',
    }
    load_dotenv(".env")
    data_base_url = os.getenv('DATA_BASE_URL')
    data_client = pymongo.MongoClient(data_base_url)
    data_base = data_client["youla_parse_db"]

    @staticmethod
    def get_specs(response):
        return {
                spec.css('.AdvertSpecs_label__2JHnS::text').get():
                    spec.css('.AdvertSpecs_data__xK2Qx::text').get() or spec.css('a::text').get() for spec in response.css('.AdvertSpecs_row__ljPcX')
            }

    @property
    def data_template(self):
        return {
            'title': lambda response: response.css("div.AdvertCard_advertTitle__1S1Ak::text").get(),
            'price': lambda response: float(response.css('div.AdvertCard_price__3dDCr::text').get().replace('\u2009', '')),
            'description': lambda response: response.css('div.AdvertCard_descriptionInner__KnuRi::text').get(),
            'specifications': lambda response: self.get_specs(response),
            'photos': lambda response: self.get_photos(response)
        }

    def save(self, data):
        print(data)
        collection = self.data_base["youla"]
        result = collection.insert_one(data)
        if result.inserted_id:
            print(f"Inserted {result.inserted_id}")
        pass

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get('href'), callback=callback)

    def get_photos(self, response):
        return [pict.attrib.get('src') for pict in response.css('figure.PhotoGallery_photo__36e_r img')]

    def parse(self, response: Response, **kwargs):
        yield from self.gen_task(response, response.css(self.css_query['brand']), self.brand_parse)

    def brand_parse(self, response: Response):
        yield from self.gen_task(response, response.css(self.css_query['pagination']), self.brand_parse)
        yield from self.gen_task(response, response.css(self.css_query['ads']), self.ads_parse)

    def ads_parse(self, response: Response):
        data = {}
        for name, value in self.data_template.items():
            try:
                data[name] = value(response)
            except AttributeError:
                pass
        return self.save(data)

'''
Собрать след стуркутру и сохранить в БД Монго
Название объявления
Список фото объявления (ссылки)
Список характеристик
Описание объявления
ссылка на автора объявления
дополнительно попробуйте вытащить телефона
'''