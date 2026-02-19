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
    df["계좌색상"] = df["account_id"].apply(lambda x: "yellow" if "private" in x.lower() else "white")

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

    df = df[[
        "계좌색상", "ticker", "current_round", "total_shares",
        "평단가(수익률)", "현재가", "총투자금액", "총투자금액(목표수익율)"
    ]]
    df.columns = ["계좌색상", "티커", "회차", "개수", "평단가(수익률)", "현재가", "총매입금액", "총투자금액(목표수익율)"]

    table_rows = ""
    for _, row in df.iterrows():
        row_html = f"<tr style='color:{row['계좌색상']}'>" + "".join(
            f"<td>{row[col]}</td>" for col in [
                "티커", "회차", "개수", "평단가(수익률)", "현재가", "총매입금액", "총투자금액(목표수익율)"
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
        "target": "12"
    },
    "private_SOXL": {
        "mode": "private",
        "auto": False,
        "ticker": "SOXL",
        "capital": "50000",
        "split": "30",
        "target": "10"
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
