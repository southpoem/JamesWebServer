import streamlit as st
import json
import os

# 1. 페이지 설정 (화면 전체 사용을 위해 wide)
st.set_page_config(layout="wide", page_title="Watch")

# 2. 상하좌우 완전 중앙 정렬을 위한 CSS
st.markdown("""
    <style>
        /* 기본 요소 숨기기 */
        header, footer, #MainMenu {visibility: hidden; display: none !important;}
        section[data-testid="stSidebar"] { display: none !important; }
        button[kind="header"] { display: none !important; }

        /* 1. 배경색 및 전체 화면 높이 설정 */
        .stApp { 
            background-color: #000000; 
        }

        /* 2. 카드들을 위아래 정중앙으로 배치하는 핵심 코드 */
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
            height: 100vh !important; /* 화면 높이 전체 확보 */
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important; /* 수직(위아래) 중앙 정렬 */
            align-items: center !important;     /* 수평(좌우) 중앙 정렬 */
        }

        /* 3. 카드 내부 텍스트 마진 제거 */
        p, h1, h2, h3 { margin: 0px !important; }

        /* 빗썸 스타일 카드 UI */
        .watch-card {
            background-color: #222222;
            border-radius: 20px;
            padding: 12px 15px;
            margin: 6px 0px; /* 카드 사이 간격 */
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 90vw; /* 워치 너비에 맞춤 */
            box-sizing: border-box;
        }

        .left-col { text-align: left; }
        .right-col { text-align: right; display: flex; flex-direction: column; align-items: flex-end; }

        .card-title { font-size: 1rem; color: #aaaaaa; margin-bottom: 3px; font-weight: 500; }
        .card-price { font-size: 1.6rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; line-height: 1.1; }

        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.95rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 4px;
        }
        .badge-red { background-color: #FF5252; }
        .badge-blue { background-color: #448AFF; }
        .badge-grey { background-color: #444444; }

        .sub-text { font-size: 0.85rem; color: #888888; font-weight: 600; }

        .kimp-plus { color: #FF5252; }
        .kimp-minus { color: #448AFF; }
    </style>
""", unsafe_allow_html=True)


# 3. 데이터 로드 함수
def load_json(file_name):
    if not os.path.exists(file_name): return None
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


# 4. 카드 생성 함수 (버그 방지를 위해 납작하게 연결)
def create_card(title, price, badge_text, badge_color, sub_text):
    html = f"<div class='watch-card'>"
    html += f"<div class='left-col'>"
    html += f"<div class='card-title'>{title}</div>"
    html += f"<div class='card-price'>{price}</div>"
    html += f"</div>"
    html += f"<div class='right-col'>"
    html += f"<div class='badge badge-{badge_color}'>{badge_text}</div>"
    html += f"<div class='sub-text'>{sub_text}</div>"
    html += f"</div>"
    html += f"</div>"
    return html


# 5. 워치 UI 렌더링
@st.fragment(run_every=1)
def show_watch_ui():
    data = load_json("status.json")
    if not data:
        st.markdown("<div style='color:white; text-align:center;'>로딩중...</div>", unsafe_allow_html=True)
        return

    macro = data.get('market', {}).get('macro', {})
    bit = data.get('market', {}).get('bithumb', {})
    btc = data.get('market', {}).get('btc', {})

    base_usd = macro.get('usd_krw', 0)
    dxy = macro.get('dxy', 0)

    # 1. 환율 카드
    card_google = create_card("🌐 구글 환율 (기준)", f"{base_usd:,.2f}", "기준", "grey", f"DXY {dxy:,.2f}")

    # 2. 테더 카드
    usdt_p, usdt_k = bit.get('price', 0), bit.get('kimp', 0)
    u_color = "red" if usdt_k > 0 else "blue"
    card_usdt = create_card("₮ 빗썸 테더 (김프)", f"{int(usdt_p):,}", f"{usdt_k:+.2f}%", u_color, "김프")

    # 3. 비트코인 카드
    btc_p, btc_k = btc.get('price_kr', 0), btc.get('kimp', 0)
    b_color = "red" if btc_k > 0 else "blue"
    card_btc = create_card("₿ 비트코인 (김프)", f"{int(btc_p):,}", f"{btc_k:+.2f}%", b_color, "김프")

    # 전체 카드 출력
    st.markdown(f"{card_google}{card_usdt}{card_btc}", unsafe_allow_html=True)


# 실행
show_watch_ui()