import json
with open(r'C:\PycharmProjects\JamesWebServer\step_2233.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

if data.get('type') == 'TOOL_RESPONSE':
    # Assuming it's a response to a view_file or run_command
    print(data.get('content')[:500])
elif data.get('type') == 'PLANNER_RESPONSE':
    print(data.get('content')[:500])
    for call in data.get('tool_calls', []):
        print("Tool call:", call.get('name'))
