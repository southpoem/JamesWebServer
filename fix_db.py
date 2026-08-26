with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
content = re.sub(r"sqlite3\.connect\(r'C:\\PycharmProjects\\InfiniteProject[^']*'\)", "sqlite3.connect(DB_PATH)", content)

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed DB path.")
