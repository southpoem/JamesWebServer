with open(r'C:\PycharmProjects\JamesWebServer\perfect_fix.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(r'C:\PycharmProjects\JamesWebServer\perfect_fix.py', 'w', encoding='utf-8') as f:
    for line in lines:
        if 'subprocess.run' in line and 'git' in line and 'restore' in line:
            continue
        f.write(line)
