import requests

url = 'https://5ka.ru/special_offers/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:82.0) Gecko/20100101 Firefox/82.0'
}

response: requests.Response = requests.get(
    url,
    headers=headers
)

with open("5ka_ru.html", "w", encoding="UTF-8") as file:
    file.write(response.text)

print(1)
