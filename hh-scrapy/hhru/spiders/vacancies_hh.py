import scrapy
from scrapy.http import Response
from dotenv import load_dotenv
import os
import pymongo
from dotenv import load_dotenv


class VacanciesHhSpider(scrapy.Spider):
    name = 'vacancies-hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']
    meta = {
        'dont_redirect': True,
        'handle_httpstatus_list': [302]
    }


    css_query = {
        'pagination': 'div.bloko-gap a.HH-Pager-Control',
        'vacancy': 'div.vacancy-serp-item__info a.bloko-link'
    }

    data_query = {
        'vacancy_name': 'h1.bloko-header-1::text',
        'salary': 'p.vacancy-salary span.bloko-header-2::text',
        'description': '//div[@class="g-user-content"]//text()',
        'skills': 'div.bloko-tag-list span.bloko-tag__section_text::text',
        'company_link': 'div.vacancy-company-wrapper a.vacancy-company-name',
        'company_name': 'div.company-header span.company-header-title-name',
        'company_site': 'div.employer-sidebar a.g-user-content',
        'activity_areas': 'div.employer-sidebar-block p::text',
        'company_descr': 'div.g-user-content p::text'
    }

    @property
    def get_vacancy_data(self):
        return {
            'vacancy_name': lambda response: response.css(self.data_query['vacancy_name']).get(),
            'salary': lambda response: ''.join(response.css(self.data_query['salary']).getall()).replace(u'\xa0', ' '),
            'description': lambda response: ''.join(response.xpath(self.data_query['description']).getall()),
            'skills': lambda response: response.css(self.data_query['skills']).getall(),
            'company_link': lambda response: f"https://hh.ru/{response.css(self.data_query['company_link']).attrib.get('href')}"
        }

    @property
    def get_company_data(self):
        return {
            'company_name': lambda response: response.css(self.data_query['company_name']).get(),
            'company_site': lambda response: response.css(self.data_query['company_site']).attrib.get('href'),
            'activity_areas': lambda response: response.css(self.data_query['activity_areas']).getall(),
            'company_description': lambda response: ' '.join(response.css(self.data_query['company_descr']).getall())
        }

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get('href'), callback=callback)

    def parse(self, response: Response):
        yield from self.gen_task(response, response.css(self.css_query['pagination']), callback=self.parse)
        # for page in response.css('div.pager-block a.HH-Pager-Control'):
        #     list_links = page.attrib.get('href')
        # yield response.follow(list_links, callback=self.brand_parse)
        # print(1)
        yield from self.gen_task(response, response.css(self.css_query['vacancy']), callback=self.vacancy_parse)

    def vacancy_parse(self, response: Response):
        data = {}
        for name, value in self.get_vacancy_data.items():
            data[name] = value(response)
        print (data)
        return self.save_data(data, 'vacancies')
        link = response.css(self.data_query['company_link']).attrib.get('href')
        yield response.follow(link, callback=self.company_parse)

    def company_parse(self, response: Response):
        data = {}
        for name, value in self.get_company_data.items():
            data[name] = value(response)
        print(data)
        return self.save_data(data, 'companies')

    @staticmethod
    def save_data(data, database_name):
        load_dotenv("\.env")
        data_base_url = os.getenv('DATA_BASE_URL')
        data_client = pymongo.MongoClient(data_base_url)
        data_base = data_client["hh_parse_db"]
        collection = data_base[database_name]
        result = collection.insert_one(data)
        if result.inserted_id:
            print(f"Inserted {result.inserted_id}")
        pass
