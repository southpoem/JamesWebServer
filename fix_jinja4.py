import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find the exact area
match = re.search(r'\{%\s*if\s*error\s*%\}.*?\{%\s*elif\s*not\s*data\s*%\}', content, re.DOTALL)
if match:
    print("Found the messed up block.")
    # We want it to be:
    # {% if error %}
    #     <div ...>{{ error }}</div>
    # {% elif current_broker == 'analysis' %}
    #     ... (the big analysis block)
    # {% elif not data %}
    
    # Let's extract the big analysis block from the content
    analysis_match = re.search(r'\{%\s*if\s*current_broker\s*==\s*\'analysis\'\s*%\}(.*?)\{%\s*elif\s*error\s*%\}', content, re.DOTALL)
    if analysis_match:
        analysis_content = analysis_match.group(1)
        
        # Now rebuild the block
        new_block = '''{% if error %}
            <div style="color: #ff5252; margin-bottom: 1rem;">{{ error }}</div>
        {% elif current_broker == 'analysis' %}''' + analysis_content + '''{% elif not data %}'''
        
        content = content[:match.start()] + new_block + content[match.end():]
        
        with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Template fixed.")
    else:
        print("Analysis block not found.")
else:
    print("Messed up block not found.")
