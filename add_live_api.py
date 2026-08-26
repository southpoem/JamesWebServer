import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

live_price_api = '''
import FinanceDataReader as fdr
import requests
import threading

krx_map_cache = {}
krx_map_lock = threading.Lock()

def get_krx_map():
    global krx_map_cache
    with krx_map_lock:
        if not krx_map_cache:
            try:
                df_krx = fdr.StockListing('KRX')
                df_etf = fdr.StockListing('ETF/KR')
                for _, row in df_krx.iterrows():
                    krx_map_cache[row['Name']] = row['Code']
                for _, row in df_etf.iterrows():
                    krx_map_cache[row['Name']] = row['Symbol']
            except Exception as e:
                logging.error(f"Failed to load KRX/ETF list: {e}")
    return krx_map_cache

@infinite_bp.route('/api/live_prices', methods=['POST'])
@login_required
def api_live_prices():
    data = request.json
    tickers = data.get('tickers', [])
    
    krx_map = get_krx_map()
    
    codes = []
    name_to_code = {}
    for name in tickers:
        if name in krx_map:
            code = krx_map[name]
            codes.append(code)
            name_to_code[name] = code
            
    if not codes:
        return jsonify({})
        
    query = "SERVICE_ITEM:" + ",".join(codes)
    url = f"https://polling.finance.naver.com/api/realtime?query={query}"
    try:
        res = requests.get(url, timeout=5)
        res_data = res.json()
        
        live_prices = {}
        if res_data.get('resultCode') == 'success':
            items = res_data['result']['areas'][0]['datas']
            code_to_price = {item['cd']: item['nv'] for item in items}
            
            for name, code in name_to_code.items():
                if code in code_to_price:
                    live_prices[name] = code_to_price[code]
                    
        return jsonify(live_prices)
    except Exception as e:
        logging.error(f"Live price fetch error: {e}")
        return jsonify({})

@infinite_bp.route('/toggle_exclude', methods=['POST'])'''

content = content.replace("@infinite_bp.route('/toggle_exclude', methods=['POST'])", live_price_api)

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("API route added.")
