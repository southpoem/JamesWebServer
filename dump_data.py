with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = -1
for i, line in enumerate(lines):
    if "data = {" in line and "today_str" in lines[i+1]:
        start = i
        break
if start != -1:
    for j in range(start, start + 30):
        print(f"{j+1}: {lines[j].strip()}")
