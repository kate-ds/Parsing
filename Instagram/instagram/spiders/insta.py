import scrapy
import json


class InstaSpider(scrapy.Spider):
    name = "insta"
    allowed_domains = ["instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    tags = ['python', 'coding', 'developers']


    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        super().__init__(*args, **kwargs)

    def parse(self, response, *args, **kwargs):
        try:
            js_data = self.js_data_extractor(response)
            yield scrapy.FormRequest (
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata= {
                    'username': self.login,
                    'enc_password': self.password
                },
                headers={
                    'X-CSRFToken': js_data['config']['csrf_token']
                }
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for tag in self.tags:
                    yield response.follow(
                        f'/explore/tags/{tag}/',
                        callback=self.tag_parse
                    )

    def tag_parse(self, response):
        print(1)

    def js_data_extractor(self, response) -> dict:
        script = response.xpath('//body/script[contains(text(), "csrf_token")]/text()').get()
        return json.loads(script.replace('window._sharedData = ', '', 1)[:-1])
