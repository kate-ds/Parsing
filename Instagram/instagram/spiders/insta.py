import scrapy
import json
from datetime import datetime
from instagram.instagram.items import InstagramTagItem, InstagramPostItem, InstagramUserFollowers


class InstaSpider(scrapy.Spider):
    name = "insta"
    allowed_domains = ["instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    followers_data = {}
    user_followers_data = {}
    user_follow_data = {}
    connections = []
    current_tag = ""
    database_collection = ""
    hash = {
        'pagination': '9b498c08113f1e09617a1703c22b2f32',
        'post': '2c4c2e343a8f64c625ba02b2aa12c7f8',
        'user_followers': '5aefa9893005572d237da5068082d8d5',
        'user_followings': '3dec7e2c57367ef3da3d987d89f9dbc8'
    }

    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        self.tags = []  # ['annecy', 'montpellier', 'travelinspiration']
        self.users = ['s_katrinka']
        self.user2 = 'ubaldosv'
        self.connection = f"Connection : {self.user2}"
        self.tasks = []

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
            if response.json().get('authenticated') and self.tags != []:
                yield self.parse_task_tags(response)
            elif response.json().get('authenticated') and self.users != []:
                yield from self.parse_task_users(response)

    def parse_task_tags(self, response):
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
                date_parse=datetime.now(),
                data={'id': page_data['id'],
                      'name': page_data['name'],
                      'profile_pic_url': page_data['profile_pic_url'],
                      'post_counts': page_data['edge_hashtag_to_media']['count']},
                images=page_data['profile_pic_url'])
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
            tag_name=self.current_tag,
            date_parse=datetime.now(),
            data=post_data,
            images=post_data['display_url'])

    # --------------------------------------- User Followers and Follow ---------------------------------------------

    def parse_task_users(self, response):
        for user in self.users:
            yield response.follow(f'/{user}/', callback=self.user_page_parse, cb_kwargs={"user": user})

    def user_page_parse(self, response, user):
        self.users.remove(user)
        user_data = self.js_data_extractor(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        yield from self.followers_api_parse(response, user_data)

    def followers_api_parse(self, response, user_data, end_cursor=None):
        variables = {"id": user_data['id'],
                     "first": 50}
        if end_cursor:
            variables["after"] = end_cursor
        url = f"/graphql/query/?query_hash={self.hash['user_followers']}&variables={json.dumps(variables)}"
        yield response.follow(url, callback=self.get_followers_data, cb_kwargs={"user_data": user_data})

    def get_followers_data(self, response, user_data):
        followers_data = response.json()['data']['user']['edge_followed_by']['edges']
        page_data = response.json()['data']['user']['edge_followed_by']['page_info']
        if not user_data['username'] in self.user_followers_data:
            self.user_followers_data[user_data['username']] = {}

        for follower in followers_data:
            self.user_followers_data[user_data['username']][follower['node']['id']] = {}
            self.user_followers_data[user_data['username']][follower['node']['id']] = follower['node']['username']
        if page_data['has_next_page']:
            yield from self.followers_api_parse(response, user_data, page_data['end_cursor'])
        else:
            if len(self.user_followers_data[user_data['username']]) == user_data['edge_followed_by']['count']:
                yield from self.follow_api_parse(response, user_data)

    def follow_api_parse(self, response, user_data, end_cursor=None):
        variables = {"id": user_data['id'],
                     "first": 100}
        if end_cursor:
            variables["after"] = end_cursor
        url = f"/graphql/query/?query_hash={self.hash['user_followings']}&variables={json.dumps(variables)}"
        yield response.follow(url, callback=self.get_follow_data, cb_kwargs={"user_data": user_data})

    def get_follow_data(self, response,
                        user_data):
        followings_data = response.json()['data']['user']['edge_follow']['edges']
        page_data = response.json()['data']['user']['edge_follow']['page_info']
        if not user_data['username'] in self.user_follow_data:
            self.user_follow_data[user_data['username']] = {}

        for follow in followings_data:
            self.user_follow_data[user_data['username']][follow['node']['id']] = {}
            self.user_follow_data[user_data['username']][follow['node']['id']] = follow['node']['username']
        if page_data['has_next_page']:
            yield from self.follow_api_parse(response, user_data, page_data['end_cursor'])
        else:
            if len(self.user_follow_data[user_data['username']]) == user_data['edge_follow']['count']:
                yield from self.get_full_data(user_data)
                yield from self.get_friends(response, user_data)


    def get_full_data(self, user_data):
        self.database_collection = "Users"
        yield InstagramUserFollowers(
            date_parse=datetime.now(),
            user_name=user_data['username'],
            user_id=user_data['id'],
            user_data=user_data['full_name'],
            followers_data=self.user_followers_data[user_data['username']],  # те, кто подписан на пользователя
            follow_data=self.user_follow_data[user_data['username']]      # на кого подписан сам пользователь
        )


# --------------------------------------- User Friends Connections ---------------------------------------------

    def get_friends(self, response, user_data) -> set:
        '''
        Метод из полученных данных будет делать лист друзей (взаимные подписки)
        @return: set of friends
        '''
        follow =  self.user_follow_data[user_data['username']].values()
        followers = self.user_followers_data[user_data['username']].values()
        friend_set = set(follow) & set(followers)
        yield from self.save_connections(response, user_data, friend_set)

    def get_unique_tasks(self, response, user_data, friend_set) -> set:
        '''
        Метод будет проверять уникальность пользователя, чтобы он не попал на парсинг повторно
        @return: set of unique users
        '''
        for friend in friend_set:

            if friend not in self.tasks:
                self.tasks.append(friend)
            else:
                friend_set.remove(friend)
        yield from self.save_connections(response, user_data, friend_set)

    def save_connections(self, response, user_data, friend_set) -> list:
        '''
        метод, который сохраняет пользователей в единую структуру
        @return: list of connections between users
        '''
        for name in friend_set:
            friend = {
                'of_user': user_data['username'],
                'friend': name
            }
            self.connections.append(friend)
            if name != self.user2:
                self.users.append(name)
            else:
                yield from self.get_connections(self.user2)
        yield from self.parse_task_users(response)

    def get_connections(self, name):
        '''
        будет добывать родительские элементы словаря и выводить их
        @return: string with message
        '''
        for user in self.connections:
            if user['friend'] == name:
                self.connection += ' - ' + str(user['of_user'])
                yield from self.get_connections(user['of_user'])
        print('Found!\n', self.connection)




