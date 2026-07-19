import os
import sqlite3
import pandas as pd
from datetime import datetime
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# [설정 항목] 필요에 따라 값을 변경하세요.
# ==========================================
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "investment.db"))
SPREADSHEET_ID = "1YrQ_d80STbxPOasvboqeRNvIN1gJNBw6hRBMFIx77Y8"  # 구글 스프레드시트 ID 입력

# 캡처할 시트명과 셀 주소 리스트 (예: "Sheet1!A1", "가격현황!B3")
CELLS_TO_SNAPSHOT = [
    "Sheet1!A1",
    "Sheet1!B2"
]

# 권한 인증 방식: "public" (링크공유 방식) 또는 "api" (서비스 계정 JSON 방식)
AUTH_METHOD = "public" 

# 서비스 계정 API 사용 시 JSON 키 파일 경로
SERVICE_ACCOUNT_FILE = "google_creds.json" 
# ==========================================

def get_sheet_cell_public(spreadsheet_id, range_name):
    """
    공유 링크가 열려있는(뷰어 권한) 구글 시트에서 특정 셀 값을 읽어옵니다.
    """
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&range={range_name}"
    # pandas를 이용하여 단일 셀 데이터 가져오기
    df = pd.read_csv(url, header=None)
    if df.empty:
        raise ValueError("가져온 데이터가 비어 있습니다.")
    return df.iloc[0, 0]

def get_sheet_cell_api(spreadsheet_id, range_name):
    """
    비공개 구글 시트에서 Google Sheets API(gspread)를 이용해 값을 읽어옵니다.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        raise ImportError("Google API를 사용하려면 'gspread google-auth' 패키지 설치가 필요합니다.")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"인증용 서비스 계정 키 파일({SERVICE_ACCOUNT_FILE})이 없습니다.")

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id)

    # range_name 파싱 (예: "Sheet1!A1" -> 시트명="Sheet1", 셀="A1")
    if "!" in range_name:
        sheet_name, cell_addr = range_name.split("!", 1)
        worksheet = sheet.worksheet(sheet_name)
    else:
        worksheet = sheet.get_worksheet(0)
        cell_addr = range_name

    return worksheet.acell(cell_addr).value

def init_db():
    """
    sqlite3 데이터베이스 테이블을 초기화합니다.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sheets_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            spreadsheet_id TEXT,
            cell_address TEXT,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()

def take_snapshot():
    """
    구글 시트의 지정된 셀 값을 읽어 데이터베이스에 저장합니다.
    """
    init_db()
    
    if SPREADSHEET_ID == "YOUR_SPREADSHEET_ID_HERE":
        logging.warning("기본 스프레드시트 ID가 설정되어 있습니다. 스냅샷 수집을 스킵합니다.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success_count = 0

    for cell in CELLS_TO_SNAPSHOT:
        try:
            if AUTH_METHOD == "public":
                val = get_sheet_cell_public(SPREADSHEET_ID, cell)
            elif AUTH_METHOD == "api":
                val = get_sheet_cell_api(SPREADSHEET_ID, cell)
            else:
                raise ValueError(f"지원하지 않는 인증 방식입니다: {AUTH_METHOD}")
            
            # DB 저장
            cursor.execute(
                "INSERT INTO sheets_snapshots (timestamp, spreadsheet_id, cell_address, value) VALUES (?, ?, ?, ?)",
                (now, SPREADSHEET_ID, cell, str(val))
            )
            logging.info(f"스냅샷 저장 성공 - [{cell}]: {val}")
            success_count += 1
        except Exception as e:
            logging.error(f"셀 데이터 [{cell}] 수집 실패: {e}")

    if success_count > 0:
        conn.commit()
        logging.info(f"총 {success_count}개 셀 가격 스냅샷 DB 반영 완료.")
    else:
        logging.warning("저장된 스냅샷 데이터가 없습니다.")

    conn.close()

if __name__ == "__main__":
    take_snapshot()
