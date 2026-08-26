with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if '⚙️ 계좌 합산 관리' in line:
            print(f'Found at line {i}')
            print(''.join(lines[i-2:i+30]))
            break
