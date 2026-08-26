import os

def find_in_binary(file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # search for bytes
    search_str = b'<!-- Broker Tabs -->'
    idx = data.find(search_str)
    if idx != -1:
        print(f"Found in {file_path} at index {idx}!")
        start = data.rfind(b'<!DOCTYPE html>', 0, idx)
        end = data.find(b'</html>', idx)
        if start != -1 and end != -1:
            html_bytes = data[start:end+7]
            # Try to decode
            try:
                # The file might have null bytes or control characters in between if it's a proprietary format
                html_str = html_bytes.decode('utf-8', errors='ignore')
                # Let's save it
                with open(r'C:\PycharmProjects\JamesWebServer\recovered_from_jetbrains.html', 'w', encoding='utf-8') as out:
                    out.write(html_str)
                print("Recovered and saved to recovered_from_jetbrains.html!")
            except Exception as e:
                print("Decode error:", e)

find_in_binary(r'C:\Users\이재혁\AppData\Local\JetBrains\PyCharm2025.3\LocalHistory\changes.storageData')
find_in_binary(r'C:\Users\이재혁\AppData\Local\JetBrains\PyCharmCE2024.1\LocalHistory\changes.storageData')
