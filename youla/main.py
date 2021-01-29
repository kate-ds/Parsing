from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from youla.spiders.autoyoula import AutoyoulaSpider
import os
import pymongo
from dotenv import load_dotenv

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule('youla.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(AutoyoulaSpider)
    crawler_process.start()
    load_dotenv(".env")
    data_base_url = os.getenv('DATA_BASE_URL')
    data_client = pymongo.MongoClient(data_base_url)
    data_base = data_client["youla_parse_db"]


