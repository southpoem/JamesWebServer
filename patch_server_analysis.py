import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    broker_filter = request.args.get('broker', 'samsung')
    if broker_filter == 'samsung':
        df = df[df['broker'].str.upper().str.contains('SAMSUNG|삼성', na=False)]
    elif broker_filter == 'meritz':
        df = df[df['broker'].str.upper().str.contains('MERITZ|메리츠', na=False)]'''

replacement = '''    broker_filter = request.args.get('broker', 'samsung')
    if broker_filter == 'analysis':
        # No filtering, use all
        pass
    elif broker_filter == 'samsung':
        df = df[df['broker'].str.upper().str.contains('SAMSUNG|삼성', na=False)]
    elif broker_filter == 'meritz':
        df = df[df['broker'].str.upper().str.contains('MERITZ|메리츠', na=False)]'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("InfiniteServer.py updated for analysis filter.")
else:
    print("Target not found in InfiniteServer.py")
