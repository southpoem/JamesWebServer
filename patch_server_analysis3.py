import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    data = {
        'today_str': today.strftime('%Y-%m-%d'),
        'last_update_time': last_update_time,
        'total_today': total_today,
        'change_1d': total_today - total_yesterday if yesterday else 0,
        'change_7d': total_today - total_last_week if last_week else 0,
        'change_30d': total_today - total_last_month if last_month else 0,
        'account_summary': account_summary,
        'ticker_summary': ticker_summary,
        'chart_dates': chart_dates,
        'chart_datasets': chart_datasets,
        'detailed_list': detailed_list,
        'family_assets': family_assets,
        'all_accounts_list': all_accounts_list
    }'''

replacement = '''
    # --- Analysis Data Preparation ---
    analysis_data = {}
    if broker_filter == 'analysis':
        all_items = []
        for tk in ticker_summary:
            all_items.append({'name': tk['ticker'], 'amount': tk['total_evaluation']})
        for fa in family_assets:
            all_items.append({'name': fa['account_name'] + ' (' + fa['asset_type'] + ')', 'amount': fa['amount']})
            
        us_keywords = ['미국', 'QQQ', 'S&P', 'DIREXION', 'PROSHARES', '나스닥']
        cash_keywords = ['현금', '예수금', 'MMF', 'CMA']
        semi_keywords = ['반도체', 'SEMICONDUCTOR', '삼성전자', 'SK하이닉스']
        index_keywords = ['나스닥', 'QQQ', 'S&P', '200TR', '지수']
        bond_keywords = ['채권', '혼합']
        
        country_group = {'미국 자산': 0, '한국 자산': 0}
        sector_group = {}
        stock_group = {}
        
        for item in all_items:
            name = item['name'].upper()
            amt = item['amount']
            
            # 1. Country Group
            if any(k in name for k in cash_keywords):
                pass # cash shouldn't be counted in US vs KR according to standard, but if we do, it's KR.
            if any(k in name for k in us_keywords):
                country_group['미국 자산'] += amt
            else:
                country_group['한국 자산'] += amt
                
            # 2. Sector Group
            sector = '기타'
            if any(k in name for k in cash_keywords): sector = '현금 (Cash)'
            elif any(k in name for k in semi_keywords): sector = '반도체 (Semiconductor)'
            elif any(k in name for k in index_keywords): sector = '시장지수 (Index)'
            elif any(k in name for k in bond_keywords): sector = '채권/혼합 (Bond/Mixed)'
            elif '보험' in name: sector = '보험 (Insurance)'
            
            sector_group[sector] = sector_group.get(sector, 0) + amt
            
            # 3. Stock Group
            stock_group[item['name']] = stock_group.get(item['name'], 0) + amt
            
        analysis_data = {
            'country': [{'label': k, 'value': v} for k, v in country_group.items() if v > 0],
            'sector': [{'label': k, 'value': v} for k, v in sector_group.items() if v > 0],
            'stock': [{'label': k, 'value': v} for k, v in stock_group.items() if v > 0]
        }
        
        # Sort desc
        analysis_data['country'].sort(key=lambda x: x['value'], reverse=True)
        analysis_data['sector'].sort(key=lambda x: x['value'], reverse=True)
        analysis_data['stock'].sort(key=lambda x: x['value'], reverse=True)

    data = {
        'today_str': today.strftime('%Y-%m-%d'),
        'last_update_time': last_update_time,
        'total_today': total_today,
        'change_1d': total_today - total_yesterday if yesterday else 0,
        'change_7d': total_today - total_last_week if last_week else 0,
        'change_30d': total_today - total_last_month if last_month else 0,
        'account_summary': account_summary,
        'ticker_summary': ticker_summary,
        'chart_dates': chart_dates,
        'chart_datasets': chart_datasets,
        'detailed_list': detailed_list,
        'family_assets': family_assets,
        'all_accounts_list': all_accounts_list,
        'analysis_data': analysis_data
    }'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Analysis data logic added.")
else:
    print("Target data dict not found.")
