import requests

def get_price(name):
    url = f"https://finance.naver.com/search/searchList.naver?query={name.encode('euc-kr').hex('%')}"
    res = requests.get(url)
    print("URL:", res.url)

get_price("삼성전자")
