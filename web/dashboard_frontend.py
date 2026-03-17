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

    if rsi_usdt_up <= 30:
        st.markdown(f"<div class='buy-signal'>🚨 BUY SIGNAL (RSI {rsi_usdt_up} <= 30)</div>", unsafe_allow_html=True)

    macro = data.get('market', {}).get('macro', {})
    up = data.get('market', {}).get('upbit', {})
    bit = data.get('market', {}).get('bithumb', {})

    if bit.get('price'):
        title_price = format_price(bit.get('price'))
        title_kimp = f"{bit.get('kimp', 0):+.2f}%"
        new_title = f"{title_price} ({title_kimp}) USDT/KRW"
        st.components.v1.html(f"<script>window.parent.document.title = '{new_title}';</script>", height=0, width=0)

    btc = data.get('market', {}).get('btc', {})
    eth = data.get('market', {}).get('eth', {})
    xrp = data.get('market', {}).get('xrp', {})

    # --- [1] Macro Table ---
    v_kospi = macro.get('kospi', 0)
    v_kosdaq = macro.get('kosdaq', 0)
    v_sp = macro.get('sp500_f', 0)
    v_nas = macro.get('nasdaq_f', 0)

    def safe_int_format(val):
        try:
            return f"{int(val):,}"
        except:
            return str(val)

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
    usd_g = macro.get('usd_krw_g', 0)
    usd_y = macro.get('usd_krw_y', 0)
    dxy = macro.get('dxy', 0)
    base_usd = macro.get('usd_krw', 0)

    highlight_bg = "background-color: rgba(255, 152, 0, 0.1);"
    highlight_color = "#FF9800"

    g_bg, g_color = "", "white"
    y_bg, y_color = "", "white"

    if usd_g > 0 and usd_g == base_usd:
        g_bg, g_color = highlight_bg, highlight_color
    elif usd_y > 0 and usd_y == base_usd:
        y_bg, y_color = highlight_bg, highlight_color

    summary_html = f"""
    <table style='width: 100%; border-collapse: collapse; margin-bottom: 5px; font-size: 0.9rem;'>
        <tr style='background-color: {theme['th_bg']}; opacity: 0.9;'>
            <td style='text-align: center; border: 1px solid {theme['border_color']}; padding: 6px;'>
                <span style='font-size:0.9em; color:white; font-weight:bold;'>DXY: </span>
                <span style='color:white; font-weight:bold;'>{dxy:,.2f}</span>
            </td>
            <td style='text-align: center; border: 1px solid {theme['border_color']}; padding: 6px; {g_bg}'>
                <span style='color:{g_color}; font-weight:bold;'>{usd_g:,.2f}</span> 
                <span style='font-size:0.85em; color:{g_color}; font-weight:bold;'>(구글)</span>
            </td>
            <td style='text-align: center; border: 1px solid {theme['border_color']}; padding: 6px; {y_bg}'>
                <span style='color:{y_color}; font-weight:bold;'>{usd_y:,.2f}</span> 
                <span style='font-size:0.85em; color:{y_color}; font-weight:bold;'>(야후)</span>
            </td>
        </tr>
    </table>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    hana_html = ""
    other_html = ""
    ex_rates = load_json("exchange_rates.json")
    if ex_rates:
        for key, bank_data in ex_rates.items():
            if key == "system_last_update" or not isinstance(bank_data, dict): continue
            bn = bank_data.get('bank_name', 'Unknown')
            ut = bank_data.get('update_time', '-')
            usd_v, jpy_v = "-", "-"
            for r in bank_data.get('rates', []):
                if r['currency'] == 'USD':
                    usd_v = f"{r['base_rate']:,.2f}"
                elif r['currency'] == 'JPY':
                    jpy_v = f"{r['base_rate']:,.2f}"

            if "하나" in bn:
                highlight_style = "color: #FF9800; font-weight: bold; background-color: rgba(255, 152, 0, 0.1);"
                hana_html += f"<tr style='{highlight_style}'><td>{bn}</td><td>{usd_v}</td><td>{jpy_v}</td><td>{ut}</td></tr>"
            else:
                other_html += f"<tr><td>{bn}</td><td>{usd_v}</td><td>{jpy_v}</td><td>{ut}</td></tr>"

    ex_rows_html = hana_html + other_html

    st.markdown(f"""
    <style>
        table.bank-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 0.85rem; color: {theme['text_color']}; }}
        table.bank-table th {{ background-color: {theme['th_bg']}; border: 1px solid {theme['border_color']}; padding: 4px; text-align: center; }}
        table.bank-table td {{ border: 1px solid {theme['border_color']}; padding: 4px; text-align: center; }}
    </style>
    <table class='bank-table'>
        <thead><tr><th>은행명</th><th>USD (달러)</th><th>JPY (100엔)</th><th>업데이트 시간</th></tr></thead>
        <tbody>{ex_rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # --- [3] Coin Table ---
    def mk_row(tk, up_p, up_k, bit_p, bit_k, rsi):
        uh = f"{format_price(up_p)} <span style='{get_color_style(up_k)}; font-size:0.85em;'>({up_k}%)</span>" if up_p else "-"
        bh = f"{format_price(bit_p)} <span style='{get_color_style(bit_k)}; font-size:0.85em;'>({bit_k}%)</span>" if bit_p else "-"
        rh = f"<span style='{get_rsi_style(rsi)}'>{rsi}</span>" if rsi else "-"
        return f"<tr><td style='text-align:center; font-weight:bold;'>{tk}</td><td style='text-align:right;'>{uh}</td><td style='text-align:right;'>{bh}</td><td style='text-align:center;'>{rh}</td></tr>"

    r_u = mk_row("USDT", up.get('price'), up.get('kimp'), bit.get('price'), bit.get('kimp'),
                 rsi_info.get('rsi_usdt', 0))
    r_b = mk_row("BTC", btc.get('upbit_price'), btc.get('upbit_kimp'), btc.get('price_kr'), btc.get('kimp'),
                 rsi_info.get('rsi_btc', 0))
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

        for df in [df_usdt, df_btc, df_kimp, df_usd]:
            if not df.empty and 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], unit='ms')

        if not df_usd.empty and not df_usdt.empty:
            df_usd = df_usd.sort_values('time')
            df_usdt = df_usdt.sort_values('time')

            df_usd_aligned = pd.merge_asof(
                df_usdt[['time']],
                df_usd[['time', 'close']],
                on='time',
                direction='backward'
            )

            df_usd_aligned['close'] = df_usd_aligned['close'].fillna(
                df_usd['close'].iloc[-1] if not df_usd.empty else 0)
            df_usd = df_usd_aligned

        cm = dict(l=40, r=40, t=10, b=10)
        cl = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", font=dict(color="white"), x=1)

        st.markdown("**📈 빗썸 테더 프리미엄 비교 (USDT vs 환율 vs BTC)**")

        if not df_usdt.empty and not df_btc.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Scatter(x=df_usdt['time'], y=df_usdt['close'], name="USDT", line=dict(color='#2962FF', width=2)),
                secondary_y=False)

            if not df_usd.empty:
                fig.add_trace(go.Scatter(x=df_usd['time'], y=df_usd['close'], name="USD/KRW",
                                         line=dict(color='#00E676', width=2, dash='dot')), secondary_y=False)

            fig.add_trace(go.Scatter(x=df_btc['time'], y=df_btc['close'], name="BTC", opacity=0.5,
                                     line=dict(color='#FF6D00', width=1.5)), secondary_y=True)

            fig.update_layout(height=230, margin=cm, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="white"), legend=cl)

            fig.update_yaxes(title_text="KRW", secondary_y=False, showgrid=True, gridcolor=theme['grid_color'],
                             fixedrange=True, tickfont=dict(color="white"), title_font=dict(color="white"), nticks=10)

            fig.update_yaxes(title_text="BTC", secondary_y=True, showgrid=False, fixedrange=True,
                             showticklabels=True, tickfont=dict(color="white"), title_font=dict(color="white"),
                             nticks=6)

            fig.update_xaxes(fixedrange=True, gridcolor=theme['grid_color'], tickformat='%m-%d %H:%M',
                             tickfont=dict(color="white"))

            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})
        else:
            st.info("시세 데이터 로딩 중...")

        st.markdown("**🌊 BTC 김프 추세 vs 가격**")
        if not df_kimp.empty and not df_btc.empty:
            fig_k = make_subplots(specs=[[{"secondary_y": True}]])
            fig_k.add_trace(
                go.Scatter(x=df_kimp['time'], y=df_kimp['kimp'], name='Kimp', line=dict(color='#00E676', width=2)),
                secondary_y=False)

            fig_k.add_trace(go.Scatter(x=df_btc['time'], y=df_btc['close'], name="BTC", opacity=0.4,
                                       line=dict(color='#FF6D00', width=1)), secondary_y=True)

            fig_k.update_layout(height=130, margin=cm, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="white"), legend=cl)

            fig_k.update_yaxes(title_text="KIMP (%)", secondary_y=False, showgrid=True, gridcolor=theme['grid_color'],
                               fixedrange=True, tickfont=dict(color="white"), title_font=dict(color="white"), nticks=5)

            fig_k.add_hline(y=0, line_color="rgba(255,255,255,0.3)" if is_dark else "rgba(0,0,0,0.3)",
                            secondary_y=False)

            fig_k.update_yaxes(title_text="BTC", secondary_y=True, showgrid=False, fixedrange=True,
                               showticklabels=True, tickfont=dict(color="white"), title_font=dict(color="white"),
                               nticks=6)

            fig_k.update_xaxes(fixedrange=True, tickformat='%H:%M', gridcolor=theme['grid_color'],
                               tickfont=dict(color="white"))

            st.plotly_chart(fig_k, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})


show_realtime_tables()
show_static_charts()