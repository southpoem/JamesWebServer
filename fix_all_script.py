import subprocess

# 1. Restore the file to the clean 299-line version
subprocess.run(['git', 'restore', r'templates\infinite_assets.html'])

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 2. Add the Global Navigation & Broker Tabs (Replace the top header block precisely)
target_header = '''<div class="page-container">
        <a href="/infinite" class="nav-link">⬅ 메인 대시보드로 돌아가기</a>
        <div class="header-with-btn">
            <h1 style="color: #fff; margin: 0;">총 자산 추적 대시보드</h1>
            <button class="toggle-btn" onclick="toggleChart('trendChartContainer')">📈 변화차트 보기</button>
        </div>'''

new_header = '''<div class="page-container">
        <!-- Global Navigation -->
        <div class="global-tabs" style="display: flex; gap: 1rem; margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem;">
            <a href="/infinite" class="global-tab active" style="color: #fff; text-decoration: none; font-size: 1.1rem; font-weight: 600; padding: 0.5rem 1rem; border-radius: 8px; background: rgba(255,255,255,0.1);">🌐 자산</a>
            <a href="/infinite/macro" class="global-tab" style="color: #aaa; text-decoration: none; font-size: 1.1rem; font-weight: 600; padding: 0.5rem 1rem; border-radius: 8px; transition: all 0.2s;">🌍 거시 경제</a>
        </div>
        <!-- Broker Tabs -->
        <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem; overflow-x: auto; white-space: nowrap; padding-bottom: 0.5rem;">
            <a href="/infinite?broker=samsung" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'samsung' %}#121212{% else %}#4facfe{% endif %}; background: {% if current_broker == 'samsung' %}#4facfe{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'samsung' %}#4facfe{% else %}transparent{% endif %};">🔵 삼성증권</a>
            <a href="/infinite?broker=meritz" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'meritz' %}#121212{% else %}#ff5252{% endif %}; background: {% if current_broker == 'meritz' %}#ff5252{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'meritz' %}#ff5252{% else %}transparent{% endif %};">🔴 메리츠증권</a>
            <a href="/infinite?broker=all" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'all' %}#121212{% else %}white{% endif %}; background: {% if current_broker == 'all' %}white{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'all' %}white{% else %}transparent{% endif %};">⚪ 전체계좌</a>
            <a href="/infinite?broker=family" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'family' %}#121212{% else %}#ffd700{% endif %}; background: {% if current_broker == 'family' %}#ffd700{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'family' %}#ffd700{% else %}transparent{% endif %};">가족 자산</a>
            <a href="/infinite?broker=analysis" style="padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; color: {% if current_broker == 'analysis' %}#121212{% else %}#f093fb{% endif %}; background: {% if current_broker == 'analysis' %}#f093fb{% else %}rgba(255,255,255,0.1){% endif %}; border: 1px solid {% if current_broker == 'analysis' %}#f093fb{% else %}transparent{% endif %};">📊 자산 분석</a>
        </div>

        <div class="header-section" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <h1 style="color: #fff; margin: 0; font-size: 1.25rem;">총자산</h1>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                {% if current_broker == 'samsung' %}
                <form action="/run_samsung_account" method="post" style="margin: 0;">
                    <button type="submit" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #4facfe; padding: 0.4rem 0.8rem; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600;">🔄 삼성증권</button>
                </form>
                {% endif %}
                {% if current_broker == 'meritz' %}
                <form action="/run_meritz_account" method="post" style="margin: 0;">
                    <button type="submit" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #ff5252; padding: 0.4rem 0.8rem; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600;">🔄 메리츠</button>
                </form>
                {% endif %}
                <button class="icon-btn toggle-btn" onclick="toggleChart('trendChartContainer')" style="background: rgba(79, 172, 254, 0.1); border: 1px solid rgba(79, 172, 254, 0.4); color: #4facfe; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9rem; transition: all 0.2s;">📈 변화추이</button>
            </div>
        </div>'''

content = content.replace(target_header, new_header)

# 3. Add Analysis UI
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
                    const analysisData = {{ data.analysis_data | tojson | safe if data.analysis_data else 'null' }};
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

# 4. Fix layout of table cells (Font sizes and live prices)
import re
content = re.sub(
    r'<td class="text-left" style="font-weight:600; color:#fff;">(.*?)</td>',
    r'<td class="text-left" style="font-weight:600; color:#fff;">\n'
    r'                                <div class="asset-info" style="justify-content: flex-start;">\n'
    r'                                    <div style="display: flex; align-items: baseline; gap: 4px;">\n'
    r'                                        <div class="asset-name" style="font-size: 0.8rem;">\1</div>\n'
    r'                                    </div>\n'
    r'                                    <div class="asset-live-price" style="font-size: 0.65rem;"></div>\n'
    r'                                </div>\n'
    r'                            </td>',
    content
)

# 5. Fix Chart Logic EXACT MATCH
chart_target = '''                // --- 1. Total Asset Trend Chart ---
                const trendCtx = document.getElementById('assetChart').getContext('2d');
                new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: {{ data.chart_dates | tojson }},
                        datasets: [{
                            label: '총 자산 평가 금액',
                            data: {{ data.chart_totals | tojson }},
                            borderColor: '#4facfe',
                            backgroundColor: 'rgba(79, 172, 254, 0.2)',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true,
                            pointBackgroundColor: '#fff',
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#aaa' } },
                            y: { 
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                ticks: { 
                                    color: '#aaa',
                                    callback: function(value) { return '₩' + value.toLocaleString(); }
                                }
                            }
                        }
                    }
                });'''

chart_replacement = '''                // --- 1. Total Asset Trend Chart ---
                const trendCtx = document.getElementById('assetChart').getContext('2d');
                new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: {{ data.chart_dates | tojson }},
                        datasets: {{ data.chart_datasets | tojson }}
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { 
                            legend: { position: 'bottom', labels: { color: '#aaa', padding: 15, usePointStyle: true, font: {size: 10} } },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': ' + context.parsed.y.toLocaleString() + '원';
                                    },
                                    footer: function(tooltipItems) {
                                        let sum = 0;
                                        tooltipItems.forEach(function(tooltipItem) {
                                            sum += tooltipItem.parsed.y;
                                        });
                                        let diffStr = '';
                                        if (tooltipItems[0].dataIndex > 0) {
                                            let prevSum = 0;
                                            const prevIndex = tooltipItems[0].dataIndex - 1;
                                            const chartInstance = Chart.getChart('assetChart');
                                            if (chartInstance) {
                                                chartInstance.data.datasets.forEach(function(dataset) {
                                                    prevSum += dataset.data[prevIndex];
                                                });
                                                const diff = sum - prevSum;
                                                diffStr = '\\n전일대비: ' + (diff > 0 ? '+' : '') + diff.toLocaleString() + '원';
                                            }
                                        }
                                        return '총액: ' + sum.toLocaleString() + '원' + diffStr;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#888', maxTicksLimit: 7 } },
                            y: { 
                                stacked: true,
                                min: 0,
                                grid: { color: 'rgba(255,255,255,0.05)' }, 
                                ticks: { 
                                    color: '#888',
                                    callback: function(value) { return (value / 10000).toLocaleString() + '만'; }
                                }
                            }
                        }
                    }
                });'''
content = content.replace(chart_target, chart_replacement)

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("FIX SCRIPT FINISHED")
