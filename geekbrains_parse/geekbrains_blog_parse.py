import os
# from dotenv import load_dotenv
import requests
import bs4
from urllib.parse import urljoin
from database import Database
from datetime import datetime


class GbParse:
    def __init__(self, start_url, database):
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_urls.add(self.start_url)
        self.database = database

    def _get_soup(self, *args, **kwargs):
        response = requests.get(*args, **kwargs)
        soup = bs4.BeautifulSoup(response.text, "lxml")
        return soup

    def parse_task(self, url, callback):
        def wrap():
            soup = self._get_soup(url)
            return callback(url, soup)

        return wrap

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.database.create_post(result)

    def comment_parse(self, commentable_id) -> list:
        def get_comments(data):
            for e in data:
                comments.append({"text": e['comment']['body'],
                                 "full_name": e['comment']['user']["full_name"]})
                print(f"Comment { e['comment']['id']}: {e['comment']['body']}")
                get_comments(e["comment"]["children"])

        r = requests.get(f'https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id={commentable_id}').json()
        if not r:
            return []

        comments = []
        get_comments(r)
        return comments

    def get_img_url(self, soup) -> str:
        try:
            return soup.find("div", attrs={"class": "blogpost-content"}).find('img')['src']
        except TypeError:
            return ""

    def post_parse(self, url, soup: bs4.BeautifulSoup) -> dict:
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})
        created_date = soup.find("div", attrs={"class": "blogpost-date-views"}).find('time').attrs['datetime']
        commentable_id = soup.find('div', attrs={'class': 'm-t-xl'}).comments['commentable-id']
        print("post parse", url)  # deb
        data = {
            "post_data": {
                "url": url,
                "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
                "image": self.get_img_url(soup),
                "created_at": datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S%z")
            },
            "comments": self.comment_parse(commentable_id),
            "author": {
                "url": urljoin(url, author_name_tag.parent.get("href")),
                "name": author_name_tag.text,
            },
            "tags": [
                {
                    "name": tag.text,
                    "url": urljoin(url, tag.get("href")),
                }
                for tag in soup.find_all("a", attrs={"class": "small"})
            ],
        }
        return data

    def pag_parse(self, url, soup: bs4.BeautifulSoup):
        gb_pagination = soup.find("ul", attrs={"class": "gb__pagination"})
        a_tags = gb_pagination.find_all("a")
        for a in a_tags:
            pag_url = urljoin(url, a.get("href"))
            if pag_url not in self.done_urls:
                task = self.parse_task(pag_url, self.pag_parse)
                self.tasks.append(task)
                self.done_urls.add(pag_url)

        posts_urls = soup.find_all("a", attrs={"class": "post-item__title"})
        for post_url in posts_urls:
            post_href = urljoin(url, post_url.get("href"))
            if post_href not in self.done_urls:
                task = self.parse_task(post_href, self.post_parse)
                self.tasks.append(task)
                self.done_urls.add(post_href)


if __name__ == '__main__':
    # load_dotenv('.env')
    # db = Database(os.getenv('DB'))
    db = Database('sqlite:///gb_blog2.db')
    parser = GbParse('https://geekbrains.ru/posts', db)
    parser.run()
    print("done")  # deb
