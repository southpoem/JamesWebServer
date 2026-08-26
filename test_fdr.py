import FinanceDataReader as fdr

try:
    df_krx = fdr.StockListing('KRX')
    print(df_krx[['Code', 'Name']].head())
except Exception as e:
    print(e)
