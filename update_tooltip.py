import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                            tooltip: {
                                displayColors: true,
                                callbacks: {
                                    label: function(context) {
                                        let val = context.raw;
                                        return context.dataset.label + ': ' + val.toLocaleString() + '원';
                                    }
                                }
                            }'''

replacement = '''                            tooltip: {
                                displayColors: true,
                                callbacks: {
                                    label: function(context) {
                                        let val = context.raw;
                                        return context.dataset.label + ': ' + val.toLocaleString() + '원';
                                    },
                                    footer: function(tooltipItems) {
                                        let total = 0;
                                        let prevTotal = 0;
                                        let dataIndex = tooltipItems[0].dataIndex;
                                        let chart = tooltipItems[0].chart;
                                        
                                        chart.data.datasets.forEach(function(dataset) {
                                            total += dataset.data[dataIndex] || 0;
                                            if (dataIndex > 0) {
                                                prevTotal += dataset.data[dataIndex - 1] || 0;
                                            }
                                        });
                                        
                                        let lines = ['-----------------'];
                                        lines.push('💰 합계: ' + total.toLocaleString() + '원');
                                        
                                        if (dataIndex > 0 && prevTotal > 0) {
                                            let diff = total - prevTotal;
                                            if (diff > 0) {
                                                lines.push('📈 전일대비: +' + diff.toLocaleString() + '원');
                                            } else if (diff < 0) {
                                                lines.push('📉 전일대비: ' + diff.toLocaleString() + '원');
                                            } else {
                                                lines.push('➖ 전일대비: 변동없음');
                                            }
                                        }
                                        return lines;
                                    }
                                }
                            }'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
