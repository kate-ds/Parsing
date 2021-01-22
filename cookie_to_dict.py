import requests
from pprint import pprint
# url ='https://magnit.ru/promo/?geo=moskva'
# response = requests.get(url)
# pprint(response)



from pprint import pprint
try:
    import cookielib
except:
    import http.cookiejar
    cookielib = http.cookiejar

cookies = ['mg_geo_id=2398; _ga=GA1.2.482071855.1611161173; _gid=GA1.2.98209337.1611161173; _geo.set=Y; _ym_visorc_9726625=w; _ym_visorc_56708149=w; _gat_UA-61230203-3=1; _gat_UA-61230203-9=1; _ym_isad=2; _ym_d=1611161173; _ym_uid=1611161173288233753; BX_USER_ID=3fe2a286206f3a058100c7879747d01a; PHPSESSID=ckdi0dnuuocsj47i4apg1vdteg; TBMCookie_5896820447423046672=649079001611161168HV0m43yZsatcrYZY+DC7vQ4VA/U=; ___utmvm=###########']
for result in cookielib.parse_ns_headers(cookies):
    print(result)

cookie_dictionary = dict(res[0] for res in cookielib.parse_ns_headers(cookies))
pprint(cookie_dictionary)