import streamlit as st
import pandas as pd
import ccxt
import time
from datetime import datetime, timedelta
import sys
import os

# ---------------------------------------------------------------------------
# [시스템 설정] 상위 폴더(web)의 key_config.py를 자동으로 찾는 코드
# ---------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))  # pages 폴더
parent_dir = os.path.dirname(current_dir)  # web 폴더 (상위)
sys.path.append(parent_dir)  # 경로 추가

try:
    import key_config
except ImportError:
    st.error(f"❌ '{parent_dir}' 경로에서 key_config.py를 찾을 수 없습니다.")
    st.stop()
# ---------------------------------------------------------------------------

st.set_page_config(layout="wide", page_title="실현 손익 리포트")

# === 1. 사이드바 설정 ===
st.sidebar.title("💰 거래 내역 조회")
target_coin = st.sidebar.selectbox("조회할 코인", ["USDT/KRW", "BTC/KRW", "ETH/KRW", "XRP/KRW"])

today = datetime.now()
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("시작일", today - timedelta(days=7))
end_date = col2.date_input("종료일", today)

run_btn = st.sidebar.button("조회 실행")


# === 2. 빗썸 API 연결 (직접 호출 방식으로 수정됨) ===
@st.cache_data(ttl=60)
def fetch_trade_history(symbol):
    try:
        bithumb = ccxt.bithumb({
            'apiKey': key_config.BITHUMB_ACCESS,
            'secret': key_config.BITHUMB_SECRET,
            'options': {'createMarketBuyOrderRequiresPrice': False}
        })

        # 기호 분리 (예: USDT/KRW -> order: USDT, payment: KRW)
        base, quote = symbol.split('/')

        # 빗썸 전용 '거래 완료 내역' API 호출
        # searchGb: 0=전체, 1=매수, 2=매도
        response = bithumb.private_post_info_user_transactions({
            "order_currency": base,
            "payment_currency": quote,
            "offset": 0,
            "count": 100,  # 최근 100건만 조회
            "searchGb": "0"
        })

        # 빗썸 응답 코드 확인 (0000: 성공)
        if response['status'] != '0000':
            return f"빗썸 에러: {response.get('message', '알 수 없는 오류')}"

        raw_data = response.get('data', [])

        # 데이터가 없는 경우 처리
        if not raw_data:
            return []

        # ccxt 표준 포맷으로 변환 (Standardization)
        formatted_trades = []
        for item in raw_data:
            # 빗썸 데이터: search 1(매수), 2(매도)
            side = 'buy' if item['search'] == '1' else 'sell'

            # 시간 변환 (마이크로초 -> 밀리초 -> datetime)
            try:
                ts = int(item['transfer_date']) / 1000
                dt = datetime.fromtimestamp(ts / 1000)
            except:
                dt = datetime.now()  # 에러시 현재시간 (방어코드)

            # 수수료 파싱 (예: "0.001 ETH" -> 0.001)
            fee_cost = 0.0
            fee_currency = quote
            if 'fee' in item and item['fee']:
                try:
                    fee_parts = item['fee'].split()
                    fee_cost = float(fee_parts[0])
                    if len(fee_parts) > 1: fee_currency = fee_parts[1]
                except:
                    pass

            # 숫자 콤마 제거 및 형변환
            try:
                price = float(str(item['price']).replace(',', ''))
                amount = float(str(item['units']).replace(',', ''))
                # 빗썸에서 'amount' 키는 총 거래액(Cost)을 의미함
                cost = float(str(item['amount']).replace(',', ''))
            except:
                continue

            formatted_trades.append({
                'datetime': dt,
                'symbol': symbol,
                'side': side,
                'price': price,
                'amount': amount,
                'cost': cost,
                'fee': {'cost': fee_cost, 'currency': fee_currency}
            })

        return formatted_trades

    except Exception as e:
        return f"API 오류: {str(e)}"


# === 3. 실현 손익 계산 (이동평균법) ===
def calculate_realized_pnl(trades):
    if isinstance(trades, str): return pd.DataFrame()  # 에러 문자열인 경우

    df = pd.DataFrame(trades)
    if df.empty: return pd.DataFrame()

    # 시간순 정렬 (과거 -> 현재)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')

    realized_profits = []

    # 평단가 계산 변수
    holding_qty = 0.0
    avg_buy_price = 0.0

    for _, row in df.iterrows():
        side = row['side']
        price = float(row['price'])
        amount = float(row['amount'])
        cost = float(row['cost'])

        # fee 처리 (안전하게)
        fee = 0.0
        if isinstance(row['fee'], dict):
            fee = float(row['fee'].get('cost', 0.0))

        ts = row['datetime']

        if side == 'buy':
            # 매수: 평단가 갱신
            total_value = (holding_qty * avg_buy_price) + cost
            total_qty = holding_qty + amount

            if total_qty > 0:
                avg_buy_price = total_value / total_qty
            holding_qty = total_qty

        elif side == 'sell':
            # 매도: 실현 손익 확정
            if holding_qty > 0:
                sell_qty = min(holding_qty, amount)

                # 수익 = (매도단가 - 평단가) * 수량 - 수수료
                gross_profit = (price - avg_buy_price) * sell_qty
                net_profit = gross_profit - fee

                profit_rate = 0.0
                if avg_buy_price > 0:
                    profit_rate = (net_profit / (avg_buy_price * sell_qty)) * 100

                realized_profits.append({
                    "time": ts,
                    "type": "SELL",
                    "price": price,
                    "avg_buy_price": round(avg_buy_price, 2),
                    "amount": sell_qty,
                    "profit": round(net_profit, 0),
                    "rate": round(profit_rate, 2)
                })

                holding_qty -= sell_qty
                if holding_qty < 0: holding_qty = 0

    return pd.DataFrame(realized_profits)


# === 4. 화면 표시 ===
st.title(f"📊 {target_coin} 실현 수익률 분석")
st.markdown("빗썸 계좌의 **매도 확정 내역**을 분석하여 실현 손익을 계산합니다.")
st.divider()

if run_btn:
    with st.spinner("빗썸 거래 내역 조회 중..."):
        raw_data = fetch_trade_history(target_coin)

        if isinstance(raw_data, str):
            st.error(raw_data)  # 에러 메시지 출력
        elif not raw_data:
            st.warning("조회된 거래 내역이 없습니다.")
        else:
            df_pnl = calculate_realized_pnl(raw_data)

            if not df_pnl.empty:
                # 날짜 필터링
                mask = (df_pnl['time'].dt.date >= start_date) & (df_pnl['time'].dt.date <= end_date)
                df_filtered = df_pnl.loc[mask]

                if not df_filtered.empty:
                    # 요약 통계
                    total_profit = df_filtered['profit'].sum()
                    win_count = len(df_filtered[df_filtered['profit'] > 0])
                    total_count = len(df_filtered)
                    win_rate = (win_count / total_count) * 100

                    c1, c2, c3 = st.columns(3)
                    c1.metric("💰 기간 총 실현손익", f"{int(total_profit):,}원", delta_color="normal")
                    c2.metric("📉 매도 횟수", f"{total_count}회")
                    c3.metric("🎯 승률 (익절)", f"{win_rate:.1f}%")

                    st.divider()

                    # 상세 테이블
                    st.subheader("📝 상세 매매 기록")
                    display_df = df_filtered[['time', 'amount', 'avg_buy_price', 'price', 'profit', 'rate']].copy()
                    display_df.columns = ['매도시간', '수량', '매수평단', '매도단가', '실현손익(원)', '수익률(%)']


                    # 스타일링 함수
                    def highlight_profit(val):
                        color = '#FF5252' if val > 0 else '#448AFF'
                        return f'color: {color}; font-weight: bold'


                    st.dataframe(
                        display_df.style.map(highlight_profit, subset=['실현손익(원)', '수익률(%)'])
                        .format({
                            '매도시간': lambda t: t.strftime('%Y-%m-%d %H:%M'),
                            '매수평단': "{:,.0f}",
                            '매도단가': "{:,.0f}",
                            '실현손익(원)': "{:,.0f}",
                            '수익률(%)': "{:.2f}%"
                        }),
                        use_container_width=True,
                        height=500
                    )
                else:
                    st.info(f"선택한 기간 ({start_date} ~ {end_date}) 내에 매도한 기록이 없습니다.")
            else:
                st.info("매도 확정된 수익 내역이 없습니다. (매수만 했거나 거래 없음)")
else:
    st.info("👈 왼쪽 사이드바에서 날짜를 선택하고 [조회 실행]을 눌러주세요.")