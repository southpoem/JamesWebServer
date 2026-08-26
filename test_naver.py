import requests
from bs4 import BeautifulSoup
import urllib.parse

def get_price(name):
    url = f"https://finance.naver.com/search/searchList.naver?query={urllib.parse.quote(name.encode('euc-kr'))}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    td = soup.select_one('td.num')
    if td:
        return td.text.strip()
    return None

print(get_price("삼성전자"))
print(get_price("KODEX 200TR"))
