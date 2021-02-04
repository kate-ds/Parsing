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

    xpath_query = {
        'pagination': 'div.bloko-gap a.HH-Pager-Control',
        'vacancy': 'div.vacancy-serp-item__info a.bloko-link',
        'other_vacancies': '//a[@data-qa="employer-page__employer-vacancies-link"]/@href'
    }

    data_query = {
        'vacancy_name': '//h1[@data-qa="vacancy-title"]//text()',
        'salary': '//p[@class="vacancy-salary"]//text()',
        'description': '//div[@data-qa="vacancy-description"]//text()',
        'skills': '//div[@class="bloko-tag-list"]//span[@data-qa="bloko-tag__text"]//text()',
        'company_link': '//div[@class="vacancy-company__details"]//@href',
        'company_name': '//div[@class="company-header"]//h1//text()',
        'company_name2': '//div[@class="vacancy-company__details"]//span//text()',
        'company_site': '//div//a[@data-qa="sidebar-company-site"]//@href',
        'activity_areas': '//div[contains(@class, "employer-sidebar-content")]//p/text()',
        'company_descr': '//div[@class="g-user-content"]//text()'
    }

    @property
    def get_vacancy_data(self):
        return {
            'vacancy_name': lambda response: response.xpath(self.data_query['vacancy_name']).get(),
            'company_name': lambda response: response.xpath(self.data_query['company_name2']).get(),
            'salary': lambda response: self.get_text(response, 'salary').replace(u'\xa0', ' '),
            'description': lambda response: self.get_text(response, 'description'),
            'skills': lambda response: response.xpath(self.data_query['skills']).getall(),
            'company_link': lambda response: f"https://hh.ru/{self.get_link(response, 'company_link')}"
        }

    @property
    def get_company_data(self):
        return {
            'company_link': lambda response: response.url,
            'company_name': lambda response: self.get_text(response, 'company_name').replace(u'\xa0', ' '),
            'company_site': lambda response: response.xpath(self.data_query['company_site']).get(),
            'activity_areas': lambda response: response.xpath(self.data_query['activity_areas']).getall(),
            'company_description': lambda response: self.get_text(response, 'company_descr')
        }

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get('href'), callback=callback)

    def get_text(self, response, query):
        descr_list = response.xpath(self.data_query[query]).getall()
        return ' '.join([e for e in descr_list if e.strip()])

    def get_link(self, response, query):
        return response.xpath(self.data_query[query]).get()

    def parse(self, response: Response):
        yield from self.gen_task(response, response.css(self.xpath_query['pagination']), callback=self.parse)
        yield from self.gen_task(response, response.css(self.xpath_query['vacancy']), callback=self.vacancy_parse)

    def vacancy_parse(self, response: Response):
        data = {}
        for name, value in self.get_vacancy_data.items():
            data[name] = value(response)
        print ('vacanсy', data)
        self.save_data(data, 'vacancies')
        yield response.follow(self.get_link(response, 'company_link'), callback=self.company_parse)

    def company_parse(self, response: Response):
        data = {}
        for name, value in self.get_company_data.items():
            data[name] = value(response)
        print('company', data)
        self.save_data(data, 'companies')
        self.other_vacancies_parse(response)

    def other_vacancies_parse(self, response):
        if response.xpath(self.xpath_query['other_vacancies']).get():
            yield response.follow(response.xpath(self.xpath_query['other_vacancies']).get(), callback=self.parse)

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


    # todo написать файлы items, loaders, pipelines