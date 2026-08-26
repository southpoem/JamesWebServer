import sqlite3
import pandas as pd
import json
conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
df = pd.read_sql_query("SELECT DISTINCT ticker FROM asset_history", conn)
print(json.dumps(df['ticker'].tolist(), ensure_ascii=False))
conn.close()
