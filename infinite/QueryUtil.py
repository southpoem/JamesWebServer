from sqlalchemy import text

query_private = text("""
    SELECT ad.account_id, ad.date, ti.ticker, ti.current_round, ti.target_profit_rate,
           ti.total_investment, ti.total_shares, ti.current_price, ti.average_buy_price
    FROM ticker_info ti
    JOIN account_daily ad ON ti.account_daily_id = ad.id
    WHERE ad.date = :latest_date
      AND ad.account_id LIKE '%private%'
    ORDER BY ad.account_id, ti.ticker
""")
