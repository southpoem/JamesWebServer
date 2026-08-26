import os

history_dir = r"C:\Users\이재혁\AppData\Roaming\Antigravity\User\History"
found = False
for root, _, files in os.walk(history_dir):
    for file in files:
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if '계좌별' in content and '주식별' in content and 'infinite_assets.html' not in content:
                    print(f"FOUND in {filepath}")
                    with open(r'C:\PycharmProjects\JamesWebServer\recovered_antigravity.html', 'w', encoding='utf-8') as out:
                        out.write(content)
                    found = True
                    break
        except:
            pass
    if found:
        break
if not found:
    print("Not found in Antigravity History.")
