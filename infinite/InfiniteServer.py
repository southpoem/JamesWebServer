import datetime
import json
import logging
import os
import sys

import pandas as pd
from flask import Blueprint, render_template, request, jsonify
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


@infinite_bp.route('/infinite', methods=['GET', 'POST'])
@login_required
def show_recent_ticker_data():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=6)
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
        df["총투자금액(목표수익율)"] = (
                df["total_investment"].astype(str) +
                " (" +
                df["target_profit_rate"].astype(float).astype(int).astype(str) +
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
    for _, row in df.iterrows():
        row_html = f"<tr style='color:{row['계좌색상']}'>" + "".join(
            f"<td>{row[col]}</td>" for col in [
                "시작일", "구분", "티커", "전략", "회차", "개수", "평단가(수익률)", "현재가", "총매입금액", "총투자금액(목표수익율)"
            ]
        ) + "</tr>"
        table_rows += row_html

    # 템플릿 파일 경로
    return render_template("infinite_main.html", latest_date=latest_date, table_rows=table_rows)


SETTINGS_FILE = "C:\\PycharmProjects\\InfiniteProject\\infinite_settings.json"


@infinite_bp.route('/infinite_settings', methods=['GET'])
@login_required
def infinite_settings():
    return render_template("settings_infinite.html")


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
