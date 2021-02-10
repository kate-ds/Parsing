import scrapy
import json
from datetime import datetime
from instagram.instagram.items import InstagramTagItem, InstagramPostItem


class InstaSpider(scrapy.Spider):
    name = "insta"
    allowed_domains = ["instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    current_tag = ""
    database_collection = ""
    hash = {
        'pagination': '9b498c08113f1e09617a1703c22b2f32',
        'post': '2c4c2e343a8f64c625ba02b2aa12c7f8'
    }

    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        self.tags = ['annecy', 'montpellier', 'travelinspiration']
        super().__init__(*args, **kwargs)

    def parse(self, response, *args, **kwargs):
        try:
            js_data = self.js_data_extractor(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={'username': self.login,
                          'enc_password': self.password},
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for tag in self.tags:
                    self.current_tag = tag
                    yield response.follow(f'/explore/tags/{tag}/', callback=self.tag_parse)

    def js_data_extractor(self, response) -> dict:
        '''
        @return: window._sharedData script  in json
        '''
        script = response.xpath('//body/script[contains(text(), "csrf_token")]/text()').get()
        return json.loads(script.replace('window._sharedData = ', '', 1)[:-1])

    def get_end_cursor(self, response):
        '''
        @return: end_cursor (str)
        '''
        try:
            js_data = self.js_data_extractor(response)
            return js_data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['page_info'][
                'end_cursor']
        except AttributeError:
            js_data = response.json()
            return js_data['data']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']

    def get_photos_data(self, data):
        '''
        @param data: json data
        @return: json with photos data
        '''
        try:
            return data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']
        except KeyError:
            return data['data']['hashtag']['edge_hashtag_to_media']['edges']

    def tag_parse(self, response):
        '''
        Function find all posts and go to the post link
        @return: Response from post page
        '''
        # сначала вытаскиваем из первой страницы ссылки на картинки
        self.database_collection = 'Tags'
        try:
            page_data = self.js_data_extractor(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
            yield InstagramTagItem(
                date_parse = datetime.now(),
                data = {'id' : page_data['id'],
                        'name': page_data['name'],
                        'profile_pic_url': page_data['profile_pic_url'],
                        'post_counts' : page_data['edge_hashtag_to_media']['count']},
                images = page_data['profile_pic_url'])
            posts = self.get_photos_data(self.js_data_extractor(response))
        except AttributeError:
            posts = self.get_photos_data(response.json())
        for post in posts:
            variables = {"shortcode": post['node']['shortcode']}
            url = f"/graphql/query/?query_hash={self.hash['post']}&variables={json.dumps(variables)}"
            yield response.follow(url, callback=self.post_parse)
        # потом добавляем новые файлы
        if self.get_end_cursor(response):
            print("self.get_end_cursor(response)", self.get_end_cursor(response))
            variables = {"tag_name": self.current_tag,
                         "first": 50,
                         "after": self.get_end_cursor(response)}
            url = f"/graphql/query/?query_hash={self.hash['pagination']}&variables={json.dumps(variables)}"
            # to to post page and return to
            yield response.follow(url, callback=self.tag_parse)


    def post_parse(self, response):
        self.database_collection = "Posts"
        post_data = response.json()['data']['shortcode_media']
        yield InstagramPostItem(
            tag_name = self.current_tag,
            date_parse = datetime.now(),
            data = post_data,
            images = post_data['display_url'])

