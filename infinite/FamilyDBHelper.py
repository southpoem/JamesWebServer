
import sqlite3
import datetime
import os

DB_PATH = r'C:\PycharmProjects\InfiniteProject\database\family_assets.db'

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS family_asset_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT,
            asset_type TEXT,
            amount REAL,
            updated_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def get_latest_family_assets():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT a.*
        FROM family_asset_history a
        INNER JOIN (
            SELECT account_name, MAX(updated_at) as max_date
            FROM family_asset_history
            GROUP BY account_name
        ) b ON a.account_name = b.account_name AND a.updated_at = b.max_date
    ''')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_family_asset(account_name, asset_type, amount):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO family_asset_history (account_name, asset_type, amount, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (account_name, asset_type, amount, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def update_family_asset(orig_account_name, new_account_name, asset_type, amount):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if orig_account_name != new_account_name:
        c.execute('UPDATE family_asset_history SET account_name = ? WHERE account_name = ?', (new_account_name, orig_account_name))
    c.execute('''
        INSERT INTO family_asset_history (account_name, asset_type, amount, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (new_account_name, asset_type, amount, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def delete_family_asset(account_name):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM family_asset_history WHERE account_name = ?', (account_name,))
    conn.commit()
    conn.close()


import pandas as pd
def get_family_history_df(target_dates=None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM family_asset_history", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame()
    df['date'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d')
    piv = df.pivot_table(index='date', columns='account_name', values='amount', aggfunc='last')
    
    if target_dates is not None and len(target_dates) > 0:
        target_dates_str = [pd.to_datetime(d).strftime('%Y-%m-%d') for d in target_dates]
        all_dates = sorted(set(list(piv.index) + target_dates_str))
    else:
        all_dates = sorted(list(piv.index))
        
    piv_full = piv.reindex(all_dates).ffill().bfill()
    
    melted = piv_full.reset_index().melt(id_vars=['date'], var_name='account_type', value_name='total_evaluation')
    melted['broker'] = '가족'
    melted['total_investment'] = melted['total_evaluation']
    melted['profit_loss'] = 0.0
    melted['quantity'] = 1.0
    melted['ticker'] = melted['account_type']
    melted['account_num'] = ''
    return melted
