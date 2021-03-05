from bs4 import BeautifulSoup as bs
import requests
import json
from pprint import pprint
from pathlib import Path

main_link = 'https://www.kinopoisk.ru'
params = {
    'quick_filters' : 'films',
    'tab' : 'all'
}
headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15'
}
link = f"{main_link}/popular/films/"

response = requests.get(link, params=params, headers=headers)
# print()
soup = bs(response.text, 'html.parser')

if response.ok:
    print('ok')
    films_list = soup.findAll('div', {'class':'desktop-seo-selection-film-item'})
    pprint(films_list)

    films = []
    for film in films_list:
        film_data = {}
        film_name = film.find('p')
        film_link = main_link + film_name.parent['href']
        film_genre = film.findAll('span', {'class': 'selection-film-item-meta_meta-additional-item'})
        try:
            film_rating = float(film.find('span', {'class': 'rating_value'}).text)
        except:
            film_rating = 0.0

        film_data['name'] = film_name.text
        film_data['rating'] = film_rating
        film_data['genre'] = film_genre
        film_data['link'] = film_link
        films.append(film_data)
        print(film_data)
pprint(films)
    # pprint(dancing_films_list)
