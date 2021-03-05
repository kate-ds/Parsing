# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline

class InstagramPipeline:
    def process_item(self, item, spider):
        return item


class SaveToMongoPipeline:

    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client['instagram_parse']

    def process_item(self, item, spider):
        self.db[spider.database_collection].insert_one(item)
        return item


class InstaImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        try:
            yield Request(item['images'])
            return item
        except KeyError:
            pass

    def item_completed(self, results, item, info):
        if results:
            item["images"] = results[0][1]
        return item




