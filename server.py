import os
import json
import time

from flask import Flask, jsonify, Response
from flask_cors import CORS


# =========================================================
# Flask 기본 설정
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# 파일 경로
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATUS_FILE = os.path.join(
    BASE_DIR,
    "status.json"
)

LATEST_FRAME_FILE = os.path.join(
    BASE_DIR,
    "latest_frame.jpg"
)


# =========================================================
# 서버 확인
# =========================================================

@app.route("/")
def home():
    return "Smart CCTV Server is running!"


# =========================================================
# CCTV 상태 API
# =========================================================

@app.route("/api/status")
def status():

    if not os.path.exists(STATUS_FILE):

        return jsonify({
            "cameraId": None,
            "cameraName": None,
            "location": None,
            "personCount": 0,
            "danger": False
        })

    try:

        with open(
            STATUS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            current_status = json.load(f)

        return jsonify(current_status)

    except (json.JSONDecodeError, OSError):

        return jsonify({
            "cameraId": None,
            "cameraName": None,
            "location": None,
            "personCount": 0,
            "danger": False
        })


# =========================================================
# JPEG가 정상적으로 완성됐는지 확인
# =========================================================

def is_valid_jpeg(data):

    if not data:
        return False

    if len(data) < 1000:
        return False

    # JPEG 시작 바이트
    if not data.startswith(b"\xff\xd8"):
        return False

    # JPEG 종료 바이트
    if not data.endswith(b"\xff\xd9"):
        return False

    return True


# =========================================================
# CCTV 영상 생성
# =========================================================

def generate_video():

    # 마지막으로 정상적으로 읽었던 화면을 보관
    last_good_frame = None

    while True:

        if not os.path.exists(LATEST_FRAME_FILE):

            time.sleep(0.03)

            continue


        try:

            with open(
                LATEST_FRAME_FILE,
                "rb"
            ) as f:

                frame_data = f.read()


            # 완성된 정상 JPEG일 때만 갱신
            if is_valid_jpeg(frame_data):

                last_good_frame = frame_data


            # 파일 쓰는 중이라 깨진 프레임이면
            # 검은 화면을 보내지 않고 이전 정상 화면 사용
            if last_good_frame is None:

                time.sleep(0.03)

                continue


            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Cache-Control: no-cache\r\n"
                b"Pragma: no-cache\r\n\r\n"
                + last_good_frame
                + b"\r\n"
            )


        except (OSError, PermissionError):

            # 파일을 쓰는 순간 잠겼다면
            # 그냥 이번 회차를 건너뜀
            pass


        time.sleep(0.03)


# =========================================================
# CCTV 영상 주소
# =========================================================

@app.route("/video_feed")
def video_feed():

    return Response(
        generate_video(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


# =========================================================
# 서버 실행
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True
    )