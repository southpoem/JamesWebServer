import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# =========================================================
# [주의사항] 터미널 명령어: streamlit run dashboard_frontend.py
# =========================================================

# 1. 페이지 설정
st.set_page_config(layout="centered", page_title="Tether Bot Dashboard")

# === 테마 관리 (Dark Mode 설정) ===
is_dark = True

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
        .stApp {{ background-color: {theme['bg_color']}; color: {theme['text_color']}; }}
        html, body, [class*="css"] {{ font-size: 14px; color: {theme['text_color']}; }}
        .block-container {{ padding: 1rem 0.5rem !important; max-width: 46rem !important; }}
        div[data-testid="stVerticalBlock"] > div {{ gap: 0rem !important; }}
        p, h1, h2, h3, h4, h5, h6 {{ margin: 0px !important; color: {theme['text_color']} !important; }}
        .info-box {{
            background-color: {theme['box_bg']}; color: {theme['text_color']};
            padding: 8px 10px; border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            font-size: 0.95rem; font-weight: 600; border: 1px solid {theme['border_color']};
        }}
        hr.custom-hr {{ margin: 10px 0 !important; border: 0; border-top: 1px solid {theme['border_color']}; }}
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
    </style>
""", unsafe_allow_html=True)


# === 데이터 로드 및 포맷팅 함수 ===
def format_price(val):
    if val is None: return "0"
    try:
        val = float(val)
        return f"{int(val / 1000):,}K" if val >= 1000000 else f"{int(val):,}"
    except:
        return str(val)

def load_json(file_name):
    if not os.path.exists(file_name): return None
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def get_color_style(rate):
    color = "#FF5252" if rate > 0 else ("#448AFF" if rate < 0 else "gray")
    return f"color: {color}; font-weight: bold;"

def get_rsi_style(val):
    if val is None: return "color: gray;"
    if val >= 70: return "color: #FF5252; font-weight: bold;"
    if val <= 30: return "color: #00E676; font-weight: bold;"
    return "color: gray;"


# =========================================================
# [Zone 2] 상단 표 영역 (1초마다 부분 자동 새로고침)
# =========================================================
@st.fragment(run_every=1)
def show_realtime_tables():
    data = load_json("status.json")
    if not data:
        st.info("데이터 로딩 중...")
        return

    st.caption(f"🌍 Last Update: {data.get('timestamp', '-')}")

    rsi_info = data.get('rsi', {})
    rsi_usdt_up = rsi_info.get('rsi_usdt_up', 0)

    # 매수 신호
    if rsi_usdt_up <= 30:
        st.markdown(f"<div class='buy-signal'>🚨 BUY SIGNAL (RSI {rsi_usdt_up} <= 30)</div>", unsafe_allow_html=True)

    macro = data.get('market', {}).get('macro', {})
    up = data.get('market', {}).get('upbit', {})
    bit = data.get('market', {}).get('bithumb', {})
    btc = data.get('market', {}).get('btc', {})
    eth = data.get('market', {}).get('eth', {})
    xrp = data.get('market', {}).get('xrp', {})

    # --- [1] Macro Table ---
    v_kospi = macro.get('kospi', 0)
    v_kosdaq = macro.get('kosdaq', 0)
    v_sp = macro.get('sp500_f', 0)
    v_nas = macro.get('nasdaq_f', 0)

    def safe_int_format(val):
        try: return f"{int(val):,}"
        except: return str(val)

    st.markdown(f"""
    <style>
        table.macro-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; color: {theme['text_color']}; }}
        table.macro-table th {{ text-align: center; background-color: {theme['th_bg']}; border: 1px solid {theme['border_color']}; padding: 4px; font-size: 0.8rem; }}
        table.macro-table td {{ text-align: center; border: 1px solid {theme['border_color']}; padding: 4px; font-size: 0.9rem; font-weight: bold; }}
        .rate-small {{ font-size: 0.8em; margin-left: 2px; }}
    </style>
    <table class='macro-table'>
        <thead><tr><th>KOSPI</th><th>KOSDAQ</th><th>S&P 500</th><th>NASDAQ</th></tr></thead>
        <tbody>
            <tr>
                <td>{safe_int_format(v_kospi)}<br><span class='rate-small' style='{get_color_style(macro.get('kospi_rate', 0))}'>({macro.get('kospi_rate', 0)}%)</span></td>
                <td>{safe_int_format(v_kosdaq)}<br><span class='rate-small' style='{get_color_style(macro.get('kosdaq_rate', 0))}'>({macro.get('kosdaq_rate', 0)}%)</span></td>
                <td>{safe_int_format(v_sp)}<br><span class='rate-small' style='{get_color_style(macro.get('sp500_f_rate', 0))}'>({macro.get('sp500_f_rate', 0)}%)</span></td>
                <td>{safe_int_format(v_nas)}<br><span class='rate-small' style='{get_color_style(macro.get('nasdaq_f_rate', 0))}'>({macro.get('nasdaq_f_rate', 0)}%)</span></td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    # --- [2] 환율 테이블 ---
    usd_g, usd_y = macro.get('usd_krw_g', 0), macro.get('usd_krw_y', 0)
    jpy_100 = macro.get('jpy_krw', 0) * 100
    jpy_str = f"{jpy_100:,.2f}" if jpy_100 > 0 else "-"

    # ★ 1. 구글과 야후를 한 줄로 합치기
    # "기준시간" 칸 자리에 "야후: 1,484.59" 처럼 들어가게 됩니다.
    ex_rows_html = f"""
        <tr style='background-color: {theme['th_bg']}; opacity: 0.9;'>
            <td><b>구글</b></td>
            <td style='color:#00E676; font-weight:bold;'>{usd_g:,.2f}</td>
            <td style='color:#00E676; font-weight:bold;'>{jpy_str}</td>
            <td style='color:#00E676; font-weight:bold;'>야후: {usd_y:,.2f}</td>
        </tr>
        """
    ex_rates = load_json("exchange_rates.json")
    if ex_rates:
        for key, bank_data in ex_rates.items():
            if key == "system_last_update" or not isinstance(bank_data, dict): continue
            bn = bank_data.get('bank_name', 'Unknown')
            ut = bank_data.get('update_time', '-')
            usd_v, jpy_v = "-", "-"
            for r in bank_data.get('rates', []):
                if r['currency'] == 'USD': usd_v = f"{r['base_rate']:,.2f}"
                elif r['currency'] == 'JPY': jpy_v = f"{r['base_rate']:,.2f}"
            ex_rows_html += f"<tr><td>{bn}</td><td>{usd_v}</td><td>{jpy_v}</td><td>{ut}</td></tr>"

    st.markdown(f"""
    <style>
        table.bank-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 0.85rem; color: {theme['text_color']}; }}
        table.bank-table th {{ background-color: {theme['th_bg']}; border: 1px solid {theme['border_color']}; padding: 4px; text-align: center; }}
        table.bank-table td {{ border: 1px solid {theme['border_color']}; padding: 4px; text-align: center; }}
    </style>
    <table class='bank-table'>
        <thead><tr><th>구분/은행</th><th>USD</th><th>JPY (100엔)</th><th>기준시간</th></tr></thead>
        <tbody>{ex_rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # --- [3] Coin Table ---
    def mk_row(tk, up_p, up_k, bit_p, bit_k, rsi):
        uh = f"{format_price(up_p)} <span style='{get_color_style(up_k)}; font-size:0.85em;'>({up_k}%)</span>" if up_p else "-"
        bh = f"{format_price(bit_p)} <span style='{get_color_style(bit_k)}; font-size:0.85em;'>({bit_k}%)</span>" if bit_p else "-"
        rh = f"<span style='{get_rsi_style(rsi)}'>{rsi}</span>" if rsi else "-"
        return f"<tr><td style='text-align:center; font-weight:bold;'>{tk}</td><td style='text-align:right;'>{uh}</td><td style='text-align:right;'>{bh}</td><td style='text-align:center;'>{rh}</td></tr>"

    r_u = mk_row("USDT", up.get('price'), up.get('kimp'), bit.get('price'), bit.get('kimp'), rsi_info.get('rsi_usdt', 0))
    r_b = mk_row("BTC", btc.get('upbit_price'), btc.get('upbit_kimp'), btc.get('price_kr'), btc.get('kimp'), rsi_info.get('rsi_btc', 0))
    r_e = mk_row("ETH", eth.get('upbit_price'), eth.get('upbit_kimp'), eth.get('price_kr'), eth.get('kimp'), None)
    r_x = mk_row("XRP", xrp.get('upbit_price'), xrp.get('upbit_kimp'), xrp.get('price_kr'), xrp.get('kimp'), None)

    st.markdown(f"""
    <style>
        table.coin-table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; color: {theme['text_color']}; }}
        table.coin-table th {{ background-color: {theme['th_bg']}; border: 1px solid {theme['border_color']}; padding: 5px; text-align: center; }}
        table.coin-table td {{ padding: 6px; border-bottom: 1px solid {theme['border_color']}; }}
    </style>
    <table class='coin-table'>
        <thead><tr><th>Coin</th><th>🔵 Upbit</th><th>🟠 Bithumb</th><th>RSI</th></tr></thead>
        <tbody>{r_u}{r_b}{r_e}{r_x}</tbody>
    </table>
    """, unsafe_allow_html=True)


# =========================================================
# [Zone 1] 하단 차트 영역 (정적 렌더링 - 깜빡임 없음)
# =========================================================
def show_static_charts():
    st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
    chart_data = load_json("chart_data.json")

    if chart_data:
        usdt_data = chart_data.get('usdt', [])
        btc_data = chart_data.get('btc', [])
        kimp_data = chart_data.get('kimp_15m', [])
        usd_chart_data = chart_data.get('usd_krw_chart', [])

        df_usdt = pd.DataFrame(usdt_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df_btc = pd.DataFrame(btc_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df_kimp = pd.DataFrame(kimp_data)
        df_usd = pd.DataFrame(usd_chart_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        # 시간대 변환 (+9시간)
        for df in [df_usdt, df_btc, df_kimp, df_usd]:
            if not df.empty and 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], unit='ms') + pd.Timedelta(hours=9)

        # =========================================================
        # ★ [핵심] 주말/시차 X축 완벽 동기화 로직
        # =========================================================
        if not df_usd.empty and not df_usdt.empty:
            df_usd = df_usd.sort_values('time')
            df_usdt = df_usdt.sort_values('time')

            df_usd_aligned = pd.merge_asof(
                df_usdt[['time']],
                df_usd[['time', 'close']],
                on='time',
                direction='backward'
            )

            df_usd_aligned['close'] = df_usd_aligned['close'].fillna(df_usd['close'].iloc[-1] if not df_usd.empty else 0)
            df_usd = df_usd_aligned

        cm = dict(l=40, r=40, t=10, b=10)
        cl = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", font=dict(color="white"), x=1)

        # ---------------------------------------------------------
        # 1. USDT vs BTC vs 환율 차트
        # ---------------------------------------------------------
        st.markdown("**📈 빗썸 테더 프리미엄 비교 (USDT vs 환율 vs BTC)**")

        if not df_usdt.empty and not df_btc.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Trace 1: Bithumb USDT
            fig.add_trace(go.Scatter(x=df_usdt['time'], y=df_usdt['close'], name="USDT", line=dict(color='#2962FF', width=2)), secondary_y=False)

            # Trace 2: 야후 원/달러 환율
            if not df_usd.empty:
                fig.add_trace(go.Scatter(x=df_usd['time'], y=df_usd['close'], name="USD/KRW", line=dict(color='#00E676', width=2, dash='dot')), secondary_y=False)

            # Trace 3: Bithumb BTC
            fig.add_trace(go.Scatter(x=df_btc['time'], y=df_btc['close'], name="BTC", opacity=0.5, line=dict(color='#FF6D00', width=1.5)), secondary_y=True)

            # ★ 폰트 색상을 "white"로 강제 지정
            # ★ 전체 기본 폰트 색상을 하얀색으로 지정
            fig.update_layout(height=230, margin=cm, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="white"), legend=cl)

            # ★ 왼쪽 Y축 (KRW): 하얀색 강제 적용 + 눈금 2배 세밀하게 (nticks=10)
            fig.update_yaxes(title_text="KRW", secondary_y=False, showgrid=True, gridcolor=theme['grid_color'],
                             fixedrange=True, tickfont=dict(color="white"), title_font=dict(color="white"), nticks=10)

            # ★ 오른쪽 Y축 (BTC): 숨김 처리 해제(showticklabels=True) + 하얀색 강제 적용 + 눈금 세밀하게 (nticks=10)
            fig.update_yaxes(title_text="BTC", secondary_y=True, showgrid=False, fixedrange=True,
                             showticklabels=True, tickfont=dict(color="white"), title_font=dict(color="white"),
                             nticks=6)

            # ★ X축 (시간): tickfont에 하얀색 강제 적용
            fig.update_xaxes(fixedrange=True, gridcolor=theme['grid_color'], tickformat='%m-%d %H:%M',
                             tickfont=dict(color="white"))

            # theme=None 은 빼고 그대로 출력 (차트 찌그러짐 방지)
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})
        else:
            st.info("시세 데이터 로딩 중...")

        # ---------------------------------------------------------
        # 2. 김프 차트
        # ---------------------------------------------------------
        st.markdown("**🌊 BTC 김프 추세 vs 가격**")
        if not df_kimp.empty and not df_btc.empty:
            fig_k = make_subplots(specs=[[{"secondary_y": True}]])
            fig_k.add_trace(go.Scatter(x=df_kimp['time'], y=df_kimp['kimp'], name='Kimp', line=dict(color='#00E676', width=2)), secondary_y=False)

            # Bithumb BTC
            fig_k.add_trace(go.Scatter(x=df_btc['time'], y=df_btc['close'], name="BTC", opacity=0.4, line=dict(color='#FF6D00', width=1)), secondary_y=True)

            # ★ 전체 기본 폰트 색상을 하얀색으로 지정
            fig_k.update_layout(height=130, margin=cm, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="white"), legend=cl)

            # ★ 왼쪽 Y축 (KIMP): 하얀색 강제 적용 + 눈금 2배 세밀하게 (nticks=10)
            fig_k.update_yaxes(title_text="KIMP (%)", secondary_y=False, showgrid=True, gridcolor=theme['grid_color'],
                               fixedrange=True, tickfont=dict(color="white"), title_font=dict(color="white"), nticks=5)

            # 0% 기준선 (그대로 유지)
            fig_k.add_hline(y=0, line_color="rgba(255,255,255,0.3)" if is_dark else "rgba(0,0,0,0.3)",
                            secondary_y=False)

            # ★ 오른쪽 Y축 (BTC): 숨김 해제(showticklabels=True) + 하얀색 강제 적용 + 눈금 2배 세밀하게 (nticks=10)
            fig_k.update_yaxes(title_text="BTC", secondary_y=True, showgrid=False, fixedrange=True,
                               showticklabels=True, tickfont=dict(color="white"), title_font=dict(color="white"),
                               nticks=6)

            # ★ X축 (시간): tickfont에 하얀색 강제 적용
            fig_k.update_xaxes(fixedrange=True, tickformat='%H:%M', gridcolor=theme['grid_color'],
                               tickfont=dict(color="white"))

            # 출력
            st.plotly_chart(fig_k, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})


# =========================================================
# 화면 렌더링 실행
# =========================================================
show_realtime_tables()
show_static_charts()