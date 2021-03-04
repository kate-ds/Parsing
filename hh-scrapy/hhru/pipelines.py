import pymongo
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

class HhruPipeline:
    def process_item(self, item, spider):
        return item


class SaveToMongoPipeline:
    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client['hh_parse_db']

    def process_item(self, item, spider):
        self.db[spider.database_collection].insert_one(item)
        return item
