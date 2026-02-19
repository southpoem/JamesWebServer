import streamlit as st
import json
import pandas as pd
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 1. 페이지 설정
st.set_page_config(layout="centered", page_title="Tether Bot Dashboard")

# === 테마 관리 (Dark Mode 고정) ===
is_dark = True

# --- 눈이 편안한 색상 테마 (Soft Gray) ---
if is_dark:
    theme = {
        "bg_color": "#1e1e1e",
        "text_color": "#d4d4d4",
        "box_bg": "#252526",
        "border_color": "#3e3e42",
        "th_bg": "#2d2d2d",
        "th_text": "#cccccc",
        "grid_color": "rgba(255,255,255,0.1)"
    }
else:
    theme = {
        "bg_color": "#ffffff",
        "text_color": "#31333F",
        "box_bg": "#f0f2f6",
        "border_color": "#d5d6d9",
        "th_bg": "#e0e0e0",
        "th_text": "#31333F",
        "grid_color": "rgba(0,0,0,0.1)"
    }

# === CSS 스타일 최적화 ===
st.markdown(f"""
    <style>
        header, footer, #MainMenu {{visibility: hidden;}}

        /* 전체 배경 및 폰트 */
        .stApp {{
            background-color: {theme['bg_color']};
            color: {theme['text_color']};
        }}
        html, body, [class*="css"] {{ 
            font-size: 14px; 
            color: {theme['text_color']};
        }}

        .block-container {{ 
            padding-top: 1rem !important; 
            padding-bottom: 1rem !important; 
            padding-left: 0.5rem !important; 
            padding-right: 0.5rem !important;
            max-width: 46rem !important;
        }}

        /* 컴포넌트 간격 삭제 */
        div[data-testid="stVerticalBlock"] > div {{
            gap: 0rem !important; 
        }}

        /* 텍스트 마진 제거 & 색상 적용 */
        p, h1, h2, h3, h4, h5, h6 {{
            margin-bottom: 0px !important;
            margin-top: 0px !important;
            color: {theme['text_color']} !important;
        }}

        /* 정보 박스 스타일 */
        .info-box {{
            background-color: {theme['box_bg']};
            color: {theme['text_color']};
            padding: 8px 10px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            font-size: 0.95rem; font-weight: 600;
            border: 1px solid {theme['border_color']};
        }}
        .info-label {{ font-size: 0.8rem; opacity: 0.8; margin-bottom: 2px; display: block; color: {theme['text_color']}; }}

        /* 구분선 스타일 */
        hr.custom-hr {{ 
            margin-top: -10px !important; 
            margin-bottom: 10px !important; 
            border: 0; 
            border-top: 1px solid {theme['border_color']}; 
            position: relative; 
            z-index: 1;
        }}

        /* 매수 신호 */
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(255, 82, 82, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255, 82, 82, 0); }}
        }}
        .buy-signal {{
            background-color: #FF5252; color: white; padding: 10px; 
            border-radius: 8px; text-align: center; font-weight: bold;
            animation: pulse 2s infinite; margin-bottom: 5px;
        }}

        div[data-testid="stCheckbox"] {{ margin-bottom: 0px; }}
    </style>
""", unsafe_allow_html=True)


# === 숫자 포맷팅 함수 ===
def format_price(val):
    if val is None: return "0"
    try:
        val = float(val)
        if val >= 1000000:
            return f"{int(val / 1000):,}K"
        else:
            return f"{int(val):,}"
    except:
        return str(val)


# 데이터 로드
def load_status():
    if not os.path.exists("status.json"): return None
    try:
        with open("status.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def load_chart_data():
    if not os.path.exists("chart_data.json"): return None
    try:
        with open("chart_data.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


# =========================================================
# [Zone 1] 차트 영역
# =========================================================

signal_placeholder = st.empty()
time_placeholder = st.empty()
metrics_placeholder = st.empty()

# 구분선
st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)

chart_data = load_chart_data()

if chart_data:
    usdt_data = chart_data.get('usdt', [])
    btc_data = chart_data.get('btc', [])
    kimp_data = chart_data.get('kimp_15m', [])

    df_usdt = pd.DataFrame(usdt_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df_btc = pd.DataFrame(btc_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df_kimp = pd.DataFrame(kimp_data)

    if not df_usdt.empty: df_usdt['time'] = pd.to_datetime(df_usdt['time'], unit='ms') + pd.Timedelta(hours=9)
    if not df_btc.empty: df_btc['time'] = pd.to_datetime(df_btc['time'], unit='ms') + pd.Timedelta(hours=9)
    if not df_kimp.empty: df_kimp['time'] = pd.to_datetime(df_kimp['time'], unit='ms') + pd.Timedelta(hours=9)

    if not df_usdt.empty:
        min_time = df_usdt['time'].min()
        max_time = df_usdt['time'].max()
        common_x_range = [min_time, max_time]
    else:
        common_x_range = None

    common_margin = dict(l=40, r=40, t=10, b=10)
    common_legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)

    chart_font_color = theme['text_color']

    # --- 1. USDT vs BTC 차트 ---
    st.markdown("**📈 빗썸 USDT vs BTC (15분봉)**")

    if not df_usdt.empty and not df_btc.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=df_usdt['time'], y=df_usdt['close'], name="USDT", line=dict(color='#2962FF', width=2)),
            secondary_y=False)
        fig.add_trace(
            go.Scatter(x=df_btc['time'], y=df_btc['close'], name="BTC", line=dict(color='#FF6D00', width=2)),
            secondary_y=True)

        fig.update_layout(
            height=200,
            margin=common_margin,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(size=9, color=chart_font_color),
            showlegend=True,
            legend=common_legend,
            xaxis=dict(range=common_x_range)
        )
        fig.update_yaxes(title_text="USDT", secondary_y=False, showgrid=True, gridcolor=theme['grid_color'])
        fig.update_yaxes(title_text="BTC", secondary_y=True, showgrid=False)
        fig.update_xaxes(fixedrange=True, gridcolor=theme['grid_color'])
        fig.update_yaxes(fixedrange=True)
        st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})
    else:
        st.info("시세 데이터 부족")

    # --- 2. 김프 vs BTC 차트 ---
    st.markdown("**🌊 BTC 김프 추세 vs 가격**")

    if not df_kimp.empty and not df_btc.empty:
        fig_k = make_subplots(specs=[[{"secondary_y": True}]])

        fig_k.add_trace(
            go.Scatter(x=df_kimp['time'], y=df_kimp['kimp'], mode='lines', name='Kimp',
                       line=dict(color='#00E676', width=2)),
            secondary_y=False
        )

        fig_k.add_trace(
            go.Scatter(x=df_btc['time'], y=df_btc['close'], name="BTC Price",
                       line=dict(color='#FF6D00', width=2)),
            secondary_y=True
        )

        fig_k.update_layout(
            height=130,
            margin=common_margin,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(size=9, color=chart_font_color),
            showlegend=True,
            legend=common_legend,
            xaxis=dict(range=common_x_range)
        )

        fig_k.update_yaxes(title_text="KIMP", secondary_y=False, showgrid=True, gridcolor=theme['grid_color'],
                           fixedrange=True)

        zero_color = "rgba(255,255,255,0.3)" if is_dark else "rgba(0,0,0,0.3)"
        fig_k.add_hline(y=0, line_dash="solid", line_color=zero_color, line_width=1, secondary_y=False)

        fig_k.update_yaxes(title_text="BTC", secondary_y=True, showgrid=False, fixedrange=True, showticklabels=False)
        fig_k.update_xaxes(fixedrange=True, visible=True, tickformat='%H:%M', gridcolor=theme['grid_color'])

        st.plotly_chart(fig_k, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})
    else:
        st.caption("김프 또는 BTC 데이터 부족")

else:
    st.info("차트 데이터 준비 중... (Backend 실행 확인)")

st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)

# # 4. 잔고 현황
# st.markdown("### 💰 자산 보유 현황")
# c1, c2 = st.columns(2)
# with c1:
#     up_balance_placeholder = st.empty()
# with c2:
#     bit_balance_placeholder = st.empty()

# =========================================================
# [Zone 2] Loop (실시간 정보만 갱신)
# =========================================================
while True:
    data = load_status()
    if data:
        time_placeholder.caption(f"🌍 Last Update: {data['timestamp']}")

        rsi_info = data.get('rsi', {})
        rsi_usdt_up = rsi_info.get('rsi_usdt_up', 0)
        rsi_usdt = rsi_info.get('rsi_usdt', 0)
        rsi_btc = rsi_info.get('rsi_btc', 0)

        buy_signal = False
        if rsi_usdt_up <= 30:
            buy_signal = True

        if buy_signal:
            signal_placeholder.markdown(
                f"<div class='buy-signal'>🚨 BUY SIGNAL (RSI {rsi_usdt_up} <= 30)</div>",
                unsafe_allow_html=True)
        else:
            signal_placeholder.empty()

        with metrics_placeholder.container():
            macro = data['market']['macro']
            up = data['market']['upbit']
            bit = data['market']['bithumb']
            btc = data['market']['btc']
            eth = data['market']['eth']
            xrp = data['market']['xrp']


            def get_color_style(rate):
                color = "#FF5252" if rate > 0 else ("#448AFF" if rate < 0 else "gray")
                return f"color: {color}; font-weight: bold;"


            def get_rsi_style(val):
                if val >= 70: return "color: #FF5252; font-weight: bold;"
                if val <= 30: return "color: #00E676; font-weight: bold;"
                return "color: gray;"


            jpy_100 = macro['jpy_krw'] * 100

            v_kospi = int(macro.get('kospi', 0))
            r_kospi = macro.get('kospi_rate', 0)
            v_kosdaq = int(macro.get('kosdaq', 0))
            r_kosdaq = macro.get('kosdaq_rate', 0)
            v_sp = int(macro.get('sp500_f', 0))
            r_sp = macro.get('sp500_f_rate', 0)
            v_nas = int(macro.get('nasdaq_f', 0))
            r_nas = macro.get('nasdaq_f_rate', 0)

            # --- [1] Macro Table ---
            macro_style = f"""
            <style>
                table.macro-table {{ width: 100%; border-collapse: collapse; margin-bottom: 4px; color: {theme['text_color']}; }}
                table.macro-table th {{ text-align: center; background-color: {theme['th_bg']}; color: {theme['th_text']}; font-size: 0.8rem; border: 1px solid {theme['border_color']}; padding: 4px; }}
                table.macro-table td {{ text-align: center; border: 1px solid {theme['border_color']}; padding: 4px; font-size: 0.9rem; font-weight: bold; }}
                .rate-small {{ font-size: 0.8em; margin-left: 2px; }}
            </style>
            """

            macro_table = f"""
            {macro_style}
            <table class='macro-table'>
                <thead>
                    <tr>
                        <th>KOSPI</th>
                        <th>KOSDAQ</th>
                        <th>S&P</th>
                        <th>NAS</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{v_kospi:,}<br><span class='rate-small' style='{get_color_style(r_kospi)}'>({r_kospi}%)</span></td>
                        <td>{v_kosdaq:,}<br><span class='rate-small' style='{get_color_style(r_kosdaq)}'>({r_kosdaq}%)</span></td>
                        <td>{v_sp:,}<br><span class='rate-small' style='{get_color_style(r_sp)}'>({r_sp}%)</span></td>
                        <td>{v_nas:,}<br><span class='rate-small' style='{get_color_style(r_nas)}'>({r_nas}%)</span></td>
                    </tr>
                </tbody>
            </table>
            """
            st.markdown(macro_table, unsafe_allow_html=True)

            # --- [2] Exchange Rate Box (Dual Source Updated) ---
            # Google과 Yahoo 환율 정보를 가져옵니다.
            # status.json이 업데이트되기 전(None)일 경우를 대비해 0.0 기본값 처리
            usd_g = macro.get('usd_krw_g', 0)
            usd_y = macro.get('usd_krw_y', 0)

            st.markdown(f"""
            <div class='info-box' style='margin-top: 5px; margin-bottom: 5px;'>
                <div>🇺🇸 구글:{usd_g:,.1f} / 야후:{usd_y:,.1f}</div>
                <div>🇯🇵 {jpy_100:,.2f}<span style='font-size:0.7em; opacity:0.7; font-weight:normal'>(100엔)</span></div>
                <div>DXY {macro['dxy']}</div>
            </div>
            <hr class='custom-hr'>
            """, unsafe_allow_html=True)


            # --- [3] Coin Table ---
            def make_row_html(ticker, up_p, up_k, bit_p, bit_k, rsi_val):
                if up_p:
                    up_html = f"{format_price(up_p)} <span style='{get_color_style(up_k)}; font-size:0.85em;'>({up_k}%)</span>"
                else:
                    up_html = "-"
                if bit_p:
                    bit_html = f"{format_price(bit_p)} <span style='{get_color_style(bit_k)}; font-size:0.85em;'>({bit_k}%)</span>"
                else:
                    bit_html = "-"
                if rsi_val:
                    rsi_html = f"<span style='{get_rsi_style(rsi_val)}'>{rsi_val}</span>"
                else:
                    rsi_html = "-"
                return f"""<tr><td class='col-ticker'>{ticker}</td><td class='col-price'>{up_html}</td><td class='col-price'>{bit_html}</td><td class='col-rsi'>{rsi_html}</td></tr>"""


            row_usdt = make_row_html("USDT", up['price'], up['kimp'], bit['price'], bit['kimp'], rsi_usdt)
            row_btc = make_row_html("BTC", btc.get('upbit_price'), btc.get('upbit_kimp'), btc['price_kr'], btc['kimp'],
                                    rsi_btc)
            row_eth = make_row_html("ETH", eth.get('upbit_price'), eth.get('upbit_kimp'), eth['price_kr'], eth['kimp'],
                                    None)
            row_xrp = make_row_html("XRP", xrp.get('upbit_price'), xrp.get('upbit_kimp'), xrp['price_kr'], xrp['kimp'],
                                    None)

            coin_style_block = f"""
            <style>
            table.market-table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; margin-bottom: 0px; color: {theme['text_color']}; }}
            table.market-table th {{ text-align: center; background-color: {theme['th_bg']}; color: {theme['th_text']}; font-size: 0.8rem; border: 1px solid {theme['border_color']}; padding: 5px; }}
            table.market-table td {{ padding: 6px 0; border-bottom: 1px solid {theme['border_color']}; vertical-align: middle; }}
            .col-ticker {{ text-align: center; font-weight: bold; width: 10%; }} 
            .col-price {{ text-align: right; width: 37%; }}
            .col-rsi {{ text-align: center; width: 16%; }}
            </style>
            """
            table_html = f"""
            {coin_style_block}
            <table class='market-table'>
                <thead>
                    <tr><th>Coin</th><th>🔵 Upbit</th><th>🟠 Bithumb</th><th>RSI</th></tr>
                </thead>
                <tbody>
                    {row_usdt}
                    {row_btc}
                    {row_eth}
                    {row_xrp}
                </tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)
    time.sleep(1)