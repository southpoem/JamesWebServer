import json

log_path = r"C:\Users\이재혁\.gemini\antigravity\brain\21c640c1-f267-4668-a902-c251703b24b3\.system_generated\logs\transcript_full.jsonl"
found = False
with open(log_path, 'r', encoding='utf-8') as f:
    for line in reversed(list(f)):
        try:
            data = json.loads(line)
        except:
            continue
            
        if data.get('type') == 'TOOL_RESPONSE':
            content = data.get('content', '')
            if content and '<!DOCTYPE html>' in content and 'samsung' in content and 'meritz' in content:
                print("Found full HTML in step:", data.get('step_index'))
                # Extract the HTML part
                start = content.find('<!DOCTYPE html>')
                html = content[start:]
                with open(r'C:\PycharmProjects\JamesWebServer\recovered_assets_full.html', 'w', encoding='utf-8') as out:
                    out.write(html)
                print("Recovered full HTML!")
                found = True
                break
if not found:
    print("Full HTML not found in TOOL_RESPONSE.")
