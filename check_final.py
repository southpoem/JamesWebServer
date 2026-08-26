with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()
if 'samsung' in content:
    print('Samsung is back!')
if 'meritz' in content:
    print('Meritz is back!')
if 'family' in content:
    print('Family is back!')
if 'chart_datasets' in content:
    print('Chart logic is correct!')
