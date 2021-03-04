# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HhruVacancyItem(scrapy.Item):
    _id = scrapy.Field()                           # Because Mongo automatically creates _id
    vacancy_link = scrapy.Field(required=True)
    vacancy_name = scrapy.Field(required=True)
    company_name = scrapy.Field()
    salary = scrapy.Field()
    description= scrapy.Field()
    skills = scrapy.Field()
    company_link = scrapy.Field()


class HhruCompanyItem(scrapy.Item):
    _id = scrapy.Field()
    company_link = scrapy.Field(required=True)
    company_name = scrapy.Field()
    company_site = scrapy.Field()
    activity_areas = scrapy.Field()
    company_description = scrapy.Field()
