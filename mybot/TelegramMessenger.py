import telegram


async def send_dollar_message(message='', token='8162163186:AAHH7qyfuUh5mVbNOVBiSIG2vasQdfW2wZA',
                              chat_id='@dollar_ping'):
    if len(message) >= 4096:
        message = message[:4096]
    bot = telegram.Bot(token=token)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        # print("✅ 텔레그램 초기 메시지 전송 시도 완료")
    except Exception as e:
        print(f"❌ 텔레그램 모듈 에러: {e}")
