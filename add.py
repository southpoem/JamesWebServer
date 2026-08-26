with open(r'C:\PycharmProjects\JamesWebServer\infinite\FamilyDBHelper.py', 'a', encoding='utf-8') as f:
    f.write('''
import pandas as pd
def get_family_history_df():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM family_asset_history", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame()
    df['date'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d')
    df_grouped = df.groupby(['date', 'account_name'])['amount'].last().reset_index()
    df_grouped = df_grouped.rename(columns={'account_name': 'account_type', 'amount': 'total_evaluation'})
    df_grouped['broker'] = '가족'
    return df_grouped
''')
