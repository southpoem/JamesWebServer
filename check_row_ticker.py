with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()
if 'row.ticker' in content:
    print("row.ticker IS present!")
else:
    print("row.ticker IS NOT present!")
