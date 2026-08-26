import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix layout for row.ticker
content = content.replace(
'''                                      <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                          <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px;">
                                              <div class="asset-name" style="font-size: 0.8rem;">{{ row.ticker }}</div>
                                              <div class="asset-qty" style="font-size: 0.6rem;">{{ "{:,.0f}".format(row.quantity) }}주</div>
                                              <div class="asset-live-price" style="font-size: 0.65rem; margin-left: 2px;"></div>
                                          </div>
                                      </div>''',
'''                                      <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                          <div style="display: flex; align-items: baseline; gap: 4px;">
                                              <div class="asset-name" style="font-size: 0.8rem;">{{ row.ticker }}</div>
                                              <div class="asset-qty" style="font-size: 0.6rem;">{{ "{:,.0f}".format(row.quantity) }}주</div>
                                          </div>
                                          <div class="asset-live-price" style="font-size: 0.65rem;"></div>
                                      </div>'''
)

# Fix layout for fa.account_name
content = content.replace(
'''                                  <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                      <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px;">
                                          <div class="asset-name" style="font-size: 0.8rem;">{{ fa.account_name }}</div>
                                          <div class="asset-qty" style="font-size: 0.6rem;">{{ fa.asset_type }} <span style="font-size: 0.7em; color: #666;">({{ fa.updated_at[:10] }})</span></div>
                                      </div>
                                  </div>''',
'''                                  <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                      <div style="display: flex; align-items: baseline; gap: 4px;">
                                          <div class="asset-name" style="font-size: 0.8rem;">{{ fa.account_name }}</div>
                                          <div class="asset-qty" style="font-size: 0.6rem;">{{ fa.asset_type }} <span style="font-size: 0.7em; color: #666;">({{ fa.updated_at[:10] }})</span></div>
                                      </div>
                                  </div>'''
)

# Fix layout for tk.ticker (from previous session)
content = content.replace(
'''                                      <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                          <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px;">
                                              <div class="asset-name" style="font-size: 0.8rem;">{{ tk.ticker }}</div>
                                              <div class="asset-qty" style="font-size: 0.6rem;">{{ "{:,.0f}".format(tk.quantity) }}주</div>
                                              <div class="asset-live-price" style="font-size: 0.65rem; margin-left: 2px;"></div>
                                          </div>
                                      </div>''',
'''                                      <div class="asset-info" style="margin-left: 0.5rem; justify-content: center;">
                                          <div style="display: flex; align-items: baseline; gap: 4px;">
                                              <div class="asset-name" style="font-size: 0.8rem;">{{ tk.ticker }}</div>
                                              <div class="asset-qty" style="font-size: 0.6rem;">{{ "{:,.0f}".format(tk.quantity) }}주</div>
                                          </div>
                                          <div class="asset-live-price" style="font-size: 0.65rem;"></div>
                                      </div>'''
)

# Now add the TAB
content = content.replace(
'''<a href="/infinite?broker=family" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'family' %}#121212{% else %}#ffd700{% endif %}; background: {% if current_broker == 'family' %}#ffd700{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'family' %}#ffd700{% else %}transparent{% endif %};">가족 자산</a>''',
'''<a href="/infinite?broker=family" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'family' %}#121212{% else %}#ffd700{% endif %}; background: {% if current_broker == 'family' %}#ffd700{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'family' %}#ffd700{% else %}transparent{% endif %};">가족 자산</a>
            <a href="/infinite?broker=analysis" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'analysis' %}#121212{% else %}#f093fb{% endif %}; background: {% if current_broker == 'analysis' %}#f093fb{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'analysis' %}#f093fb{% else %}transparent{% endif %};">📊 자산 분석</a>'''
)

# Now inject the UI logic exactly before {% elif not data %}
ui_logic = '''{% elif current_broker == 'analysis' %}
            <div style="padding: 1rem 0;">
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="font-size: 1.1rem; color: #fff; margin-bottom: 1rem; text-align: center; font-weight: 700;">🇺🇸 미국 vs 🇰🇷 한국</h3>
                    <div style="position: relative; height: 220px; width: 100%;">
                        <canvas id="countryChart"></canvas>
                    </div>
                    <ul style="list-style: none; padding: 0; margin-top: 1.5rem;" id="countryLegend"></ul>
                </div>
                
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="font-size: 1.1rem; color: #fff; margin-bottom: 1rem; text-align: center; font-weight: 700;">🏢 업종별 비중</h3>
                    <div style="position: relative; height: 260px; width: 100%;">
                        <canvas id="sectorChart"></canvas>
                    </div>
                    <ul style="list-style: none; padding: 0; margin-top: 1.5rem;" id="sectorLegend"></ul>
                </div>
                
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="font-size: 1.1rem; color: #fff; margin-bottom: 1rem; text-align: center; font-weight: 700;">📈 종목별 비중</h3>
                    <div style="position: relative; height: 300px; width: 100%;">
                        <canvas id="stockChart"></canvas>
                    </div>
                    <ul style="list-style: none; padding: 0; margin-top: 1.5rem;" id="stockLegend"></ul>
                </div>
            </div>
            
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const analysisData = {{ data.analysis_data | tojson | safe }};
                    if (!analysisData) return;
                    
                    const createDoughnut = (ctxId, legendId, dataArr) => {
                        if (!dataArr || dataArr.length === 0) return;
                        
                        const labels = dataArr.map(d => d.label);
                        const values = dataArr.map(d => d.value);
                        const total = values.reduce((a, b) => a + b, 0);
                        
                        const colors = [
                            '#FF5252', '#4FACFE', '#FEE140', '#43E97B', '#F093FB', 
                            '#00f2fe', '#f83600', '#f9d423', '#b224ef', '#f5576c', 
                            '#2193b0', '#6dd5ed', '#cc2b5e', '#753a88', '#ee0979',
                            '#ff6a00', '#11998e', '#38ef7d', '#fc4a1a', '#f7b733'
                        ];
                        
                        new Chart(document.getElementById(ctxId), {
                            type: 'doughnut',
                            data: {
                                labels: labels,
                                datasets: [{
                                    data: values,
                                    backgroundColor: colors.slice(0, labels.length),
                                    borderWidth: 0
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: { display: false },
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                let v = context.raw;
                                                let pct = (v / total * 100).toFixed(1) + '%';
                                                return  : 원 ();
                                            }
                                        }
                                    }
                                },
                                cutout: '65%'
                            }
                        });
                        
                        const legendHtml = dataArr.map((d, i) => {
                            let pct = total > 0 ? (d.value / total * 100).toFixed(1) : 0;
                            return 
                            <li style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; font-size: 0.85rem; padding: 4px 0; border-bottom: 1px dotted rgba(255,255,255,0.1);">
                                <div style="display: flex; align-items: center; gap: 10px; max-width: 65%;">
                                    <span style="width: 12px; height: 12px; border-radius: 50%; background: ; flex-shrink: 0;"></span>
                                    <span style="color: #eee; word-break: break-all; line-height: 1.3;"></span>
                                </div>
                                <div style="text-align: right; line-height: 1.3;">
                                    <span style="color: #fff; font-weight: 700; font-size: 0.95rem;">%</span>
                                    <br><span style="color: #888; font-size: 0.75rem;">원</span>
                                </div>
                            </li>;
                        }).join('');
                        document.getElementById(legendId).innerHTML = legendHtml;
                    };
                    
                    createDoughnut('countryChart', 'countryLegend', analysisData.country);
                    createDoughnut('sectorChart', 'sectorLegend', analysisData.sector);
                    createDoughnut('stockChart', 'stockLegend', analysisData.stock);
                });
            </script>
        {% elif not data %}'''

content = content.replace('{% elif not data %}', ui_logic)

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("All fixes applied perfectly!")
