import ccxt
import requests
import sys
import os
import pprint

# === 1. key_config.py 불러오기 ===
print("\n🔍 [1] 설정 파일(key_config.py) 확인 중...")
try:
    import key_config

    print("   ✅ key_config.py 파일을 찾았습니다.")
except ImportError:
    print("   ❌ 오류: key_config.py 파일을 찾을 수 없습니다.")
    print("   -> test_api.py 파일이 key_config.py와 같은 폴더에 있는지 확인하세요.")
    sys.exit()

# === 2. 현재 서버의 공인 IP 확인 ===
print("\n🌐 [2] 현재 서버의 공인 IP 확인 중...")
try:
    response = requests.get('https://api.ipify.org?format=json', timeout=5)
    my_ip = response.json()['ip']
    print(f"   👉 현재 IP: {my_ip}")
    print("   ⚠️ 이 IP가 거래소 API 관리에 등록되어 있어야 합니다!")
except Exception as e:
    print(f"   ❌ IP 확인 실패: {e}")

# === 3. 빗썸 (Bithumb) 연결 테스트 ===
print("\n🟠 [3] 빗썸(Bithumb) 연결 테스트...")

if not key_config.BITHUMB_ACCESS or "여기에" in key_config.BITHUMB_ACCESS:
    print("   ⚠️ 빗썸 키가 설정되지 않았습니다.")
else:
    try:
        bithumb = ccxt.bithumb({
            'apiKey': key_config.BITHUMB_ACCESS,
            'secret': key_config.BITHUMB_SECRET,
        })
        # 잔고 조회 시도
        balance = bithumb.fetch_balance()
        krw = balance['KRW']['free']
        print("   ✅ 빗썸 연결 성공!")
        print(f"   💰 보유 KRW: {int(krw):,}원")

    except ccxt.AuthenticationError as e:
        print("   ❌ [인증 실패] 키가 틀렸거나, IP가 등록되지 않았습니다.")
        print(f"   -> 에러 메시지: {e}")
        print("   -> 1. IP가 등록되었는지 확인하세요.")
        print("   -> 2. Connect Key와 Secret Key가 반대로 들어가지 않았는지 확인하세요.")
    except Exception as e:
        print(f"   ❌ [기타 에러]: {e}")

# === 4. 업비트 (Upbit) 연결 테스트 ===
print("\n🟣 [4] 업비트(Upbit) 연결 테스트...")

if not key_config.UPBIT_ACCESS or "여기에" in key_config.UPBIT_ACCESS:
    print("   ⚠️ 업비트 키가 설정되지 않았습니다.")
else:
    try:
        upbit = ccxt.upbit({
            'apiKey': key_config.UPBIT_ACCESS,
            'secret': key_config.UPBIT_SECRET,
        })
        # 잔고 조회 시도
        balance = upbit.fetch_balance()
        krw = balance['KRW']['free']
        print("   ✅ 업비트 연결 성공!")
        print(f"   💰 보유 KRW: {int(krw):,}원")

    except ccxt.AuthenticationError as e:
        print("   ❌ [인증 실패] 키가 틀렸거나, IP가 등록되지 않았습니다.")
        print(f"   -> 에러 메시지: {e}")
    except Exception as e:
        print(f"   ❌ [기타 에러]: {e}")

print("\n🏁 테스트 종료\n")