import json
import os

import Constant


def load_settings():
    setting_file = os.path.join(Constant.DATA_FOLDER_PATH, Constant.SETTINGS_PATH)
    if os.path.exists(setting_file):
        with open(setting_file, 'r') as f:
            return json.load(f)
    else:
        return {}


def get_current_market():
    data = load_settings()
    if "selected_market" in data:
        current_market_data = data["selected_market"]
    else:
        current_market_data = "G"

    return current_market_data


def save_or_toggle_setting():
    setting_file = os.path.join(Constant.DATA_FOLDER_PATH, Constant.SETTINGS_PATH)

    if os.path.exists(setting_file):
        # 파일이 있으면 읽기
        with open(setting_file, 'r') as f:
            setting = json.load(f)

        # selected_market 값 토글 (Y -> G, G -> Y)
        current_value = setting.get('selected_market', 'G')
        if current_value == 'Y':
            setting['selected_market'] = 'G'
        else:
            setting['selected_market'] = 'Y'

        # 저장
        with open(setting_file, 'w') as f:
            json.dump(setting, f, indent=4)

        print(f"설정 파일 존재: selected_market을 '{current_value}' -> '{setting['selected_market']}'로 변경했습니다.")

    else:
        # 파일이 없으면 생성
        setting = {
            "selected_market": "G"
        }
        with open(setting_file, 'w') as f:
            json.dump(setting, f, indent=4)

        print("설정 파일 없음: 새로 만들고 selected_market을 'G'로 설정했습니다.")
