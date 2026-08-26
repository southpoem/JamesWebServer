import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update row.ticker block
target_row = '''                                      <div class="asset-info" style="margin-left: 0.5rem;">
                                          <div class="asset-name">{{ row.ticker }}</div>
                                          <div class="asset-qty">{{ "{:,.0f}".format(row.quantity) }}주</div>
                                      </div>'''
replace_row = '''                                      <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                          <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px;">
                                              <div class="asset-name" style="font-size: 0.8rem;">{{ row.ticker }}</div>
                                              <div class="asset-qty" style="font-size: 0.6rem;">{{ "{:,.0f}".format(row.quantity) }}주</div>
                                              <div class="asset-live-price" style="font-size: 0.65rem; margin-left: 2px;"></div>
                                          </div>
                                      </div>'''

# 2. Update fa.account_name block
target_fa = '''                                  <div class="asset-info" style="margin-left: 0.5rem;">
                                      <div class="asset-name">{{ fa.account_name }}</div>
                                      <div class="asset-qty">{{ fa.asset_type }} <span style="font-size: 0.7em; color: #666;">({{ fa.updated_at[:10] }})</span></div>
                                  </div>'''
replace_fa = '''                                  <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                      <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px;">
                                          <div class="asset-name" style="font-size: 0.8rem;">{{ fa.account_name }}</div>
                                          <div class="asset-qty" style="font-size: 0.6rem;">{{ fa.asset_type }} <span style="font-size: 0.7em; color: #666;">({{ fa.updated_at[:10] }})</span></div>
                                      </div>
                                  </div>'''

# 3. Update tk.ticker block
target_tk = '''                                  <div class="asset-info">
                                      <div class="asset-name">{{ tk.ticker }}</div>
                                      <div class="asset-qty">{{ "{:,.0f}".format(tk.quantity) }}주</div>
                                  </div>'''
replace_tk = '''                                  <div class="asset-info" style="justify-content: center;">
                                      <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px;">
                                          <div class="asset-name" style="font-size: 0.8rem;">{{ tk.ticker }}</div>
                                          <div class="asset-qty" style="font-size: 0.6rem;">{{ "{:,.0f}".format(tk.quantity) }}주</div>
                                          <div class="asset-live-price" style="font-size: 0.65rem; margin-left: 2px;"></div>
                                      </div>
                                  </div>'''

if target_row in content: content = content.replace(target_row, replace_row)
if target_fa in content: content = content.replace(target_fa, replace_fa)
if target_tk in content: content = content.replace(target_tk, replace_tk)

# 4. Update JS logic
target_js = '''                              let unitPriceEl = item.querySelector('.asset-unit-price');
                              if (!unitPriceEl) {
                                  unitPriceEl = document.createElement('span');
                                  unitPriceEl.className = 'asset-unit-price';
                                  unitPriceEl.style.marginLeft = '8px';
                                  unitPriceEl.style.fontWeight = '600';
                                  unitPriceEl.style.fontSize = '0.7rem';
                                  qtyEl.appendChild(unitPriceEl);
                              }
                              unitPriceEl.style.color = color;
                              
                              // e.g. 259,500원  2,500 ▲ 0.97%
                              let diffStr = liveData.cv == 0 ? '0' : liveData.cv.toLocaleString();
                              unitPriceEl.innerHTML = livePrice.toLocaleString() + '원 <span style="margin-left:8px; opacity:0.9; font-weight:500;">' + diffStr + ' ' + rfStr + ' ' + liveData.cr + '%</span>';'''

replace_js = '''                              let livePriceEl = item.querySelector('.asset-live-price');
                              if (livePriceEl) {
                                  livePriceEl.style.color = color;
                                  livePriceEl.style.fontWeight = '600';
                                  
                                  let diffStr = liveData.cv == 0 ? '0' : liveData.cv.toLocaleString();
                                  livePriceEl.innerHTML = livePrice.toLocaleString() + '원 <span style="margin-left:6px; opacity:0.9; font-weight:500;">' + diffStr + ' ' + rfStr + ' ' + liveData.cr + '%</span>';
                              }'''

if target_js in content:
    content = content.replace(target_js, replace_js)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("HTML and JS updated.")
else:
    print("JS target not found.")
