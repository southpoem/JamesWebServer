
import os, re
dirs = [r'C:\PycharmProjects\JamesWebServer', r'C:\PycharmProjects\InfiniteProject']
pattern = re.compile(r'((http://|https://)?[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]+)?)')
for d in dirs:
    if not os.path.exists(d): continue
    for root, _, files in os.walk(d):
        if '.venv' in root or '__pycache__' in root or '.git' in root: continue
        for f in files:
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    for i, line in enumerate(file):
                        m = pattern.search(line)
                        if m:
                            print(f'{path}:{i+1}: {m.group(0)}')
            except Exception:
                pass

