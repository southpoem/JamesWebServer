import os
import math
import sqlite3
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CACHE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simulation_cache.db")


class BacktestEngine:
    """
    주식 퀀트 전략 백테스팅 & 시뮬레이션 엔진
    - 무한매수법 (v2.2, v2.1, v1.0, Only Buying)
    - 밸류 리밸런싱 (Value Rebalancing, VR)
    - 적립식 분할매수 (DCA)
    - 벤치마크 (QQQ / SPY Buy & Hold)
    - 로컬 SQLite 시세 캐싱 지원
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
        로컬 DB 캐시를 확인하고 없는 구간은 Yahoo Finance에서 조회하여 캐싱합니다.
        반환값: DataFrame with index 'date' (YYYY-MM-DD), columns: [Open, High, Low, Close, Volume]
        """
        cls._init_db()
        ticker = ticker.upper().strip()

        # 1. DB에서 캐시 확인
        conn = sqlite3.connect(CACHE_DB_PATH)
        query = "SELECT date, open, high, low, close, volume FROM price_history WHERE ticker = ? AND date >= ? AND date <= ? ORDER BY date ASC"
        df_cached = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))
        conn.close()

        # 충분한 데이터가 캐시되어 있는지 확인 (대략 시작일과 종료일 차이의 거래일 수)
        need_fetch = False
        if df_cached.empty:
            need_fetch = True
        else:
            cached_min = df_cached['date'].min()
            cached_max = df_cached['date'].max()
            if cached_min > start_date or cached_max < (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=4)).strftime("%Y-%m-%d"):
                need_fetch = True

        if need_fetch:
            try:
                logging.info(f"Downloading {ticker} from Yahoo Finance: {start_date} ~ {end_date}")
                # 넉넉하게 1달 전부터 받아옴
                fetch_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
                fetch_end = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
                raw_df = yf.download(ticker, start=fetch_start, end=fetch_end, progress=False)

                if not raw_df.empty:
                    # MultiIndex 컬럼 평탄화
                    if isinstance(raw_df.columns, pd.MultiIndex):
                        raw_df.columns = [c[0] for c in raw_df.columns]

                    rows_to_insert = []
                    for idx, row in raw_df.iterrows():
                        date_str = idx.strftime("%Y-%m-%d")
                        o = float(row.get('Open', 0))
                        h = float(row.get('High', 0))
                        l = float(row.get('Low', 0))
                        c = float(row.get('Close', 0))
                        v = float(row.get('Volume', 0))
                        rows_to_insert.append((ticker, date_str, o, h, l, c, v))

                    conn = sqlite3.connect(CACHE_DB_PATH)
                    cur = conn.cursor()
                    cur.executemany("""
                        REPLACE INTO price_history (ticker, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, rows_to_insert)
                    conn.commit()
                    conn.close()

                    # 캐시 후 다시 조회
                    conn = sqlite3.connect(CACHE_DB_PATH)
                    df_cached = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))
                    conn.close()
            except Exception as e:
                logging.error(f"Error fetching data from Yahoo Finance for {ticker}: {e}")

        if df_cached.empty:
            return pd.DataFrame()

        df_cached.set_index('date', inplace=True)
        df_cached.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return df_cached

    @classmethod
    def calculate_quant_metrics(cls, daily_equity, initial_capital, benchmark_equity=None):
        """
        성과 지표(Total Return, CAGR, MDD, Sharpe Ratio, Win Rate 등)를 산출합니다.
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

        # 거래일 기준 연환산 (252영업일)
        total_days = len(values)
        years = max(total_days / 252.0, 0.05)
        cagr = ((final_val / initial_capital) ** (1.0 / years) - 1.0) * 100

        # MDD (최대 낙폭) 계산
        peak = values[0]
        mdd = 0.0
        for v in values:
            if v > peak:
                peak = v
            dd = ((v - peak) / peak) * 100
            if dd < mdd:
                mdd = dd

        # 변동성 및 샤프 지수
        s_values = pd.Series(values)
        daily_returns = s_values.pct_change().dropna()
        daily_vol = daily_returns.std()
        annual_vol = daily_vol * np.sqrt(252) * 100 if not np.isnan(daily_vol) else 0.0

        risk_free_rate = 0.03  # 연 3%
        rf_daily = (1 + risk_free_rate) ** (1 / 252) - 1
        excess_returns = daily_returns - rf_daily
        sharpe = (excess_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0.0
        if np.isnan(sharpe) or np.isinf(sharpe):
            sharpe = 0.0

        # 벤치마크 지표
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
                                 compounding=True, strategy_type="v2.2"):
        """
        라오어 무한매수법 v2.2 (또는 v2.1, v1) 일별 백테스트 실행
        """
        df = cls.get_price_df(ticker, start_date, end_date)
        df_bench = cls.get_price_df("QQQ", start_date, end_date)

        if df.empty:
            return {"error": f"데이터를 불러올 수 없습니다: {ticker}"}

        # 날짜 정렬 및 공통 날짜 인덱싱
        common_dates = df.index.intersection(df_bench.index if not df_bench.empty else df.index)
        if len(common_dates) < 5:
            return {"error": "분석 가능한 데이터 기간이 부족합니다."}

        df = df.loc[common_dates]
        if not df_bench.empty:
            df_bench = df_bench.loc[common_dates]

        # 벤치마크 초기 계산 (동일 자본금으로 QQQ Buy & Hold)
        bench_start_price = float(df_bench.iloc[0]['Close']) if not df_bench.empty else 1.0
        bench_shares = initial_capital / bench_start_price

        # 시뮬레이션 상태 변수
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

            # 벤치마크 가치
            bench_close = float(df_bench.loc[date_str]['Close']) if not df_bench.empty else close_p
            bench_val = bench_shares * bench_close
            benchmark_equity.append({
                "date": date_str,
                "total_value": round(bench_val, 2)
            })

            # --- 무한매수 매매 로직 ---
            cycle_ended = False

            # Case A: 보유 주식이 0인 경우 (사이클의 첫날)
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

            # Case B: 보유 주식이 있는 경우 (전략 계산 및 매도/매수 체결)
            else:
                # 회차 계산
                current_round = (average_price * total_shares) / daily_investment
                current_round = math.ceil(current_round * 100) / 100
                if current_round > cycle_max_round:
                    cycle_max_round = current_round

                # 별 퍼센트 계산
                half_split = total_splits / 2.0
                per_round = (target_rate * 100.0) / half_split
                star_percent = (target_rate * 100.0) - (per_round * current_round)
                star_rate = star_percent / 100.0

                star_point_price = round(average_price * (1 + star_rate), 2)
                quarter_sell_price = star_point_price
                full_sell_price = round(average_price * (1 + target_rate), 2)

                quarter_sell_quantity = int(round(total_shares * 0.25))
                total_sell_quantity = total_shares - quarter_sell_quantity

                discounted_buy_price = round(star_point_price - 0.01, 2)

                # --- 1) 전량 지정가 익절 매도 체결 확인 (장중 High >= 목표가) ---
                if high_p >= full_sell_price:
                    exec_price = max(open_p, full_sell_price)
                    sell_proceeds = total_shares * exec_price
                    realized_profit = sell_proceeds - total_cost
                    cash += sell_proceeds

                    duration = (datetime.strptime(date_str, "%Y-%m-%d") - datetime.strptime(cycle_start_date, "%Y-%m-%d")).days
                    return_pct = (realized_profit / cycle_start_capital) * 100.0

                    trade_markers.append({
                        "date": date_str,
                        "type": "SELL",
                        "price": round(exec_price, 2),
                        "shares": total_shares,
                        "note": f"사이클 {cycle_num} 전량 익절 (+{return_pct:.1f}%)"
                    })

                    cycle_history.append({
                        "cycle": cycle_num,
                        "start_date": cycle_start_date,
                        "end_date": date_str,
                        "duration_days": duration,
                        "trades": cycle_trades_count,
                        "max_round": round(cycle_max_round, 1),
                        "gain_pct": round(return_pct, 2),
                        "net_profit": round(realized_profit, 2),
                        "final_capital": round(cash, 2)
                    })

                    # 복리 옵션 적용
                    if compounding:
                        current_capital = cash
                    daily_investment = current_capital / float(total_splits)

                    # 사이클 리셋
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
                    # --- 2) 쿼터 매도 (LOC 매도: 당일 종가 Close >= 쿼터매도가) ---
                    if quarter_sell_quantity > 0 and close_p >= quarter_sell_price:
                        q_proceeds = quarter_sell_quantity * close_p
                        cash += q_proceeds
                        total_shares -= quarter_sell_quantity
                        total_cost -= (quarter_sell_quantity * average_price)
                        cycle_trades_count += 1
                        trade_markers.append({
                            "date": date_str,
                            "type": "SELL",
                            "price": round(close_p, 2),
                            "shares": quarter_sell_quantity,
                            "note": f"쿼터 LOC 매도 ({quarter_sell_quantity}주)"
                        })

                    # --- 3) LOC 분할 매수 체결 (종가 Close가 지정가 이하일 때 종가 Close로 체결!) ---
                    if current_round <= half_split:
                        # 전반전: 할인매수(0.5회분) + 평단매수(0.5회분)
                        disc_qty = math.floor((daily_investment / 2.0) / discounted_buy_price) if discounted_buy_price > 0 else 0
                        avg_qty = math.floor((daily_investment / 2.0) / average_price) if average_price > 0 else 0

                        bought_qty = 0
                        # 종가가 할인매수가 이하이면 할인매수 체결
                        if close_p <= discounted_buy_price and disc_qty > 0:
                            bought_qty += disc_qty
                        # 종가가 평단가 이하이면 평단매수 체결
                        if close_p <= average_price and avg_qty > 0:
                            bought_qty += avg_qty

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
                                "note": f"전반전 LOC 매수 ({bought_qty}주)"
                            })
                    else:
                        # 후반전: 1회분 전체로 할인매수만 주문
                        disc_qty = math.floor(daily_investment / discounted_buy_price) if discounted_buy_price > 0 else 0
                        if close_p <= discounted_buy_price and disc_qty > 0 and cash >= (disc_qty * close_p):
                            buy_cost = disc_qty * close_p
                            cash -= buy_cost
                            total_shares += disc_qty
                            total_cost += buy_cost
                            average_price = total_cost / total_shares if total_shares > 0 else 0
                            cycle_trades_count += 1
                            trade_markers.append({
                                "date": date_str,
                                "type": "BUY",
                                "price": round(close_p, 2),
                                "shares": disc_qty,
                                "note": f"후반전 LOC 할인매수 ({disc_qty}주)"
                            })

            # 일별 평가 총액 기록
            stock_val = total_shares * close_p
            total_val = cash + stock_val
            daily_equity.append({
                "date": date_str,
                "total_value": round(total_val, 2),
                "cash": round(cash, 2),
                "stock_value": round(stock_val, 2),
                "benchmark_value": round(bench_val, 2)
            })

        # 아직 진행 중인 마지막 사이클이 있다면 기록
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

        # 성과 지표 계산
        kpi = cls.calculate_quant_metrics(daily_equity, initial_capital, benchmark_equity)
        completed_cycles = [c for c in cycle_history if not str(c["cycle"]).endswith("(진행 중)")]
        win_rate = (len([c for c in completed_cycles if c["net_profit"] > 0]) / len(completed_cycles) * 100) if completed_cycles else 100.0
        avg_days = sum([c["duration_days"] for c in completed_cycles]) / len(completed_cycles) if completed_cycles else 0.0

        kpi["total_cycles"] = len(completed_cycles)
        kpi["win_rate"] = round(win_rate, 1)
        kpi["avg_cycle_days"] = round(avg_days, 1)

        return {
            "strategy": f"무한매수법 {strategy_type.upper()}",
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "initial_capital": initial_capital,
            "kpi": kpi,
            "daily_equity": daily_equity,
            "trade_markers": trade_markers[-50:],  # 최근 50개 마커
            "cycle_history": cycle_history[::-1]   # 최신순
        }

    @classmethod
    def simulate_vr(cls, ticker="TQQQ", start_date="2020-01-01", end_date="2024-01-01", initial_capital=50000):
        """
        밸류 리밸런싱 (Value Rebalancing - VR) 시뮬레이션
        - 2주(10거래일) 주기 밴드 풀 매수/매도 리밸런싱
        """
        df = cls.get_price_df(ticker, start_date, end_date)
        if df.empty or len(df) < 15:
            return []

        # 초기 설정: 50% 주식, 50% 현금 풀
        stock_alloc = initial_capital * 0.5
        cash_pool = initial_capital * 0.5
        shares = math.floor(stock_alloc / float(df.iloc[0]['Open']))
        cash_pool += (stock_alloc - shares * float(df.iloc[0]['Open']))

        # 목표 가치 V 설정 및 2주 주기 증액 (연 10% 목표 가정)
        V = shares * float(df.iloc[0]['Open'])
        two_week_growth = 1.0 + (0.10 / 26.0)

        daily_equity = []
        step = 0

        for date_str, row in df.iterrows():
            close_p = float(row['Close'])
            step += 1

            # 2주(10거래일)마다 리밸런싱
            if step % 10 == 0:
                V = V * two_week_growth
                cur_val = shares * close_p
                # 밴드 ±15%
                upper_band = V * 1.15
                lower_band = V * 0.85

                if cur_val > upper_band:
                    # 상단 돌파: 초과분 매도하여 풀로 입금
                    sell_amount = (cur_val - V) * 0.5
                    sell_shares = math.floor(sell_amount / close_p)
                    if sell_shares > 0:
                        shares -= sell_shares
                        cash_pool += sell_shares * close_p
                elif cur_val < lower_band:
                    # 하단 돌파: 부족분 매수하여 풀에서 출금
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
        """
        월적립식 분할매수 (Dollar-Cost Averaging - DCA) 시뮬레이션
        - 초기 50% 매수 + 매월 20영업일마다 남은 자본금 분할 적립 매수
        """
        df = cls.get_price_df(ticker, start_date, end_date)
        if df.empty or len(df) < 15:
            return []

        # 월 분할 적립
        months = max(int(len(df) / 21), 1)
        monthly_installment = initial_capital / float(months)

        cash = float(initial_capital)
        shares = 0
        daily_equity = []
        step = 0

        for date_str, row in df.iterrows():
            close_p = float(row['Close'])
            step += 1

            # 매 20거래일마다 정기 매수
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
        """
        단순 보유 (Buy & Hold) 벤치마크 시뮬레이션
        """
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
        """
        4대 전략 동시 비교 시뮬레이션
        1) 무한매수 v2.2
        2) 밸류 리밸런싱 (VR)
        3) 월적립 (DCA)
        4) QQQ 단순보유 (Buy & Hold)
        """
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

        # 공통 날짜 매칭
        dates = [d["date"] for d in eq_inf]
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

        # 전략별 퀀트 지표 산출
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
