import os
import math
import sqlite3
import logging
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CACHE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simulation_cache.db")


class BacktestEngine:
    """
    주식 퀀트 전략 백테스팅 & 시뮬레이션 엔진
    - 라오어 무한매수법 전체 버전 (v1.0, v2.0, v2.1, v2.2, v3.0, v4.0)
    - 지원 티커: TQQQ, QLD, QQQ, SOXL, LABU 등
    - 밸류 리밸런싱 (Value Rebalancing, VR)
    - 적립식 분할매수 (DCA)
    - 벤치마크 (QQQ Buy & Hold)
    - 로컬 SQLite 시세 캐싱 및 Yahoo Finance 직접 연동
    """

    @classmethod
    def _init_db(cls):
        conn = sqlite3.connect(CACHE_DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                ticker TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (ticker, date)
            )
        """)
        conn.commit()
        conn.close()

    @classmethod
    def get_price_df(cls, ticker, start_date, end_date):
        """
        로컬 DB 캐시를 확인하고 없는 구간은 Yahoo Finance Chart API에서 직접 조회하여 캐싱합니다.
        반환값: DataFrame with index 'date' (YYYY-MM-DD), columns: [Open, High, Low, Close, Volume]
        """
        cls._init_db()
        ticker = ticker.upper().strip()

        conn = sqlite3.connect(CACHE_DB_PATH)
        query = "SELECT date, open, high, low, close, volume FROM price_history WHERE ticker = ? AND date >= ? AND date <= ? ORDER BY date ASC"
        df_cached = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))

        cur = conn.cursor()
        cur.execute("SELECT min(date), max(date), count(*) FROM price_history WHERE ticker = ?", (ticker,))
        global_min, global_max, count = cur.fetchone()
        conn.close()

        need_fetch = False
        target_end_thresh = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=4)).strftime("%Y-%m-%d")
        if not global_min or not global_max or count == 0:
            need_fetch = True
        elif global_min > start_date or global_max < target_end_thresh:
            need_fetch = True

        if need_fetch:
            try:
                logging.info(f"Downloading {ticker} via Yahoo Chart API for {start_date} ~ {end_date}")
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=10y&interval=1d"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                res = requests.get(url, headers=headers, timeout=10)
                data = res.json()
                result = data.get('chart', {}).get('result', [])
                if result:
                    res_item = result[0]
                    timestamps = res_item.get('timestamp', [])
                    quote = res_item.get('indicators', {}).get('quote', [{}])[0]
                    rows = []
                    for i in range(len(timestamps)):
                        d_str = datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
                        o = quote.get('open', [])[i]
                        h = quote.get('high', [])[i]
                        l = quote.get('low', [])[i]
                        c = quote.get('close', [])[i]
                        v = quote.get('volume', [])[i]
                        if None not in (o, h, l, c):
                            rows.append((ticker, d_str, float(o), float(h), float(l), float(c), float(v) if v is not None else 0.0))
                    if rows:
                        conn = sqlite3.connect(CACHE_DB_PATH)
                        cur = conn.cursor()
                        cur.executemany("REPLACE INTO price_history (ticker, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
                        conn.commit()
                        conn.close()
            except Exception as e:
                logging.error(f"Error fetching data via Chart API for {ticker}: {e}")

        conn = sqlite3.connect(CACHE_DB_PATH)
        df_cached = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))
        conn.close()

        if df_cached.empty:
            return pd.DataFrame()

        df_cached.set_index('date', inplace=True)
        df_cached.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return df_cached

    @classmethod
    def calculate_quant_metrics(cls, daily_equity, initial_capital, benchmark_equity=None):
        """
        성과 지표(Total Return, CAGR, MDD, Sharpe Ratio, Volatility 등) 산출
        """
        if not daily_equity or len(daily_equity) < 2:
            return {
                "final_balance": initial_capital,
                "total_return": 0.0,
                "cagr": 0.0,
                "mdd": 0.0,
                "sharpe": 0.0,
                "volatility": 0.0,
                "benchmark_return": 0.0,
                "benchmark_mdd": 0.0
            }

        values = [d["total_value"] for d in daily_equity]
        final_val = values[-1]
        total_ret = ((final_val - initial_capital) / initial_capital) * 100

        total_days = len(values)
        years = max(total_days / 252.0, 0.05)
        cagr = ((final_val / initial_capital) ** (1.0 / years) - 1.0) * 100

        peak = values[0]
        mdd = 0.0
        for v in values:
            if v > peak:
                peak = v
            dd = ((v - peak) / peak) * 100
            if dd < mdd:
                mdd = dd

        s_values = pd.Series(values)
        daily_returns = s_values.pct_change().dropna()
        daily_vol = daily_returns.std()
        annual_vol = daily_vol * np.sqrt(252) * 100 if not np.isnan(daily_vol) else 0.0

        risk_free_rate = 0.03
        rf_daily = (1 + risk_free_rate) ** (1 / 252) - 1
        excess_returns = daily_returns - rf_daily
        sharpe = (excess_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0.0
        if np.isnan(sharpe) or np.isinf(sharpe):
            sharpe = 0.0

        bench_ret = 0.0
        bench_mdd = 0.0
        if benchmark_equity and len(benchmark_equity) == len(daily_equity):
            b_vals = [b["total_value"] for b in benchmark_equity]
            bench_ret = ((b_vals[-1] - b_vals[0]) / b_vals[0]) * 100
            b_peak = b_vals[0]
            for b in b_vals:
                if b > b_peak:
                    b_peak = b
                b_dd = ((b - b_peak) / b_peak) * 100
                if b_dd < bench_mdd:
                    bench_mdd = b_dd

        return {
            "final_balance": float(round(final_val, 2)),
            "total_return": float(round(total_ret, 2)),
            "cagr": float(round(cagr, 2)),
            "mdd": float(round(mdd, 2)),
            "sharpe": float(round(float(sharpe), 2)),
            "volatility": float(round(float(annual_vol), 2)),
            "benchmark_return": float(round(bench_ret, 2)),
            "benchmark_mdd": float(round(bench_mdd, 2))
        }

    @classmethod
    def simulate_infinite_buying(cls, ticker="TQQQ", start_date="2020-01-01", end_date="2024-01-01",
                                 initial_capital=50000, total_splits=40, target_profit_rate=12.0,
                                 compounding=True, strategy_type="v2.2", sell_ratio=0.5):
        """
        라오어 무한매수법 버전별 정밀 백테스트
        - 지원 버전: v1.0, v2.0, v2.1, v2.2, v3.0, v4.0
        """
        st = str(strategy_type).lower().strip()
        if "v1" in st:
            ver = "v1.0"
        elif "v2.0" in st or "v20" in st:
            ver = "v2.0"
        elif "v2.1" in st or "v21" in st:
            ver = "v2.1"
        elif "v3" in st:
            ver = "v3.0"
            if total_splits == 40:
                total_splits = 20  # v3.0의 표준 규칙은 20분할
        elif "v4" in st:
            ver = "v4.0"
        else:
            ver = "v2.2"

        df = cls.get_price_df(ticker, start_date, end_date)
        df_bench = cls.get_price_df("QQQ", start_date, end_date)
        df_qld = cls.get_price_df("QLD", start_date, end_date)

        if df.empty:
            return {"error": f"데이터를 불러올 수 없습니다: {ticker}"}

        common_dates = df.index.intersection(df_bench.index if not df_bench.empty else df.index)
        if len(common_dates) < 5:
            return {"error": "분석 가능한 데이터 기간이 부족합니다."}

        df = df.loc[common_dates]
        if not df_bench.empty:
            df_bench = df_bench.loc[common_dates]
        if not df_qld.empty:
            df_qld = df_qld.loc[df_qld.index.intersection(common_dates)]

        bench_start_price = float(df_bench.iloc[0]['Close']) if not df_bench.empty else 1.0
        bench_shares = initial_capital / bench_start_price

        qld_start_price = float(df_qld.iloc[0]['Close']) if not df_qld.empty else 1.0
        qld_shares = initial_capital / qld_start_price

        current_capital = float(initial_capital)
        cash = float(current_capital)
        total_shares = 0
        total_cost = 0.0
        average_price = 0.0
        current_round = 0.0

        daily_investment = current_capital / float(total_splits)
        target_rate = float(target_profit_rate) / 100.0

        daily_equity = []
        benchmark_equity = []
        trade_markers = []
        cycle_history = []

        cycle_num = 1
        cycle_start_date = common_dates[0]
        cycle_start_capital = current_capital
        cycle_trades_count = 0
        cycle_max_round = 0.0

        for date_str in common_dates:
            row = df.loc[date_str]
            open_p = float(row['Open'])
            high_p = float(row['High'])
            low_p = float(row['Low'])
            close_p = float(row['Close'])

            bench_close = float(df_bench.loc[date_str]['Close']) if not df_bench.empty and date_str in df_bench.index else close_p
            bench_val = bench_shares * bench_close
            benchmark_equity.append({
                "date": date_str,
                "total_value": round(bench_val, 2)
            })

            qld_close = float(df_qld.loc[date_str]['Close']) if not df_qld.empty and date_str in df_qld.index else close_p
            qld_val = qld_shares * qld_close

            cycle_ended = False

            # Case A: 사이클 첫날 (보유 주식 0)
            if total_shares == 0:
                buy_shares = math.floor(daily_investment / close_p)
                if buy_shares > 0 and cash >= buy_shares * close_p:
                    cost = buy_shares * close_p
                    cash -= cost
                    total_shares += buy_shares
                    total_cost += cost
                    average_price = close_p
                    current_round = 1.0
                    cycle_trades_count += 1
                    trade_markers.append({
                        "date": date_str,
                        "type": "BUY",
                        "price": round(close_p, 2),
                        "shares": buy_shares,
                        "note": f"사이클 {cycle_num} 시작 (1회차 LOC 종가 매수)"
                    })

            # Case B: 주식을 보유 중인 경우
            else:
                # 회차 T 계산
                if ver in ["v1.0", "v4.0"]:
                    current_round += 1.0
                else:
                    current_round = (average_price * total_shares) / daily_investment
                    current_round = math.ceil(current_round * 100) / 100

                if current_round > cycle_max_round:
                    cycle_max_round = current_round

                half_split = total_splits / 2.0
                full_sell_price = round(average_price * (1 + target_rate), 2)

                # 버전별 매도 / 손절 조건 산출
                sold_shares = 0
                sell_proceeds = 0.0

                # --- 1) 매도 체결 판정 ---
                if ver == "v1.0":
                    # v1.0: 100% 목표가 지정가 매도
                    if high_p >= full_sell_price:
                        exec_p = max(open_p, full_sell_price)
                        proceeds = total_shares * exec_p
                        cash += proceeds
                        sold_shares += total_shares
                        sell_proceeds += proceeds
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(exec_p, 2),
                            "shares": total_shares,
                            "note": f"v1.0 목표가 전량 매도 ({total_shares}주)"
                        })

                elif ver == "v2.0":
                    # v2.0: 100% 목표가 지정가 매도 + 쿼터 손절
                    if high_p >= full_sell_price:
                        exec_p = max(open_p, full_sell_price)
                        proceeds = total_shares * exec_p
                        cash += proceeds
                        sold_shares += total_shares
                        sell_proceeds += proceeds
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(exec_p, 2),
                            "shares": total_shares,
                            "note": f"v2.0 목표가 전량 매도 ({total_shares}주)"
                        })
                    elif current_round >= total_splits and close_p < average_price * 0.90:
                        # 원금 소진 및 -10% 하락 시 25% 쿼터 손절
                        stop_qty = max(int(total_shares * 0.25), 1)
                        proceeds = stop_qty * close_p
                        cash += proceeds
                        sold_shares += stop_qty
                        sell_proceeds += proceeds
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(close_p, 2),
                            "shares": stop_qty,
                            "note": f"v2.0 쿼터 손절 ({stop_qty}주)"
                        })

                elif ver == "v2.1":
                    # v2.1: 전반전 2단 매도, 후반전 3단 매도
                    if current_round <= half_split:
                        # 전반: 50% 지정가 매도 + 50% LOC 매도
                        q_limit = math.ceil(total_shares * 0.5)
                        q_loc = total_shares - q_limit
                        if high_p >= full_sell_price and q_limit > 0:
                            exec_p = max(open_p, full_sell_price)
                            proceeds = q_limit * exec_p
                            cash += proceeds
                            sold_shares += q_limit
                            sell_proceeds += proceeds
                        if close_p >= full_sell_price and q_loc > 0:
                            proceeds = q_loc * close_p
                            cash += proceeds
                            sold_shares += q_loc
                            sell_proceeds += proceeds
                    else:
                        # 후반: 50% 지정가 + 25% 중간LOC + 25% 본전LOC
                        q_limit = math.ceil(total_shares * 0.5)
                        q_mid = math.floor(total_shares * 0.25)
                        q_break = total_shares - q_limit - q_mid
                        mid_price = round(average_price * (1 + target_rate * 0.5), 2)

                        if high_p >= full_sell_price and q_limit > 0:
                            exec_p = max(open_p, full_sell_price)
                            proceeds = q_limit * exec_p
                            cash += proceeds
                            sold_shares += q_limit
                            sell_proceeds += proceeds
                        if close_p >= mid_price and q_mid > 0:
                            proceeds = q_mid * close_p
                            cash += proceeds
                            sold_shares += q_mid
                            sell_proceeds += proceeds
                        if close_p >= average_price and q_break > 0:
                            proceeds = q_break * close_p
                            cash += proceeds
                            sold_shares += q_break
                            sell_proceeds += proceeds

                    if sold_shares > 0:
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(close_p, 2),
                            "shares": sold_shares,
                            "note": f"v2.1 분할 매도 ({sold_shares}주)"
                        })

                elif ver in ["v2.2", "v3.0"]:
                    # v2.2 & v3.0: 별퍼센트(☆%) 및 별점 LOC 매도 + 목표가 지정가 매도
                    div_t = half_split
                    per_round = (target_rate * 100.0) / div_t
                    star_percent = (target_rate * 100.0) - (per_round * current_round)
                    star_rate = star_percent / 100.0
                    star_point_price = round(average_price * (1 + star_rate), 2)
                    discounted_buy_price = round(star_point_price - 0.01, 2)

                    ratio = float(sell_ratio) if ver == "v2.2" else 0.25
                    loc_sell_qty = int(round(total_shares * ratio))
                    limit_sell_qty = total_shares - loc_sell_qty

                    # 지정가 매도
                    if high_p >= full_sell_price and limit_sell_qty > 0:
                        exec_p = max(open_p, full_sell_price)
                        proceeds = limit_sell_qty * exec_p
                        cash += proceeds
                        sold_shares += limit_sell_qty
                        sell_proceeds += proceeds
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(exec_p, 2),
                            "shares": limit_sell_qty,
                            "note": f"{ver} 지정가 매도 ({limit_sell_qty}주)"
                        })
                    # LOC 매도
                    if close_p >= star_point_price and loc_sell_qty > 0:
                        proceeds = loc_sell_qty * close_p
                        cash += proceeds
                        sold_shares += loc_sell_qty
                        sell_proceeds += proceeds
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(close_p, 2),
                            "shares": loc_sell_qty,
                            "note": f"{ver} 별점 LOC 매도 ({loc_sell_qty}주)"
                        })

                elif ver == "v4.0":
                    # v4.0: 목표가 지정가 매도 + 리버스 모드(Reverse Mode)
                    if high_p >= full_sell_price:
                        exec_p = max(open_p, full_sell_price)
                        proceeds = total_shares * exec_p
                        cash += proceeds
                        sold_shares += total_shares
                        sell_proceeds += proceeds
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(exec_p, 2),
                            "shares": total_shares,
                            "note": f"v4.0 목표가 전량 매도 ({total_shares}주)"
                        })
                    elif current_round >= total_splits and cash < daily_investment:
                        # 리버스 모드: 25% 쿼터 매도로 현금 확보 후 회차 리셋(30회차)
                        rev_qty = max(int(total_shares * 0.25), 1)
                        proceeds = rev_qty * close_p
                        cash += proceeds
                        sold_shares += rev_qty
                        sell_proceeds += proceeds
                        current_round = total_splits * 0.75
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(close_p, 2),
                            "shares": rev_qty,
                            "note": f"v4.0 리버스 모드 쿼터 매도 ({rev_qty}주)"
                        })

                # 매도 정산 및 사이클 완주 판정
                if sold_shares > 0:
                    cost_of_sold = sold_shares * average_price
                    total_cost -= cost_of_sold
                    total_shares -= sold_shares

                    if total_shares == 0:
                        profit = cash - cycle_start_capital
                        duration = (datetime.strptime(date_str, "%Y-%m-%d") - datetime.strptime(cycle_start_date, "%Y-%m-%d")).days
                        return_pct = (profit / cycle_start_capital) * 100.0

                        cycle_history.append({
                            "cycle": cycle_num,
                            "start_date": cycle_start_date,
                            "end_date": date_str,
                            "duration_days": duration,
                            "trades": cycle_trades_count,
                            "max_round": round(cycle_max_round, 1),
                            "gain_pct": round(return_pct, 2),
                            "net_profit": round(profit, 2),
                            "final_capital": round(cash, 2)
                        })

                        if compounding:
                            current_capital = cash
                        daily_investment = current_capital / float(total_splits)

                        total_shares = 0
                        total_cost = 0.0
                        average_price = 0.0
                        current_round = 0.0
                        cycle_ended = True
                        cycle_num += 1
                        cycle_start_date = date_str
                        cycle_start_capital = current_capital
                        cycle_trades_count = 0
                        cycle_max_round = 0.0
                    else:
                        average_price = total_cost / total_shares if total_shares > 0 else 0

                # --- 2) LOC 매수 체결 판정 (주식이 남아있고 사이클 지속 중) ---
                if not cycle_ended and total_shares > 0:
                    bought_qty = 0

                    if ver == "v1.0":
                        # v1.0: 매일 1회분 단순 종가 매수
                        qty = math.floor(daily_investment / close_p)
                        if qty > 0 and cash >= qty * close_p:
                            bought_qty = qty

                    elif ver in ["v2.0", "v2.1"]:
                        if current_round <= half_split:
                            avg_qty = math.floor((daily_investment / 2.0) / average_price) if average_price > 0 else 0
                            big_qty = math.floor((daily_investment / 2.0) / (average_price * 1.10)) if average_price > 0 else 0
                            if close_p <= average_price and avg_qty > 0:
                                bought_qty += avg_qty
                            if close_p <= average_price * 1.10 and big_qty > 0:
                                bought_qty += big_qty
                        else:
                            avg_qty = math.floor(daily_investment / average_price) if average_price > 0 else 0
                            if close_p <= average_price and avg_qty > 0:
                                bought_qty += avg_qty

                    elif ver in ["v2.2", "v3.0"]:
                        if current_round <= half_split:
                            disc_qty = math.floor((daily_investment / 2.0) / discounted_buy_price) if discounted_buy_price > 0 else 0
                            avg_qty = math.floor((daily_investment / 2.0) / average_price) if average_price > 0 else 0
                            if close_p <= discounted_buy_price and disc_qty > 0:
                                bought_qty += disc_qty
                            if close_p <= average_price and avg_qty > 0:
                                bought_qty += avg_qty
                        else:
                            disc_qty = math.floor(daily_investment / discounted_buy_price) if discounted_buy_price > 0 else 0
                            if close_p <= discounted_buy_price and disc_qty > 0:
                                bought_qty += disc_qty

                    elif ver == "v4.0":
                        inv = min(daily_investment, cash)
                        if current_round <= half_split:
                            q1 = math.floor((inv / 2.0) / (average_price * 1.10)) if average_price > 0 else 0
                            q2 = math.floor((inv / 2.0) / average_price) if average_price > 0 else 0
                            if close_p <= average_price * 1.10:
                                bought_qty += q1
                            if close_p <= average_price:
                                bought_qty += q2
                        else:
                            q = math.floor(inv / average_price) if average_price > 0 else 0
                            if close_p <= average_price:
                                bought_qty += q

                    if bought_qty > 0 and cash >= (bought_qty * close_p):
                        buy_cost = bought_qty * close_p
                        cash -= buy_cost
                        total_shares += bought_qty
                        total_cost += buy_cost
                        average_price = total_cost / total_shares if total_shares > 0 else 0
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "BUY",
                            "price": round(close_p, 2),
                            "shares": bought_qty,
                            "note": f"{ver} LOC 매수 ({bought_qty}주)"
                        })

            stock_val = total_shares * close_p
            total_val = cash + stock_val
            daily_equity.append({
                "date": date_str,
                "total_value": round(total_val, 2),
                "cash": round(cash, 2),
                "stock_value": round(stock_val, 2),
                "benchmark_value": round(bench_val, 2),
                "qld_value": round(qld_val, 2)
            })

        if total_shares > 0:
            unrealized_profit = (total_shares * float(df.iloc[-1]['Close'])) - total_cost
            duration = (datetime.strptime(common_dates[-1], "%Y-%m-%d") - datetime.strptime(cycle_start_date, "%Y-%m-%d")).days
            cycle_history.append({
                "cycle": f"{cycle_num} (진행 중)",
                "start_date": cycle_start_date,
                "end_date": common_dates[-1],
                "duration_days": duration,
                "trades": cycle_trades_count,
                "max_round": round(cycle_max_round, 1),
                "gain_pct": round((unrealized_profit / cycle_start_capital) * 100.0, 2),
                "net_profit": round(unrealized_profit, 2),
                "final_capital": round(cash + (total_shares * float(df.iloc[-1]['Close'])), 2)
            })

        kpi = cls.calculate_quant_metrics(daily_equity, initial_capital, benchmark_equity)
        completed_cycles = [c for c in cycle_history if not str(c["cycle"]).endswith("(진행 중)")]
        win_rate = (len([c for c in completed_cycles if c["net_profit"] > 0]) / len(completed_cycles) * 100) if completed_cycles else 100.0
        avg_days = sum([c["duration_days"] for c in completed_cycles]) / len(completed_cycles) if completed_cycles else 0.0

        # QLD 단순보유 벤치마크 지표 산출
        qld_vals = [d["qld_value"] for d in daily_equity]
        qld_ret = round(((qld_vals[-1] - initial_capital) / initial_capital) * 100, 2) if qld_vals else 0.0
        qld_peak = qld_vals[0] if qld_vals else initial_capital
        qld_mdd = 0.0
        for qv in qld_vals:
            if qv > qld_peak:
                qld_peak = qv
            q_dd = ((qv - qld_peak) / qld_peak) * 100
            if q_dd < qld_mdd:
                qld_mdd = q_dd

        kpi["qld_return"] = qld_ret
        kpi["qld_mdd"] = round(qld_mdd, 2)
        kpi["total_cycles"] = len(completed_cycles)
        kpi["win_rate"] = round(win_rate, 1)
        kpi["avg_cycle_days"] = round(avg_days, 1)

        return {
            "strategy": f"무한매수법 {ver.upper()}",
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "initial_capital": initial_capital,
            "kpi": kpi,
            "daily_equity": daily_equity,
            "trade_markers": trade_markers[-50:],
            "cycle_history": cycle_history[::-1]
        }

    @classmethod
    def compare_all_versions(cls, ticker="TQQQ", start_date="2020-01-01", end_date="2024-01-01",
                             initial_capital=50000, target_profit_rate=12.0, compounding=True):
        """
        단일 종목에 대해 무한매수법 전체 버전 (v1.0 ~ v4.0)을 동시 비교
        """
        versions = [
            ("v1.0", "무한매수법 v1.0 (정액/지정가)", "#94a3b8"),
            ("v2.0", "무한매수법 v2.0 (전후반/큰수/쿼터손절)", "#f59e0b"),
            ("v2.1", "무한매수법 v2.1 (분할 매도/LOC)", "#10b981"),
            ("v2.2", "무한매수법 v2.2 (별퍼센트 공식/표준)", "#38bdf8"),
            ("v3.0", "무한매수법 v3.0 (20분할 고속 회전)", "#a855f7"),
            ("v4.0", "무한매수법 v4.0 (소진시 리버스모드)", "#ec4899")
        ]

        results = {}
        for ver, label, color in versions:
            res = cls.simulate_infinite_buying(
                ticker=ticker, start_date=start_date, end_date=end_date,
                initial_capital=initial_capital, target_profit_rate=target_profit_rate,
                compounding=compounding, strategy_type=ver
            )
            if "error" not in res:
                results[ver] = (res, label, color)

        if not results:
            return {"error": f"비교 데이터를 생성할 수 없습니다: {ticker}"}

        first_ver = list(results.keys())[0]
        base_dates = [d["date"] for d in results[first_ver][0]["daily_equity"]]

        comparison_chart = []
        for i, dt in enumerate(base_dates):
            point = {"date": dt}
            for ver in results:
                eq = results[ver][0]["daily_equity"]
                val = eq[i]["total_value"] if i < len(eq) else eq[-1]["total_value"]
                point[ver] = val
            comparison_chart.append(point)

        matrix = []
        for ver, (res, label, color) in results.items():
            kpi = res["kpi"]
            matrix.append({
                "strategy": label,
                "version": ver,
                "color": color,
                "total_return": kpi["total_return"],
                "cagr": kpi["cagr"],
                "mdd": kpi["mdd"],
                "sharpe": kpi["sharpe"],
                "volatility": kpi["volatility"],
                "final_balance": kpi["final_balance"],
                "net_profit": round(kpi["final_balance"] - initial_capital, 2),
                "total_cycles": kpi["total_cycles"],
                "win_rate": kpi["win_rate"]
            })

        matrix.sort(key=lambda x: x["cagr"], reverse=True)

        return {
            "mode": "version_comparison",
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "initial_capital": initial_capital,
            "comparison_chart": comparison_chart,
            "matrix": matrix
        }

    @classmethod
    def compare_all_tickers(cls, strategy_type="v2.2", start_date="2020-01-01", end_date="2024-01-01",
                            initial_capital=50000, target_profit_rate=12.0, compounding=True):
        """
        단일 전략 버전에 대해 5대 주요 종목 (TQQQ, QLD, QQQ, SOXL, LABU)을 동시 비교
        """
        tickers = [
            ("TQQQ", "TQQQ (나스닥 3X)", "#38bdf8"),
            ("QLD", "QLD (나스닥 2X)", "#34d399"),
            ("QQQ", "QQQ (나스닥 1X)", "#94a3b8"),
            ("SOXL", "SOXL (반도체 3X)", "#fbbf24"),
            ("LABU", "LABU (바이오 3X)", "#f43f5e")
        ]

        results = {}
        for t, label, color in tickers:
            res = cls.simulate_infinite_buying(
                ticker=t, start_date=start_date, end_date=end_date,
                initial_capital=initial_capital, target_profit_rate=target_profit_rate,
                compounding=compounding, strategy_type=strategy_type
            )
            if "error" not in res:
                results[t] = (res, label, color)

        if not results:
            return {"error": f"비교 데이터를 생성할 수 없습니다: {strategy_type}"}

        # 공통 날짜
        all_date_sets = [set(d["date"] for d in results[t][0]["daily_equity"]) for t in results]
        common = sorted(list(set.intersection(*all_date_sets)))

        comparison_chart = []
        for dt in common:
            point = {"date": dt}
            for t in results:
                eq_dict = {d["date"]: d["total_value"] for d in results[t][0]["daily_equity"]}
                point[t] = eq_dict.get(dt, initial_capital)
            comparison_chart.append(point)

        matrix = []
        for t, (res, label, color) in results.items():
            kpi = res["kpi"]
            matrix.append({
                "ticker": t,
                "strategy": f"{t} ({strategy_type.upper()})",
                "label": label,
                "color": color,
                "total_return": kpi["total_return"],
                "cagr": kpi["cagr"],
                "mdd": kpi["mdd"],
                "sharpe": kpi["sharpe"],
                "volatility": kpi["volatility"],
                "final_balance": kpi["final_balance"],
                "net_profit": round(kpi["final_balance"] - initial_capital, 2),
                "total_cycles": kpi["total_cycles"],
                "win_rate": kpi["win_rate"]
            })

        matrix.sort(key=lambda x: x["cagr"], reverse=True)

        return {
            "mode": "ticker_comparison",
            "strategy": strategy_type.upper(),
            "period": f"{start_date} ~ {end_date}",
            "initial_capital": initial_capital,
            "comparison_chart": comparison_chart,
            "matrix": matrix
        }

    @classmethod
    def simulate_vr(cls, ticker="TQQQ", start_date="2020-01-01", end_date="2024-01-01", initial_capital=50000):
        """밸류 리밸런싱 (Value Rebalancing - VR) 시뮬레이션"""
        df = cls.get_price_df(ticker, start_date, end_date)
        if df.empty or len(df) < 15:
            return []

        stock_alloc = initial_capital * 0.5
        cash_pool = initial_capital * 0.5
        shares = math.floor(stock_alloc / float(df.iloc[0]['Open']))
        cash_pool += (stock_alloc - shares * float(df.iloc[0]['Open']))

        V = shares * float(df.iloc[0]['Open'])
        two_week_growth = 1.0 + (0.10 / 26.0)

        daily_equity = []
        step = 0

        for date_str, row in df.iterrows():
            close_p = float(row['Close'])
            step += 1

            if step % 10 == 0:
                V = V * two_week_growth
                cur_val = shares * close_p
                upper_band = V * 1.15
                lower_band = V * 0.85

                if cur_val > upper_band:
                    sell_amount = (cur_val - V) * 0.5
                    sell_shares = math.floor(sell_amount / close_p)
                    if sell_shares > 0:
                        shares -= sell_shares
                        cash_pool += sell_shares * close_p
                elif cur_val < lower_band:
                    buy_amount = (V - cur_val) * 0.5
                    buy_shares = math.floor(buy_amount / close_p)
                    cost = buy_shares * close_p
                    if cash_pool >= cost and buy_shares > 0:
                        cash_pool -= cost
                        shares += buy_shares

            total_val = cash_pool + (shares * close_p)
            daily_equity.append({
                "date": date_str,
                "total_value": round(total_val, 2)
            })

        return daily_equity

    @classmethod
    def simulate_dca(cls, ticker="TQQQ", start_date="2020-01-01", end_date="2024-01-01", initial_capital=50000):
        """정기 적립식 분할매수 (DCA)"""
        df = cls.get_price_df(ticker, start_date, end_date)
        if df.empty or len(df) < 15:
            return []

        months = max(int(len(df) / 21), 1)
        monthly_installment = initial_capital / float(months)

        cash = float(initial_capital)
        shares = 0
        daily_equity = []
        step = 0

        for date_str, row in df.iterrows():
            close_p = float(row['Close'])
            step += 1

            if step == 1 or step % 20 == 0:
                inv = min(monthly_installment, cash)
                buy_shares = math.floor(inv / close_p)
                if buy_shares > 0 and cash >= buy_shares * close_p:
                    cash -= buy_shares * close_p
                    shares += buy_shares

            total_val = cash + (shares * close_p)
            daily_equity.append({
                "date": date_str,
                "total_value": round(total_val, 2)
            })

        return daily_equity

    @classmethod
    def simulate_buy_and_hold(cls, ticker="QQQ", start_date="2020-01-01", end_date="2024-01-01", initial_capital=50000):
        """단순 보유 (Buy & Hold)"""
        df = cls.get_price_df(ticker, start_date, end_date)
        if df.empty:
            return []

        start_p = float(df.iloc[0]['Open'])
        shares = initial_capital / start_p

        daily_equity = []
        for date_str, row in df.iterrows():
            close_p = float(row['Close'])
            daily_equity.append({
                "date": date_str,
                "total_value": round(shares * close_p, 2)
            })

        return daily_equity

    @classmethod
    def run_comparison(cls, ticker="TQQQ", start_date="2020-01-01", end_date="2024-01-01", initial_capital=50000):
        """다중 전략 4자 비교 (무한매수 v2.2 vs VR vs DCA vs QQQ)"""
        res_infinite = cls.simulate_infinite_buying(
            ticker=ticker, start_date=start_date, end_date=end_date,
            initial_capital=initial_capital, total_splits=40, target_profit_rate=12.0, compounding=True
        )

        eq_vr = cls.simulate_vr(ticker=ticker, start_date=start_date, end_date=end_date, initial_capital=initial_capital)
        eq_dca = cls.simulate_dca(ticker=ticker, start_date=start_date, end_date=end_date, initial_capital=initial_capital)
        eq_qqq = cls.simulate_buy_and_hold(ticker="QQQ", start_date=start_date, end_date=end_date, initial_capital=initial_capital)

        if "error" in res_infinite:
            return res_infinite

        eq_inf = res_infinite["daily_equity"]

        vr_dict = {d["date"]: d["total_value"] for d in eq_vr}
        dca_dict = {d["date"]: d["total_value"] for d in eq_dca}
        qqq_dict = {d["date"]: d["total_value"] for d in eq_qqq}

        comparison_chart = []
        for d in eq_inf:
            dt = d["date"]
            comparison_chart.append({
                "date": dt,
                "infinite": d["total_value"],
                "vr": vr_dict.get(dt, d["total_value"]),
                "dca": dca_dict.get(dt, d["total_value"]),
                "qqq": qqq_dict.get(dt, d["total_value"])
            })

        metrics_inf = res_infinite["kpi"]
        metrics_vr = cls.calculate_quant_metrics(eq_vr, initial_capital)
        metrics_dca = cls.calculate_quant_metrics(eq_dca, initial_capital)
        metrics_qqq = cls.calculate_quant_metrics(eq_qqq, initial_capital)

        matrix = [
            {
                "strategy": "무한매수법 v2.2",
                "color": "#38bdf8",
                "total_return": metrics_inf["total_return"],
                "cagr": metrics_inf["cagr"],
                "mdd": metrics_inf["mdd"],
                "sharpe": metrics_inf["sharpe"],
                "volatility": metrics_inf["volatility"],
                "final_balance": metrics_inf["final_balance"],
                "net_profit": round(metrics_inf["final_balance"] - initial_capital, 2)
            },
            {
                "strategy": "밸류 리밸런싱 (VR)",
                "color": "#c084fc",
                "total_return": metrics_vr["total_return"],
                "cagr": metrics_vr["cagr"],
                "mdd": metrics_vr["mdd"],
                "sharpe": metrics_vr["sharpe"],
                "volatility": metrics_vr["volatility"],
                "final_balance": metrics_vr["final_balance"],
                "net_profit": round(metrics_vr["final_balance"] - initial_capital, 2)
            },
            {
                "strategy": "정기 적립식 (DCA)",
                "color": "#fbbf24",
                "total_return": metrics_dca["total_return"],
                "cagr": metrics_dca["cagr"],
                "mdd": metrics_dca["mdd"],
                "sharpe": metrics_dca["sharpe"],
                "volatility": metrics_dca["volatility"],
                "final_balance": metrics_dca["final_balance"],
                "net_profit": round(metrics_dca["final_balance"] - initial_capital, 2)
            },
            {
                "strategy": "QQQ 단순 보유 (Buy & Hold)",
                "color": "#94a3b8",
                "total_return": metrics_qqq["total_return"],
                "cagr": metrics_qqq["cagr"],
                "mdd": metrics_qqq["mdd"],
                "sharpe": metrics_qqq["sharpe"],
                "volatility": metrics_qqq["volatility"],
                "final_balance": metrics_qqq["final_balance"],
                "net_profit": round(metrics_qqq["final_balance"] - initial_capital, 2)
            }
        ]

        return {
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "initial_capital": initial_capital,
            "comparison_chart": comparison_chart,
            "matrix": matrix
        }
