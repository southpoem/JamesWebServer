
import re
with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Instead of exact match, let's use regex to match from <div class="page-container"> down to </div> below button
pattern = r'<div class="page-container">\s*<a href="/infinite" class="nav-link">.*?</div>'
import re
new_content = re.sub(pattern, '''<div class="page-container">
        <!-- Global Navigation -->
        <div class="global-tabs" style="margin-bottom: 1rem;">
            <a href="/infinite" class="global-tab active" style="margin-right: 1rem; color: #fff; text-decoration: none; font-weight: 600; font-size: 1.2rem;">🌐 자산</a>
            <a href="/infinite/macro" class="global-tab" style="color: #aaa; text-decoration: none; font-weight: 600; font-size: 1.2rem;">🌍 거시 경제</a>
        </div>
        <!-- Broker Tabs -->
        <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem; overflow-x: auto; white-space: nowrap; padding-bottom: 0.5rem;">
            <a href="/infinite?broker=samsung" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'samsung' %}#121212{% else %}#4facfe{% endif %}; background: {% if current_broker == 'samsung' %}#4facfe{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'samsung' %}#4facfe{% else %}transparent{% endif %};">🔵 삼성증권</a>
            <a href="/infinite?broker=meritz" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'meritz' %}#121212{% else %}#ff5252{% endif %}; background: {% if current_broker == 'meritz' %}#ff5252{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'meritz' %}#ff5252{% else %}transparent{% endif %};">🔴 메리츠증권</a>
            <a href="/infinite?broker=all" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'all' %}#121212{% else %}white{% endif %}; background: {% if current_broker == 'all' %}white{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'all' %}white{% else %}transparent{% endif %};">⚪ 전체계좌</a>
            <a href="/infinite?broker=family" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'family' %}#121212{% else %}#ffd700{% endif %}; background: {% if current_broker == 'family' %}#ffd700{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'family' %}#ffd700{% else %}transparent{% endif %};">가족 자산</a>
            <a href="/infinite?broker=analysis" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'analysis' %}#121212{% else %}#f093fb{% endif %}; background: {% if current_broker == 'analysis' %}#f093fb{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'analysis' %}#f093fb{% else %}transparent{% endif %};">📊 자산 분석</a>
        </div>

        <div class="header-section" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <h1 style="color: #fff; margin: 0; font-size: 1.25rem;">총자산</h1>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                {% if current_broker == 'samsung' %}
                <form action="/run_samsung_account" method="post" style="margin: 0;">
                    <button type="submit" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #4facfe; padding: 0.4rem 0.8rem; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600;">🔄 삼성증권</button>
                </form>
                {% endif %}
                {% if current_broker == 'meritz' %}
                <form action="/run_meritz_account" method="post" style="margin: 0;">
                    <button type="submit" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #ff5252; padding: 0.4rem 0.8rem; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600;">🔄 메리츠</button>
                </form>
                {% endif %}
                <button class="icon-btn toggle-btn" onclick="toggleChart('trendChartContainer')" style="background: rgba(79, 172, 254, 0.1); border: 1px solid rgba(79, 172, 254, 0.4); color: #4facfe; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9rem; transition: all 0.2s;">📈 변화추이</button>
            </div>
        </div>''', content, flags=re.DOTALL)
    
with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
