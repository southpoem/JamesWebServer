import traceback
from flask import Flask, render_template

app = Flask(__name__, template_folder=r'C:\PycharmProjects\JamesWebServer\templates')

@app.route('/')
def test():
    data = {
        'today_str': '2026-08-26',
        'last_update_time': '2026-08-26 12:00:00',
        'total_today': 100,
        'change_1d': 0,
        'change_7d': 0,
        'change_30d': 0,
        'account_summary': [],
        'ticker_summary': [],
        'chart_dates': [],
        'chart_datasets': [],
        'detailed_list': [],
        'family_assets': [],
        'all_accounts_list': [],
        'analysis_data': {}
    }
    return render_template('infinite_assets.html', data=data, current_broker='samsung', error=None)

with app.app_context():
    try:
        test()
        print("Render successful for samsung.")
    except Exception as e:
        traceback.print_exc()

@app.route('/analysis')
def test_analysis():
    data = {
        'today_str': '2026-08-26',
        'last_update_time': '2026-08-26 12:00:00',
        'total_today': 100,
        'change_1d': 0,
        'change_7d': 0,
        'change_30d': 0,
        'account_summary': [],
        'ticker_summary': [],
        'chart_dates': [],
        'chart_datasets': [],
        'detailed_list': [],
        'family_assets': [],
        'all_accounts_list': [],
        'analysis_data': {'country': [], 'sector': [], 'stock': []}
    }
    return render_template('infinite_assets.html', data=data, current_broker='analysis', error=None)

with app.app_context():
    try:
        test_analysis()
        print("Render successful for analysis.")
    except Exception as e:
        traceback.print_exc()

