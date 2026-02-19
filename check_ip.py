import requests

try:
    # 내 공인 IP 확인 사이트 호출
    response = requests.get('https://api.ipify.org?format=json')
    my_ip = response.json()['ip']
    print("========================================")
    print(f"현재 봇이 사용 중인 공인 IP: {my_ip}")
    print("========================================")
    print("이 IP가 빗썸 API 관리에 등록되어 있는지 확인하세요.")
except Exception as e:
    print(f"IP 확인 실패: {e}")