import sqlite3
import pandas as pd
conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
df = pd.read_sql_query("SELECT DISTINCT ticker FROM asset_history", conn)
print(df['ticker'].tolist())
conn.close()
