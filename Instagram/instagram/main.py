from instagram.instagram.spiders.insta import InstaSpider
from dotenv import load_dotenv
from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import os

if __name__ == '__main__':
    load_dotenv(Path(__file__).parent.joinpath(".env"))
    crawler_settings = Settings()
    crawler_settings.setmodule('settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(InstaSpider, login=os.getenv('LOGIN'), password=os.getenv('PASSWORD'))
    crawler_process.start()