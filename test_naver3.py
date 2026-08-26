import requests
import urllib.parse
from bs4 import BeautifulSoup

def get_price(name):
    url = f"https://finance.naver.com/search/searchList.naver?query={urllib.parse.quote(name.encode('euc-kr'))}"
    res = requests.get(url)
    print("URL:", res.url)
    if 'item/main' in res.url:
        soup = BeautifulSoup(res.text, 'html.parser')
        price = soup.select_one('p.no_today span.blind')
        if price:
            print(price.text)
            
get_price("삼성전자")
get_price("KODEX 200TR")
