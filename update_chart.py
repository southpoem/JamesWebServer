import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    chart_data_df = df.groupby('date')['total_evaluation'].sum().reset_index()
    chart_dates = chart_data_df['date'].dt.strftime('%Y-%m-%d').tolist()
    chart_totals = chart_data_df['total_evaluation'].tolist()

    missing_today_data = False
    actual_today = datetime.now().date()
    if chart_dates and pd.to_datetime(chart_dates[-1]).date() < actual_today:
        missing_today_data = True
        chart_dates.append(actual_today.strftime('%Y-%m-%d') + ' (미포함)')
        chart_totals.append(chart_totals[-1])

    detailed_list = df_today.sort_values(by=['account_type', 'account_num', 'total_evaluation'], ascending=[True, True, False]).to_dict('records')

    db_mtime = os.path.getmtime(DB_PATH)
    last_update_time = datetime.fromtimestamp(db_mtime).strftime('%Y-%m-%d %H:%M:%S')

    from infinite import FamilyDBHelper
    family_assets = []
    if broker_filter == 'family':
        try:
            family_assets = FamilyDBHelper.get_latest_family_assets()
            for fa in family_assets:
                total_today += fa['amount']
        except Exception as e:
            logging.error(f"Failed to load family assets: {e}")'''

replacement = '''    from infinite import FamilyDBHelper
    family_assets = []
    if broker_filter == 'family':
        try:
            family_assets = FamilyDBHelper.get_latest_family_assets()
            for fa in family_assets:
                total_today += fa['amount']
                
            fam_df = FamilyDBHelper.get_family_history_df()
            if not fam_df.empty:
                fam_df['date'] = pd.to_datetime(fam_df['date'])
                df = pd.concat([df, fam_df], ignore_index=True)
        except Exception as e:
            logging.error(f"Failed to load family assets: {e}")

    chart_dates_dt = sorted(df['date'].unique())
    chart_dates = [d.strftime('%Y-%m-%d') for d in chart_dates_dt]
    
    missing_today_data = False
    actual_today = datetime.now().date()
    if chart_dates and pd.to_datetime(chart_dates[-1]).date() < actual_today:
        missing_today_data = True
        chart_dates.append(actual_today.strftime('%Y-%m-%d') + ' (미포함)')
    
    chart_datasets = []
    colors = ['#ff5252', '#4facfe', '#ffd700', '#4caf50', '#9c27b0', '#ff9800', '#00bcd4', '#e91e63', '#8bc34a', '#3f51b5']
    color_idx = 0
    
    df['account_label'] = df['broker'] + ' ' + df['account_type'].apply(lambda x: re.sub(r'\([^)]*\)', '', str(x)).strip())
    latest_date = df['date'].max()
    latest_totals = df[df['date'] == latest_date].groupby('account_label')['total_evaluation'].sum().sort_values(ascending=False)
    
    for account_label in latest_totals.index:
        group = df[df['account_label'] == account_label]
        date_vals = group.groupby('date')['total_evaluation'].sum().to_dict()
        data_arr = []
        last_val = 0
        for d in chart_dates_dt:
            val = date_vals.get(d, last_val)
            data_arr.append(float(val))
            last_val = val
        if missing_today_data:
            data_arr.append(data_arr[-1])
            
        color = colors[color_idx % len(colors)]
        color_idx += 1
        
        chart_datasets.append({
            'label': account_label,
            'data': data_arr,
            'borderColor': color,
            'backgroundColor': color + '33',
            'borderWidth': 2,
            'tension': 0.4,
            'fill': True,
            'pointRadius': 2
        })
        
    detailed_list = df_today.sort_values(by=['account_type', 'account_num', 'total_evaluation'], ascending=[True, True, False]).to_dict('records')
    db_mtime = os.path.getmtime(DB_PATH)
    last_update_time = datetime.fromtimestamp(db_mtime).strftime('%Y-%m-%d %H:%M:%S')'''

if target in content:
    content = content.replace(target, replacement)
    
    # Also update data dict to include chart_datasets
    data_dict_target = '''        'chart_dates': chart_dates,
        'chart_totals': chart_totals,
        'detailed_list': detailed_list,'''
        
    data_dict_rep = '''        'chart_dates': chart_dates,
        'chart_datasets': chart_datasets,
        'detailed_list': detailed_list,'''
    content = content.replace(data_dict_target, data_dict_rep)
    
    with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
