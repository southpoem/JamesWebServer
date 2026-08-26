import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Since the previous replacement put broken syntax, we need to match the broken syntax and fix it.
# Let's just find the unitPriceEl.innerHTML line using regex.

content = re.sub(
    r"unitPriceEl\.innerHTML\s*=\s*\$\{livePrice.*?</span>;",
    "unitPriceEl.innerHTML = livePrice.toLocaleString() + '원 <span style=\"margin-left:8px; opacity:0.9; font-weight:500;\">' + diffStr + ' ' + rfStr + ' ' + liveData.cr + '%</span>';",
    content
)

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Syntax fixed")
