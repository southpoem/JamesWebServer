import FinanceDataReader as fdr
import requests
from flask import Blueprint, jsonify

krx_map = {}

def get_live_prices(ticker_names):
    global krx_map
    if not krx_map:
        df_krx = fdr.StockListing('KRX')
        krx_map = dict(zip(df_krx['Name'], df_krx['Code']))
    
    codes = []
    name_to_code = {}
    for name in ticker_names:
        if name in krx_map:
            code = krx_map[name]
            codes.append(code)
            name_to_code[name] = code
            
    if not codes:
        return {}
        
    query = "SERVICE_ITEM:" + ",".join(codes)
    url = f"https://polling.finance.naver.com/api/realtime?query={query}"
    res = requests.get(url)
    data = res.json()
    
    live_prices = {}
    if data.get('resultCode') == 'success':
        items = data['result']['areas'][0]['datas']
        code_to_price = {item['cd']: item['nv'] for item in items}
        
        for name, code in name_to_code.items():
            if code in code_to_price:
                live_prices[name] = code_to_price[code]
                
    return live_prices

print(get_live_prices(["삼성전자", "KODEX 200TR"]))
