import ctypes

from flask import Flask, jsonify, send_file, render_template, request, redirect, url_for, session
# 메인 페이지

import os

import Constant
import Secret
from auth.Login import login_required

from infinite import Settings
from infinite.InfiniteServer import infinite_bp

app = Flask(__name__)
app.secret_key = 'thisismyworld'  # 꼭 있어야 세션 작동함 (아무 문자열이나)
app.register_blueprint(infinite_bp)

# 이미지 저장 디렉터리 설정
IMAGE_DIRECTORY = "images"
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)


# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 간단한 사용자 인증 (하드코딩 예시)
        if username == Secret.id and password == Secret.password:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return "Login Failed. Please try again."

    return render_template('login.html')


# 메인 페이지
@app.route('/')
@login_required
def index():
    settings = Settings.load_settings()  # settings.json 불러오기
    return render_template('index.html', settings=settings)


# 스크립트1 실행
@app.route('/run_change_base_usdt', methods=['POST'])
@login_required
def run_script1():
    Settings.save_or_toggle_setting()
    return redirect(url_for('index'))


# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/btcnusdt.html")
def btcnusdt():
    # 샘플 이미지를 반환 (디렉터리에서 파일 선택)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, Constant.chart_name)
    print(f"image_path = {image_path}")
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    return jsonify({"status": "error", "message": "Image not found"}), 404


# 샘플 이미지 업로드 (테스트용)
@app.route('/upload-picture', methods=['POST'])
def upload_picture():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    file_path = os.path.join(IMAGE_DIRECTORY, file.filename)
    file.save(file_path)
    return jsonify({"status": "success", "message": f"File {file.filename} uploaded!"})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1508)
