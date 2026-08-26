import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    def get_account_label(row):
        broker = str(row['broker'])
        acc_type = re.sub(r'\([^)]*\)', '', str(row['account_type'])).strip()
        
        is_samsung = 'SAMSUNG' in broker.upper() or '삼성' in broker
        is_meritz = 'MERITZ' in broker.upper() or '메리츠' in broker
        is_family = '가족' in broker
        
        b_name = '삼성증권' if is_samsung else ('메리츠' if is_meritz else ('가족 수동자산' if is_family else broker))
        
        if broker_filter in ['samsung', 'meritz']:
            return f"{b_name} {acc_type}"
        else:
            return f"{b_name} 전체"'''

replacement = '''    def get_account_label(row):
        broker = str(row['broker'])
        acc_type = re.sub(r'\([^)]*\)', '', str(row['account_type'])).strip()
        acc_num = str(row.get('account_num', 'nan'))
        if acc_num == 'nan' or not acc_num:
            acc_num = ''
        
        is_samsung = 'SAMSUNG' in broker.upper() or '삼성' in broker
        is_meritz = 'MERITZ' in broker.upper() or '메리츠' in broker
        is_family = '가족' in broker
        
        b_name = '삼성증권' if is_samsung else ('메리츠' if is_meritz else ('가족 수동자산' if is_family else broker))
        
        if broker_filter in ['samsung', 'meritz']:
            if is_family or not acc_num:
                return f"{b_name} {acc_type}"
            masked_num = '*' + acc_num[-5:] if len(acc_num) >= 5 else acc_num
            return f"{b_name} {acc_type} ({masked_num})"
        else:
            return f"{b_name} 전체"'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
