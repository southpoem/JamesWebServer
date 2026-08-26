import re

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'r', encoding='utf-8') as f:
    content = f.read()

route_code = '''
@infinite_bp.route('/toggle_exclude', methods=['POST'])
@login_required
def toggle_exclude():
    broker = request.form.get('broker')
    account_num = request.form.get('account_num')
    is_excluded = request.form.get('is_excluded') == 'true'
    
    conn = sqlite3.connect(r'C:\PycharmProjects\InfiniteProject\account.db')
    c = conn.cursor()
    if is_excluded:
        c.execute("INSERT OR IGNORE INTO excluded_accounts (broker, account_num) VALUES (?, ?)", (broker, account_num))
    else:
        c.execute("DELETE FROM excluded_accounts WHERE broker = ? AND account_num = ?", (broker, account_num))
    conn.commit()
    conn.close()
    
    return redirect(url_for('infinite.infinite_assets', broker=request.args.get('broker', 'samsung')))

@infinite_bp.route('/infinite', methods=['GET'])'''

content = content.replace("@infinite_bp.route('/infinite', methods=['GET'])", route_code)

with open(r'C:\PycharmProjects\JamesWebServer\infinite\InfiniteServer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Route added.")
