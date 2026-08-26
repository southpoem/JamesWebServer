import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make .asset-qty font smaller (0.75rem -> 0.7rem or 0.65rem)
content = re.sub(
    r'\.asset-qty\s*\{\s*font-size:\s*0\.75rem;',
    '.asset-qty {\n            font-size: 0.65rem;',
    content
)

# Update JS for unitPriceEl size (0.85rem -> 0.75rem or 0.7rem)
content = re.sub(
    r"unitPriceEl\.style\.fontSize\s*=\s*'0\.85rem';",
    "unitPriceEl.style.fontSize = '0.7rem';",
    content
)

# Adjust margin-left from 12px to 8px
content = re.sub(
    r"unitPriceEl\.style\.marginLeft\s*=\s*'12px';",
    "unitPriceEl.style.marginLeft = '8px';",
    content
)

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Font sizes updated.")
