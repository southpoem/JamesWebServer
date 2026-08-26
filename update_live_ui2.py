import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                        if (livePrices[ticker]) {
                            const livePrice = livePrices[ticker];
                            const qtyEl = item.querySelector('.asset-qty');
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

replacement = '''                        if (livePrices[ticker]) {
                            const liveData = livePrices[ticker];
                            const livePrice = liveData.nv;
                            const qtyEl = item.querySelector('.asset-qty');
                            if (!qtyEl) return;
                            
                            let qtyStr = qtyEl.innerText.split('주')[0].replace(/[^0-9.-]/g, '');
                            
                            // Format real-time unit price like screenshot
                            let rfStr = '';
                            let color = '#888';
                            if (liveData.rf == '2' || liveData.rf == '4') { rfStr = '▲'; color = '#ff5252'; }
                            else if (liveData.rf == '5' || liveData.rf == '1') { rfStr = '▼'; color = '#4facfe'; }
                            else { rfStr = '-'; }
                            
                            let unitPriceEl = item.querySelector('.asset-unit-price');
                            if (!unitPriceEl) {
                                unitPriceEl = document.createElement('span');
                                unitPriceEl.className = 'asset-unit-price';
                                unitPriceEl.style.marginLeft = '12px';
                                unitPriceEl.style.fontWeight = '600';
                                unitPriceEl.style.fontSize = '0.85rem';
                                qtyEl.appendChild(unitPriceEl);
                            }
                            unitPriceEl.style.color = color;
                            
                            // e.g. 259,500원   2,500 ▲ 0.97%
                            let diffStr = liveData.cv == 0 ? '0' : liveData.cv.toLocaleString();
                            unitPriceEl.innerHTML = ${livePrice.toLocaleString()}원 <span style="margin-left:8px; opacity:0.9; font-weight:500;">  %</span>;
'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("UI updated")
else:
    print("Target not found")
