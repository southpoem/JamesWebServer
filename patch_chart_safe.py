with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                          labels: {{ data.chart_dates | tojson }},
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
                          }]'''

replacement = '''                          labels: {{ data.chart_dates | tojson }},
                          datasets: {{ data.chart_datasets | tojson }}'''

content = content.replace(target, replacement)

scales_target = '''                          plugins: { legend: { display: false } },
                          scales: {
                              x: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#aaa' } },
                              y: { 
                                  grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                  ticks: { 
                                      color: '#aaa',
                                      callback: function(value) { return (value / 10000).toLocaleString() + '만'; }
                                  }
                              }
                          }'''

scales_replacement = '''                          plugins: { 
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
                          }'''
content = content.replace(scales_target, scales_replacement)

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Safely replaced chart variables!")
