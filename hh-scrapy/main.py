from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from hhru.spiders.vacancies_hh import VacanciesHhSpider
import os
import pymongo
from dotenv import load_dotenv


if __name__ == '__main__':
    load_dotenv(".env")
    data_base_url = os.getenv('DATA_BASE_URL')
    data_client = pymongo.MongoClient(data_base_url)
    crawler_settings = Settings()
    crawler_settings.setmodule('hhru.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(VacanciesHhSpider)
    crawler_process.start()