import logging

import requests
from bs4 import BeautifulSoup

NYSEARCA = ["QLD", "SOXL", "LABU", "TMF"]


def fetch_current_price(ticker="TQQQ"):
    url = f'https://www.google.com/finance/quote/{ticker}'

    if ticker in NYSEARCA:
        url = url + ":NYSEARCA"
    else:
        url = url + ":NASDAQ"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    response = requests.get(url, headers=headers, timeout=3)
    soup = BeautifulSoup(response.text, 'html.parser')
    rate = soup.find('div', class_='YMlKec fxKbKc').text
    rate = rate.replace('$', '').replace(',', '')
    logging.info(f"fetch_current_price - {ticker} : {rate}")
    return float(rate.replace(',', ''))

# fetch_current_price("LABU")
