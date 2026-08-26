import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace inline onclick
target_onclick = '''<div class="total-summary" onclick="document.body.classList.toggle('reveal-privacy')">'''
replace_onclick = '''<div class="total-summary" onclick="togglePrivacy()">'''
content = content.replace(target_onclick, replace_onclick)

# We need to render the tickers that are currently displayed to JS so we can fetch them.
# The tickers are rendered in the 'By Ticker' tab: data.ticker_summary.
# We also have assets listed in the 'By Account' tab: data.detailed_list.
# It's easier to just pass all tickers from data.ticker_summary to JS.
js_script = '''
            <script>
                let livePricesFetched = false;
                
                async function fetchLivePrices() {
                    if (livePricesFetched) return;
                    
                    const tickers = [
                        {% for tk in data.ticker_summary %}
                            "{{ tk.ticker|safe }}"{% if not loop.last %},{% endif %}
                        {% endfor %}
                    ];
                    
                    if (tickers.length === 0) return;
                    
                    // Show small indicator
                    const indicator = document.createElement('div');
                    indicator.id = 'livePriceIndicator';
                    indicator.innerHTML = '🔄 실시간 시세 불러오는 중...';
                    indicator.style.cssText = 'position:fixed; bottom:20px; right:20px; background:rgba(0,0,0,0.7); color:#fff; padding:10px 15px; border-radius:20px; font-size:0.85rem; z-index:9999;';
                    document.body.appendChild(indicator);
                    
                    try {
                        const response = await fetch("{{ url_for('infinite.api_live_prices') }}", {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ tickers: tickers })
                        });
                        const livePrices = await response.json();
                        
                        if (Object.keys(livePrices).length > 0) {
                            applyLivePrices(livePrices);
                        }
                        livePricesFetched = true;
                        indicator.innerHTML = '✅ 실시간 시세 반영됨';
                        setTimeout(() => indicator.remove(), 2000);
                    } catch (e) {
                        console.error('Failed to fetch live prices', e);
                        indicator.remove();
                    }
                }
                
                function togglePrivacy() {
                    document.body.classList.toggle('reveal-privacy');
                    if (document.body.classList.contains('reveal-privacy')) {
                        fetchLivePrices();
                    }
                }
                
                function applyLivePrices(livePrices) {
                    let totalEvaluationDiff = 0;
                    
                    // Update the DOM elements directly
                    // We need to find elements by ticker name.
                    // The asset lists (both Account view and Ticker view) have the ticker name in .asset-name
                    document.querySelectorAll('.asset-item').forEach(item => {
                        const nameEl = item.querySelector('.asset-name');
                        if (!nameEl) return;
                        
                        let ticker = nameEl.innerText.trim();
                        // For Account view, the ticker name is often split or formatted.
                        // Wait, in account view, it's just the ticker.
                        if (livePrices[ticker]) {
                            const livePrice = livePrices[ticker];
                            const qtyEl = item.querySelector('.asset-qty');
                            if (!qtyEl) return;
                            
                            // Extract quantity (e.g. "1,000주")
                            let qtyStr = qtyEl.innerText.replace(/[^0-9.-]/g, '');
                            let qty = parseFloat(qtyStr);
                            if (isNaN(qty)) return;
                            
                            let oldEvalStr = item.querySelector('.asset-value').innerText.replace(/[^0-9.-]/g, '');
                            let oldEval = parseFloat(oldEvalStr);
                            
                            let newEval = livePrice * qty;
                            let evalDiff = newEval - oldEval;
                            totalEvaluationDiff += evalDiff;
                            
                            // Update UI for this item
                            item.querySelector('.asset-value').innerText = newEval.toLocaleString() + '원';
                            
                            // Profit calculation requires finding the total_investment.
                            // old_profit = oldEval - total_invest => total_invest = oldEval - old_profit
                            let profitEl = item.querySelector('.asset-profit');
                            let oldProfitStr = profitEl.innerText.split('원')[0].replace(/[^0-9.-]/g, '');
                            let oldProfit = parseFloat(oldProfitStr);
                            
                            let totalInvest = oldEval - oldProfit;
                            let newProfit = newEval - totalInvest;
                            let newProfitPct = totalInvest > 0 ? (newProfit / totalInvest * 100) : 0;
                            
                            profitEl.innerText = (newProfit > 0 ? '+' : '') + newProfit.toLocaleString() + '원 (' + (newProfitPct > 0 ? '+' : '') + newProfitPct.toFixed(2) + '%)';
                            
                            // Update color class
                            profitEl.classList.remove('up', 'down');
                            if (newProfit > 0) profitEl.classList.add('up');
                            else if (newProfit < 0) profitEl.classList.add('down');
                        }
                    });
                    
                    // Update Top Summary
                    if (totalEvaluationDiff !== 0) {
                        const totalEl = document.querySelector('.total-summary .amount');
                        let oldTotal = parseFloat(totalEl.innerText.replace(/[^0-9.-]/g, ''));
                        let newTotal = oldTotal + totalEvaluationDiff;
                        totalEl.innerText = newTotal.toLocaleString() + '원';
                        
                        // Update Top Profit
                        const topProfitEl = document.querySelector('.total-summary > div:nth-child(3)');
                        let oldTopProfitStr = topProfitEl.innerText.split('원')[0].replace(/[^0-9.-]/g, '');
                        let oldTopProfit = parseFloat(oldTopProfitStr);
                        
                        let topInvest = oldTotal - oldTopProfit;
                        let newTopProfit = newTotal - topInvest;
                        let newTopProfitPct = topInvest > 0 ? (newTopProfit / topInvest * 100) : 0;
                        
                        topProfitEl.innerText = (newTopProfit > 0 ? '+' : '') + newTopProfit.toLocaleString() + '원 (' + (newTopProfitPct > 0 ? '+' : '') + newTopProfitPct.toFixed(2) + '%)';
                        topProfitEl.classList.remove('up', 'down');
                        if (newTopProfit > 0) topProfitEl.classList.add('up');
                        else if (newTopProfit < 0) topProfitEl.classList.add('down');
                        
                        // Note: Daily change (change_1d) also shifts by totalEvaluationDiff
                        const changeEl = document.querySelector('.total-summary .change');
                        let oldChangeStr = changeEl.innerText.replace(/[^0-9.-]/g, '');
                        let oldChange = parseFloat(oldChangeStr);
                        if (changeEl.innerText.includes('내렸어요')) oldChange = -oldChange;
                        let newChange = oldChange + totalEvaluationDiff;
                        
                        changeEl.innerText = '어제보다 ' + Math.abs(newChange).toLocaleString() + '원 ' + (newChange > 0 ? '올랐어요' : (newChange < 0 ? '내렸어요' : '같아요'));
                        changeEl.classList.remove('up', 'down');
                        if (newChange > 0) changeEl.classList.add('up');
                        else if (newChange < 0) changeEl.classList.add('down');
                    }
                }
            </script>
'''

# Find the end of body to insert script
target_body = '''</body>'''
if target_onclick in content:
    content = content.replace(target_body, js_script + "\n</body>")
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("UI updated.")
else:
    print("onclick not found")
