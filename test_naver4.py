import requests
import urllib.parse
from bs4 import BeautifulSoup

def get_price(name):
    url = f"https://finance.naver.com/search/searchList.naver?query={urllib.parse.quote(name.encode('euc-kr'))}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    for tr in soup.select('table.tbl_search tbody tr'):
        tds = tr.select('td')
        if tds:
            stock_name = tds[0].text.strip()
            price = tds[1].text.strip()
            print(stock_name, price)

get_price("삼성전자")
