import json
import re

with open(r'C:\PycharmProjects\JamesWebServer\step_2233.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

content_str = str(data)

# Let's extract the HTML using a regex search for something unique at the top and bottom of infinite_assets.html
start = content_str.find('<!DOCTYPE html>')
end = content_str.find('</html>') + 7
if start != -1 and end != -1:
    html = content_str[start:end]
    # Unescape the string representations
    html = html.replace('\\\\', '\\').replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
    print(f"Extracted HTML length: {len(html)}")
    print(html[:200])
else:
    print("HTML not found clearly in step 2233")
