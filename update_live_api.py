import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        if res_data.get('resultCode') == 'success':
            items = res_data['result']['areas'][0]['datas']
            code_to_price = {item['cd']: item['nv'] for item in items}
            
            for name, code in name_to_code.items():
                if code in code_to_price:
                    live_prices[name] = code_to_price[code]'''

replacement = '''        if res_data.get('resultCode') == 'success':
            items = res_data['result']['areas'][0]['datas']
            code_to_data = {item['cd']: {
                'nv': item['nv'],
                'cv': item['cv'],
                'cr': item['cr'],
                'rf': item['rf']
            } for item in items}
            
            for name, code in name_to_code.items():
                if code in code_to_data:
                    live_prices[name] = code_to_data[code]'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("InfiniteServer updated")
else:
    print("Target not found")
