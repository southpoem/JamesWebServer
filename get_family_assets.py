import sqlite3
import pandas as pd
import json
try:
    conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\database\family_assets.db')
    df = pd.read_sql_query("SELECT DISTINCT asset_type FROM family_asset_history", conn)
    print(json.dumps(df['asset_type'].tolist(), ensure_ascii=False))
    conn.close()
except Exception as e:
    print(e)
