with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'endif' in line:
            print(f"{i+1}: {line.strip()}")
