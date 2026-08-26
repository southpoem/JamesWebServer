import FinanceDataReader as fdr
df = fdr.StockListing('ETF/KR')
print(df[df['Name'].str.contains('KODEX 200')][['Symbol', 'Name']].head())
