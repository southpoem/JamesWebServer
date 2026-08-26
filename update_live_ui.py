import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                            const qtyEl = item.querySelector('.asset-qty');
                            if (!qtyEl) return;
                            
                            let qtyStr = qtyEl.innerText.replace(/[^0-9.-]/g, '');'''

replacement = '''                            const qtyEl = item.querySelector('.asset-qty');
                            if (!qtyEl) return;
                            
                            let qtyStr = qtyEl.innerText.split('주')[0].replace(/[^0-9.-]/g, '');
                            
                            // Insert real-time unit price
                            let unitPriceEl = item.querySelector('.asset-unit-price');
                            if (!unitPriceEl) {
                                unitPriceEl = document.createElement('span');
                                unitPriceEl.className = 'asset-unit-price';
                                unitPriceEl.style.color = '#ff9800'; // Orange color to indicate live
                                unitPriceEl.style.marginLeft = '6px';
                                unitPriceEl.style.fontWeight = '500';
                                qtyEl.appendChild(unitPriceEl);
                            }
                            unitPriceEl.innerText = '(@' + livePrice.toLocaleString() + '원)';
'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
