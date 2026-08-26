import traceback
from flask import Flask, render_template

app = Flask(__name__, template_folder=r'C:\PycharmProjects\JamesWebServer\templates')

@app.route('/')
def test():
    data = {
        'total_today': 100,
        'change_1d': 0,
        'account_summary': [],
        'ticker_summary': [],
        'detailed_list': [],
        'family_assets': [],
        'analysis_data': {}
    }
    return render_template('infinite_assets.html', data=data, current_broker='samsung')

with app.app_context():
    try:
        test()
        print("Render successful for samsung.")
    except Exception as e:
        traceback.print_exc()

@app.route('/analysis')
def test_analysis():
    data = {
        'total_today': 100,
        'change_1d': 0,
        'account_summary': [],
        'ticker_summary': [],
        'detailed_list': [],
        'family_assets': [],
        'analysis_data': {'country': [], 'sector': [], 'stock': []}
    }
    return render_template('infinite_assets.html', data=data, current_broker='analysis')

with app.app_context():
    try:
        test_analysis()
        print("Render successful for analysis.")
    except Exception as e:
        traceback.print_exc()

