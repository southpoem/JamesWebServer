with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open(r'C:\PycharmProjects\JamesWebServer\dump3.txt', 'w', encoding='utf-8') as fw:
    for i in range(410, min(480, len(lines))):
        fw.write(f"{i+1}: {lines[i].strip()}\n")
