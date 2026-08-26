import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''                // --- 1. Total Asset Trend Chart ---
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

# Regex to match the block starting from "// --- 1. Total Asset Trend Chart ---" up to the next "// --- 2. Portfolio Pie Chart ---"
pattern = r'// ---\s*1\.\s*Total Asset Trend Chart\s*---.*?// ---\s*2\.\s*Portfolio Pie Chart\s*---'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, replacement + '\n\n                // --- 2. Portfolio Pie Chart ---', content, flags=re.DOTALL)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced via regex.")
else:
    print("Regex not found.")
