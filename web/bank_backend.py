import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
import os
from datetime import datetime


class MyBankScraper:
    # 1. target_currencies 인자 추가 (기본값 설정 가능)
    def __init__(self, target_currencies=["USD", "JPY"]):
        self.base_url = "https://www.mibank.me/exchange/bank/index.php"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # ★ 은행 코드와 이름 하드코딩 매핑
        self.bank_mapping = {
            "005": "하나",
            "004": "국민",
            "020": "우리",
            "088": "신한"
        }
        # 매핑된 딕셔너리의 키값들을 수집 대상 코드로 사용
        self.bank_codes = list(self.bank_mapping.keys())

        # 현재 스크립트 위치에 파일 저장
        self.output_file = "exchange_rates.json"

        # 대문자로 변환하여 저장 (예: ['usd', 'jpy'] -> ['USD', 'JPY'])
        self.target_currencies = [c.upper() for c in target_currencies]

    def parse_page(self, search_code):
        params = {"search_code": search_code}
        try:
            print(f">>> [{search_code}] 데이터 수집 시작... (대상: {self.target_currencies})")
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 업데이트 시각
            update_tag = soup.select_one("h5.update")
            update_time = "Unknown"
            if update_tag:
                match = re.search(r'(\d{4}\.\d{2}\.\d{2}\s\d{2}:\d{2})', update_tag.get_text())
                if match: update_time = match.group(1)

            # ★ 매핑된 딕셔너리에서 은행 이름 가져오기 (없으면 Bank_코드)
            bank_name = self.bank_mapping.get(search_code, f"Bank_{search_code}")

            rates = []
            rows = soup.select("table.exchange_table tbody tr")

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 9: continue

                img_tag = cols[0].find("img")
                if not img_tag: continue
                currency_code = img_tag["src"].split("/")[-1].replace(".png", "").upper()

                # 2. ★ 핵심 필터링: 타겟 통화가 아니면 건너뜀 (Skip)
                if currency_code not in self.target_currencies:
                    continue

                def clean_float(text):
                    cleaned = re.sub(r'[^0-9.]', '', text)
                    return float(cleaned) if cleaned else 0.0

                rates.append({
                    "currency": currency_code,
                    "base_rate": clean_float(cols[8].get_text(strip=True)),
                    "remittance_send": clean_float(cols[6].get_text(strip=True)),
                    "remittance_fee_rate": cols[7].get_text(strip=True)
                })

            return {
                "bank_code": search_code,
                "bank_name": bank_name,
                "update_time": update_time,
                "rates": rates
            }

        except Exception as e:
            print(f"!!! [{search_code}] 파싱 오류: {e}")
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
            print(f"### [{data['bank_name']}] JSON 저장 완료 (대상 통화만)")
        except Exception as e:
            print(f"JSON 저장 실패: {e}")

    def run(self):
        while True:
            for code in self.bank_codes:
                result = self.parse_page(code)
                if result:
                    self.save_to_json(result)

                wait = random.uniform(5, 8)
                time.sleep(wait)

            print("\n[Cycle Completed] 60초 대기...\n")
            time.sleep(5)


if __name__ == "__main__":
    # ★ 여기서 원하는 통화만 리스트 형태로 전달하시면 됩니다!
    scraper = MyBankScraper(target_currencies=["USD", "JPY"])
    scraper.run()