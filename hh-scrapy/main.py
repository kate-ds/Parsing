from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from hhru.spiders.vacancies_hh import VacanciesHhSpider

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule('hhru.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(VacanciesHhSpider)
    crawler_process.start()