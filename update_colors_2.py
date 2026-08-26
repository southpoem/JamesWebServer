import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''    samsung_colors = ['#4facfe', '#00f2fe', '#2980b9', '#3498db', '#6dd5ed']
    meritz_colors = ['#ff5252', '#ff1744', '#f50057', '#d50000', '#ff8a80']
    family_colors = ['#ffd700', '#ffeb3b', '#fbc02d', '#f57f17', '#ffee58']
    other_colors = ['#4caf50', '#9c27b0', '#ff9800', '#00bcd4', '#e91e63']'''

replace1 = '''    samsung_colors = ['#4facfe', '#00f2fe', '#2980b9', '#3498db', '#6dd5ed']
    meritz_colors = ['#ff5252', '#ff1744', '#f50057', '#d50000', '#ff8a80']
    family_colors = ['#ffd700', '#ffeb3b', '#fbc02d', '#f57f17', '#ffee58']
    other_colors = ['#ff5252', '#4facfe', '#ffd700', '#4caf50', '#9c27b0', '#ff9800', '#00bcd4', '#e91e63', '#8bc34a', '#3f51b5']'''

if target1 in content:
    content = content.replace(target1, replace1)

target2 = '''        if '삼성' in account_label:
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

replace2 = '''        if broker_filter in ['samsung', 'meritz']:
            color = other_colors[oth_idx % len(other_colors)]
            oth_idx += 1
        else:
            if '삼성' in account_label:
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

if target2 in content:
    content = content.replace(target2, replace2)
    with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target2 not found")
