import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'datasets:\s*\[\s*\{.*?data:\s*\{\{\s*data\.chart_totals\s*\|\s*tojson\s*\}\}.*?\}\s*\]'

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, 'datasets: {{ data.chart_datasets | tojson }}', content, flags=re.DOTALL)
    
    scales_pattern = r'plugins:\s*\{\s*legend:\s*\{\s*display:\s*false\s*\}\s*\},'
    scales_replacement = '''plugins: { 
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
                        },'''
    content = re.sub(scales_pattern, scales_replacement, content, flags=re.DOTALL)
    content = re.sub(r'y:\s*\{', 'y: {\n                                stacked: true,\n                                min: 0,', content)
    
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully.")
else:
    print("Pattern not found.")
