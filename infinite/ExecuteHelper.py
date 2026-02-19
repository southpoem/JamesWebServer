import ctypes


def run_as_admin(bat_path):
    # 관리자 권한으로 실행하는 함수
    params = f'"{bat_path}"'
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 1)
        print("관리자 권한으로 실행했습니다.")
    except Exception as e:
        print(f"실패했습니다: {e}")