import json

log_path = r"C:\Users\이재혁\.gemini\antigravity\brain\21c640c1-f267-4668-a902-c251703b24b3\.system_generated\logs\transcript_full.jsonl"
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
        except:
            continue
            
        if data.get('type') == 'TOOL_RESPONSE':
            content = data.get('content', '')
            if '<!-- Broker Tabs -->' in content and '<!DOCTYPE html>' in content:
                print("Found in step:", data.get('step_index'))
                # Extract it
                start = content.find('<!DOCTYPE html>')
                html = content[start:]
                with open(r'C:\PycharmProjects\JamesWebServer\recovered_assets_first.html', 'w', encoding='utf-8') as out:
                    out.write(html)
                print("Recovered!")
                break
