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
import re

print("\n" + "=" * 50)
print("🔍 [디버깅] 경로 확인 시작")
print("=" * 50)

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)

try:
    import mybot.TelegramMessenger as tm

    print("🎉 모듈 import 성공! (tm으로 사용 가능)")
except ImportError as e:
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
        self.bithumb_pub = ccxt.bithumb()

        self.cached_macro = {
            "usd_krw": 1460.0, "usd_krw_g": 1460.0, "usd_krw_y": 1460.0, "usd_krw_m": 1460.0,
            "jpy_krw": 9.12, "dxy": 100.0, "dxy_m": 100.0,
            "kospi": 0.0, "kospi_rate": 0.0, "kosdaq": 0.0, "kosdaq_rate": 0.0,
            "sp500_f": 0.0, "sp500_f_rate": 0.0, "nasdaq_f": 0.0, "nasdaq_f_rate": 0.0,
            "source": "Init"
        }
        self.prev_closes = {"kospi": 0, "kosdaq": 0, "sp500_f": 0, "nasdaq_f": 0}
        self.last_index_update = 0

        self.forex_buffer = []
        self.last_alert_time = 0

    def check_volatility(self, current_price):
        if self.last_reported_price == 0:
            self.last_reported_price = current_price
            print(f"🏁 [감시 시작] 기준 환율: {current_price:.2f}원")
            return

        is_int_changed = int(current_price) != int(self.last_reported_price)
        diff = current_price - self.last_reported_price
        is_diff_enough = abs(diff) >= 0.5

        if is_int_changed and is_diff_enough:
            if diff > 0:
                emoji, direction, sign = "📈", "상승", "+"
            else:
                emoji, direction, sign = "📉", "하락", ""

            msg = f"{emoji} 환율 {direction} ({sign}{diff:.2f}원): {self.last_reported_price:.2f}원 -> {current_price:.2f}원"
            print(f"\n🔔 {msg}")

            try:
                if 'mybot.TelegramMessenger' in sys.modules:
                    asyncio.run(tm.send_dollar_message(msg))
            except Exception as e:
                pass

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

    def get_marketwatch_price(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            res = requests.get(url, headers=headers, timeout=3)
            soup = BeautifulSoup(res.text, 'html.parser')

            meta_price = soup.find('meta', attrs={'name': 'price'})
            if meta_price and meta_price.get('content'):
                text_val = meta_price['content'].replace(',', '')
                match = re.search(r"[-+]?\d*\.\d+|\d+", text_val)
                if match:
                    return float(match.group())

            price_h2 = soup.find('h2', {'class': 'intraday__price'})
            if price_h2:
                el = price_h2.find('bg-quote')
                if el:
                    text_val = el.text.strip().replace(',', '')
                    match = re.search(r"[-+]?\d*\.\d+|\d+", text_val)
                    if match:
                        return float(match.group())
        except Exception as e:
            pass
        return None

    def update_indices_realtime(self):
        headers = {"User-Agent": "Mozilla/5.0"}

        dom_symbols = {"kospi": "KOSPI", "kosdaq": "KOSDAQ"}
        dom_url = "https://m.stock.naver.com/api/index/{}/price?pageSize=1&page=1"

        for key, symbol in dom_symbols.items():
            try:
                res = requests.get(dom_url.format(symbol), headers=headers, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    if len(data) > 0:
                        recent = data[0]
                        self.cached_macro[key] = float(recent.get("closePrice", "0").replace(",", ""))
                        self.cached_macro[f"{key}_rate"] = float(recent.get("fluctuationsRatio", "0"))
            except Exception as e:
                pass

        ovs_symbols = {"sp500_f": ".INX", "nasdaq_f": ".IXIC"}
        ovs_url = "https://api.stock.naver.com/index/{}/basic"

        for key, symbol in ovs_symbols.items():
            try:
                res = requests.get(ovs_url.format(symbol), headers=headers, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    self.cached_macro[key] = float(data.get("closePrice", "0").replace(",", ""))
                    self.cached_macro[f"{key}_rate"] = float(data.get("fluctuationsRatio", "0"))
            except Exception as e:
                pass

        try:
            usa = yf.download("DX-Y.NYB", period="1d", interval="1m", progress=False)
            if not usa.empty:
                if isinstance(usa.columns, pd.MultiIndex):
                    usa.columns = usa.columns.get_level_values(0)
                val = float(usa['Close'].iloc[-1])
                if not math.isnan(val):
                    self.cached_macro["dxy"] = round(val, 2)
        except Exception as e:
            pass

        try:
            dxy_m = self.get_marketwatch_price("https://www.marketwatch.com/investing/index/dxy")
            if dxy_m:
                self.cached_macro["dxy_m"] = round(dxy_m, 2)
        except Exception as e:
            pass

    def update_macro_data(self):
        try:
            usd_g = self.get_google_price("USD-KRW")
            if usd_g:
                self.cached_macro["usd_krw_g"] = round(usd_g, 2)
        except:
            pass

        try:
            yf_ticker = yf.Ticker("KRW=X")
            hist = yf_ticker.history(period="1d", interval="1m")
            if not hist.empty:
                usd_y = float(hist['Close'].iloc[-1])
                self.cached_macro["usd_krw_y"] = round(usd_y, 2)
                self.check_volatility(usd_y)
        except:
            pass

        if self.cached_macro.get("usd_krw_g", 0) > 0:
            self.cached_macro["usd_krw"] = self.cached_macro["usd_krw_g"]
        else:
            self.cached_macro["usd_krw"] = self.cached_macro["usd_krw_y"]

        try:
            jpy = self.get_google_price("JPY-KRW")
            if jpy:
                self.cached_macro["jpy_krw"] = round(jpy, 4)
        except:
            pass

        if time.time() - self.last_index_update > 3:
            self.update_indices_realtime()
            self.last_index_update = time.time()

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

    def fetch_bithumb_15m_direct(self, symbol):
        try:
            sym = symbol.replace('/', '_')
            url = f"https://api.bithumb.com/public/candlestick/{sym}/15m"
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                data = res.json()
                if data.get('status') == '0000':
                    ohlcv = []
                    for row in data['data'][-100:]:
                        ohlcv.append([
                            int(row[0]),  # Time (UTC Epoch)
                            float(row[1]),  # Open
                            float(row[3]),  # High
                            float(row[4]),  # Low
                            float(row[2]),  # Close
                            float(row[5])  # Volume
                        ])
                    return ohlcv
        except Exception as e:
            print(f"Bithumb Direct Fetch Error ({symbol}): {e}")
        return []

    def get_chart_and_kimp_data(self):
        try:
            usdt = self.fetch_bithumb_15m_direct('USDT/KRW')
            btc_kr = self.fetch_bithumb_15m_direct('BTC/KRW')

            btc_us = self.binance.fetch_ohlcv('BTC/USDT', '15m', limit=100)
            usdt_up = self.upbit.fetch_ohlcv('USDT/KRW', '15m', limit=100)

            # ★ KST 변환 꼼수 제거 (순수 UTC 로 통일)
            usd_krw_chart_data = []
            try:
                usd_df = yf.download("KRW=X", period="7d", interval="15m", progress=False)
                if not usd_df.empty:
                    if isinstance(usd_df.columns, pd.MultiIndex):
                        usd_df.columns = usd_df.columns.get_level_values(0)
                    for dt, row in usd_df.tail(100).iterrows():
                        usd_krw_chart_data.append([
                            int(dt.timestamp() * 1000),
                            float(row['Open']), float(row['High']),
                            float(row['Low']), float(row['Close']), 0
                        ])
            except Exception as e:
                pass

            # ★ KST 변환 꼼수 제거 (순수 UTC 로 통일)
            dxy_chart_data = []
            try:
                dxy_df = yf.download("DX-Y.NYB", period="7d", interval="15m", progress=False)
                if not dxy_df.empty:
                    if isinstance(dxy_df.columns, pd.MultiIndex):
                        dxy_df.columns = dxy_df.columns.get_level_values(0)
                    for dt, row in dxy_df.tail(100).iterrows():
                        dxy_chart_data.append([
                            int(dt.timestamp() * 1000),
                            float(row['Open']), float(row['High']),
                            float(row['Low']), float(row['Close']), 0
                        ])
            except Exception as e:
                pass

            kimp_15m_series = []
            if btc_kr and btc_us:
                df_kr = pd.DataFrame(btc_kr, columns=['time', 'open', 'high', 'low', 'close', 'volume']).sort_values(
                    'time')
                df_us = pd.DataFrame(btc_us, columns=['time', 'open', 'high', 'low', 'close', 'volume']).sort_values(
                    'time')

                df_merge = pd.merge_asof(df_kr, df_us, on='time', suffixes=('_kr', '_us'), direction='backward')
                ex_rate = self.cached_macro['usd_krw']

                df_merge['kimp'] = ((df_merge['close_kr'] / (df_merge['close_us'] * ex_rate)) - 1) * 100
                kimp_15m_series = df_merge[['time', 'kimp']].dropna().to_dict('records')

            return {
                "usdt": usdt,
                "btc": btc_kr,
                "usd_krw_chart": usd_krw_chart_data,
                "dxy_chart": dxy_chart_data,
                "kimp_15m": kimp_15m_series,
                "rsi_usdt": self.calculate_rsi(usdt),
                "rsi_btc": self.calculate_rsi(btc_kr),
                "rsi_usdt_up": self.calculate_rsi(usdt_up)
            }
        except Exception as e:
            print(f"Chart Data Error: {e}")
            return {"usdt": [], "btc": [], "usd_krw_chart": [], "dxy_chart": [], "kimp_15m": [], "rsi_usdt": 0,
                    "rsi_btc": 0,
                    "rsi_usdt_up": 0}

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

            res = requests.get("https://api.bithumb.com/public/ticker/ALL_KRW", timeout=3)
            bithumb_data = res.json()

            if bithumb_data.get('status') == '0000':
                b_data = bithumb_data['data']
                p_bit = float(b_data['USDT']['closing_price'])
                p_btc_kr_bit = float(b_data['BTC']['closing_price'])
                p_eth_kr_bit = float(b_data['ETH']['closing_price'])
                p_xrp_kr_bit = float(b_data['XRP']['closing_price'])
            else:
                raise Exception("빗썸 실시간 다이렉트 API 응답 오류")

            p_up = self.upbit.fetch_ticker('USDT/KRW')['last']
            p_btc_kr_up = self.upbit.fetch_ticker('BTC/KRW')['last']
            p_btc_gl = self.binance.fetch_ticker('BTC/USDT')['last']

            p_eth_kr_up = self.upbit.fetch_ticker('ETH/KRW')['last']
            p_eth_gl = self.binance.fetch_ticker('ETH/USDT')['last']

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
    print("=== 🤖 봇 시작 (차트 KST 시간대 버그 패치 완료) ===")
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
                    "rsi_usdt": chart_data.get('rsi_usdt', 0),
                    "rsi_usdt_up": chart_data.get('rsi_usdt_up', 0),
                    "rsi_btc": chart_data.get('rsi_btc', 0)
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