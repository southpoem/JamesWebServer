import pandas as pd


def calculate_forex_difference_by_date(file_path: str) -> None:
    import pandas as pd

    df = pd.read_csv(file_path, encoding='cp949')

    df_even = df.iloc[1::2].reset_index(drop=True)
    df_odd = df.iloc[2::2].reset_index(drop=True)

    df_even = df_even[df_even['환전구분'].isin(['외화매수', '외화매도'])].reset_index(drop=True)
    df_even['원화금액'] = df_odd['외화금액'].astype(str).str.replace(',', '').astype(float)

    summary = df_even.groupby(['일자', '환전구분'])['원화금액'].sum().unstack(fill_value=0)
    summary['차액(매도 - 매수)'] = summary.get('외화매도', 0) - summary.get('외화매수', 0)

    for index, row in summary.iterrows():
        print(f"[{index}]")
        print(f"총 매수 금액: {row.get('외화매수', 0):,.0f} 원")
        print(f"총 매도 금액: {row.get('외화매도', 0):,.0f} 원")
        print(f"차액 (매도 - 매수): {row['차액(매도 - 매수)']:,.0f} 원\n")


def calculate_forex_difference_verbose(file_path: str) -> None:
    import pandas as pd

    df = pd.read_csv(file_path, encoding='cp949')

    df_even = df.iloc[1::2].reset_index(drop=True)
    df_odd = df.iloc[2::2].reset_index(drop=True)

    df_even = df_even[df_even['환전구분'].isin(['외화매수', '외화매도'])].reset_index(drop=True)
    df_even['원화금액'] = df_odd['외화금액'].astype(str).str.replace(',', '').astype(float)

    total_buy = df_even[df_even['환전구분'] == '외화매수']['원화금액'].sum()
    total_sell = df_even[df_even['환전구분'] == '외화매도']['원화금액'].sum()
    difference = total_sell - total_buy

    print(f"총 매수 금액: {total_buy:,.0f} 원")
    print(f"총 매도 금액: {total_sell:,.0f} 원")
    print(f"차액 (매도 - 매수): {difference:,.0f} 원")


calculate_forex_difference_by_date("C:\\PycharmProjects\\InfiniteProject\\currency.csv")
calculate_forex_difference_verbose("C:\\PycharmProjects\\InfiniteProject\\currency.csv")
