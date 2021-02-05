from scrapy.loader import ItemLoader
from .items import HhruVacancyItem, HhruCompanyItem
from itemloaders.processors import TakeFirst, MapCompose, Compose
from urllib.parse import urljoin

def get_text(list: list):
    return ' '.join([e for e in list if e.strip()])

def clear_unicode(item):
    return item.replace(u'\xa0', '')

def get_link(href):
    return urljoin('https://hh.ru/', href)


class HhruVacancyLoader(ItemLoader):
    default_item_class = HhruVacancyItem
    vacancy_link_out = TakeFirst()
    vacancy_name_out = TakeFirst()
    company_name_in = Compose(get_text, clear_unicode)
    company_name_out = TakeFirst()
    salary_in = Compose(get_text, clear_unicode)
    salary_out = TakeFirst()
    description_in = Compose(get_text, clear_unicode)
    description_out = TakeFirst()
    skills_in = MapCompose(clear_unicode)
    company_link_in = Compose(TakeFirst(), get_link)
    company_link_out = TakeFirst()



    # 'company_description': lambda response: self.get_text(response, self.companies_data_query['company_description'])


class HHruCompanyLoader(ItemLoader):
    default_item_class = HhruCompanyItem
    company_link_out = TakeFirst()
    company_name_in = Compose(get_text, clear_unicode)
    company_name_out = TakeFirst()
    company_site_out = TakeFirst()
    activity_areas_in = MapCompose(clear_unicode)
    company_description_in = Compose(get_text, clear_unicode)
    company_description_out = TakeFirst()


