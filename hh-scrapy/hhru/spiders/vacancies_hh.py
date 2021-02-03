import scrapy
from scrapy.http import Response


class VacanciesHhSpider(scrapy.Spider):
    name = 'vacancies-hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']
    meta = {
        'dont_redirect': True,
        'handle_httpstatus_list': [302]
    }

    css_query = {
        'pagination': 'div.pager-block a.HH-Pager-Control',
        'vacancy': 'div.vacancy-serp-item__info a.bloko-link',
        'company': ''
    }

    data_query = {
        'vacancy_name': 'h1.bloko-header-1::text',
        'salary': 'p.vacancy-salary span.bloko-header-2::text',
        'description': ''
    }

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get('href'), callback=callback)

    def parse(self, response: Response):
        yield from self.gen_task(response, response.css(self.css_query['pagination']), callback=self.parse)
        yield from self.gen_task(response, response.css(self.css_query['vacancy']), callback=self.vacancy_parse)

    def vacancy_parse(self, response: Response):
        print(1)
        data = {}
        data['vacancy_name'] = response.css(self.data_query['vacancy_name']).get
        salary = response.css(self.data_query['salary']).getall
        data['salary'] = ''.join(salary).replace(u'\xa0', ' ')
        data['description'] = ''
        for name, query in self.data_query.items():
            data[name] = response.css(query).get()



    def save_data(self):
        pass
