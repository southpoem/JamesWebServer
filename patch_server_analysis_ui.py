import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add tab
tab_target = '''            <button class="tab-btn {% if current_broker == 'family' %}active{% endif %}" onclick="location.href='?broker=family'" style="flex: 1;">가족 자산</button>
        </div>'''

tab_replacement = '''            <button class="tab-btn {% if current_broker == 'family' %}active{% endif %}" onclick="location.href='?broker=family'" style="flex: 1; border-right: 1px solid #333;">가족 자산</button>
            <button class="tab-btn {% if current_broker == 'analysis' %}active{% endif %}" onclick="location.href='?broker=analysis'" style="flex: 1; color: #f093fb;">자산 분석</button>
        </div>'''

if tab_target in content:
    content = content.replace(tab_target, tab_replacement)
else:
    print("Tab target not found.")

# Add UI layout logic
ui_target = '''        {% if data.total_today == 0 and not current_broker == 'family' %}'''

ui_replacement = '''        {% if current_broker == 'analysis' %}
            <div style="padding: 1rem;">
                <h2 style="font-size: 1.2rem; margin-bottom: 1.5rem; color: #fff; text-align: center; font-weight: 700;">💡 내 자산 포트폴리오 분석</h2>
                
                <!-- Country Chart -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="font-size: 1rem; color: #ccc; margin-bottom: 1rem; text-align: center; font-weight: 600;">🇺🇸 미국 vs 🇰🇷 한국</h3>
                    <div style="position: relative; height: 200px; width: 100%;">
                        <canvas id="countryChart"></canvas>
                    </div>
                    <ul style="list-style: none; padding: 0; margin-top: 1.5rem;" id="countryLegend"></ul>
                </div>
                
                <!-- Sector Chart -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="font-size: 1rem; color: #ccc; margin-bottom: 1rem; text-align: center; font-weight: 600;">🏢 업종별 비중</h3>
                    <div style="position: relative; height: 250px; width: 100%;">
                        <canvas id="sectorChart"></canvas>
                    </div>
                    <ul style="list-style: none; padding: 0; margin-top: 1.5rem;" id="sectorLegend"></ul>
                </div>
                
                <!-- Stock Chart -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="font-size: 1rem; color: #ccc; margin-bottom: 1rem; text-align: center; font-weight: 600;">📈 종목별 비중</h3>
                    <div style="position: relative; height: 300px; width: 100%;">
                        <canvas id="stockChart"></canvas>
                    </div>
                    <ul style="list-style: none; padding: 0; margin-top: 1.5rem;" id="stockLegend"></ul>
                </div>
            </div>
            
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const analysisData = {{ data.analysis_data | tojson | safe }};
                    
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
                                    borderWidth: 1,
                                    borderColor: '#1a1a2e'
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
                            <li style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; font-size: 0.85rem; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <div style="display: flex; align-items: center; gap: 10px; max-width: 60%;">
                                    <span style="width: 12px; height: 12px; border-radius: 50%; background: ; flex-shrink: 0;"></span>
                                    <span style="color: #eee; word-break: break-all; line-height: 1.2;"></span>
                                </div>
                                <div style="text-align: right; line-height: 1.2;">
                                    <span style="color: #fff; font-weight: 700; font-size: 0.9rem;">%</span>
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
        {% elif data.total_today == 0 and not current_broker == 'family' %}'''

if ui_target in content:
    content = content.replace(ui_target, ui_replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Template UI logic added.")
else:
    print("UI target not found.")
