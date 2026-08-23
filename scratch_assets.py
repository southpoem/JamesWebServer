import pandas as pd
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "C:\\PycharmProjects\\InfiniteProject\\account.db"

def get_asset_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM asset_history", conn)
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
        return None

    if df.empty:
        return None

    df['date'] = pd.to_datetime(df['date'])
    available_dates = sorted(df['date'].unique())
    today = available_dates[-1]
    
    def get_closest_date(target_date):
        past_dates = [d for d in available_dates if d <= target_date]
        return past_dates[-1] if past_dates else None

    yesterday = get_closest_date(today - pd.Timedelta(days=1))
    if yesterday == today:
        past_dates = [d for d in available_dates if d < today]
        yesterday = past_dates[-1] if past_dates else None

    last_week = get_closest_date(today - pd.Timedelta(days=7))
    if last_week == today:
        last_week = None

    last_month = get_closest_date(today - pd.Timedelta(days=30))
    if last_month == today:
        last_month = None

    def get_totals(dt):
        if dt is None:
            return 0
        return df[df['date'] == dt]['total_evaluation'].sum()

    total_today = get_totals(today)
    total_yesterday = get_totals(yesterday)
    total_last_week = get_totals(last_week)
    total_last_month = get_totals(last_month)

    df_today = df[df['date'] == today]
    account_summary = df_today.groupby(['account_type', 'account_num', 'broker']).agg({
        'total_investment': 'sum',
        'total_evaluation': 'sum',
        'profit_loss': 'sum'
    }).reset_index().to_dict('records')

    ticker_summary = df_today.groupby('ticker').agg({
        'total_evaluation': 'sum',
        'profit_loss': 'sum',
        'quantity': 'sum'
    }).reset_index().to_dict('records')

    data = {
        'today_str': today.strftime('%Y-%m-%d'),
        'total_today': total_today,
        'change_1d': total_today - total_yesterday if yesterday else 0,
        'change_7d': total_today - total_last_week if last_week else 0,
        'change_30d': total_today - total_last_month if last_month else 0,
        'account_summary': account_summary,
        'ticker_summary': ticker_summary
    }
    return data

if __name__ == '__main__':
    print(get_asset_data())
