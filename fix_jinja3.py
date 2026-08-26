with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the escaped quotes
content = content.replace(r"\'", "'")

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)
