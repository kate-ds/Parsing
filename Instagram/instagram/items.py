# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstagramTagItem(scrapy.Item):
    _id = scrapy.Field()
    tag_name = scrapy.Field()
    date_parse = scrapy.Field(required=True)
    data = scrapy.Field()
    images = scrapy.Field()

class InstagramPostItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field(required=True)
    data = scrapy.Field()
    images = scrapy.Field()




