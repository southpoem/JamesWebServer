import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''<a href="/infinite?broker=family" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'family' %}#121212{% else %}#ffd700{% endif %}; background: {% if current_broker == 'family' %}#ffd700{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'family' %}#ffd700{% else %}transparent{% endif %};">가족 자산</a>'''

replacement = '''<a href="/infinite?broker=family" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'family' %}#121212{% else %}#ffd700{% endif %}; background: {% if current_broker == 'family' %}#ffd700{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'family' %}#ffd700{% else %}transparent{% endif %};">가족 자산</a>
            <a href="/infinite?broker=analysis" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'analysis' %}#121212{% else %}#f093fb{% endif %}; background: {% if current_broker == 'analysis' %}#f093fb{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'analysis' %}#f093fb{% else %}transparent{% endif %};">📊 자산 분석</a>'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Tab added successfully.")
else:
    print("Tab target NOT found. Trying regex...")
    content = re.sub(
        r'<a href="/infinite\?broker=family".*?>가족 자산</a>',
        replacement,
        content
    )
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Regex replacement run.")
