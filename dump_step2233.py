import json
import os

log_path = r"C:\Users\이재혁\.gemini\antigravity\brain\21c640c1-f267-4668-a902-c251703b24b3\.system_generated\logs\transcript_full.jsonl"
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('step_index') == 2233:
            with open(r'C:\PycharmProjects\JamesWebServer\step_2233.json', 'w', encoding='utf-8') as out:
                json.dump(data, out, indent=2, ensure_ascii=False)
            print("Dumped step 2233")
