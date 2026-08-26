import re

with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                function applyLivePrices(livePrices) {
                    let totalEvaluationDiff = 0;
                    
                    document.querySelectorAll('.asset-item').forEach(item => {
                        const nameEl = item.querySelector('.asset-name');
                        if (!nameEl) return;
                        
                        let ticker = nameEl.innerText.trim();
                        if (livePrices[ticker]) {
                            const livePrice = livePrices[ticker];
                            const qtyEl = item.querySelector('.asset-qty');
                            if (!qtyEl) return;
                            
                            let qtyStr = qtyEl.innerText.replace(/[^0-9.-]/g, '');
                            let qty = parseFloat(qtyStr);
                            if (isNaN(qty)) return;
                            
                            let oldEvalStr = item.querySelector('.asset-value').innerText.replace(/[^0-9.-]/g, '');
                            let oldEval = parseFloat(oldEvalStr);
                            
                            let newEval = livePrice * qty;
                            let evalDiff = newEval - oldEval;
                            
                            // To prevent double counting in UI if the same asset is rendered multiple times (e.g., account vs ticker tab),
                            // actually, they are rendered multiple times in DOM!
                            // So totalEvaluationDiff shouldn't just be accumulated over ALL .asset-item elements!
                            // We only accumulate it once per unique ticker!
                            
                            // Wait, .asset-item exists in both "byAccount" and "byTicker" tabs.
                            // If we iterate all of them, evalDiff is applied to the UI correctly for both,
                            // but we should only sum evalDiff for the top summary ONCE per ticker or ONCE per account.
                        }
                    });
                }'''

replacement = '''                function applyLivePrices(livePrices) {
                    let totalEvaluationDiff = 0;
                    let processedTickers = new Set();
                    
                    document.querySelectorAll('.asset-item').forEach(item => {
                        const nameEl = item.querySelector('.asset-name');
                        if (!nameEl) return;
                        
                        let ticker = nameEl.innerText.trim();
                        if (livePrices[ticker]) {
                            const livePrice = livePrices[ticker];
                            const qtyEl = item.querySelector('.asset-qty');
                            if (!qtyEl) return;
                            
                            let qtyStr = qtyEl.innerText.replace(/[^0-9.-]/g, '');
                            let qty = parseFloat(qtyStr);
                            if (isNaN(qty)) return;
                            
                            let oldEvalStr = item.querySelector('.asset-value').innerText.replace(/[^0-9.-]/g, '');
                            let oldEval = parseFloat(oldEvalStr);
                            
                            let newEval = livePrice * qty;
                            let evalDiff = newEval - oldEval;
                            
                            // We might encounter the same asset multiple times if it's in multiple accounts.
                            // The easiest way to get total change is to sum evalDiff from 'byTicker' tab only.
                            // Let's identify if it's in the byTicker tab.
                            const inByTicker = item.closest('#byTicker') !== null;
                            if (inByTicker) {
                                totalEvaluationDiff += evalDiff;
                            }
                            
                            // Update UI for this item
                            item.querySelector('.asset-value').innerText = newEval.toLocaleString() + '원';
                            
                            let profitEl = item.querySelector('.asset-profit');
                            let oldProfitStr = profitEl.innerText.split('원')[0].replace(/[^0-9.-]/g, '');
                            let oldProfit = parseFloat(oldProfitStr);
                            if (profitEl.innerText.includes('-') && oldProfit > 0 && profitEl.classList.contains('down')) {
                                oldProfit = -oldProfit; // parse negative sign properly if needed
                            }
                            // Actually it's better to just recalculate from investment.
                            let totalInvest = oldEval - oldProfit;
                            let newProfit = newEval - totalInvest;
                            let newProfitPct = totalInvest > 0 ? (newProfit / totalInvest * 100) : 0;
                            
                            profitEl.innerText = (newProfit > 0 ? '+' : '') + newProfit.toLocaleString() + '원 (' + (newProfitPct > 0 ? '+' : '') + newProfitPct.toFixed(2) + '%)';
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
                        
                        const topProfitEl = document.querySelector('.total-summary > div:nth-child(3)');
                        let oldTopProfitStr = topProfitEl.innerText.split('원')[0].replace(/[^0-9.-]/g, '');
                        let oldTopProfit = parseFloat(oldTopProfitStr);
                        if (topProfitEl.innerText.includes('-') && oldTopProfit > 0 && topProfitEl.classList.contains('down')) {
                             oldTopProfit = -oldTopProfit;
                        }
                        
                        let topInvest = oldTotal - oldTopProfit;
                        let newTopProfit = newTotal - topInvest;
                        let newTopProfitPct = topInvest > 0 ? (newTopProfit / topInvest * 100) : 0;
                        
                        topProfitEl.innerText = (newTopProfit > 0 ? '+' : '') + newTopProfit.toLocaleString() + '원 (' + (newTopProfitPct > 0 ? '+' : '') + newTopProfitPct.toFixed(2) + '%)';
                        topProfitEl.classList.remove('up', 'down');
                        if (newTopProfit > 0) topProfitEl.classList.add('up');
                        else if (newTopProfit < 0) topProfitEl.classList.add('down');
                        
                        const changeEl = document.querySelector('.total-summary .change');
                        let oldChangeStr = changeEl.innerText.replace(/[^0-9.-]/g, '');
                        let oldChange = parseFloat(oldChangeStr);
                        if (changeEl.innerText.includes('내렸어요')) oldChange = -oldChange;
                        let newChange = oldChange + totalEvaluationDiff;
                        
                        changeEl.innerText = '어제보다 ' + Math.abs(newChange).toLocaleString() + '원 ' + (newChange > 0 ? '올랐어요' : (newChange < 0 ? '내렸어요' : '같아요'));
                        changeEl.classList.remove('up', 'down');
                        if (newChange > 0) changeEl.classList.add('up');
                        else if (newChange < 0) changeEl.classList.add('down');
                        
                        // Update '전체 주식 합산' if present
                        const tickerTopTotalEl = document.querySelector('#byTicker .account-total');
                        if (tickerTopTotalEl) {
                            let oldTTopStr = tickerTopTotalEl.innerText.replace(/[^0-9.-]/g, '');
                            let oldTTop = parseFloat(oldTTopStr);
                            let newTTop = oldTTop + totalEvaluationDiff;
                            tickerTopTotalEl.innerText = newTTop.toLocaleString() + '원';
                            
                            const tickerTopProfitEl = document.querySelector('#byTicker .asset-profit');
                            if (tickerTopProfitEl) {
                                let oldTPStr = tickerTopProfitEl.innerText.split('원')[0].replace(/[^0-9.-]/g, '');
                                let oldTP = parseFloat(oldTPStr);
                                if (tickerTopProfitEl.innerText.includes('-') && oldTP > 0 && tickerTopProfitEl.classList.contains('down')) oldTP = -oldTP;
                                
                                let tInvest = oldTTop - oldTP;
                                let newTP = newTTop - tInvest;
                                let newTPct = tInvest > 0 ? (newTP / tInvest * 100) : 0;
                                
                                tickerTopProfitEl.innerText = (newTP > 0 ? '+' : '') + newTP.toLocaleString() + '원 (' + (newTPct > 0 ? '+' : '') + newTPct.toFixed(2) + '%)';
                                tickerTopProfitEl.classList.remove('up', 'down');
                                if (newTP > 0) tickerTopProfitEl.classList.add('up');
                                else if (newTP < 0) tickerTopProfitEl.classList.add('down');
                            }
                        }
                    }
                }'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'C:\PycharmProjects\JamesWebServer\templates\infinite_assets.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("UI updated.")
else:
    print("Target not found")
