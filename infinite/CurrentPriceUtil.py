import logging
import requests
from bs4 import BeautifulSoup

NYSEARCA = ["QLD", "SOXL", "LABU", "TMF", "BULZ"]


def fetch_current_price(ticker="TQQQ"):
    url = f'https://www.google.com/finance/quote/{ticker}'

    if ticker in NYSEARCA:
        url = url + ":NYSEARCA"
    else:
        url = url + ":NASDAQ"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_element = soup.find('div', class_='YMlKec fxKbKc')
        if not price_element:
            price_element = soup.find('span', class_='YMlKec')
        if not price_element:
            price_element = soup.find('div', class_='N6SYTe')
        if not price_element:
            price_element = soup.find(class_=lambda x: x and 'YMlKec' in x)
            
        if price_element:
            rate = price_element.text
        else:
            # Ultimate fallback: search for $ inside short strings and try to parse
            rate = None
            for tag in soup.find_all(['div', 'span']):
                txt = tag.text.strip() if tag.text else ""
                if txt.startswith('$') and len(txt) < 15:
                    val = txt.replace('$', '').replace(',', '').strip()
                    try:
                        float(val)
                        rate = txt
                        break
                    except ValueError:
                        continue
            if not rate:
                raise Exception(f"Cannot find price for {ticker} on Google Finance")
                
        rate = rate.replace('$', '').replace(',', '').strip()
        logging.info(f"fetch_current_price - {ticker} : {rate}")
        return float(rate)
    except Exception as e:
        logging.error(f"Error fetching current price for {ticker}: {e}")
        raise e
