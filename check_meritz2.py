
import sqlite3
import pandas as pd
conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
df = pd.read_sql_query('SELECT DISTINCT broker, account_type, account_num FROM asset_history WHERE broker LIKE \'%메리츠%\' OR broker LIKE \'%MERITZ%\'', conn)
print(df)
conn.close()

