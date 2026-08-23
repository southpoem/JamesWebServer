# -*- coding: utf-8 -*-
"""
텔레그램 채널 메시지 수집 및 Gemini AI 정기 요약 시스템
===================================================

[필수 의존성 라이브러리 설치]
pip install telethon apscheduler google-generativeai

[실행 전 설정]
1. 최초 실행 시 같은 폴더에 'telegram_settings.json' 템플릿 파일이 생성됩니다.
2. 해당 파일에 텔레그램 API ID, API HASH, Gemini API Key 및 요약할 대상 채널을 입력하십시오.
   - Telegram API ID/HASH 발급처: https://my.telegram.org
   - Gemini API Key 발급처: https://aistudio.google.com
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import google.generativeai as genai

# 설정 파일명
SETTINGS_FILE = "telegram_settings.json"
DB_FILE = "telegram_messages.db"

def load_settings():
    """설정 파일을 불러오거나 없으면 기본 템플릿 생성"""
    default_settings = {
        "telegram_api_id": 0,
        "telegram_api_hash": "YOUR_TELEGRAM_API_HASH",
        "gemini_api_key": "YOUR_GEMINI_API_KEY",
        "target_channel": "@target_channel_username",
        "summary_receiver": "@your_summary_channel_or_username",
        "summarize_interval_hours": 6
    }
    
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=4)
        print(f"[*] '{SETTINGS_FILE}' 템플릿 파일이 생성되었습니다. 설정을 변경한 뒤 다시 실행해 주세요.")
        return None
        
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[-] 설정 파일 로드 실패: {e}")
        return None

def init_db():
    """SQLite 데이터베이스 테이블 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_messages (
            message_id INTEGER PRIMARY KEY,
            channel_name TEXT,
            message_text TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_message(msg_id, channel, text):
    """메시지를 데이터베이스에 안전하게 저장"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO channel_messages VALUES (?, ?, ?, ?)",
            (msg_id, channel, text, datetime.now().isoformat())
        )
        conn.commit()
    except Exception as e:
        print(f"[-] DB 저장 오류: {e}")
    finally:
        conn.close()

async def summarize_and_send(settings, client):
    """지정된 시간 간격의 수집 메시지를 추출하여 Gemini API로 요약 후 전송"""
    interval_hours = settings.get("summarize_interval_hours", 6)
    target_channel = settings.get("target_channel")
    receiver = settings.get("summary_receiver")
    
    print(f"[*] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 정기 요약 배치 기동 (최근 {interval_hours}시간 대상)")
    
    # 요약 대상 시간 계산
    time_limit = (datetime.now() - timedelta(hours=interval_hours)).isoformat()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT message_text, created_at FROM channel_messages WHERE created_at >= ? ORDER BY created_at ASC",
        (time_limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("[*] 최근 시간대 수집된 신규 메시지가 없어 요약을 건너뜁니다.")
        return
        
    # 요약에 활용할 텍스트 빌드
    raw_texts = []
    for row in rows:
        # 타임스탬프에서 시:분만 추출
        try:
            dt = datetime.fromisoformat(row[1])
            time_str = dt.strftime("%H:%M")
        except:
            time_str = row[1][:16]
        raw_texts.append(f"[{time_str}] {row[0]}")
        
    combined_text = "\n---\n".join(raw_texts)
    
    # Gemini API 연동 요약
    try:
        genai.configure(api_key=settings["gemini_api_key"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "당신은 텔레그램 채널의 정보 유출 및 요약을 전문으로 하는 친절한 AI 비서입니다.\n"
            f"다음은 최근 K리그2 수원의 라이벌 채널 또는 유관 정보지에서 수집된 지난 {interval_hours}시간 동안의 원본 메시지 스트림입니다.\n"
            "이 메시지들을 분석하여 중요 주제별로 일목요연하게 묶고, "
            "각 주제의 핵심 줄거리와 실질적인 의미를 친절한 이모지를 사용해 한글로 일목요연하게 브리핑 요약문으로 만들어주세요.\n\n"
            f"[수집된 메시지 목록]\n{combined_text}"
        )
        
        response = model.generate_content(prompt)
        summary_result = response.text
        
        # 결과 메시지 제작
        header_text = (
            f"📊 **[정기 요약 브리핑]**\n"
            f"📅 기준 시간: {datetime.now().strftime('%m월 %d일 %H:%M')}\n"
            f"🎯 요약 범위: 최근 {interval_hours}시간 수집분 ({len(rows)}건)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        # 텔레그램 발송
        await client.send_message(receiver, header_text + summary_result)
        print("[+] 요약 브리핑 발송 완료!")
        
    except Exception as e:
        print(f"[-] 요약 생성 및 발송 중 예외 발생: {e}")

async def main():
    # 설정 파일 검증
    settings = load_settings()
    if not settings:
        return
        
    # 설정 유효성 검사
    if settings["telegram_api_id"] == 0 or settings["telegram_api_hash"] == "YOUR_TELEGRAM_API_HASH":
        print("[-] 'telegram_settings.json' 파일을 열어 실제 텔레그램 API ID와 API HASH를 입력해 주세요.")
        return
        
    # DB 세팅
    init_db()
    
    # 텔레그램 클라이언트 객체 초기화
    client = TelegramClient(
        'summarizer_session', 
        settings["telegram_api_id"], 
        settings["telegram_api_hash"]
    )
    
    # 수집 대상 채널 파싱
    target_chat = settings["target_channel"]
    
    # 실시간 메시지 핸들러 등록
    @client.on(events.NewMessage(chats=target_chat))
    async def handle_new_message(event):
        if event.raw_text:
            print(f"[+] 메시지 감지 [ID: {event.id}]: {event.raw_text[:30]}...")
            save_message(event.id, target_chat, event.raw_text)

    # 텔레그램 클라이언트 시작 (필요시 콘솔창에 휴대폰 인증번호 입력 진행)
    await client.start()
    print(f"[+] 텔레그램 계정 로그인 성공! 수집 대상 채널: {target_chat}")
    
    # 정기 요약 스케줄러 세팅
    scheduler = AsyncIOScheduler()
    # 설정된 주기(시간) 마다 실행하도록 스케줄 등록
    scheduler.add_job(
        summarize_and_send, 
        'interval', 
        hours=settings.get("summarize_interval_hours", 6),
        args=[settings, client]
    )
    scheduler.start()
    print(f"[+] 정기 요약 배치 스케줄 가동 완료 (주기: {settings.get('summarize_interval_hours', 6)}시간)")
    
    # 대기 작동 개시
    print("[*] 텔레그램 실시간 리스너가 작동 중입니다. 종료하려면 Ctrl+C를 누르세요.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] 프로그램이 사용자에 의해 종료되었습니다.")
