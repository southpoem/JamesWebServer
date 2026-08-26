import sqlite3

def init_excluded_db():
    conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS excluded_accounts (
        broker TEXT,
        account_num TEXT,
        PRIMARY KEY (broker, account_num)
    )''')
    conn.commit()
    conn.close()

init_excluded_db()
print("Excluded table created.")
