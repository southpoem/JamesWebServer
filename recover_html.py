import json
with open(r'C:\PycharmProjects\JamesWebServer\step_2233.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Type:", data.get('type'))
if 'tool_calls' in data:
    for tc in data['tool_calls']:
        print("Tool:", tc.get('name'))
        for k, v in tc.get('args', {}).items():
            if isinstance(v, str) and len(v) > 100:
                print(f"Arg {k} has long string (len {len(v)})")
                if '<!DOCTYPE html>' in v:
                    with open(r'C:\PycharmProjects\JamesWebServer\recovered_assets.html', 'w', encoding='utf-8') as out:
                        out.write(v)
                    print("RECOVERED TO recovered_assets.html")
