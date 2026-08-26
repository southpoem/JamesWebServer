with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_main.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '내 자산관리' in line or '무한매수법 현황' in line:
            print(f"Line {i+1}: {line.strip()}")
