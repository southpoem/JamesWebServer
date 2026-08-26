import os
import re
import zlib

def extract_from_binary(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Sometimes it is compressed with deflate/zlib?
    # Actually, let's just find the exact byte sequence if it's plaintext
    start_marker = '<!-- Global Navigation -->'.encode('utf-8')
    end_marker = '</html>'.encode('utf-8')
    
    matches = []
    idx = 0
    while True:
        idx = data.find(start_marker, idx)
        if idx == -1:
            break
        end_idx = data.find(end_marker, idx)
        if end_idx != -1:
            chunk = data[idx:end_idx + len(end_marker)]
            try:
                decoded = chunk.decode('utf-8')
                matches.append(decoded)
            except:
                pass
        idx += len(start_marker)
        
    if matches:
        print(f"Found {len(matches)} potential full matches in {filepath}")
        # Get the largest one, or the one that contains 'family'
        best_match = None
        for m in matches:
            if 'family' in m and 'meritz' in m and 'analysis' in m:
                if best_match is None or len(m) > len(best_match):
                    best_match = m
        if best_match:
            # We need to prepend the DOCTYPE and head because we started from Global Navigation
            head = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>자산 상세 조회 - James World</title>
    <meta name="color-scheme" content="dark" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .page-container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
        .summary-card { background: rgba(30,30,40,0.8); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.5rem; text-align: center; }
        .summary-card h3 { margin: 0 0 0.5rem 0; font-size: 1rem; color: #888; }
        .summary-card .value { font-size: 1.5rem; font-weight: 700; color: #fff; }
        .summary-card .up { color: #00e676; }
        .summary-card .down { color: #ff5252; }
        .data-tables { display: grid; grid-template-columns: 1fr; gap: 2rem; }
        table { width: 100%; border-collapse: collapse; background: rgba(30,30,40,0.8); border-radius: 12px; overflow: hidden; }
        th, td { padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { background: rgba(255,255,255,0.05); font-weight: 600; color: #aaa; text-align: center; }
        td.text-left { text-align: left; }
        .nav-link { display: inline-block; margin-bottom: 1rem; color: #4facfe; text-decoration: none; font-weight: 600; }
        .nav-link:hover { text-decoration: underline; }
        
        .header-with-btn {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .header-with-btn h2 {
            margin: 0;
            color: #fff;
            font-size: 1.25rem;
        }
        .toggle-btn {
            background: rgba(79, 172, 254, 0.1);
            border: 1px solid rgba(79, 172, 254, 0.4);
            color: #4facfe;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .toggle-btn:hover {
            background: rgba(79, 172, 254, 0.2);
        }
        .chart-container {
            display: none; /* hidden by default */
            background: rgba(30,30,40,0.8);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        .global-tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 1rem;
        }
        .global-tab {
            color: #aaa;
            text-decoration: none;
            font-size: 1.1rem;
            font-weight: 600;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .global-tab:hover {
            background: rgba(255,255,255,0.05);
            color: #fff;
        }
        .global-tab.active {
            color: #fff;
            background: rgba(255,255,255,0.1);
        }
    </style>
</head>
<body>
    <div class="page-container">
'''
            full_html = head + best_match
            with open(r'C:\PycharmProjects\JamesWebServer\recovered_best.html', 'w', encoding='utf-8') as out:
                out.write(full_html)
            print("Successfully recovered the best match from LocalHistory!")

extract_from_binary(r'C:\Users\이재혁\AppData\Local\JetBrains\PyCharm2025.3\LocalHistory\changes.storageData')
extract_from_binary(r'C:\Users\이재혁\AppData\Local\JetBrains\PyCharmCE2024.1\LocalHistory\changes.storageData')
