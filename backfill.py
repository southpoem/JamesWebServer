
import sqlite3
import pandas as pd
from datetime import timedelta, datetime

def backfill():
    # 1. Main DB
    conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
    df = pd.read_sql_query('SELECT * FROM asset_history', conn)
    
    # Get all distinct dates in the db
    all_dates = sorted(df['date'].unique())
    if not all_dates:
        return
    global_min_date_str = all_dates[0]
    
    # Backfill Meritz
    df_meritz = df[df['broker'].str.contains('MERITZ|메리츠', case=False, na=False)]
    if not df_meritz.empty:
        meritz_min_date = df_meritz['date'].min()
        if meritz_min_date > global_min_date_str:
            print(f'Backfilling Meritz from {meritz_min_date} to {global_min_date_str}')
            meritz_first_day_data = df_meritz[df_meritz['date'] == meritz_min_date]
            
            # Find missing dates
            missing_dates = [d for d in all_dates if d < meritz_min_date]
            new_rows = []
            for d in missing_dates:
                for _, row in meritz_first_day_data.iterrows():
                    new_row = row.to_dict()
                    new_row['date'] = d
                    new_rows.append(new_row)
            
            if new_rows:
                pd.DataFrame(new_rows).to_sql('asset_history', conn, if_exists='append', index=False)
                print(f'Inserted {len(new_rows)} rows for Meritz')
                
    conn.commit()
    conn.close()

    # 2. Family DB
    conn2 = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\database\family_assets.db')
    c2 = conn2.cursor()
    c2.execute('SELECT * FROM family_asset_history')
    rows = c2.fetchall()
    
    if rows:
        # columns: id, account_name, asset_type, amount, updated_at
        df_fam = pd.DataFrame(rows, columns=['id', 'account_name', 'asset_type', 'amount', 'updated_at'])
        
        for name in df_fam['account_name'].unique():
            df_acc = df_fam[df_fam['account_name'] == name]
            first_dt_str = df_acc['updated_at'].min()
            first_date_str = first_dt_str[:10]
            
            missing_dates = [d for d in all_dates if d < first_date_str]
            if missing_dates:
                first_row = df_acc[df_acc['updated_at'] == first_dt_str].iloc[0]
                
                for d in missing_dates:
                    new_dt = f'{d} 00:00:00'
                    c2.execute('''
                        INSERT INTO family_asset_history (account_name, asset_type, amount, updated_at)
                        VALUES (?, ?, ?, ?)
                    ''', (first_row['account_name'], first_row['asset_type'], first_row['amount'], new_dt))
                print(f'Backfilled family account {name} for {len(missing_dates)} days')
                
    conn2.commit()
    conn2.close()

backfill()

