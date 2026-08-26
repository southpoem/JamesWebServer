with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_main.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i > 100 and i < 150:
            print(f"{i+1}: {line.strip().encode('utf-8', errors='ignore')}")
