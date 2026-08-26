import os
for root, _, files in os.walk(r'C:\PycharmProjects\JamesWebServer\templates'):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if '내 자산관리' in content or '무한매수법 현황' in content:
                        print(f"Found in {f}")
            except:
                pass
