import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the nested if by changing it to elif
target = '''        {% if error %}
            <div style="color: #ff5252; margin-bottom: 1rem;">{{ error }}</div>
        {% if current_broker == 'analysis' %}'''

replacement = '''        {% if error %}
            <div style="color: #ff5252; margin-bottom: 1rem;">{{ error }}</div>
        {% elif current_broker == 'analysis' %}'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Syntax error fixed.")
else:
    print("Target not found. Looking for alternatives...")
    # Just in case there is some whitespace mismatch
    content = re.sub(
        r'\{%\s*if\s*current_broker\s*==\s*\'analysis\'\s*%\}',
        r'{% elif current_broker == \'analysis\' %}',
        content,
        count=1
    )
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Regex replacement run.")
