import sqlite3
import pandas as pd
conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
df = pd.read_sql_query("SELECT DISTINCT ticker, current_price FROM asset_history WHERE date = (SELECT MAX(date) FROM asset_history) LIMIT 20", conn)
print(df)
conn.close()
