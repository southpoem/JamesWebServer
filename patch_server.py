import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add route for toggle_exclude
route_code = '''
@infinite_bp.route('/toggle_exclude', methods=['POST'])
@login_required
def toggle_exclude():
    broker = request.form.get('broker')
    account_num = request.form.get('account_num')
    is_excluded = request.form.get('is_excluded') == 'true'
    
    conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
    c = conn.cursor()
    if is_excluded:
        c.execute("INSERT OR IGNORE INTO excluded_accounts (broker, account_num) VALUES (?, ?)", (broker, account_num))
    else:
        c.execute("DELETE FROM excluded_accounts WHERE broker = ? AND account_num = ?", (broker, account_num))
    conn.commit()
    conn.close()
    
    return redirect(url_for('infinite.assets', broker=request.args.get('broker', 'samsung')))

@infinite_bp.route('/assets')'''

content = content.replace("@infinite_bp.route('/assets')", route_code)

# 2. Add filtering logic in assets route
target_fetch = '''    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM asset_history", conn)
        conn.close()
    except Exception as e:
        logging.error(f"Asset history DB error: {e}")
        return render_template('infinite_assets.html', error=f"DB Error: {e}", data=None, current_broker='samsung')

    if df.empty:
        return render_template('infinite_assets.html', data=None, current_broker='samsung')'''

replacement_fetch = '''    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM asset_history", conn)
        
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS excluded_accounts (broker TEXT, account_num TEXT, PRIMARY KEY (broker, account_num))")
        excluded_df = pd.read_sql_query("SELECT broker, account_num FROM excluded_accounts", conn)
        excluded_list = excluded_df.to_dict('records')
        conn.close()
    except Exception as e:
        logging.error(f"Asset history DB error: {e}")
        return render_template('infinite_assets.html', error=f"DB Error: {e}", data=None, current_broker='samsung')

    if df.empty:
        return render_template('infinite_assets.html', data=None, current_broker='samsung')
        
    all_accounts_df = df[['broker', 'account_type', 'account_num']].drop_duplicates()
    all_accounts_list = all_accounts_df.to_dict('records')
    for acc in all_accounts_list:
        acc['is_excluded'] = any(e['broker'] == acc['broker'] and e['account_num'] == acc['account_num'] for e in excluded_list)
        acc['masked_num'] = '*' + str(acc['account_num'])[-5:] if len(str(acc['account_num'])) >= 5 else str(acc['account_num'])
        b_str = str(acc['broker']).upper()
        acc['broker_clean'] = '삼성증권' if 'SAMSUNG' in b_str or '삼성' in b_str else ('메리츠' if 'MERITZ' in b_str or '메리츠' in b_str else str(acc['broker']))

    for excl in excluded_list:
        df = df[~((df['broker'] == excl['broker']) & (df['account_num'] == excl['account_num']))]'''

if target_fetch in content:
    content = content.replace(target_fetch, replacement_fetch)
else:
    print("Fetch logic not found!")

# 3. Add all_accounts_list to data dict
target_data = '''        'family_assets': family_assets
    }'''
replacement_data = '''        'family_assets': family_assets,
        'all_accounts_list': all_accounts_list
    }'''

if target_data in content:
    content = content.replace(target_data, replacement_data)
else:
    print("Data dict not found!")

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("InfiniteServer.py updated.")
