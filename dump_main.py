with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_main.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 40:
            print(f"{i+1}: {line.strip()}")
