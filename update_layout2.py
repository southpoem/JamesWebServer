import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 4. Update JS logic using regex
content = re.sub(
    r"let unitPriceEl = item\.querySelector\('\.asset-unit-price'\);[\s\S]*?liveData\.cr \+ '%</span>';",
    '''let livePriceEl = item.querySelector('.asset-live-price');
                              if (livePriceEl) {
                                  livePriceEl.style.color = color;
                                  livePriceEl.style.fontWeight = '600';
                                  
                                  let diffStr = liveData.cv == 0 ? '0' : liveData.cv.toLocaleString();
                                  livePriceEl.innerHTML = livePrice.toLocaleString() + '원 <span style="margin-left:6px; opacity:0.9; font-weight:500;">' + diffStr + ' ' + rfStr + ' ' + liveData.cr + '%</span>';
                              }''',
    content
)

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("JS logic updated.")
