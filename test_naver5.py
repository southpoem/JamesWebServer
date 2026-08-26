import requests
import urllib.parse
from bs4 import BeautifulSoup

url = f"https://finance.naver.com/search/searchList.naver?query={urllib.parse.quote('삼성전자'.encode('euc-kr'))}"
res = requests.get(url)
print(res.text[:500])
