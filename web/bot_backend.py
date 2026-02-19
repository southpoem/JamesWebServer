import asyncio
import sys

import ccxt
import yfinance as yf
import FinanceDataReader as fdr
import time
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import math
import os
print("\n" + "="*50)
print("🔍 [디버깅] 경로 확인 시작")
print("="*50)

# 1. 현재 실행 중인 파일의 위치
current_file_path = os.path.abspath(__file__)
print(f"1. 현재 파일 위치:\n   👉 {current_file_path}")

# 2. 현재 파일의 폴더 (web 폴더 예상)
current_dir = os.path.dirname(current_file_path)
print(f"2. 현재 파일의 폴더:\n   👉 {current_dir}")

# 3. 프로젝트 루트 폴더 (한 단계 위)
project_root = os.path.dirname(current_dir)
print(f"3. 프로젝트 루트(최상위) 폴더:\n   👉 {project_root}")

# 4. sys.path에 루트 추가 전 확인
print(f"4. sys.path 추가 전 개수: {len(sys.path)}")

# 5. 경로 추가 실행
if project_root not in sys.path:
    sys.path.append(project_root)
    print(f"5. ✅ sys.path에 루트 폴더 추가 완료!")
else:
    print(f"5. ℹ️ 이미 sys.path에 루트 폴더가 있습니다.")

# 6. 실제 파일이 있는지 물리적으로 확인 (가장 중요!)
target_file = os.path.join(project_root, 'mybot', 'TelegramMessenger.py')
is_exist = os.path.exists(target_file)

print(f"6. 불러오려는 파일 확인:")
print(f"   대상 경로: {target_file}")
if is_exist:
    print("   결과: ✅ 파일이 실제로 존재합니다!")
else:
    print("   결과: ❌ 파일이 없습니다! (폴더명이나 파일명을 확인하세요)")

print("="*50 + "\n")

# ---------------------------------------------------------
# 아래부터 기존 import 코드를 작성하세요
# ---------------------------------------------------------

try:
    # 폴더명(mybot)과 파일명(TelegramMessenger)이 맞는지 확인
    import mybot.TelegramMessenger as tm
    print("🎉 모듈 import 성공! (tm으로 사용 가능)")
except ImportError as e:
    print(f"🔥 모듈 import 실패 에러: {e}")
    # 여기서 멈추게 하려면 sys.exit() 사용
    sys.exit()
try:
    import key_config
except ImportError:
    key_config = None


class MarketObserver:
    def __init__(self):
        self.last_reported_price = 0
        self.last_reported_int = 0
        if key_config:
            self.upbit = ccxt.upbit({'apiKey': key_config.UPBIT_ACCESS, 'secret': key_config.UPBIT_SECRET})
            self.bithumb = ccxt.bithumb({'apiKey': key_config.BITHUMB_ACCESS, 'secret': key_config.BITHUMB_SECRET})
        else:
            self.upbit = ccxt.upbit()
            self.bithumb = ccxt.bithumb()
        self.binance = ccxt.binance()

        self.cached_macro = {
            "usd_krw": 1460.0, "usd_krw_g": 1460.0, "usd_krw_y": 1460.0,
            "jpy_krw": 9.12, "dxy": 100.0,
            "kospi": 0.0, "kospi_rate": 0.0, "kosdaq": 0.0, "kosdaq_rate": 0.0,
            "sp500_f": 0.0, "sp500_f_rate": 0.0, "nasdaq_f": 0.0, "nasdaq_f_rate": 0.0,
            "source": "Init"
        }
        self.prev_closes = {"kospi": 0, "kosdaq": 0, "sp500_f": 0, "nasdaq_f": 0}
        self.last_index_update = 0
        self.init_prev_closes()

        # [신규 추가] 5분 변동성 체크를 위한 버퍼 및 변수
        self.forex_buffer = []  # [(timestamp, price), ...] 형태
        self.last_alert_time = 0  # 알림 도배 방지용

    def check_volatility(self, current_price):
        # 1. 초기값 설정 (봇 켜고 첫 데이터)
        if self.last_reported_price == 0:
            self.last_reported_price = current_price
            print(f"🏁 [감시 시작] 기준 환율: {current_price:.2f}원")
            return

        # 2. 조건 확인
        # 조건 A: 정수 앞자리가 바뀌었는가? (예: 1441.x -> 1442.x)
        is_int_changed = int(current_price) != int(self.last_reported_price)

        # 조건 B: 변동폭이 0.5 이상인가?
        diff = current_price - self.last_reported_price
        is_diff_enough = abs(diff) >= 0.5

        # 3. [두 조건 모두 만족(AND)] 시 알림 발송
        if is_int_changed and is_diff_enough:

            # 아이콘 및 방향 설정
            if diff > 0:
                emoji = "📈"  # 상승
                direction = "상승"
                sign = "+"
            else:
                emoji = "📉"  # 하락
                direction = "하락"
                sign = ""

            # 메시지 작성
            msg = f"{emoji} 환율 {direction} ({sign}{diff:.2f}원): {self.last_reported_price:.2f}원 -> {current_price:.2f}원"

            print(f"\n🔔 {msg}")

            # 텔레그램 전송
            try:
                # 텔레그램 모듈이 로드되었을 때만 전송
                if 'mybot.TelegramMessenger' in sys.modules:
                    asyncio.run(tm.send_dollar_message(msg))
            except Exception as e:
                print(f"❌ 텔레그램 전송 에러: {e}")

            # [중요] 기준값 업데이트 (알림을 보냈을 때만 갱신)
            self.last_reported_price = current_price


    def get_naver_index(self, market_code):
        try:
            url = f"https://finance.naver.com/sise/sise_index.naver?code={market_code}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=2)
            soup = BeautifulSoup(res.text, 'html.parser')
            now_value = soup.find("em", id="now_value")
            return float(now_value.text.replace(',', '')) if now_value else None
        except:
            return None

    def get_google_price(self, ticker_str):
        try:
            url = f"https://www.google.com/finance/quote/{ticker_str}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=2)
            soup = BeautifulSoup(res.text, 'html.parser')
            el = soup.find('div', {'class': 'YMlKec fxKbKc'})
            return float(el.text.replace(',', '')) if el else None
        except:
            return None

    def update_indices_realtime(self):
        try:
            k_pi = self.get_naver_index("KOSPI")
            k_dq = self.get_naver_index("KOSDAQ")
            if k_pi:
                self.cached_macro["kospi"] = round(k_pi, 2)
                if self.prev_closes["kospi"] > 0:
                    self.cached_macro["kospi_rate"] = round(
                        ((k_pi - self.prev_closes["kospi"]) / self.prev_closes["kospi"]) * 100, 2)
            if k_dq:
                self.cached_macro["kosdaq"] = round(k_dq, 2)
                if self.prev_closes["kosdaq"] > 0:
                    self.cached_macro["kosdaq_rate"] = round(
                        ((k_dq - self.prev_closes["kosdaq"]) / self.prev_closes["kosdaq"]) * 100, 2)
        except:
            pass
        try:
            usa = yf.download(["ES=F", "NQ=F", "DX-Y.NYB"], period="1d", interval="1m", progress=False)
            if not usa.empty:
                closes = usa['Close'].iloc[-1]
                try:
                    val = float(closes["ES=F"])
                    if not math.isnan(val):
                        self.cached_macro["sp500_f"] = round(val, 2)
                        if self.prev_closes["sp500_f"] > 0:
                            self.cached_macro["sp500_f_rate"] = round(
                                ((val - self.prev_closes["sp500_f"]) / self.prev_closes["sp500_f"]) * 100, 2)
                except:
                    pass
                try:
                    val = float(closes["NQ=F"])
                    if not math.isnan(val):
                        self.cached_macro["nasdaq_f"] = round(val, 2)
                        if self.prev_closes["nasdaq_f"] > 0:
                            self.cached_macro["nasdaq_f_rate"] = round(
                                ((val - self.prev_closes["nasdaq_f"]) / self.prev_closes["nasdaq_f"]) * 100, 2)
                except:
                    pass
                try:
                    val = float(closes["DX-Y.NYB"])
                    if not math.isnan(val):
                        self.cached_macro["dxy"] = round(val, 2)
                except:
                    pass
        except:
            pass

    def update_macro_data(self):
        # 1. Google Finance Fetch
        try:
            usd_g = self.get_google_price("USD-KRW")
            if usd_g:
                self.cached_macro["usd_krw_g"] = round(usd_g, 2)
        except:
            pass

        # 2. Yahoo Finance Fetch (KRW=X) - [수정됨: 변동성 체크 연결]
        try:
            yf_ticker = yf.Ticker("KRW=X")
            hist = yf_ticker.history(period="1d", interval="1m")
            if not hist.empty:
                usd_y = float(hist['Close'].iloc[-1])
                self.cached_macro["usd_krw_y"] = round(usd_y, 2)

                # [신규] 여기서 야후 가격으로 변동성 체크 함수 호출
                self.check_volatility(usd_y)

        except:
            pass

        # 3. Main Reference (Google preferred, else Yahoo)
        if self.cached_macro.get("usd_krw_g", 0) > 0:
            self.cached_macro["usd_krw"] = self.cached_macro["usd_krw_g"]
        else:
            self.cached_macro["usd_krw"] = self.cached_macro["usd_krw_y"]

        # JPY (Google)
        try:
            jpy = self.get_google_price("JPY-KRW")
            if jpy:
                self.cached_macro["jpy_krw"] = round(jpy, 4)
        except:
            pass

        if time.time() - self.last_index_update > 3:
            self.update_indices_realtime()
            self.last_index_update = time.time()

    def init_prev_closes(self):
        try:
            ks = fdr.DataReader('KS11', data_source='naver')
            if len(ks) >= 2: self.prev_closes["kospi"] = float(ks['Close'].iloc[-2])
            usa = yf.download(["ES=F", "NQ=F"], period="5d", interval="1d", progress=False)
            if not usa.empty:
                closes = usa['Close']
                if len(closes) >= 2:
                    self.prev_closes["sp500_f"] = float(closes["ES=F"].iloc[-2])
                    self.prev_closes["nasdaq_f"] = float(closes["NQ=F"].iloc[-2])
        except:
            pass

    def calculate_rsi(self, ohlcv, period=14):
        try:
            if not ohlcv: return 0.0
            df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            delta = df['close'].diff()
            gain, loss = delta.where(delta > 0, 0), -delta.where(delta < 0, 0)
            avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
            rs = avg_gain / avg_loss
            return round((100 - (100 / (1 + rs))).iloc[-1], 2)
        except:
            return 0.0

    def get_chart_and_kimp_data(self):
        try:
            usdt = self.bithumb.fetch_ohlcv('USDT/KRW', '15m', limit=100)
            btc_kr = self.bithumb.fetch_ohlcv('BTC/KRW', '15m', limit=100)

            btc_us = self.binance.fetch_ohlcv('BTC/USDT', '15m', limit=100)
            usdt_up = self.upbit.fetch_ohlcv('USDT/KRW', '15m', limit=100)

            kimp_15m_series = []
            if btc_kr and btc_us:
                df_kr = pd.DataFrame(btc_kr, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                df_us = pd.DataFrame(btc_us, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

                df_merge = pd.merge(df_kr, df_us, on='time', suffixes=('_kr', '_us'))
                ex_rate = self.cached_macro['usd_krw']

                df_merge['kimp'] = ((df_merge['close_kr'] / (df_merge['close_us'] * ex_rate)) - 1) * 100
                kimp_15m_series = df_merge[['time', 'kimp']].to_dict('records')

            return {
                "usdt": usdt,
                "btc": btc_kr,
                "kimp_15m": kimp_15m_series,
                "rsi_usdt": self.calculate_rsi(usdt),
                "rsi_btc": self.calculate_rsi(btc_kr),
                "rsi_usdt_up": self.calculate_rsi(usdt_up)
            }
        except Exception as e:
            print(f"Chart Data Error: {e}")
            return {"usdt": [], "btc": [], "kimp_15m": [], "rsi_usdt": 0, "rsi_btc": 0, "rsi_usdt_up": 0}

    def get_balance(self):
        try:
            up = self.upbit.fetch_balance()
            bit = self.bithumb.fetch_balance()
            return {
                "upbit": {"krw": int(up['KRW']['free']), "usdt": float(up['USDT']['free'] if 'USDT' in up else 0)},
                "bithumb": {"krw": int(bit['KRW']['free']), "usdt": float(bit['USDT']['free'] if 'USDT' in bit else 0)}
            }
        except:
            return {"upbit": {"krw": 0, "usdt": 0}, "bithumb": {"krw": 0, "usdt": 0}}

    def execute_order(self, cmd):
        try:
            exch = self.upbit if cmd['exchange'] == 'UPBIT' else self.bithumb
            symbol, side, amt = cmd['symbol'], cmd['side'], float(cmd['amount'])
            if cmd['exchange'] == 'UPBIT' and side == 'buy':
                exch.create_order(symbol, 'market', 'buy', None, price=amt)
            elif side == 'buy':
                exch.create_market_buy_order(symbol, amt)
            elif side == 'sell':
                exch.create_market_sell_order(symbol, amt)
            print(f"✅ Executed: {cmd['exchange']} {side} {amt}")
        except Exception as e:
            print(f"❌ Execution Failed: {e}")

    def get_realtime_status(self):
        try:
            ex_rate = self.cached_macro['usd_krw']
            theo_usdt = 1.0 * ex_rate

            p_up = self.upbit.fetch_ticker('USDT/KRW')['last']
            p_bit = self.bithumb.fetch_ticker('USDT/KRW')['last']

            p_btc_kr_bit = self.bithumb.fetch_ticker('BTC/KRW')['last']
            p_btc_kr_up = self.upbit.fetch_ticker('BTC/KRW')['last']
            p_btc_gl = self.binance.fetch_ticker('BTC/USDT')['last']

            p_eth_kr_bit = self.bithumb.fetch_ticker('ETH/KRW')['last']
            p_eth_kr_up = self.upbit.fetch_ticker('ETH/KRW')['last']
            p_eth_gl = self.binance.fetch_ticker('ETH/USDT')['last']

            p_xrp_kr_bit = self.bithumb.fetch_ticker('XRP/KRW')['last']
            p_xrp_kr_up = self.upbit.fetch_ticker('XRP/KRW')['last']
            p_xrp_gl = self.binance.fetch_ticker('XRP/USDT')['last']

            kimp_btc_bit = round(((p_btc_kr_bit / (p_btc_gl * ex_rate)) - 1) * 100, 2)
            kimp_btc_up = round(((p_btc_kr_up / (p_btc_gl * ex_rate)) - 1) * 100, 2)

            kimp_eth_bit = round(((p_eth_kr_bit / (p_eth_gl * ex_rate)) - 1) * 100, 2)
            kimp_eth_up = round(((p_eth_kr_up / (p_eth_gl * ex_rate)) - 1) * 100, 2)

            kimp_xrp_bit = round(((p_xrp_kr_bit / (p_xrp_gl * ex_rate)) - 1) * 100, 2)
            kimp_xrp_up = round(((p_xrp_kr_up / (p_xrp_gl * ex_rate)) - 1) * 100, 2)

            return {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "market": {
                    "macro": self.cached_macro,
                    "upbit": {"price": p_up, "kimp": round(((p_up / theo_usdt) - 1) * 100, 2)},
                    "bithumb": {"price": p_bit, "kimp": round(((p_bit / theo_usdt) - 1) * 100, 2)},
                    "btc": {
                        "price_kr": p_btc_kr_bit, "kimp": kimp_btc_bit,
                        "upbit_price": p_btc_kr_up, "upbit_kimp": kimp_btc_up
                    },
                    "eth": {
                        "price_kr": p_eth_kr_bit, "kimp": kimp_eth_bit,
                        "upbit_price": p_eth_kr_up, "upbit_kimp": kimp_eth_up
                    },
                    "xrp": {
                        "price_kr": p_xrp_kr_bit, "kimp": kimp_xrp_bit,
                        "upbit_price": p_xrp_kr_up, "upbit_kimp": kimp_xrp_up
                    },
                    "balance": self.get_balance()
                }
            }
        except Exception as e:
            print(f"Realtime Data Error: {e}")
            return None


def run_bot():
    print("=== 🤖 봇 시작 (Dual Exchange Rate Added) ===")
    observer = MarketObserver()
    last_chart_update = 0

    while True:
        try:
            if os.path.exists("command.json"):
                with open("command.json", 'r') as f:
                    try:
                        cmd = json.load(f)
                    except:
                        cmd = {}
                if cmd:
                    observer.execute_order(cmd)
                    with open("command.json", 'w') as f: json.dump({}, f)

            observer.update_macro_data()

            curr = time.time()
            if curr - last_chart_update > 15:
                chart_data = observer.get_chart_and_kimp_data()
                with open("chart_data.json", 'w', encoding='utf-8') as f:
                    json.dump(chart_data, f, indent=4, ensure_ascii=False)
                last_chart_update = curr

                observer.latest_rsi = {
                    "rsi_usdt": chart_data['rsi_usdt'],
                    "rsi_usdt_up": chart_data['rsi_usdt_up'],
                    "rsi_btc": chart_data['rsi_btc']
                }

            status_data = observer.get_realtime_status()
            if status_data:
                if hasattr(observer, 'latest_rsi'):
                    status_data['rsi'] = observer.latest_rsi
                else:
                    status_data['rsi'] = {"rsi_usdt": 0, "rsi_usdt_up": 0, "rsi_btc": 0}

                with open("status.json", 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, indent=4, ensure_ascii=False)

                print(f"[{status_data['timestamp']}] Data Updated..")

            time.sleep(1)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_bot()