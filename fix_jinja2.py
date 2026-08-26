import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Undo the wrong replacement
content = content.replace('{% elif current_broker == \\\'analysis\\\' %}', '{% if current_broker == \\\'analysis\\\' %}')

# Now find the right one.
# It should be right after:
# {% if error %}
#    <div style="color: #ff5252; margin-bottom: 1rem;">{{ error }}</div>
# {% if current_broker == 'analysis' %}

target_correct = '''        {% if error %}
            <div style="color: #ff5252; margin-bottom: 1rem;">{{ error }}</div>
        {% if current_broker == 'analysis' %}'''

replacement_correct = '''        {% if error %}
            <div style="color: #ff5252; margin-bottom: 1rem;">{{ error }}</div>
        {% elif current_broker == 'analysis' %}'''

if target_correct in content:
    content = content.replace(target_correct, replacement_correct)
else:
    # try regex just for the structural part
    content = re.sub(
        r'\{%\s*if\s*error\s*%\}[\s\S]*?\{\{\s*error\s*\}\}</div>\s*\{%\s*if\s*current_broker\s*==\s*\'analysis\'\s*%\}',
        r'{% if error %}\n            <div style="color: #ff5252; margin-bottom: 1rem;">{{ error }}</div>\n        {% elif current_broker == \'analysis\' %}',
        content
    )

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)
