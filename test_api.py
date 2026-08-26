import requests

code = "005930" # Samsung Elec
url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
res = requests.get(url)
data = res.json()
if data['resultCode'] == 'success':
    item = data['result']['areas'][0]['datas'][0]
    print(item)
