import json
import os

log_path = r"C:\Users\이재혁\.gemini\antigravity\brain\21c640c1-f267-4668-a902-c251703b24b3\.system_generated\logs\transcript_full.jsonl"
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
        except:
            continue
            
        content_str = str(data)
        if 'meritz' in content_str and 'samsung' in content_str and 'asset-live-price' in content_str:
            print("Found live price layout in step:", data.get('step_index'))
