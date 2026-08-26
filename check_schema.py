
import sqlite3
import pandas as pd
conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
df = pd.read_sql_query('SELECT * FROM asset_history LIMIT 1', conn)
print(df.columns)

