import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update get_account_label
target_label = '''    def get_account_label(row):
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

replace_label = '''    def get_account_label(row):
        broker = str(row['broker'])
        acc_type = re.sub(r'\([^)]*\)', '', str(row['account_type'])).strip()
        acc_num = str(row.get('account_num', 'nan'))
        if acc_num == 'nan' or not acc_num:
            acc_num = ''
        
        is_samsung = 'SAMSUNG' in broker.upper() or '삼성' in broker
        is_meritz = 'MERITZ' in broker.upper() or '메리츠' in broker
        is_family = '가족' in broker
        
        if broker_filter in ['samsung', 'meritz']:
            b_name = '삼성증권' if is_samsung else ('메리츠' if is_meritz else ('가족' if is_family else broker))
            if is_family or not acc_num:
                return f"{b_name} {acc_type}"
            masked_num = '*' + acc_num[-5:] if len(acc_num) >= 5 else acc_num
            return f"{b_name} {acc_type} ({masked_num})"
        else:
            if is_samsung: return "삼성"
            if is_meritz: return "메리츠"
            if is_family: return "가족"
            return broker'''

if target_label in content:
    content = content.replace(target_label, replace_label)
else:
    print("target_label not found")

# 2. Update Color logic
target_color = '''    chart_datasets = []
    colors = ['#ff5252', '#4facfe', '#ffd700', '#4caf50', '#9c27b0', '#ff9800', '#00bcd4', '#e91e63', '#8bc34a', '#3f51b5']
    color_idx = 0'''

replace_color = '''    chart_datasets = []
    
    samsung_colors = ['#4facfe', '#00f2fe', '#2980b9', '#3498db', '#6dd5ed']
    meritz_colors = ['#ff5252', '#ff1744', '#f50057', '#d50000', '#ff8a80']
    family_colors = ['#ffd700', '#ffeb3b', '#fbc02d', '#f57f17', '#ffee58']
    other_colors = ['#4caf50', '#9c27b0', '#ff9800', '#00bcd4', '#e91e63']
    
    sam_idx = 0
    mer_idx = 0
    fam_idx = 0
    oth_idx = 0'''

if target_color in content:
    content = content.replace(target_color, replace_color)
else:
    print("target_color not found")

target_color_apply = '''        color = colors[color_idx % len(colors)]
        color_idx += 1'''

replace_color_apply = '''        if '삼성' in account_label:
            color = samsung_colors[sam_idx % len(samsung_colors)]
            sam_idx += 1
        elif '메리츠' in account_label:
            color = meritz_colors[mer_idx % len(meritz_colors)]
            mer_idx += 1
        elif '가족' in account_label:
            color = family_colors[fam_idx % len(family_colors)]
            fam_idx += 1
        else:
            color = other_colors[oth_idx % len(other_colors)]
            oth_idx += 1'''

if target_color_apply in content:
    content = content.replace(target_color_apply, replace_color_apply)
else:
    print("target_color_apply not found")

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Update complete")
