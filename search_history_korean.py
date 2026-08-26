import os
def search_history(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Try searching for 계좌별 in utf-8
    keyword = '계좌별'.encode('utf-8')
    idx = data.find(keyword)
    if idx != -1:
        print(f"FOUND '계좌별' in {filepath} at index {idx}")
        # Extract a chunk around it
        start = max(0, idx - 1000)
        end = min(len(data), idx + 5000)
        chunk = data[start:end]
        try:
            text = chunk.decode('utf-8', errors='ignore')
            with open(r'C:\PycharmProjects\JamesWebServer\extracted_history.txt', 'w', encoding='utf-8') as out:
                out.write(text)
            print("Extracted to extracted_history.txt")
        except:
            pass

search_history(r'C:\Users\이재혁\AppData\Local\JetBrains\PyCharm2025.3\LocalHistory\changes.storageData')
search_history(r'C:\Users\이재혁\AppData\Local\JetBrains\PyCharmCE2024.1\LocalHistory\changes.storageData')
