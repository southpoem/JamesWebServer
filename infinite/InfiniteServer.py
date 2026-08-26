from datetime import datetime, date, timedelta
import json
import logging
import os
import sys
import time
import urllib.request

import pandas as pd
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy import text

from auth.Login import login_required
from infinite import Settings, ExecuteHelper
from infinite.CurrentPriceUtil import fetch_current_price

infinite_bp = Blueprint('infinite', __name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = "C:\\PycharmProjects\\InfiniteProject\\account.db"

from jinja2 import Template


def init_fear_greed_db(engine):
    query = """
    CREATE TABLE IF NOT EXISTS fear_greed_history (
        date TEXT PRIMARY KEY,
        score REAL,
        rating TEXT,
        timestamp INTEGER
    )
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()
    except Exception as e:
        logging.error(f"Error initializing fear_greed_history table: {e}")


def save_fear_and_greed_history(data):
    if not data or 'fear_and_greed_historical' not in data:
        return
    
    historical_points = data['fear_and_greed_historical'].get('data', [])
    if not historical_points:
        return

    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        init_fear_greed_db(engine)

        records = []
        for item in historical_points:
            ts_ms = item.get('x')
            score = item.get('y')
            rating = item.get('rating', '')
            if ts_ms and score is not None:
                t_struct = time.localtime(ts_ms / 1000)
                date_str = time.strftime('%Y-%m-%d', t_struct)
                records.append({
                    "date": date_str,
                    "score": round(score, 2),
                    "rating": rating,
                    "timestamp": int(ts_ms / 1000)
                })

        if records:
            upsert_query = """
            INSERT OR REPLACE INTO fear_greed_history (date, score, rating, timestamp)
            VALUES (:date, :score, :rating, :timestamp)
            """
            with engine.connect() as conn:
                for rec in records:
                    conn.execute(text(upsert_query), rec)
                conn.commit()
    except Exception as e:
        logging.error(f"Error saving fear_greed_history to DB: {e}")


_CACHE_FEAR_GREED = {"last_fetch": 0, "data": None}
_CACHE_SPREAD = {"last_fetch": 0, "data": None}
_CACHE_POLICY = {"last_fetch": 0, "data": None}


def is_refresh_needed(last_timestamp, target_hour):
    if last_timestamp == 0:
        return True
    
    now_dt = datetime.now()
    last_dt = datetime.fromtimestamp(last_timestamp)
    
    target_today = now_dt.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    
    if now_dt >= target_today and last_dt < target_today:
        return True
    if now_dt.date() > last_dt.date() and now_dt.hour >= target_hour:
        return True
        
    return False


def fetch_fear_and_greed():
    global _CACHE_FEAR_GREED
    if not is_refresh_needed(_CACHE_FEAR_GREED["last_fetch"], 6) and _CACHE_FEAR_GREED["data"] is not None:
        return _CACHE_FEAR_GREED["data"]

    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.cnn.com/'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            save_fear_and_greed_history(data)

            fg = data['fear_and_greed']
            
            score = round(float(fg.get('score', 50)))
            rating_en = str(fg.get('rating', 'neutral')).lower()
            
            if score <= 24:
                rating_kr = "극도의 공포"
                color = "#EF4444"
                badge_class = "badge-red"
            elif score <= 44:
                rating_kr = "공포"
                color = "#F97316"
                badge_class = "badge-orange"
            elif score <= 55:
                rating_kr = "중립"
                color = "#F59E0B"
                badge_class = "badge-yellow"
            elif score <= 75:
                rating_kr = "탐욕"
                color = "#10B981"
                badge_class = "badge-green"
            else:
                rating_kr = "극도의 탐욕"
                color = "#38BDF8"
                badge_class = "badge-blue"
                
            res_obj = {
                "score": score,
                "rating_en": rating_en.upper(),
                "rating_kr": rating_kr,
                "color": color,
                "badge_class": badge_class,
                "previous_close": round(float(fg.get('previous_close', 50))),
                "previous_1_week": round(float(fg.get('previous_1_week', 50))),
                "previous_1_month": round(float(fg.get('previous_1_month', 50))),
                "previous_1_year": round(float(fg.get('previous_1_year', 50))),
                "updated_at": time.strftime("%m-%d %H:%M") + " (매일 오전 06시 동기화)"
            }
            _CACHE_FEAR_GREED["last_fetch"] = time.time()
            _CACHE_FEAR_GREED["data"] = res_obj
            return res_obj
    except Exception as e:
        logging.error(f"Error fetching Fear & Greed Index: {e}")
        if _CACHE_FEAR_GREED["data"] is not None:
            return _CACHE_FEAR_GREED["data"]
        return {
            "score": 50,
            "rating_en": "NEUTRAL",
            "rating_kr": "중립",
            "color": "#F59E0B",
            "badge_class": "badge-yellow",
            "previous_close": 50,
            "previous_1_week": 50,
            "previous_1_month": 50,
            "previous_1_year": 50,
            "updated_at": time.strftime("%m-%d %H:%M")
        }


@infinite_bp.route('/infinite/macro', methods=['GET', 'POST'])
@login_required
def show_recent_ticker_data():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    today = date.today()
    start_date = today - timedelta(days=6)
    account_filter = request.args.get("account", None)

    with engine.connect() as conn:
        latest_date = conn.execute(
            text("SELECT MAX(date) FROM account_daily WHERE date >= :start_date"),
            {"start_date": start_date}
        ).scalar()

    if not latest_date:
        return "최근 일주일간 저장된 데이터가 없습니다."

    base_query = """
    SELECT ad.account_id, ad.date, ti.ticker, ti.current_round, ti.target_profit_rate,
           ti.total_investment, ti.total_shares, ti.current_price, ti.average_buy_price
    FROM ticker_info ti
    JOIN account_daily ad ON ti.account_daily_id = ad.id
    WHERE ad.date = :latest_date
    """

    if account_filter:
        base_query += " AND ad.account_id LIKE :account_filter"
    base_query += " ORDER BY ad.account_id, ti.ticker"

    with engine.connect() as conn:
        if account_filter:
            df = pd.read_sql(text(base_query), conn, params={
                "latest_date": latest_date,
                "account_filter": f"%{account_filter}%"
            })
        else:
            df = pd.read_sql(text(base_query), conn, params={"latest_date": latest_date})

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d")
    df["구분"] = df["account_id"].apply(lambda x: "Private" if "private" in x.lower() else "Public")
    
    def get_row_color(row):
        try:
            shares = float(str(row["total_shares"]).replace(",", ""))
            if shares > 0:
                return "yellow"
        except:
            pass
        return "white"
    df["계좌색상"] = df.apply(get_row_color, axis=1)

    current_prices = {}
    df["현재가"] = ""
    df["평단가(수익률)"] = ""

    for i, row in df.iterrows():
        ticker = row["ticker"]
        avg = float(row["average_buy_price"])
        try:
            current = current_prices.get(ticker) or fetch_current_price(ticker)
            current_prices[ticker] = current
            df.at[i, "현재가"] = f"{current:.2f}"
            profit = ((current - avg) / avg) * 100
            df.at[i, "평단가(수익률)"] = f"{avg:.2f} ({profit:+.2f}%)"
        except Exception as e:
            logging.error(f"Error processing ticker {ticker}: {e}", exc_info=True)
            df.at[i, "현재가"] = "N/A"
            df.at[i, "평단가(수익률)"] = "N/A"

    df["총투자금액"] = (df["total_shares"].astype(float) * df["current_price"].astype(float)).astype(int)
    # 수정된 코드 (86~88라인 대체)
    if not df.empty:
        clean_target = df["target_profit_rate"].astype(str).str.replace("%", "").str.strip()
        df["총투자금액(목표수익율)"] = (
                df["total_investment"].astype(str) +
                " (" +
                clean_target +
                "%)"
        )
    else:
        df["총투자금액(목표수익율)"] = ""
    #
    # df["총투자금액(목표수익율)"] = df.apply(
    #     lambda row: f"{row['total_investment']} ({int(float(row['target_profit_rate']))}%)", axis=1
    # )

    # Load settings to get start_date
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    df["시작일"] = ""
    df["전략"] = ""
    for idx, row in df.iterrows():
        key = f"{row['account_id'].lower()}_{row['ticker'].upper()}"
        start_date = settings.get(key, {}).get("start_date", "2026-07-11")
        strategy_val = settings.get(key, {}).get("strategy", "v2.2")
        readable_strategy = "v2.2" if strategy_val == "v2.2" else "Only Buying"
        df.at[idx, "시작일"] = start_date
        df.at[idx, "전략"] = readable_strategy

    df = df[[
        "계좌색상", "시작일", "구분", "ticker", "전략", "current_round", "total_shares",
        "평단가(수익률)", "현재가", "총투자금액", "총투자금액(목표수익율)"
    ]]
    df.columns = ["계좌색상", "시작일", "구분", "티커", "전략", "회차", "개수", "평단가(수익률)", "현재가", "총매입금액", "총투자금액(목표수익율)"]

    table_rows = ""
    ticker_cards = []
    for _, row in df.iterrows():
        row_html = f"<tr style='color:{row['계좌색상']}'>" + "".join(
            f"<td>{row[col]}</td>" for col in [
                "시작일", "구분", "티커", "전략", "회차", "개수", "평단가(수익률)", "현재가", "총매입금액", "총투자금액(목표수익율)"
            ]
        ) + "</tr>"
        table_rows += row_html

        try:
            curr_rnd = int(row["회차"])
        except:
            curr_rnd = 0
        try:
            tot_split = int(str(row["총투자금액(목표수익율)"]).split("(")[0]) if "(" in str(row["총투자금액(목표수익율)"]) else 40
        except:
            tot_split = 40
        
        # We parse total_splits and target_profit_rate
        key = f"{row['account_id'].lower()}_{row['티커'].upper()}" if 'account_id' in row else f"public_{row['티커'].upper()}"
        setting_info = settings.get(key, {})
        tot_split = int(setting_info.get("split", 40))
        target_rate = setting_info.get("target", "12")
        tot_invest = setting_info.get("capital", "0")

        progress_pct = min(100, int((curr_rnd / tot_split) * 100)) if tot_split > 0 else 0
        
        try:
            # Parse average price and profit
            avg_str = str(row["평단가(수익률)"])
            avg_val = float(avg_str.split(" ")[0]) if " " in avg_str else float(avg_str)
        except:
            avg_val = 0.0
            
        try:
            curr_val = float(row["현재가"])
        except:
            curr_val = avg_val

        profit_pct = ((curr_val - avg_val) / avg_val * 100) if avg_val > 0 else 0.0

        try:
            qty_val = float(row["개수"])
        except:
            qty_val = 0.0

        acc_id_str = str(row.get('account_id', '')).lower() if 'account_id' in row else ''
        broker_name = "삼성증권" if "samsung" in acc_id_str else "메리츠증권"
        broker_badge = "badge-blue" if "samsung" in acc_id_str else "badge-yellow"

        ticker_cards.append({
            "ticker": row["티커"],
            "account_id": key,
            "broker": broker_name,
            "broker_badge": broker_badge,
            "is_private": row["구분"] == "Private",
            "mode": row["구분"],
            "start_date": row["시작일"],
            "strategy": row["전략"],
            "current_round": curr_rnd,
            "total_splits": tot_split,
            "quantity": int(qty_val) if qty_val.is_integer() else qty_val,
            "average_price": f"${avg_val:.2f}" if avg_val > 0 else "$0.00",
            "current_price": f"${curr_val:.2f}" if curr_val > 0 else "$0.00",
            "profit_rate": f"{profit_pct:+.2f}",
            "profit_val": profit_pct,
            "total_buy": f"${(qty_val * avg_val):,.2f}",
            "total_invest": f"${float(tot_invest):,.0f}" if tot_invest.isdigit() else f"${tot_invest}",
            "target_profit_rate": target_rate,
            "progress_percent": progress_pct
        })

    fear_greed = fetch_fear_and_greed()
    return render_template("infinite_main.html", latest_date=latest_date, table_rows=table_rows, ticker_cards=ticker_cards, fear_greed=fear_greed)


def fetch_macro_indicators():
    global _CACHE_SPREAD, _CACHE_POLICY

    # 1. Real-time Symbols (DXY, VIX, USD/KRW, USD/JPY)
    rt_symbols = {
        'dxy': 'DX-Y.NYB',
        'vix': '^VIX',
        'usdkrw': 'KRW=X',
        'usdjpy': 'JPY=X'
    }
    
    results = {}
    for key, sym in rt_symbols.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                meta = res['chart']['result'][0]['meta']
                curr = meta.get('regularMarketPrice', 0.0)
                prev = meta.get('chartPreviousClose', curr)
                diff = curr - prev
                pct = (diff / prev * 100) if prev else 0.0
                
                results[key] = {
                    "price": round(curr, 2),
                    "change": round(diff, 2),
                    "change_pct": f"{pct:+.2f}%",
                    "up": diff >= 0
                }
        except Exception as e:
            logging.error(f"Error fetching real-time symbol {sym}: {e}")
            results[key] = {"price": 0.0, "change": 0.0, "change_pct": "0.00%", "up": True}

    vix_val = results['vix']['price']
    if vix_val < 15:
        vix_status = "안정 (Low Risk)"
        vix_badge = "badge-green"
    elif vix_val < 25:
        vix_status = "보통 (Moderate Risk)"
        vix_badge = "badge-yellow"
    elif vix_val < 35:
        vix_status = "경계 (Elevated Risk)"
        vix_badge = "badge-orange"
    else:
        vix_status = "극도 공포/매수기회 (High Volatility)"
        vix_badge = "badge-red"

    # 2. AM 06:00 Refresh: Yield Spread (US10Y - US2Y)
    if is_refresh_needed(_CACHE_SPREAD["last_fetch"], 6) or _CACHE_SPREAD["data"] is None:
        try:
            url_10y = "https://query1.finance.yahoo.com/v8/finance/chart/^TNX?interval=1d&range=2d"
            url_5y = "https://query1.finance.yahoo.com/v8/finance/chart/^FVX?interval=1d&range=2d"
            
            req1 = urllib.request.Request(url_10y, headers={'User-Agent': 'Mozilla/5.0'})
            res1 = json.loads(urllib.request.urlopen(req1, timeout=4).read())
            us10y_val = round(res1['chart']['result'][0]['meta'].get('regularMarketPrice', 4.26), 2)
            
            req2 = urllib.request.Request(url_5y, headers={'User-Agent': 'Mozilla/5.0'})
            res2 = json.loads(urllib.request.urlopen(req2, timeout=4).read())
            us5y_val = round(res2['chart']['result'][0]['meta'].get('regularMarketPrice', 4.36), 2)
            
            us2y_est = round(us5y_val - 0.12, 2)
            spread = round(us10y_val - us2y_est, 2)
            
            if spread < 0:
                spread_status = f"장단기 금리 역전 ({spread:+.2f}%)"
                spread_badge = "badge-red"
            else:
                spread_status = f"정상화 / 양의 스프레드 ({spread:+.2f}%)"
                spread_badge = "badge-green"

            _CACHE_SPREAD["data"] = {
                "us10y": us10y_val,
                "us2y": us2y_est,
                "spread": spread,
                "spread_str": f"{spread:+.2f}%",
                "spread_status": spread_status,
                "spread_badge": spread_badge,
                "updated_at": time.strftime("%m-%d %H:%M") + " (매일 오전 06시 동기화)"
            }
            _CACHE_SPREAD["last_fetch"] = time.time()
        except Exception as e:
            logging.error(f"Error updating Yield Spread cache: {e}")
            if _CACHE_SPREAD["data"] is None:
                _CACHE_SPREAD["data"] = {
                    "us10y": 4.26, "us2y": 4.36, "spread": -0.10, "spread_str": "-0.10%",
                    "spread_status": "장단기 금리 역전 (-0.10%)", "spread_badge": "badge-red",
                    "updated_at": time.strftime("%m-%d %H:%M")
                }

    # 3. PM 22:00 Refresh: Policy Indicators (WTI, Core PCE, CME FedWatch)
    if is_refresh_needed(_CACHE_POLICY["last_fetch"], 22) or _CACHE_POLICY["data"] is None:
        try:
            url_wti = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?interval=1d&range=2d"
            req_w = urllib.request.Request(url_wti, headers={'User-Agent': 'Mozilla/5.0'})
            res_w = json.loads(urllib.request.urlopen(req_w, timeout=4).read())
            meta_w = res_w['chart']['result'][0]['meta']
            curr_w = meta_w.get('regularMarketPrice', 78.18)
            prev_w = meta_w.get('chartPreviousClose', curr_w)
            diff_w = curr_w - prev_w
            pct_w = (diff_w / prev_w * 100) if prev_w else 0.0

            _CACHE_POLICY["data"] = {
                "wti": {
                    "price": round(curr_w, 2),
                    "change": round(diff_w, 2),
                    "change_pct": f"{pct_w:+.2f}%",
                    "up": diff_w >= 0
                },
                "pce": 2.8,
                "fed_hold_prob": 55.9,
                "fed_cut_prob": 44.1,
                "updated_at": time.strftime("%m-%d %H:%M") + " (매일 오후 10시 동기화)"
            }
            _CACHE_POLICY["last_fetch"] = time.time()
        except Exception as e:
            logging.error(f"Error updating Policy indicators cache: {e}")
            if _CACHE_POLICY["data"] is None:
                _CACHE_POLICY["data"] = {
                    "wti": {"price": 78.18, "change": 0.0, "change_pct": "0.00%", "up": True},
                    "pce": 2.8, "fed_hold_prob": 55.9, "fed_cut_prob": 44.1,
                    "updated_at": time.strftime("%m-%d %H:%M")
                }

    spread_data = _CACHE_SPREAD["data"]
    policy_data = _CACHE_POLICY["data"]

    return {
        "dxy": results['dxy'],
        "vix": results['vix'],
        "vix_status": vix_status,
        "vix_badge": vix_badge,
        "usdkrw": results['usdkrw'],
        "usdjpy": results['usdjpy'],
        "us10y": spread_data['us10y'],
        "us2y": spread_data['us2y'],
        "spread": spread_data['spread'],
        "spread_str": spread_data['spread_str'],
        "spread_status": spread_data['spread_status'],
        "spread_badge": spread_data['spread_badge'],
        "spread_updated_at": spread_data['updated_at'],
        "wti": policy_data['wti'],
        "pce": policy_data['pce'],
        "fed_hold_prob": policy_data['fed_hold_prob'],
        "fed_cut_prob": policy_data['fed_cut_prob'],
        "policy_updated_at": policy_data['updated_at'],
        "realtime_updated_at": time.strftime("%H:%M:%S") + " ⚡ 실시간"
    }


import sqlite3



import FinanceDataReader as fdr
import requests
import threading

krx_map_cache = {}
krx_map_lock = threading.Lock()

def get_krx_map():
    global krx_map_cache
    with krx_map_lock:
        if not krx_map_cache:
            try:
                df_krx = fdr.StockListing('KRX')
                df_etf = fdr.StockListing('ETF/KR')
                for _, row in df_krx.iterrows():
                    krx_map_cache[row['Name']] = row['Code']
                for _, row in df_etf.iterrows():
                    krx_map_cache[row['Name']] = row['Symbol']
            except Exception as e:
                logging.error(f"Failed to load KRX/ETF list: {e}")
    return krx_map_cache

@infinite_bp.route('/api/live_prices', methods=['GET', 'POST'])
@infinite_bp.route('/infinite/api/live_prices', methods=['GET', 'POST'])
@login_required
def api_live_prices():
    tickers = []
    if request.method == 'POST':
        if request.is_json and request.json:
            tickers = request.json.get('tickers', [])
        elif request.form:
            tickers = request.form.getlist('tickers')
            
    if not tickers:
        ticker_param = request.args.get('tickers')
        if ticker_param:
            tickers = [t.strip() for t in ticker_param.split(',') if t.strip()]
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT DISTINCT ticker FROM asset_history")
                tickers = [r[0] for r in c.fetchall() if r[0]]
                conn.close()
            except Exception as e:
                logging.error(f"Error reading asset_history tickers: {e}")
                tickers = []
                
    krx_map = get_krx_map()
    
    kr_name_to_code = {}
    us_tickers = []
    
    for name in tickers:
        if not name:
            continue
        if name in krx_map:
            kr_name_to_code[name] = krx_map[name]
        else:
            us_tickers.append(name)
            
    live_prices = {}
    
    # 1. KRX real-time stock price query
    if kr_name_to_code:
        codes = list(set(kr_name_to_code.values()))
        query = "SERVICE_ITEM:" + ",".join(codes)
        url = f"https://polling.finance.naver.com/api/realtime?query={query}"
        try:
            res = requests.get(url, timeout=5)
            res_data = res.json()
            if res_data.get('resultCode') == 'success':
                items = res_data.get('result', {}).get('areas', [{}])[0].get('datas', [])
                code_to_data = {item['cd']: item for item in items}
                
                for name, code in kr_name_to_code.items():
                    if code in code_to_data:
                        it = code_to_data[code]
                        nv = it.get('nv', 0)
                        cv = it.get('cv', 0)
                        cr = it.get('cr', 0.0)
                        rf = str(it.get('rf', '3'))
                        
                        over_market_info = None
                        nxt = it.get('nxtOverMarketPriceInfo')
                        if nxt:
                            st = nxt.get('overMarketStatus', '')
                            is_open = st in ['OPEN', 'PREOPEN']
                            p_str = str(nxt.get('overPrice', '0')).replace(',', '').strip()
                            cv_str = str(nxt.get('compareToPreviousClosePrice', '0')).replace(',', '').strip()
                            cr_str = str(nxt.get('fluctuationsRatio', '0')).replace(',', '').strip()
                            try:
                                over_p = float(p_str)
                            except:
                                over_p = 0
                            if over_p > 0:
                                try:
                                    over_cv = float(cv_str)
                                except:
                                    over_cv = 0
                                try:
                                    over_cr = float(cr_str)
                                except:
                                    over_cr = 0
                                over_sign = str(nxt.get('compareToPreviousPrice', {}).get('code', '3'))
                                stype = nxt.get('tradingSessionType', '')
                                sname = '시간외'
                                if 'PRE' in stype: sname = '프리장'
                                elif 'AFTER' in stype: sname = '시간외'
                                over_market_info = {
                                    'is_open': is_open,
                                    'session_type': stype,
                                    'session_name': sname,
                                    'price': over_p,
                                    'change_val': over_cv,
                                    'change_rate': over_cr,
                                    'sign': over_sign
                                }

                        live_prices[name] = {
                            'price': nv,
                            'change_val': cv,
                            'change_rate': cr,
                            'sign': rf,
                            'currency': 'KRW',
                            'over_market': over_market_info,
                            'nv': nv,
                            'cv': cv,
                            'cr': cr,
                            'rf': rf,
                            'stck_prpr': nv,
                            'prdy_vrss': cv,
                            'prdy_ctrt': cr,
                            'prdy_vrss_sign': rf
                        }
        except Exception as e:
            logging.error(f"KRX live price fetch error: {e}")
            
    # 2. US real-time stock price query
    for us_t in set(us_tickers):
        try:
            url = f"https://polling.finance.naver.com/api/realtime/worldstock/stock/{us_t}"
            res = requests.get(url, timeout=3)
            res_json = res.json()
            datas = res_json.get('datas', [])
            if datas:
                d = datas[0]
                price = float(d.get('closePriceRaw') or d.get('closePrice') or 0)
                change_val = float(d.get('compareToPreviousClosePriceRaw') or d.get('compareToPreviousClosePrice') or 0)
                change_rate = float(d.get('fluctuationsRatioRaw') or d.get('fluctuationsRatio') or 0)
                sign_obj = d.get('compareToPreviousPrice') or {}
                sign = str(sign_obj.get('code', '3'))
                
                over_market_info = None
                over = d.get('overMarketPriceInfo')
                if over:
                    st = over.get('overMarketStatus', '')
                    is_open = st in ['OPEN', 'PREOPEN']
                    p_str = str(over.get('overPrice', '0')).replace(',', '').strip()
                    cv_str = str(over.get('compareToPreviousClosePrice', '0')).replace(',', '').strip()
                    cr_str = str(over.get('fluctuationsRatio', '0')).replace(',', '').strip()
                    try:
                        over_p = float(p_str)
                    except:
                        over_p = 0
                    if over_p > 0:
                        try:
                            over_cv = float(cv_str)
                        except:
                            over_cv = 0
                        try:
                            over_cr = float(cr_str)
                        except:
                            over_cr = 0
                        over_sign = str(over.get('compareToPreviousPrice', {}).get('code', '3'))
                        stype = over.get('tradingSessionType', '')
                        sname = '장외'
                        if 'PRE' in stype: sname = '프리'
                        elif 'AFTER' in stype: sname = '애프터'
                        over_market_info = {
                            'is_open': is_open,
                            'session_type': stype,
                            'session_name': sname,
                            'price': over_p,
                            'change_val': over_cv,
                            'change_rate': over_cr,
                            'sign': over_sign
                        }

                live_prices[us_t] = {
                    'price': price,
                    'change_val': change_val,
                    'change_rate': change_rate,
                    'sign': sign,
                    'currency': 'USD',
                    'over_market': over_market_info,
                    'nv': price,
                    'cv': change_val,
                    'cr': change_rate,
                    'rf': sign,
                    'stck_prpr': price,
                    'prdy_vrss': change_val,
                    'prdy_ctrt': change_rate,
                    'prdy_vrss_sign': sign
                }
        except Exception as e:
            logging.debug(f"US live price fetch error for {us_t}: {e}")
            
    return jsonify({
        'status': 'success',
        'data': live_prices
    })

@infinite_bp.route('/toggle_exclude', methods=['POST'])
@infinite_bp.route('/infinite/toggle_exclude', methods=['POST'])
@login_required
def toggle_exclude():
    broker = request.form.get('broker') or '메리츠'
    account_num = request.form.get('account_num')
    is_excluded = request.form.get('is_excluded') == 'true'
    current_broker = request.form.get('current_broker') or request.args.get('broker', 'meritz')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS excluded_accounts (broker TEXT, account_num TEXT, PRIMARY KEY (broker, account_num))")
        if is_excluded:
            c.execute("INSERT OR REPLACE INTO excluded_accounts (broker, account_num) VALUES (?, ?)", (broker, account_num))
        else:
            c.execute("DELETE FROM excluded_accounts WHERE account_num = ?", (account_num,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"toggle_exclude error: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'status': 'success', 'is_excluded': is_excluded})
        
    return redirect(url_for('infinite.infinite_assets', broker=current_broker))

@infinite_bp.route('/infinite', methods=['GET'])
@login_required
def infinite_assets():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM asset_history", conn)
        
        # --- US Ticker Mapping ---
        def map_us_ticker(t):
            if pd.isnull(t): return t
            t_upper = str(t).upper()
            if 'PROSHARES QQQ 2X' in t_upper: return 'QLD'
            if 'PROSHARES ULTRAPRO QQQ' in t_upper: return 'TQQQ'
            if 'DIREXION SEMICONDUCTOR DAILY 3X' in t_upper: return 'SOXL'
            if 'DIREXION DAILY SEMICONDUCTOR BULL 3X' in t_upper: return 'SOXL'
            if 'PROSHARES ULTRAPRO SHORT QQQ' in t_upper: return 'SQQQ'
            return t
        df['ticker'] = df['ticker'].apply(map_us_ticker)

        
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS excluded_accounts (broker TEXT, account_num TEXT, PRIMARY KEY (broker, account_num))")
        excluded_df = pd.read_sql_query("SELECT broker, account_num FROM excluded_accounts", conn)
        excluded_acc_nums = set(excluded_df['account_num'].tolist()) if not excluded_df.empty else set()
        conn.close()
    except Exception as e:
        logging.error(f"Asset history DB error: {e}")
        return render_template('infinite_assets.html', error=f"DB Error: {e}", data=None, current_broker='samsung')

    if df.empty:
        return render_template('infinite_assets.html', data=None, current_broker='samsung')
        
    all_accounts_df = df[['broker', 'account_type', 'account_num']].drop_duplicates()
    all_accounts_list = all_accounts_df.to_dict('records')
    for acc in all_accounts_list:
        acc['is_excluded'] = acc['account_num'] in excluded_acc_nums
        acc['masked_num'] = '*' + str(acc['account_num'])[-5:] if len(str(acc['account_num'])) >= 5 else str(acc['account_num'])
        b_str = str(acc['broker']).upper()
        acc['broker_clean'] = '삼성증권' if 'SAMSUNG' in b_str or '삼성' in b_str else ('메리츠' if 'MERITZ' in b_str or '메리츠' in b_str else str(acc['broker']))

    df = df[~df['account_num'].isin(excluded_acc_nums)]

    broker_filter = request.args.get('broker', 'samsung')
    df_all = df.copy()  # keep unfiltered for family tab sub-totals
    if broker_filter == 'analysis':
        # No filtering, use all
        pass
    elif broker_filter == 'samsung':
        df = df[df['broker'].str.upper().str.contains('SAMSUNG|삼성', na=False)]
    elif broker_filter == 'meritz':
        df = df[df['broker'].str.upper().str.contains('MERITZ|메리츠', na=False)]
    # For family tab: use all brokers (no filter on df)

    if df.empty:
        return render_template('infinite_assets.html', data=None, current_broker=broker_filter)

    df['date'] = pd.to_datetime(df['date'])
    available_dates = sorted(df['date'].unique())
    today = available_dates[-1]
    
    def get_closest_date(target_date):
        past_dates = [d for d in available_dates if d <= target_date]
        return past_dates[-1] if past_dates else None

    yesterday = get_closest_date(today - pd.Timedelta(days=1))
    if yesterday == today:
        past_dates = [d for d in available_dates if d < today]
        yesterday = past_dates[-1] if past_dates else None

    last_week = get_closest_date(today - pd.Timedelta(days=7))
    if last_week == today:
        last_week = None

    last_month = get_closest_date(today - pd.Timedelta(days=30))
    if last_month == today:
        last_month = None

    def get_totals(dt):
        if dt is None:
            return 0
        return float(df[df['date'] == dt]['total_evaluation'].sum())

    total_today = get_totals(today)
    total_yesterday = get_totals(yesterday)
    total_last_week = get_totals(last_week)
    total_last_month = get_totals(last_month)

    import re
    df_today = df[df['date'] == today].copy()
    
    # 5만원 이하의 자투리 자산은 화면 표시(리스트, 차트 등)에서 숨김 처리
    df_today = df_today[df_today['total_evaluation'] > 50000]
    
    df_today['account_type'] = df_today['account_type'].apply(lambda x: re.sub(r'\(.*?\)', '', str(x)).strip())
    df_today['account_num'] = df_today['account_num'].apply(lambda x: '*' + str(x)[-5:] if len(str(x)) >= 5 else str(x))
    account_summary = df_today.groupby(['account_type', 'account_num', 'broker']).agg({
        'total_investment': 'sum',
        'total_evaluation': 'sum',
        'profit_loss': 'sum'
    }).reset_index().to_dict('records')

    ticker_summary = df_today.groupby('ticker').agg({
        'total_investment': 'sum',
        'total_evaluation': 'sum',
        'profit_loss': 'sum',
        'quantity': 'sum'
    }).reset_index().to_dict('records')

    from infinite import FamilyDBHelper
    family_assets = []
    if broker_filter == 'family':
        try:
            family_assets = FamilyDBHelper.get_latest_family_assets()
            for fa in family_assets:
                total_today += fa['amount']
                account_summary.append({
                    'broker': '가족',
                    'account_num': '',
                    'account_type': f"{fa['account_name']} ({fa['asset_type']})",
                    'total_investment': fa['amount'],
                    'total_evaluation': fa['amount'],
                    'profit_loss': 0
                })
                
            fam_df = FamilyDBHelper.get_family_history_df()
            if not fam_df.empty:
                fam_df['date'] = pd.to_datetime(fam_df['date'])
                df = pd.concat([df, fam_df], ignore_index=True)
        except Exception as e:
            logging.error(f"Failed to load family assets: {e}")

    chart_dates_dt = sorted(df['date'].unique())
    chart_dates = [d.strftime('%Y-%m-%d') for d in chart_dates_dt]
    
    missing_today_data = False
    actual_today = datetime.now().date()
    if chart_dates and pd.to_datetime(chart_dates[-1]).date() < actual_today:
        missing_today_data = True
        chart_dates.append(actual_today.strftime('%Y-%m-%d') + ' (미포함)')
    
    chart_datasets = []
    
    samsung_colors = ['#4facfe', '#00f2fe', '#2980b9', '#3498db', '#6dd5ed']
    meritz_colors = ['#ff5252', '#ff1744', '#f50057', '#d50000', '#ff8a80']
    family_colors = ['#ffd700', '#ffeb3b', '#fbc02d', '#f57f17', '#ffee58']
    other_colors = ['#ff5252', '#4facfe', '#ffd700', '#4caf50', '#9c27b0', '#ff9800', '#00bcd4', '#e91e63', '#8bc34a', '#3f51b5']
    
    sam_idx = 0
    mer_idx = 0
    fam_idx = 0
    oth_idx = 0
    
    def get_account_label(row):
        broker = str(row['broker'])
        acc_type = re.sub(r'\([^)]*\)', '', str(row['account_type'])).strip()
        acc_num = str(row.get('account_num', 'nan'))
        if acc_num == 'nan' or not acc_num:
            acc_num = ''
        
        is_samsung = 'SAMSUNG' in broker.upper() or '삼성' in broker
        is_meritz = 'MERITZ' in broker.upper() or '메리츠' in broker
        is_family = '가족' in broker
        
        if broker_filter in ['samsung', 'meritz']:
            b_name = '삼성증권' if is_samsung else ('메리츠' if is_meritz else ('가족' if is_family else broker))
            if is_family or not acc_num:
                return f"{b_name} {acc_type}"
            masked_num = '*' + acc_num[-5:] if len(acc_num) >= 5 else acc_num
            return f"{b_name} {acc_type} ({masked_num})"
        else:
            if is_samsung: return "삼성"
            if is_meritz: return "메리츠"
            if is_family: return "가족"
            return broker

    df['account_label'] = df.apply(get_account_label, axis=1)
    latest_date = df['date'].max()
    latest_totals = df.groupby('account_label').apply(lambda x: x.sort_values('date').iloc[-1]['total_evaluation']).sort_values(ascending=False)
    
    for account_label in latest_totals.index:
        group = df[df['account_label'] == account_label]
        date_vals = group.groupby('date')['total_evaluation'].sum().to_dict()
        data_arr = []
        last_val = 0
        for d in chart_dates_dt:
            val = date_vals.get(d, last_val)
            data_arr.append(float(val))
            last_val = val
        if missing_today_data:
            data_arr.append(data_arr[-1])
            
        if broker_filter in ['samsung', 'meritz']:
            color = other_colors[oth_idx % len(other_colors)]
            oth_idx += 1
        else:
            if '삼성' in account_label:
                color = samsung_colors[sam_idx % len(samsung_colors)]
                sam_idx += 1
            elif '메리츠' in account_label:
                color = meritz_colors[mer_idx % len(meritz_colors)]
                mer_idx += 1
            elif '가족' in account_label:
                color = family_colors[fam_idx % len(family_colors)]
                fam_idx += 1
            else:
                color = other_colors[oth_idx % len(other_colors)]
                oth_idx += 1
        
        chart_datasets.append({
            'label': account_label,
            'data': data_arr,
            'borderColor': color,
            'backgroundColor': color + '33',
            'borderWidth': 2,
            'tension': 0.4,
            'fill': True,
            'pointRadius': 2
        })
        
    detailed_list = df_today.sort_values(by=['account_type', 'account_num', 'total_evaluation'], ascending=[True, True, False]).to_dict('records')
    db_mtime = os.path.getmtime(DB_PATH)
    last_update_time = datetime.fromtimestamp(db_mtime).strftime('%Y-%m-%d %H:%M:%S')


    # --- Analysis Data Preparation ---
    analysis_data = {}
    if broker_filter == 'analysis':
        all_items = []
        for tk in ticker_summary:
            all_items.append({'name': tk['ticker'], 'amount': tk['total_evaluation']})
        for fa in family_assets:
            all_items.append({'name': fa['account_name'] + ' (' + fa['asset_type'] + ')', 'amount': fa['amount']})
            
        us_keywords = ['미국', 'QQQ', 'S&P', 'DIREXION', 'PROSHARES', '나스닥']
        cash_keywords = ['현금', '예수금', 'MMF', 'CMA']
        semi_keywords = ['반도체', 'SEMICONDUCTOR', '삼성전자', 'SK하이닉스']
        index_keywords = ['나스닥', 'QQQ', 'S&P', '200TR', '지수']
        bond_keywords = ['채권', '혼합']
        
        country_group = {'미국 자산': 0, '한국 자산': 0}
        sector_group = {}
        stock_group = {}
        
        for item in all_items:
            name = item['name'].upper()
            amt = item['amount']
            
            # 1. Country Group
            if any(k in name for k in cash_keywords):
                pass # cash shouldn't be counted in US vs KR according to standard, but if we do, it's KR.
            if any(k in name for k in us_keywords):
                country_group['미국 자산'] += amt
            else:
                country_group['한국 자산'] += amt
                
            # 2. Sector Group
            sector = '기타'
            if any(k in name for k in cash_keywords): sector = '현금 (Cash)'
            elif any(k in name for k in semi_keywords): sector = '반도체 (Semiconductor)'
            elif any(k in name for k in index_keywords): sector = '시장지수 (Index)'
            elif any(k in name for k in bond_keywords): sector = '채권/혼합 (Bond/Mixed)'
            elif '보험' in name: sector = '보험 (Insurance)'
            
            sector_group[sector] = sector_group.get(sector, 0) + amt
            
            # 3. Stock Group
            stock_group[item['name']] = stock_group.get(item['name'], 0) + amt
            
        analysis_data = {
            'country': [{'label': k, 'value': v} for k, v in country_group.items() if v > 0],
            'sector': [{'label': k, 'value': v} for k, v in sector_group.items() if v > 0],
            'stock': [{'label': k, 'value': v} for k, v in stock_group.items() if v > 0]
        }
        
        # Sort desc
        analysis_data['country'].sort(key=lambda x: x['value'], reverse=True)
        analysis_data['sector'].sort(key=lambda x: x['value'], reverse=True)
        analysis_data['stock'].sort(key=lambda x: x['value'], reverse=True)

    # Compute family total for accurate deltas
    family_total = sum(fa['amount'] for fa in family_assets) if broker_filter == 'family' else 0

    # For family tab: compute sub-totals per broker from the full unfiltered df
    family_sub = {'samsung': 0, 'meritz': 0, 'manual': 0, 'grand_total': 0,
                  'samsung_pl': 0, 'samsung_pl_rate': 0,
                  'meritz_pl': 0, 'meritz_pl_rate': 0,
                  'total_pl': 0, 'total_pl_rate': 0}
    if broker_filter == 'family':
        try:
            df_all['date'] = pd.to_datetime(df_all['date'])
            latest_all = df_all['date'].max()
            df_all_today = df_all[df_all['date'] == latest_all]

            # Samsung
            df_sam = df_all_today[df_all_today['broker'].str.upper().str.contains('SAMSUNG|삼성', na=False)]
            samsung_eval  = float(df_sam['total_evaluation'].sum())
            samsung_invest = float(df_sam['total_investment'].sum())
            samsung_pl    = float(df_sam['profit_loss'].sum())
            samsung_pl_rate = (samsung_pl / samsung_invest * 100) if samsung_invest > 0 else 0

            # Meritz
            df_mer = df_all_today[df_all_today['broker'].str.upper().str.contains('MERITZ|메리츠', na=False)]
            meritz_eval   = float(df_mer['total_evaluation'].sum())
            meritz_invest  = float(df_mer['total_investment'].sum())
            meritz_pl     = float(df_mer['profit_loss'].sum())
            meritz_pl_rate = (meritz_pl / meritz_invest * 100) if meritz_invest > 0 else 0

            # Manual (수동입력은 수익률 없음)
            manual_total  = float(sum(fa['amount'] for fa in family_assets))

            # Grand total
            grand_total   = samsung_eval + meritz_eval + manual_total
            total_pl      = samsung_pl + meritz_pl
            total_invest   = samsung_invest + meritz_invest
            total_pl_rate  = (total_pl / total_invest * 100) if total_invest > 0 else 0

            family_sub = {
                'samsung': samsung_eval,
                'samsung_pl': samsung_pl,
                'samsung_pl_rate': samsung_pl_rate,
                'meritz': meritz_eval,
                'meritz_pl': meritz_pl,
                'meritz_pl_rate': meritz_pl_rate,
                'manual': manual_total,
                'grand_total': grand_total,
                'total_pl': total_pl,
                'total_pl_rate': total_pl_rate,
            }
            # Override total_today with actual grand total for family
            total_today = grand_total
        except Exception as e:
            logging.error(f"Failed to compute family_sub: {e}")

    df_raw_today = df[df['date'] == today]
    total_eval_direct = float(df_raw_today['total_evaluation'].sum())
    total_invest_direct = float(df_raw_today['total_investment'].sum())
    total_pl_direct = float(df_raw_today['profit_loss'].sum())
    total_pl_rate_direct = (total_pl_direct / total_invest_direct * 100) if total_invest_direct > 0 else 0

    data = {
        'today_str': today.strftime('%Y-%m-%d'),
        'last_update_time': last_update_time,
        'total_today': total_today,
        'total_eval': total_eval_direct,
        'total_pl': total_pl_direct,
        'total_invest': total_invest_direct,
        'total_pl_rate': total_pl_rate_direct,
        'change_1d': (total_today - family_total) - total_yesterday if yesterday else 0,
        'change_7d': (total_today - family_total) - total_last_week if last_week else 0,
        'change_30d': (total_today - family_total) - total_last_month if last_month else 0,
        'account_summary': account_summary,
        'ticker_summary': ticker_summary,
        'chart_dates': chart_dates,
        'chart_datasets': chart_datasets,
        'detailed_list': detailed_list,
        'family_assets': family_assets,
        'family_sub': family_sub,
        'all_accounts_list': all_accounts_list,
        'analysis_data': analysis_data
    }
    
    return render_template('infinite_assets.html', data=data, current_broker=broker_filter)


@infinite_bp.route('/macro', methods=['GET'])
@login_required
def macro_dashboard():
    fear_greed = fetch_fear_and_greed()
    macro = fetch_macro_indicators()
    return render_template("macro.html", fear_greed=fear_greed, macro=macro)


SETTINGS_FILE = "C:\\PycharmProjects\\InfiniteProject\\infinite_settings.json"


@infinite_bp.route('/infinite_settings', methods=['GET'])
@login_required
def infinite_settings():
    return render_template("settings_infinite.html")


@infinite_bp.route('/infinite_charts', methods=['GET'])
@login_required
def infinite_charts():
    return render_template("infinite_chart.html")


@infinite_bp.route('/api/chart_data', methods=['GET'])
@login_required
def get_chart_data():
    timeframe = request.args.get('tf', '1d').lower()
    
    interval_map = {
        '1d': ('1d', '3mo'),
        '1w': ('1wk', '1y'),
        '1m': ('1mo', '5y'),
        '1y': ('1mo', 'max')
    }
    
    i_param, r_param = interval_map.get(timeframe, ('1d', '3mo'))
    tickers = ['TQQQ', 'QLD', 'QQQ']
    data_by_ticker = {}
    timestamps = []
    
    for t in tickers:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?interval={i_param}&range={r_param}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                chart_res = res['chart']['result'][0]
                raw_ts = chart_res.get('timestamp', [])
                raw_cl = chart_res['indicators']['quote'][0].get('close', [])
                
                clean_ts = []
                clean_cl = []
                for ts, cl in zip(raw_ts, raw_cl):
                    if ts is not None and cl is not None:
                        clean_ts.append(ts)
                        clean_cl.append(round(cl, 2))
                
                data_by_ticker[t] = clean_cl
                if not timestamps or len(clean_ts) > len(timestamps):
                    timestamps = clean_ts
        except Exception as e:
            logging.error(f"Error fetching chart data for {t}: {e}")
            data_by_ticker[t] = []
            
    date_labels = []
    for ts in timestamps:
        t_struct = time.localtime(ts)
        if timeframe == '1d':
            date_labels.append(time.strftime('%m-%d', t_struct))
        elif timeframe == '1w':
            date_labels.append(time.strftime('%Y-%m-%d', t_struct))
        else:
            date_labels.append(time.strftime('%Y-%m', t_struct))

    # Downsample for Yearly (1y)
    if timeframe == '1y' and len(date_labels) > 20:
        yearly_labels = []
        yearly_data = {t: [] for t in tickers}
        last_year = None
        for idx, lbl in enumerate(date_labels):
            yr = lbl.split('-')[0]
            if yr != last_year:
                if last_year is not None:
                    yearly_labels.append(last_year)
                    for t in tickers:
                        series = data_by_ticker[t]
                        val = series[idx-1] if idx-1 < len(series) else (series[-1] if series else 0)
                        yearly_data[t].append(val)
                last_year = yr
        if last_year:
            yearly_labels.append(last_year)
            for t in tickers:
                series = data_by_ticker[t]
                val = series[-1] if series else 0
                yearly_data[t].append(val)
        
        date_labels = yearly_labels
        data_by_ticker = yearly_data

    return jsonify({
        "status": "success",
        "labels": date_labels,
        "series": data_by_ticker
    })


@infinite_bp.route('/api/fear_greed_history', methods=['GET'])
@login_required
def get_fear_greed_history():
    # Sync DB first
    fetch_fear_and_greed()

    engine = create_engine(f"sqlite:///{DB_PATH}")
    init_fear_greed_db(engine)

    query = "SELECT date, score, rating FROM fear_greed_history ORDER BY date ASC"
    try:
        with engine.connect() as conn:
            df_fg = pd.read_sql(text(query), conn)
    except Exception as e:
        logging.error(f"Error querying fear_greed_history DB: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    if df_fg.empty:
        return jsonify({"status": "error", "message": "No Fear & Greed data available"}), 404

    fg_dates = df_fg['date'].tolist()
    fg_scores = df_fg['score'].tolist()
    fg_ratings = df_fg['rating'].tolist()

    # Fetch QQQ, QLD, TQQQ daily history for 1 year matching range
    tickers = ['QQQ', 'QLD', 'TQQQ']
    ticker_series = {t: [] for t in tickers}
    ticker_prices_by_date = {t: {} for t in tickers}

    for t in tickers:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?interval=1d&range=1y"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                chart_res = res['chart']['result'][0]
                raw_ts = chart_res.get('timestamp', [])
                raw_cl = chart_res['indicators']['quote'][0].get('close', [])
                
                for ts, cl in zip(raw_ts, raw_cl):
                    if ts and cl:
                        d_str = time.strftime('%Y-%m-%d', time.localtime(ts))
                        ticker_prices_by_date[t][d_str] = round(cl, 2)
        except Exception as e:
            logging.error(f"Error fetching ticker comparison {t} for F&G: {e}")

    for t in tickers:
        p_dict = ticker_prices_by_date[t]
        last_p = 0
        for d in fg_dates:
            if d in p_dict:
                last_p = p_dict[d]
            ticker_series[t].append(last_p)

    return jsonify({
        "status": "success",
        "dates": fg_dates,
        "fg_scores": fg_scores,
        "fg_ratings": fg_ratings,
        "nasdaq_prices": ticker_series['QQQ'],
        "series": ticker_series
    })


DEFAULT_SETTINGS = {
    "public_TQQQ": {
        "mode": "public",
        "auto": True,
        "ticker": "TQQQ",
        "capital": "90000",
        "split": "40",
        "target": "12",
        "strategy": "v2.2"
    },
    "private_SOXL": {
        "mode": "private",
        "auto": False,
        "ticker": "SOXL",
        "capital": "50000",
        "split": "30",
        "target": "10",
        "strategy": "v2.2"
    }
}


@infinite_bp.route('/infinite_load_settings', methods=['GET'])
@login_required
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return jsonify(DEFAULT_SETTINGS)

    with open(SETTINGS_FILE, "r") as f:
        data = json.load(f)
    return jsonify(data)


@infinite_bp.route('/infinite_save_settings', methods=['POST'])
@login_required
def save_settings():
    data = request.json
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return jsonify({"message": "설정이 저장되었습니다."})


@infinite_bp.route('/infinite_help', methods=['GET'])
def infinite_help():
    return render_template("infinite_help.html")


@infinite_bp.route('/run_infinite_buying', methods=['POST'])
@login_required
def run_infinite_buying():
    print("run_infinite_buying")
    bat_file_path = r"C:\Users\이재혁\OneDrive\바탕 화면\무한매수\무한매수v2.2.bat"
    ExecuteHelper.run_as_admin(bat_file_path)
    return "", 204


@infinite_bp.route('/run_infinite_account', methods=['POST'])
@login_required
def run_infinite_account():
    print("run_infinite_account")
    bat_file_path = r"C:\Users\이재혁\OneDrive\바탕 화면\무한매수\계좌업데이트.bat"
    ExecuteHelper.run_as_admin(bat_file_path)
    return "", 204


@infinite_bp.route('/run_samsung_account', methods=['POST'])
@login_required
def run_samsung_account():
    print("run_samsung_account")
    bat_file_path = r"C:\Users\이재혁\OneDrive\바탕 화면\samsung_account.bat"
    ExecuteHelper.run_as_admin(bat_file_path)
    return "", 204


@infinite_bp.route('/run_meritz_account', methods=['POST'])
@login_required
def run_meritz_account():
    print("run_meritz_account")
    bat_file_path = r"C:\Users\이재혁\OneDrive\바탕 화면\meritz_account.bat"
    ExecuteHelper.run_as_admin(bat_file_path)
    return "", 204


@infinite_bp.route('/infinite_chart')
@login_required
def infinite_chart():
    chart_data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        'datasets': [
            {'label': 'Team A', 'data': [12, 19, 3, 5, 2]},
            {'label': 'Team B', 'data': [4, 12, 7, 9, 10]},
            {'label': 'Team C', 'data': [8, 6, 13, 3, 7]}
        ]
    }
    return render_template("multi_line_chart.html", chart_data=chart_data)


@infinite_bp.route('/api/ticker_history', methods=['GET'])
@login_required
def get_ticker_history():
    account = request.args.get("account")
    ticker = request.args.get("ticker")
    if not account or not ticker:
        return jsonify({"status": "error", "message": "Missing account or ticker"}), 400

    engine = create_engine(f"sqlite:///{DB_PATH}")
    query = """
    SELECT ad.date, ti.total_shares, ti.average_buy_price, ti.current_price
    FROM ticker_info ti
    JOIN account_daily ad ON ti.account_daily_id = ad.id
    WHERE ad.account_id = :account AND ti.ticker = :ticker
    ORDER BY ad.date ASC
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params={"account": account.lower(), "ticker": ticker.upper()})
        
    if df.empty:
        return jsonify({
            "ticker": ticker,
            "account": account,
            "dates": [],
            "close_prices": [],
            "avg_prices": [],
            "buy_points": []
        })

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.sort_values(by="date")

    dates = df["date"].tolist()
    close_prices = df["current_price"].astype(float).tolist()
    avg_prices = df["average_buy_price"].astype(float).tolist()

    buy_points = []
    prev_shares = 0.0
    for row in df.itertuples():
        curr_shares = float(row.total_shares)
        if curr_shares > prev_shares:
            buy_points.append({
                "x": row.date,
                "y": float(row.current_price),
                "shares_added": int(curr_shares - prev_shares),
                "total_shares": int(curr_shares),
                "avg_price": float(row.average_buy_price)
            })
        prev_shares = curr_shares

    # Load settings to get start_date
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        except:
            pass

    key = f"{account.lower()}_{ticker.upper()}"
    configured_start_date = settings.get(key, {}).get("start_date", "2026-07-11")

    return jsonify({
        "ticker": ticker,
        "account": account,
        "dates": dates,
        "close_prices": close_prices,
        "avg_prices": avg_prices,
        "buy_points": buy_points,
        "start_date": configured_start_date
    })


VR_SETTINGS_FILE = "C:\\PycharmProjects\\InfiniteProject\\vr_settings.json"
VR_HISTORY_FILE = "C:\\PycharmProjects\\InfiniteProject\\vr_history.json"


@infinite_bp.route('/vr', methods=['GET'])
@login_required
def show_vr_dashboard():
    settings = {}
    if os.path.exists(VR_SETTINGS_FILE):
        try:
            with open(VR_SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            logging.error(f"Error loading VR settings: {e}")

    history = []
    if os.path.exists(VR_HISTORY_FILE):
        try:
            with open(VR_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            logging.error(f"Error loading VR history: {e}")

    history = list(reversed(history))

    slots_data = []
    for key, slot in sorted(settings.items()):
        if not slot.get("auto") or not slot.get("ticker"):
            slot_copy = slot.copy()
            slot_copy["key"] = key
            slot_copy["active"] = False
            slots_data.append(slot_copy)
            continue

        ticker = slot["ticker"].upper()
        shares = float(slot.get("shares", 0))
        V = float(slot.get("V", 0))
        P = float(slot.get("P", 0))
        G = float(slot.get("G", 10))
        band_pct = float(slot.get("band_percent", 15))
        gradient_add = float(slot.get("gradient_add", 0))

        try:
            current_price = fetch_current_price(ticker)
        except Exception as e:
            logging.error(f"Error fetching price for {ticker}: {e}")
            current_price = 0.0

        eval_val = shares * current_price
        upper_band = V * (1 + band_pct / 100)
        lower_band = V * (1 - band_pct / 100)

        rec_action = "HOLD"
        rec_shares = 0
        rec_value = 0.0
        status_color = "green"

        if current_price > 0:
            if eval_val > upper_band:
                rec_action = "SELL"
                rec_value = eval_val - V
                rec_shares = int((eval_val - V) / current_price)
                status_color = "red"
            elif eval_val < lower_band:
                rec_action = "BUY"
                rec_value = V - eval_val
                max_pool_shares = int(P / current_price)
                wanted_shares = int((V - eval_val) / current_price)
                rec_shares = min(wanted_shares, max_pool_shares)
                status_color = "blue"

        next_V_est = V + (P / G) + gradient_add

        slot_copy = slot.copy()
        slot_copy["key"] = key
        slot_copy["active"] = True
        slot_copy["current_price"] = current_price
        slot_copy["eval_val"] = eval_val
        slot_copy["upper_band"] = upper_band
        slot_copy["lower_band"] = lower_band
        slot_copy["rec_action"] = rec_action
        slot_copy["rec_shares"] = rec_shares
        slot_copy["rec_value"] = rec_value
        slot_copy["status_color"] = status_color
        slot_copy["next_V_est"] = next_V_est
        slots_data.append(slot_copy)

    return render_template(
        'vr_main.html',
        slots=slots_data,
        history=history[:100]
    )


@infinite_bp.route('/vr/settings', methods=['GET'])
@login_required
def show_vr_settings():
    settings = {}
    if os.path.exists(VR_SETTINGS_FILE):
        try:
            with open(VR_SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            logging.error(f"Error loading VR settings: {e}")

    for idx in range(4):
        key = f"slot_{idx}"
        if key not in settings:
            settings[key] = {
                "auto": False,
                "mode": "public" if idx < 2 else "private",
                "ticker": "",
                "V": 0,
                "P": 0,
                "G": 10,
                "shares": 0,
                "average_price": 0.0,
                "band_percent": 15,
                "gradient_add": 0,
                "start_date": ""
            }

    sorted_slots = [dict(settings[f"slot_{idx}"], key=f"slot_{idx}") for idx in range(4)]
    return render_template('settings_infinite_vr.html', slots=sorted_slots)


@infinite_bp.route('/api/vr/save_settings', methods=['POST'])
@login_required
def api_save_vr_settings():
    try:
        settings = {}
        if os.path.exists(VR_SETTINGS_FILE):
            try:
                with open(VR_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except:
                pass

        for idx in range(4):
            key = f"slot_{idx}"
            settings[key] = {
                "auto": request.form.get(f"auto_{idx}") == "on",
                "mode": request.form.get(f"mode_{idx}", "public"),
                "ticker": request.form.get(f"ticker_{idx}", "").upper().strip(),
                "V": float(request.form.get(f"V_{idx}", 0) or 0),
                "P": float(request.form.get(f"P_{idx}", 0) or 0),
                "G": float(request.form.get(f"G_{idx}", 10) or 10),
                "shares": float(request.form.get(f"shares_{idx}", 0) or 0),
                "average_price": float(request.form.get(f"average_price_{idx}", 0) or 0),
                "band_percent": float(request.form.get(f"band_percent_{idx}", 15) or 15),
                "gradient_add": float(request.form.get(f"gradient_add_{idx}", 0) or 0),
                "start_date": request.form.get(f"start_date_{idx}", "").strip()
            }

        with open(VR_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        return "<script>alert('VR 설정값이 저장되었습니다.'); location.href='/vr';</script>"
    except Exception as e:
        logging.error(f"Error saving VR settings: {e}")
        return f"설정 저장 오류: {e}", 500


@infinite_bp.route('/api/vr/rebalance', methods=['POST'])
@login_required
def api_log_vr_rebalance():
    try:
        data = request.json
        slot_key = data.get("slot_key")
        action = data.get("action")
        shares_diff = float(data.get("shares_diff", 0))
        price = float(data.get("price", 0))
        add_cash = float(data.get("add_cash", 0))

        if not slot_key:
            return jsonify({"success": False, "error": "Invalid slot_key"}), 400

        if not os.path.exists(VR_SETTINGS_FILE):
            return jsonify({"success": False, "error": "Settings not found"}), 400

        with open(VR_SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)

        slot = settings.get(slot_key)
        if not slot:
            return jsonify({"success": False, "error": "Slot not found"}), 400

        ticker = slot["ticker"].upper()
        old_V = slot.get("V", 0)
        old_P = slot.get("P", 0)
        old_shares = slot.get("shares", 0)
        old_avg = slot.get("average_price", 0.0)

        cost_gain = shares_diff * price
        new_shares = old_shares
        new_avg = old_avg
        new_P = old_P

        if action == "BUY":
            new_shares = old_shares + shares_diff
            if new_shares > 0:
                new_avg = round((old_avg * old_shares + cost_gain) / new_shares, 2)
            new_P = old_P - cost_gain
        elif action == "SELL":
            new_shares = max(0.0, old_shares - shares_diff)
            new_P = old_P + cost_gain

        new_P_with_add = new_P + add_cash
        new_V = old_V + (new_P / slot["G"]) + add_cash

        slot["shares"] = new_shares
        slot["average_price"] = new_avg
        slot["P"] = new_P_with_add
        slot["V"] = new_V

        with open(VR_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        history = []
        if os.path.exists(VR_HISTORY_FILE):
            try:
                with open(VR_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                pass

        history_entry = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "slot_key": slot_key,
            "ticker": ticker,
            "action": action,
            "shares_diff": int(shares_diff),
            "price": price,
            "old_V": old_V,
            "new_V": new_V,
            "old_P": old_P,
            "new_P": new_P_with_add,
            "add_cash": add_cash,
            "new_shares": new_shares,
            "new_avg": new_avg
        }
        history.append(history_entry)

        with open(VR_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)

        return jsonify({"success": True, "new_V": new_V, "new_P": new_P_with_add})
    except Exception as e:
        logging.error(f"Error during rebalance: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@infinite_bp.route('/api/vr/chart_data', methods=['GET'])
@login_required
def api_vr_chart_data():
    try:
        slot_key = request.args.get("slot_key")
        if not slot_key:
            return jsonify({"status": "error", "message": "slot_key is required"}), 400

        if not os.path.exists(VR_SETTINGS_FILE):
            return jsonify({"status": "error", "message": "Settings file not found"}), 400

        with open(VR_SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)

        slot = settings.get(slot_key)
        if not slot:
            return jsonify({"status": "error", "message": "Slot not found"}), 400

        ticker = slot.get("ticker", "").upper()
        band_pct = float(slot.get("band_percent", 15))
        start_date = slot.get("start_date", "2026-07-11")

        history = []
        if os.path.exists(VR_HISTORY_FILE):
            try:
                with open(VR_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                pass

        slot_logs = [log for log in history if log.get("slot_key") == slot_key]

        labels = []
        v_values = []
        upper_band = []
        lower_band = []
        eval_values = []

        if not slot_logs:
            try:
                current_price = fetch_current_price(ticker)
            except:
                current_price = slot.get("average_price", 0.0)
            
            V = slot.get("V", 0.0)
            shares = slot.get("shares", 0.0)
            eval_val = shares * current_price

            labels.append(start_date)
            v_values.append(V)
            upper_band.append(V * (1 + band_pct / 100))
            lower_band.append(V * (1 - band_pct / 100))
            eval_values.append(eval_val)
        else:
            first_log = slot_logs[0]
            log_date_str = first_log["date"].split(" ")[0]
            labels.append(start_date if start_date < log_date_str else log_date_str)
            
            old_V = first_log["old_V"]
            v_values.append(old_V)
            upper_band.append(old_V * (1 + band_pct / 100))
            lower_band.append(old_V * (1 - band_pct / 100))

            diff = first_log["shares_diff"]
            act = first_log["action"]
            if act == "BUY":
                old_shares = first_log["new_shares"] - diff
            elif act == "SELL":
                old_shares = first_log["new_shares"] + diff
            else:
                old_shares = first_log["new_shares"]
            
            eval_values.append(old_shares * first_log["price"])

            for log in slot_logs:
                date_only = log["date"].split(" ")[0]
                labels.append(date_only)
                
                V_val = log["new_V"]
                v_values.append(V_val)
                upper_band.append(V_val * (1 + band_pct / 100))
                lower_band.append(V_val * (1 - band_pct / 100))
                
                eval_val = log["new_shares"] * log["price"]
                eval_values.append(eval_val)

        return jsonify({
            "status": "success",
            "ticker": ticker,
            "labels": labels,
            "v_values": v_values,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "eval_values": eval_values
        })
    except Exception as e:
        logging.error(f"Error serving VR chart data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


TQQQ_CACHE_FILE = "C:\\PycharmProjects\\InfiniteProject\\tqqq_sim_cache.json"


@infinite_bp.route('/vr/simulation', methods=['GET'])
@login_required
def show_vr_simulation():
    return render_template('vr_simulation.html')


@infinite_bp.route('/api/vr/simulation_data', methods=['GET'])
@login_required
def api_vr_simulation_data():
    try:
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        cache_data = None
        
        if os.path.exists(TQQQ_CACHE_FILE):
            try:
                with open(TQQQ_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading TQQQ cache: {e}")

        if not cache_data or cache_data.get("updated_date") != today_str:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/TQQQ?period1=1704153600&period2=2000000000&interval=1d"
            logging.info("Cache miss. Fetching daily TQQQ from Yahoo Finance Chart API...")
            try:
                import urllib.request
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode())
                
                result = res_data['chart']['result'][0]
                timestamps = result['timestamp']
                close_list = result['indicators']['quote'][0]['close']
                
                valid_points = []
                for ts, p in zip(timestamps, close_list):
                    if p is not None:
                        date_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                        valid_points.append({"date": date_str, "close": float(p)})
                        
                cache_data = {
                    "updated_date": today_str,
                    "points": valid_points
                }
                
                with open(TQQQ_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=4, ensure_ascii=False)
                    
            except Exception as e:
                logging.error(f"Failed to fetch Yahoo chart: {e}")
                if not cache_data:
                    return jsonify({"status": "error", "message": f"데이터 수집 실패 및 캐시 없음: {e}"}), 500

        points = cache_data["points"]
        if not points:
            return jsonify({"status": "error", "message": "시뮬레이션 할 데이터 포인트가 없습니다."}), 500

        initial_capital = 100000.0
        G = 10.0
        band_percent = 15.0
        rebalance_interval = 10

        initial_close = points[0]["close"]
        initial_stock_value = initial_capital * 0.5
        shares = initial_stock_value / initial_close
        pool = initial_capital * 0.5
        V = initial_stock_value

        dates = []
        close_prices = []
        v_values = []
        upper_bands = []
        lower_bands = []
        eval_values = []
        pool_values = []
        total_assets = []

        trading_day_counter = 0

        for pt in points:
            date_str = pt["date"]
            close_price = pt["close"]

            eval_val = shares * close_price
            upper_b = V * (1 + band_percent / 100)
            lower_b = V * (1 - band_percent / 100)

            dates.append(date_str)
            close_prices.append(close_price)
            v_values.append(V)
            upper_bands.append(upper_b)
            lower_bands.append(lower_b)
            eval_values.append(eval_val)
            pool_values.append(pool)
            total_assets.append(eval_val + pool)

            if trading_day_counter > 0 and trading_day_counter % rebalance_interval == 0:
                if eval_val > upper_b:
                    sell_val = eval_val - V
                    shares -= sell_val / close_price
                    pool += sell_val
                elif eval_val < lower_b:
                    buy_val = min(V - eval_val, pool)
                    shares += buy_val / close_price
                    pool -= buy_val

                eval_val = shares * close_price
                V = V + (pool / G)

            trading_day_counter += 1

        # Calculate simulated next trade threshold prices
        sim_buy_price = lower_bands[-1] / shares if shares > 0 else 0
        sim_sell_price = upper_bands[-1] / shares if shares > 0 else 0

        # Calculate exact quantities to buy/sell at threshold
        sim_buy_qty = int((V * (band_percent / 100)) / sim_buy_price) if sim_buy_price > 0 else 0
        sim_sell_qty = int((V * (band_percent / 100)) / sim_sell_price) if sim_sell_price > 0 else 0

        # Load live active slot details for Slot 0
        live_portfolio = None
        if os.path.exists(VR_SETTINGS_FILE):
            try:
                with open(VR_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                
                # Look for Slot 0 or any active TQQQ slot
                for skey, slot in settings.items():
                    if slot.get("auto") and slot.get("ticker"):
                        live_shares = float(slot.get("shares", 0))
                        live_V = float(slot.get("V", 0))
                        live_band_pct = float(slot.get("band_percent", 15))
                        
                        live_buy = (live_V * (1 - live_band_pct / 100)) / live_shares if live_shares > 0 else 0
                        live_sell = (live_V * (1 + live_band_pct / 100)) / live_shares if live_shares > 0 else 0
                        
                        live_portfolio = {
                            "ticker": slot.get("ticker"),
                            "shares": live_shares,
                            "V": live_V,
                            "P": float(slot.get("P", 0)),
                            "buy_price": live_buy,
                            "sell_price": live_sell
                        }
                        break
            except Exception as ex:
                logging.error(f"Error loading live slot config: {ex}")

        return jsonify({
            "status": "success",
            "initial_capital": initial_capital,
            "final_asset_val": total_assets[-1],
            "final_return": ((total_assets[-1] - initial_capital) / initial_capital) * 100,
            "final_shares": shares,
            "final_pool": pool,
            "final_eval": eval_values[-1],
            "sim_buy_price": sim_buy_price,
            "sim_sell_price": sim_sell_price,
            "sim_buy_qty": sim_buy_qty,
            "sim_sell_qty": sim_sell_qty,
            "live_portfolio": live_portfolio,
            "dates": dates,
            "close_prices": close_prices,
            "v_values": v_values,
            "upper_band": upper_bands,
            "lower_band": lower_bands,
            "eval_values": eval_values,
            "pool_values": pool_values,
            "total_assets": total_assets
        })
    except Exception as e:
        logging.error(f"Error generating VR simulation data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@infinite_bp.route('/add_family_asset', methods=['POST'])
@infinite_bp.route('/infinite/add_family_asset', methods=['POST'])
@login_required
def route_add_family_asset():
    account_name = request.form.get('account_name')
    asset_type = request.form.get('asset_type')
    amount = request.form.get('amount')
    if account_name and asset_type and amount:
        try:
            amount = float(amount.replace(',', ''))
            from infinite import FamilyDBHelper
            FamilyDBHelper.add_family_asset(account_name, asset_type, amount)
        except Exception as e:
            logging.error(f"Error adding family asset: {e}")
    return redirect(url_for('infinite.infinite_assets', broker='family'))

@infinite_bp.route('/delete_family_asset', methods=['POST'])
@infinite_bp.route('/infinite/delete_family_asset', methods=['POST'])
@login_required
def route_delete_family_asset():
    account_name = request.form.get('account_name')
    if account_name:
        try:
            from infinite import FamilyDBHelper
            FamilyDBHelper.delete_family_asset(account_name)
        except Exception as e:
            logging.error(f"Error deleting family asset: {e}")
    return redirect(url_for('infinite.infinite_assets', broker='family'))
