import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''            <div style="margin-top: 2rem; background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 1.5rem;">
                <h3 style="margin-top: 0; color: #fff; font-size: 1.1rem; margin-bottom: 1rem;">⚙️ 계좌 합산 관리</h3>
                <p style="font-size: 0.85rem; color: #888; margin-bottom: 1rem;">체크를 해제하면 해당 계좌가 총 자산 합산 및 차트 계산에서 완전히 제외됩니다.</p>
                
                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.8rem;">
                    {% for acc in data.all_accounts_list|sort(attribute='broker_clean') %}
                    <li style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); padding: 0.8rem; border-radius: 8px;">
                        <div>
                            <div style="font-size: 0.95rem; color: #ddd;">{{ acc.broker_clean }} {{ acc.account_type|replace('(', '')|replace(')', '') }}</div>
                            <div style="font-size: 0.8rem; color: #888;">{{ acc.masked_num }}</div>
                        </div>
                        <form action="{{ url_for('infinite.toggle_exclude', broker=current_broker) }}" method="POST" style="margin: 0;">
                            <input type="hidden" name="broker" value="{{ acc.broker }}">
                            <input type="hidden" name="account_num" value="{{ acc.account_num }}">
                            <input type="hidden" name="is_excluded" value="{% if acc.is_excluded %}false{% else %}true{% endif %}">
                            <label class="switch" style="position: relative; display: inline-block; width: 46px; height: 24px;">
                                <input type="checkbox" onchange="this.form.submit()" {% if not acc.is_excluded %}checked{% endif %} style="opacity: 0; width: 0; height: 0;">
                                <span class="slider round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: {% if acc.is_excluded %}#555{% else %}#4caf50{% endif %}; transition: .4s; border-radius: 24px;">
                                    <span style="position: absolute; content: ''; height: 18px; width: 18px; left: {% if acc.is_excluded %}3px{% else %}25px{% endif %}; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%;"></span>
                                </span>
                            </label>
                        </form>
                    </li>
                    {% endfor %}
                </ul>
            </div>'''

replacement = '''            {% if current_broker == 'all' %}
            <div style="margin-top: 2rem; text-align: center;">
                <button id="showExcludeSettingsBtn" onclick="document.getElementById('excludeSettingsBox').style.display = 'block'; this.style.display = 'none';" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #ccc; padding: 0.7rem 1.2rem; border-radius: 20px; font-size: 0.9rem; cursor: pointer; display: inline-flex; align-items: center; gap: 0.5rem;">
                    ⚙️ 합산 제외 계좌 설정
                </button>
            </div>
            
            <div id="excludeSettingsBox" style="display: none; margin-top: 1rem; background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: #fff; font-size: 1.1rem;">⚙️ 계좌 합산 관리</h3>
                    <button onclick="document.getElementById('excludeSettingsBox').style.display = 'none'; document.getElementById('showExcludeSettingsBtn').style.display = 'inline-flex';" style="background: none; border: none; color: #888; cursor: pointer; font-size: 1.2rem;">✕</button>
                </div>
                <p style="font-size: 0.85rem; color: #888; margin-bottom: 1rem;">체크를 해제하면 해당 계좌가 총 자산 합산 및 차트 계산에서 완전히 제외됩니다.</p>
                
                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.8rem;">
                    {% for acc in data.all_accounts_list|sort(attribute='broker_clean') %}
                    <li style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); padding: 0.8rem; border-radius: 8px;">
                        <div>
                            <div style="font-size: 0.95rem; color: #ddd;">{{ acc.broker_clean }} {{ acc.account_type|replace('(', '')|replace(')', '') }}</div>
                            <div style="font-size: 0.8rem; color: #888;">{{ acc.masked_num }}</div>
                        </div>
                        <form action="{{ url_for('infinite.toggle_exclude', broker=current_broker) }}" method="POST" style="margin: 0;">
                            <input type="hidden" name="broker" value="{{ acc.broker }}">
                            <input type="hidden" name="account_num" value="{{ acc.account_num }}">
                            <input type="hidden" name="is_excluded" value="{% if acc.is_excluded %}false{% else %}true{% endif %}">
                            <label class="switch" style="position: relative; display: inline-block; width: 46px; height: 24px;">
                                <input type="checkbox" onchange="this.form.submit()" {% if not acc.is_excluded %}checked{% endif %} style="opacity: 0; width: 0; height: 0;">
                                <span class="slider round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: {% if acc.is_excluded %}#555{% else %}#4caf50{% endif %}; transition: .4s; border-radius: 24px;">
                                    <span style="position: absolute; content: ''; height: 18px; width: 18px; left: {% if acc.is_excluded %}3px{% else %}25px{% endif %}; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%;"></span>
                                </span>
                            </label>
                        </form>
                    </li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
