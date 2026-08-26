import os
import glob

history_dir = r"C:\Users\이재혁\AppData\Roaming\Antigravity\User\History"
found_files = []

for root, _, files in os.walk(history_dir):
    for file in files:
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if '<!-- Broker Tabs -->' in content and '<!DOCTYPE html>' in content:
                    found_files.append((filepath, os.path.getmtime(filepath)))
        except:
            pass

found_files.sort(key=lambda x: x[1], reverse=True)
if found_files:
    print(f"Found {len(found_files)} backups!")
    latest = found_files[0][0]
    print("Latest backup:", latest)
    with open(latest, 'r', encoding='utf-8') as f:
        with open(r'C:\PycharmProjects\JamesWebServer\recovered_from_vscode.html', 'w', encoding='utf-8') as out:
            out.write(f.read())
    print("Recovered to recovered_from_vscode.html!")
else:
    print("No backup found.")
