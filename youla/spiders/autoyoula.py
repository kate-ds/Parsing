import scrapy
import os
import pymongo
import re
from dotenv import load_dotenv
from scrapy.http import Response
from urllib.parse import unquote
from scrapy_splash import SplashRequest


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']
    css_query = {
        'brand': 'div.ColumnItemList_container__5gTrc a.blackLink',
        'pagination': 'div.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu',
    }
    get_phone_script = '''
                function main(splash, args)
                    assert(splash:go(args.url))
                    assert(splash:runjs('document.querySelector(".Button_button__3NYks").click()'))
                    assert(splash:wait(3.0))
                    local phone = assert(splash:select('.PopupPhoneNumber_number__1hybY'))
                    return phone.node.text
    end'''

    @staticmethod
    def get_specs(response):
        return {
            spec.css('.AdvertSpecs_label__2JHnS::text').get():
                spec.css('.AdvertSpecs_data__xK2Qx::text').get() or spec.css('a::text').get() for spec in
            response.css('.AdvertSpecs_row__ljPcX')
        }

    @staticmethod
    def get_script(response):
        script_text = response.css('script::text').re_first(r'^window.transitState.*')
        return unquote(script_text[42:-3])

    @property
    def data_template(self):
        return {
            'url': lambda response: response.url,
            'title': lambda response: self.get_text(response, "div.AdvertCard_advertTitle__1S1Ak::text"),
            'price': lambda response: float(
                self.get_text(response, 'div.AdvertCard_price__3dDCr::text').replace('\u2009', '')),
            'description': lambda response: self.get_text(response, 'div.AdvertCard_descriptionInner__KnuRi::text'),
            'specifications': lambda response: self.get_specs(response),
            'photos': lambda response: self.get_photos(response),
            'user_or_dealer_url': lambda response: self.get_user_or_dealer_link(response),
            'phone' : lambda response: self.get_phone(response)
        }

    @staticmethod
    def save(data):
        print(data)
        load_dotenv("\.env")
        data_base_url = os.getenv('DATA_BASE_URL')
        data_client = pymongo.MongoClient(data_base_url)
        data_base = data_client["youla_parse_db"]
        collection = data_base["youla"]
        result = collection.insert_one(data)
        if result.inserted_id:
            print(f"Inserted {result.inserted_id}")
        pass

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get('href'), callback=callback)

    @staticmethod
    def get_text(response, query):
        try:
            return response.css(query).get()
        except:
            return None

    def get_photos(self, response):
        try:
            regex_xl = r'https:\/\/static.am\/automobile_m3\/document\/xl\/[a-z0-9]*\/[a-z0-9]*\/[a-z0-9.]*'
            regex_l = r'https:\/\/static.am\/automobile_m3\/document\/l\/[a-z0-9]*\/[a-z0-9]*\/[a-z0-9.]*'
            regex_m = r'https:\/\/static.am\/automobile_m3\/document\/m\/[a-z0-9]*\/[a-z0-9]*\/[a-z0-9.]*'
            regex_s = r'https:\/\/static.am\/automobile_m3\/document\/s\/[a-z0-9]*\/[a-z0-9]*\/[a-z0-9.]*'
            list_photos = re.findall(regex_xl, self.get_script(response)) or \
                          re.findall(regex_l, self.get_script(response)) or \
                          re.findall(regex_m, self.get_script(response)) or \
                          re.findall(regex_s, self.get_script(response))
            return list(set(list_photos))
        except:
            return None

    def get_user_or_dealer_link(self, response):
        try:
            user_id = re.findall(r'\["youlaId","(.+)","avatar"', self.get_script(response))
            return f"https://youla.ru/user/{user_id[0]}"
        except IndexError:
            dealer_name = re.findall(r'"sellerLink","(.+)","type"', self.get_script(response))
            return f"https://auto.youla.ru{dealer_name[0]}"

    def parse(self, response: Response, **kwargs):
        yield from self.gen_task(response, response.css(self.css_query['brand']), self.brand_parse)

    def brand_parse(self, response: Response):
        ''' (the same pagination)
        for page in response.css('div.Paginator_block__2XAPy a.Paginator_button__u1e7D'):
            list_links = page.attrib.get('href')
            yield response.follow(list_links, callback=self.brand_parse)
        '''
        yield from self.gen_task(response, response.css(self.css_query['pagination']), self.brand_parse)
        yield from self.gen_task(response, response.css(self.css_query['ads']), self.ads_parse)

    def get_phone(self, response: Response):
        try:
            return SplashRequest(response.url, args={'wait': 0.5, 'lua_source': self.get_phone_script})
        except:
            return None


    def ads_parse(self, response: Response):
        data = {}
        for name, value in self.data_template.items():
            try:
                data[name] = value(response)
            except AttributeError:
                pass
        return self.save(data)
