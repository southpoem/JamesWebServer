import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "    df['account_label'] = df['broker'] + ' ' + df['account_type'].apply(lambda x: re.sub(r'\([^)]*\)', '', str(x)).strip())"

replacement = '''    def get_account_label(row):
        broker = str(row['broker'])
        acc_type = re.sub(r'\([^)]*\)', '', str(row['account_type'])).strip()
        
        is_samsung = 'SAMSUNG' in broker.upper() or '삼성' in broker
        is_meritz = 'MERITZ' in broker.upper() or '메리츠' in broker
        is_family = '가족' in broker
        
        b_name = '삼성증권' if is_samsung else ('메리츠' if is_meritz else ('가족 수동자산' if is_family else broker))
        
        if broker_filter in ['samsung', 'meritz']:
            return f"{b_name} {acc_type}"
        else:
            return f"{b_name} 전체"

    df['account_label'] = df.apply(get_account_label, axis=1)'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
