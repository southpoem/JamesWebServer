import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
import os
from datetime import datetime


class MyBankScraper:
    def __init__(self, target_currencies=["USD", "JPY"]):
        # ★ [주소 변경] 신규 도메인으로 교체
        self.base_url = "https://exchange.mibank.me/bank"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }

        # 은행 코드는 그대로 유지 (마이뱅크 표준 코드)
        self.bank_mapping = {
            "005": "하나",
            "004": "국민",
            "020": "우리",
            "088": "신한"
        }
        self.bank_codes = list(self.bank_mapping.keys())
        self.output_file = "exchange_rates.json"
        self.target_currencies = [c.upper() for c in target_currencies]

    def parse_page(self, search_code):
        # ★ [파라미터 변경] search_code -> bank_cd 로 교체
        params = {"bank_cd": search_code}
        try:
            print(f">>> [{self.bank_mapping.get(search_code)}] ({search_code}) 데이터 수집 시도...")
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. 업데이트 시각 파싱 (span.date)
            update_time = "Unknown"
            update_tag = soup.select_one("span.date")
            if update_tag:
                match = re.search(r'(\d{4}[.-]\d{2}[.-]\d{2}\s\d{2}:\d{2})', update_tag.get_text())
                if match:
                    update_time = match.group(1).replace('-', '.')

            bank_name = self.bank_mapping.get(search_code, f"Bank_{search_code}")

            # 2. 테이블 탐색 (table.main_table.content)
            target_table = soup.select_one("table.main_table.content")

            if not target_table:
                print(f"!!! [{bank_name}] 테이블을 찾지 못했습니다. URL을 확인해 주세요.")
                return None

            rates = []
            rows = target_table.find_all("tr")

            for row in rows:
                cols = row.find_all(["td", "th"])
                if len(cols) < 5: continue

                row_text = row.get_text(separator=' ', strip=True).upper()
                if "매매기준율" in row_text or "통화" in row_text:
                    continue

                currency_code = None
                for tgt in self.target_currencies:
                    if tgt in row_text:
                        currency_code = tgt
                        break

                if not currency_code:
                    img_tag = row.find("img")
                    if img_tag and img_tag.get("src"):
                        for tgt in self.target_currencies:
                            if tgt.lower() in img_tag["src"].lower():
                                currency_code = tgt
                                break

                if not currency_code:
                    continue

                def clean_float(text):
                    cleaned = re.sub(r'[^0-9.]', '', text)
                    return float(cleaned) if cleaned else 0.0

                try:
                    # 행/열 선택 로직 (역순 인덱싱)
                    base_rate = clean_float(cols[-1].get_text(strip=True))
                    remittance_send = clean_float(cols[-3].get_text(strip=True))
                    remittance_fee_rate = cols[-2].get_text(strip=True)
                except IndexError:
                    continue

                rates.append({
                    "currency": currency_code,
                    "base_rate": base_rate,
                    "remittance_send": remittance_send,
                    "remittance_fee_rate": remittance_fee_rate
                })

            if rates:
                return {
                    "bank_code": search_code,
                    "bank_name": bank_name,
                    "update_time": update_time,
                    "rates": rates
                }
            return None

        except Exception as e:
            print(f"!!! [{search_code}] 통신/파싱 오류: {e}")
            return None

    def save_to_json(self, data):
        current_db = {}
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content: current_db = json.loads(content)
            except Exception:
                pass

        current_db[data['bank_code']] = data
        current_db['system_last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(current_db, f, indent=4, ensure_ascii=False)
            print(f"✅ [{data['bank_name']}] 고시 환율 업데이트 완료 ({data['update_time']})")
        except Exception as e:
            print(f"JSON 저장 실패: {e}")

    def run(self):
        print("=== 🏦 마이뱅크 실시간 환율 스크래퍼 가동 (신규 URL 모드) ===")
        while True:
            for code in self.bank_codes:
                result = self.parse_page(code)
                if result:
                    self.save_to_json(result)

                # 사이트 부하 방지를 위한 딜레이
                wait = random.uniform(3, 5)
                time.sleep(wait)

            print(f"\n[대기] 한 사이클 완료. 60초 후 다시 수집합니다. ({datetime.now().strftime('%H:%M:%S')})\n")
            time.sleep(60)


if __name__ == "__main__":
    scraper = MyBankScraper(target_currencies=["USD", "JPY"])
    scraper.run()