import scrapy
from scrapy.http import Response
from ..loaders import HhruVacancyLoader, HHruCompanyLoader

class VacanciesHhSpider(scrapy.Spider):
    database_collection = ''
    name = 'vacancies-hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    xpath_query = {
        'pagination': 'div.bloko-gap a.HH-Pager-Control',
        'vacancy': 'div.vacancy-serp-item__info a.bloko-link',
        'other_vacancies': '//a[@data-qa="employer-page__employer-vacancies-link"]/@href'
    }

    vacancies_data_query = {
        'vacancy_name': '//h1[@data-qa="vacancy-title"]//text()',
        'company_name': '//div[@class="vacancy-company__details"]//span//text()',
        'salary': '//p[@class="vacancy-salary"]//text()',
        'description': '//div[@data-qa="vacancy-description"]//text()',
        'skills': '//div[@class="bloko-tag-list"]//span[@data-qa="bloko-tag__text"]//text()',
        'company_link': '//div[@class="vacancy-company__details"]//a[@class="vacancy-company-name"]/@href'
    }

    companies_data_query = {
        'company_name': '//div[@class="company-header"]//span[@class="company-header-title-name"]//text()',
        'company_site': '//div//a[@data-qa="sidebar-company-site"]//@href',
        'activity_areas': '//div[contains(@class, "employer-sidebar-content")]//p/text()',
        'company_description': '//div[@class="company-description"]//p//text()'
    }

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get('href'), callback=callback)

    def get_link(self, response, query):
        return response.xpath(query).get()

    def parse(self, response: Response, **kwargs):
        yield from self.gen_task(response, response.css(self.xpath_query['pagination']), callback=self.parse)
        yield from self.gen_task(response, response.css(self.xpath_query['vacancy']), callback=self.vacancy_parse)

    def vacancy_parse(self, response: Response):
        loader = HhruVacancyLoader(response=response)
        self.database_collection = 'vacancies'
        loader.add_value('vacancy_link', response.url)
        for key, selector in self.vacancies_data_query.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()
        yield response.follow(self.get_link(response, self.vacancies_data_query['company_link']), callback=self.company_parse)

    def company_parse(self, response: Response):
        loader = HHruCompanyLoader(response=response)
        self.database_collection = 'companies'
        loader.add_value('company_link', response.url)
        for key, selector in self.companies_data_query.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()
        self.other_vacancies_parse(response)

    def other_vacancies_parse(self, response):
        if response.xpath(self.xpath_query['other_vacancies']).get():
            yield response.follow(response.xpath(self.xpath_query['other_vacancies']).get(), callback=self.parse)
