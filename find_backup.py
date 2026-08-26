import json
import os

log_path = r"C:\Users\이재혁\.gemini\antigravity\brain\21c640c1-f267-4668-a902-c251703b24b3\.system_generated\logs\transcript_full.jsonl"
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'infinite_assets.html' in line and 'samsung' in line and 'meritz' in line:
                data = json.loads(line)
                if data.get('type') == 'PLANNER_RESPONSE' or data.get('type') == 'USER_INPUT' or data.get('type') == 'SYSTEM' or data.get('type') == 'TOOL_RESPONSE':
                    # Check if the content contains a large chunk of HTML
                    content = str(data)
                    if '<!-- Broker Tabs -->' in content:
                        print("Found in step:", data.get('step_index'))
