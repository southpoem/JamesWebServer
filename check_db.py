
import sqlite3
import pandas as pd
conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
df = pd.read_sql_query('SELECT broker, MIN(date) as first_date, MAX(date) as last_date, COUNT(*) as cnt FROM asset_history GROUP BY broker', conn)
print(df)
conn.close()

conn2 = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\database\family_assets.db')
try:
    df2 = pd.read_sql_query('SELECT account_name, MIN(updated_at) as first_date, MAX(updated_at) as last_date FROM family_asset_history GROUP BY account_name', conn2)
    print(df2)
except Exception as e:
    print('family db error:', e)
conn2.close()

