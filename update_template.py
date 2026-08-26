import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                // --- 1. Line Chart ---
                const trendCtx = document.getElementById('assetLineChart').getContext('2d');
                trendChartObj = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: {{ data.chart_dates | tojson }},
                        datasets: [{
                            label: '총 자산',
                            data: {{ data.chart_totals | tojson }},
                            borderColor: '#ff5252',
                            backgroundColor: 'rgba(255, 82, 82, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true,
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { 
                            legend: { display: false },
                            tooltip: {
                                displayColors: false,
                                callbacks: {
                                    label: function(context) {
                                        let val = context.raw;
                                        let prevVal = context.dataIndex > 0 ? context.dataset.data[context.dataIndex - 1] : null;
                                        let lines = ['💰 총 자산: ' + val.toLocaleString()];
                                        if (prevVal !== null) {
                                            let diff = val - prevVal;
                                            let pct = prevVal > 0 ? (diff / prevVal * 100).toFixed(2) : 0;
                                            let sign = diff > 0 ? '▲' : (diff < 0 ? '▼' : '-');
                                            lines.push('📈 전일비: ' + sign + Math.abs(diff).toLocaleString() + ' (' + sign + Math.abs(pct) + '%)');
                                        }
                                        return lines;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                ticks: {
                                    callback: function(value) {
                                        return value.toLocaleString();
                                    },
                                    color: '#888'
                                },
                                grid: { color: 'rgba(255,255,255,0.05)' }
                            },
                            x: {
                                ticks: { color: '#888', maxTicksLimit: 7 },
                                grid: { display: false }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index',
                        }
                    }
                });'''

replacement = '''                // --- 1. Line Chart ---
                const trendCtx = document.getElementById('assetLineChart').getContext('2d');
                trendChartObj = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: {{ data.chart_dates | tojson }},
                        datasets: {{ data.chart_datasets | tojson }}
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { 
                            legend: { 
                                display: true,
                                position: 'top',
                                labels: { color: '#ddd', boxWidth: 12 }
                            },
                            tooltip: {
                                displayColors: true,
                                callbacks: {
                                    label: function(context) {
                                        let val = context.raw;
                                        return context.dataset.label + ': ' + val.toLocaleString() + '원';
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                stacked: true,
                                ticks: {
                                    callback: function(value) {
                                        return value.toLocaleString();
                                    },
                                    color: '#888'
                                },
                                grid: { color: 'rgba(255,255,255,0.05)' }
                            },
                            x: {
                                ticks: { color: '#888', maxTicksLimit: 7 },
                                grid: { display: false }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index',
                        }
                    }
                });'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
