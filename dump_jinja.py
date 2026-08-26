with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '{%' in line or 'data' in line:
            if i > 250:
                print(f"Line {i+1}: {line.strip().encode('utf-8', errors='ignore')}")
