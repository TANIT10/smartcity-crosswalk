
import os
import json
import time
import threading

import cv2
import numpy as np

from flask import Flask, jsonify, Response, request
from flask_cors import CORS

from vidgear.gears import CamGear
from ultralytics import YOLO


# =========================================================
# 기본 경로
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CAMERA_FILE = os.path.join(
    BASE_DIR,
    "cameras.json"
)

ROI_DIR = os.path.join(
    BASE_DIR,
    "roi"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "yolov8n.pt"
)


# =========================================================
# Flask
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# 웹에서 사용할 현재 상태
# =========================================================

current_status = {
    "cameraId": None,
    "cameraName": None,
    "location": None,
    "personCount": 0,
    "danger": False
}


# 가장 최근 YOLO 처리 프레임
latest_frame_bytes = None

# 웹에서 CCTV 변경 요청이 들어오면 저장
requested_camera_id = None


# 여러 스레드가 동시에 데이터를 만질 때 사용
status_lock = threading.Lock()
frame_lock = threading.Lock()


# =========================================================
# ROI 전역 변수
# =========================================================

pts = []
frame_copy = None


# =========================================================
# 상태 업데이트
# =========================================================

def update_status(
    camera_id,
    camera_name,
    camera_location,
    person_count
):

    global current_status

    new_status = {
        "cameraId": camera_id,
        "cameraName": camera_name,
        "location": camera_location,
        "personCount": person_count,
        "danger": person_count > 0
    }

    with status_lock:
        current_status = new_status


# =========================================================
# 최신 영상 메모리 저장
# =========================================================

def update_web_frame(frame):

    global latest_frame_bytes

    try:

        # OpenCV 확인 창은 1280x720을 유지하고,
        # 웹으로 보낼 영상만 조금 작게 만들어 전송 부담을 줄임
        web_frame = cv2.resize(
            frame,
            (960, 540)
        )

        success, encoded_frame = cv2.imencode(
            ".jpg",
            web_frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                65
            ]
        )

        if not success:
            return

        frame_bytes = encoded_frame.tobytes()

        with frame_lock:
            latest_frame_bytes = frame_bytes

    except Exception as e:

        print(
            f"[경고] 웹 영상 변환 실패: {e}"
        )


# =========================================================
# Flask 메인 주소
# =========================================================

@app.route("/")
def home():

    return "Smart CCTV Server is running!"


# =========================================================
# CCTV 상태 API
# =========================================================

@app.route("/api/status")
def api_status():

    with status_lock:
        data = dict(current_status)

    return jsonify(data)

# =========================================================
# 등록된 CCTV 목록 API
# =========================================================

@app.route("/api/cameras")
def api_cameras():

    cameras = load_cameras()

    return jsonify(cameras)

@app.route("/api/switch_camera", methods=["POST"])
def switch_camera():

    global requested_camera_id

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "요청 데이터가 없습니다."
        }), 400

    camera_id = data.get("cameraId")

    if not camera_id:
        return jsonify({
            "success": False,
            "message": "cameraId가 없습니다."
        }), 400

    requested_camera_id = camera_id

    return jsonify({
        "success": True,
        "cameraId": camera_id
    })


# =========================================================
# 웹 CCTV 영상 생성
# =========================================================

def generate_video():

    while True:

        with frame_lock:
            frame_data = latest_frame_bytes

        if frame_data is None:

            time.sleep(0.03)

            continue


        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Cache-Control: no-cache\r\n\r\n"
            + frame_data
            + b"\r\n"
        )


        time.sleep(0.05)


# =========================================================
# CCTV 영상 API
# =========================================================

@app.route("/video_feed")
def video_feed():

    return Response(
        generate_video(),
        mimetype=(
            "multipart/x-mixed-replace;"
            " boundary=frame"
        ),
        headers={
            "Cache-Control":
                "no-cache, no-store, must-revalidate",
            "Pragma":
                "no-cache",
            "Expires":
                "0"
        }
    )


# =========================================================
# Flask 서버 별도 스레드 실행
# =========================================================

def run_flask_server():

    print()
    print("======================================")
    print(" Flask Server")
    print("======================================")
    print("API   : http://127.0.0.1:5000/api/status")
    print("VIDEO : http://127.0.0.1:5000/video_feed")
    print("======================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )


# =========================================================
# CCTV 목록 불러오기
# =========================================================

def load_cameras():

    if not os.path.exists(CAMERA_FILE):

        print(
            "[오류] cameras.json 파일이 없습니다."
        )

        return []


    try:

        with open(
            CAMERA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            cameras = json.load(f)

        return cameras


    except (
        json.JSONDecodeError,
        OSError
    ) as e:

        print(
            f"[오류] cameras.json 읽기 실패: {e}"
        )

        return []


# =========================================================
# CCTV 선택
# =========================================================

def select_camera(cameras):

    print()
    print("======================================")
    print(" CCTV 목록")
    print("======================================")


    for index, camera in enumerate(
        cameras,
        start=1
    ):

        print(
            f"{index}. "
            f"{camera['name']} "
            f"({camera['location']})"
        )


    print("======================================")


    while True:

        try:

            choice = input(
                "실행할 CCTV 번호 입력: "
            )

            number = int(choice)


            if 1 <= number <= len(cameras):

                return cameras[
                    number - 1
                ]


            print(
                "[경고] 목록에 있는 번호를 입력해주세요."
            )


        except ValueError:

            print(
                "[경고] 숫자를 입력해주세요."
            )


# =========================================================
# ROI 클릭
# =========================================================

def draw_roi(
    event,
    x,
    y,
    flags,
    param
):

    global pts
    global frame_copy


    if event == cv2.EVENT_LBUTTONDOWN:

        pts.append(
            (x, y)
        )


        cv2.circle(
            frame_copy,
            (x, y),
            5,
            (0, 0, 255),
            -1
        )


        if len(pts) > 1:

            cv2.line(
                frame_copy,
                pts[-2],
                pts[-1],
                (0, 0, 255),
                2
            )


# =========================================================
# ROI 설정
# =========================================================

def setup_roi(
    frame,
    roi_file
):

    global pts
    global frame_copy


    pts = []

    frame_copy = frame.copy()


    window_name = "Setup ROI"


    cv2.namedWindow(
        window_name
    )


    cv2.setMouseCallback(
        window_name,
        draw_roi
    )


    print()
    print("======================================")
    print(" ROI 설정")
    print("======================================")
    print("마우스 왼쪽 클릭 : 점 찍기")
    print("Z : 마지막 점 취소")
    print("C : 모든 점 초기화")
    print("ENTER : ROI 저장")
    print("Q 또는 ESC : 취소")
    print("======================================")


    while True:

        display = frame_copy.copy()


        if len(pts) >= 3:

            temp_polygon = np.array(
                pts,
                np.int32
            )


            cv2.polylines(
                display,
                [temp_polygon],
                isClosed=True,
                color=(255, 0, 0),
                thickness=2
            )


        cv2.putText(
            display,
            "Click points | ENTER Save | Z Undo | C Clear | Q Exit",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2
        )


        cv2.imshow(
            window_name,
            display
        )


        key = (
            cv2.waitKey(20)
            & 0xFF
        )


        # ENTER
        if key == 13:

            if len(pts) < 3:

                print(
                    "[경고] 최소 3개의 점을 찍어주세요."
                )

                continue


            try:

                with open(
                    roi_file,
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        pts,
                        f
                    )


                print(
                    "[완료] ROI 좌표가 저장되었습니다."
                )


            except OSError as e:

                print(
                    f"[오류] ROI 저장 실패: {e}"
                )

                continue


            cv2.destroyWindow(
                window_name
            )


            return np.array(
                pts,
                np.int32
            )


        # Z
        elif key in (
            ord("z"),
            ord("Z")
        ):

            if len(pts) > 0:

                pts.pop()

                frame_copy = frame.copy()


                for i, point in enumerate(
                    pts
                ):

                    cv2.circle(
                        frame_copy,
                        point,
                        5,
                        (0, 0, 255),
                        -1
                    )


                    if i > 0:

                        cv2.line(
                            frame_copy,
                            pts[i - 1],
                            point,
                            (0, 0, 255),
                            2
                        )


        # C
        elif key in (
            ord("c"),
            ord("C")
        ):

            pts = []

            frame_copy = frame.copy()


        # Q / ESC
        elif key in (
            ord("q"),
            ord("Q"),
            27
        ):

            cv2.destroyWindow(
                window_name
            )

            return None


# =========================================================
# 프로그램 시작
# =========================================================

print()
print("======================================")
print(" Smart CCTV Crosswalk System")
print("======================================")


os.makedirs(
    ROI_DIR,
    exist_ok=True
)


# =========================================================
# CCTV 선택
# =========================================================

cameras = load_cameras()


if len(cameras) == 0:

    print(
        "[오류] 등록된 CCTV가 없습니다."
    )

    raise SystemExit


selected_camera = select_camera(
    cameras
)


camera_id = selected_camera[
    "id"
]

camera_name = selected_camera[
    "name"
]

camera_location = selected_camera[
    "location"
]

camera_url = selected_camera[
    "url"
]


ROI_FILE = os.path.join(
    ROI_DIR,
    f"{camera_id}.json"
)


print()
print("======================================")
print(
    f"선택된 CCTV : {camera_name}"
)
print(
    f"위치        : {camera_location}"
)
print(
    f"ID          : {camera_id}"
)
print("======================================")


# =========================================================
# CCTV 연결
# =========================================================

print()
print(
    "영상을 불러오는 중입니다. 잠시만 기다려주세요..."
)


stream = CamGear(
    source=camera_url,
    stream_mode=True,
    logging=True,
    STREAM_RESOLUTION="480p"
).start()


frame = stream.read()


if frame is None:

    print(
        "[오류] 영상을 불러오지 못했습니다."
    )

    stream.stop()

    raise SystemExit


# 화면 크기 통일
frame = cv2.resize(
    frame,
    (1280, 720)
)


# =========================================================
# ROI 불러오기
# =========================================================

roi_polygon = None


if os.path.exists(
    ROI_FILE
):

    print()
    print(
        "[안내] 이 CCTV의 기존 ROI 좌표를 발견했습니다."
    )
    print(
        "ENTER : 기존 ROI 사용"
    )
    print(
        "R : ROI 새로 설정"
    )
    print(
        "Q 또는 ESC : 종료"
    )


    try:

        with open(
            ROI_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            saved_pts = json.load(f)


        saved_polygon = np.array(
            saved_pts,
            np.int32
        )


    except (
        json.JSONDecodeError,
        OSError
    ):

        saved_polygon = None


    if saved_polygon is not None:

        preview = frame.copy()


        cv2.polylines(
            preview,
            [saved_polygon],
            isClosed=True,
            color=(255, 0, 0),
            thickness=2
        )


        selection_window = (
            "ROI Selection"
        )


        while True:

            display = preview.copy()


            cv2.putText(
                display,
                "ENTER Use Saved ROI | R Redraw ROI | Q Exit",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )


            cv2.imshow(
                selection_window,
                display
            )


            key = (
                cv2.waitKey(20)
                & 0xFF
            )


            if key == 13:

                roi_polygon = (
                    saved_polygon
                )

                cv2.destroyWindow(
                    selection_window
                )

                break


            elif key in (
                ord("r"),
                ord("R")
            ):

                cv2.destroyWindow(
                    selection_window
                )


                roi_polygon = setup_roi(
                    frame,
                    ROI_FILE
                )

                break


            elif key in (
                ord("q"),
                ord("Q"),
                27
            ):

                cv2.destroyWindow(
                    selection_window
                )

                stream.stop()

                cv2.destroyAllWindows()

                raise SystemExit


    else:

        roi_polygon = setup_roi(
            frame,
            ROI_FILE
        )


else:

    print()
    print(
        "[안내] 이 CCTV에는 저장된 ROI가 없습니다."
    )


    roi_polygon = setup_roi(
        frame,
        ROI_FILE
    )


if roi_polygon is None:

    stream.stop()

    cv2.destroyAllWindows()

    raise SystemExit


# =========================================================
# YOLO
# =========================================================

print()
print(
    "[안내] YOLO 모델을 불러옵니다."
)


model = YOLO(
    MODEL_FILE
)


print(
    "[완료] YOLO 모델 로드 완료"
)


# =========================================================
# Flask 서버 시작
# =========================================================

flask_thread = threading.Thread(
    target=run_flask_server,
    daemon=True
)

flask_thread.start()


# 초기 상태
update_status(
    camera_id,
    camera_name,
    camera_location,
    0
)


print()
print("======================================")
print(" 탐지를 시작합니다.")
print("======================================")
print("Q 또는 ESC : 종료")
print("R : ROI 다시 설정")
print("======================================")


# =========================================================
# 메인 탐지
# =========================================================

window_name = (
    f"Smart CCTV - {camera_name}"
)


while True:

    # =====================================================
    # 웹에서 CCTV 변경 요청 확인
    # =====================================================

    requested_id = requested_camera_id

    if (
        requested_id is not None
        and requested_id != camera_id
    ):
        print()
        print(
            f"[안내] CCTV 변경 요청 감지: {requested_id}"
        )

        # 같은 요청이 매 프레임 반복되지 않도록 먼저 비움
        requested_camera_id = None

        latest_cameras = load_cameras()
        new_camera = None

        for camera in latest_cameras:
            if camera.get("id") == requested_id:
                new_camera = camera
                break

        if new_camera is None:
            print(
                "[경고] 요청한 CCTV를 cameras.json에서 찾을 수 없습니다."
            )

        else:
            new_stream = None
            new_frame = None

            try:
                print(
                    f"[안내] 새 CCTV 연결 중: {new_camera['name']}"
                )

                new_stream = CamGear(
    source=new_camera["url"],
    stream_mode=True,
    logging=True,
    STREAM_RESOLUTION="480p"
).start()

                new_frame = new_stream.read()

            except Exception as e:
                print(
                    f"[경고] 새 CCTV 연결 실패: {e}"
                )

            if new_frame is None:
                print(
                    "[경고] 새 CCTV 영상을 불러오지 못했습니다. 기존 CCTV를 계속 사용합니다."
                )

                if new_stream is not None:
                    try:
                        new_stream.stop()
                    except Exception:
                        pass

            else:
                new_frame = cv2.resize(
                    new_frame,
                    (1280, 720)
                )

                new_camera_id = new_camera["id"]
                new_camera_name = new_camera["name"]
                new_camera_location = new_camera["location"]
                new_camera_url = new_camera["url"]

                new_roi_file = os.path.join(
                    ROI_DIR,
                    f"{new_camera_id}.json"
                )

                new_roi_polygon = None

                # 저장된 ROI가 있으면 자동 사용
                if os.path.exists(new_roi_file):
                    try:
                        with open(
                            new_roi_file,
                            "r",
                            encoding="utf-8"
                        ) as f:
                            saved_pts = json.load(f)

                        new_roi_polygon = np.array(
                            saved_pts,
                            np.int32
                        )

                        print(
                            "[완료] 새 CCTV의 저장된 ROI를 불러왔습니다."
                        )

                    except (
                        json.JSONDecodeError,
                        OSError,
                        ValueError,
                        TypeError
                    ) as e:
                        print(
                            f"[경고] 새 CCTV ROI 읽기 실패: {e}"
                        )

                # ROI가 없으면 새로 설정
                if new_roi_polygon is None:
                    print()
                    print(
                        "[안내] 선택한 CCTV에 저장된 ROI가 없습니다."
                    )
                    print(
                        "[안내] 새 CCTV ROI를 설정해주세요."
                    )

                    new_roi_polygon = setup_roi(
                        new_frame,
                        new_roi_file
                    )

                if new_roi_polygon is None:
                    print(
                        "[경고] ROI 설정이 취소되어 기존 CCTV를 계속 사용합니다."
                    )

                    try:
                        new_stream.stop()
                    except Exception:
                        pass

                else:
                    old_stream = stream
                    old_window_name = window_name

                    # 새 CCTV로 실제 교체
                    stream = new_stream
                    selected_camera = new_camera
                    camera_id = new_camera_id
                    camera_name = new_camera_name
                    camera_location = new_camera_location
                    camera_url = new_camera_url
                    ROI_FILE = new_roi_file
                    roi_polygon = new_roi_polygon

                    window_name = (
                        f"Smart CCTV - {camera_name}"
                    )

                    try:
                        old_stream.stop()
                    except Exception:
                        pass

                    try:
                        cv2.destroyWindow(
                            old_window_name
                        )
                    except cv2.error:
                        pass

                    update_status(
                        camera_id,
                        camera_name,
                        camera_location,
                        0
                    )

                    print()
                    print("======================================")
                    print(
                        f"[완료] CCTV 변경 완료: {camera_name}"
                    )
                    print(
                        f"위치: {camera_location}"
                    )
                    print(
                        f"ID  : {camera_id}"
                    )
                    print("======================================")
                    print()

                    continue

    elif (
        requested_id is not None
        and requested_id == camera_id
    ):
        # 현재 CCTV를 다시 선택한 경우 요청만 제거
        requested_camera_id = None


    # =====================================================
    # 현재 CCTV 프레임 읽기
    # =====================================================

    frame = stream.read()

    if frame is None:
        print(
            "[안내] 영상이 종료되었습니다."
        )
        break

    frame = cv2.resize(
        frame,
        (1280, 720)
    )


    # =====================================================
    # YOLO 사람 탐지
    # =====================================================

    results = model(
        frame,
        classes=[0],
        conf=0.25,
        imgsz=480,
        verbose=False
    )

    person_count = 0

    cv2.polylines(
        frame,
        [roi_polygon],
        isClosed=True,
        color=(255, 0, 0),
        thickness=2
    )

    for result in results:
        boxes = result.boxes

        for box in boxes:
            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            points_to_check = [
                (x1, y1),
                (x2, y1),
                (x1, y2),
                (x2, y2),
                (
                    int((x1 + x2) / 2),
                    int((y1 + y2) / 2)
                )
            ]

            is_inside = False

            for point in points_to_check:
                test = cv2.pointPolygonTest(
                    roi_polygon,
                    point,
                    False
                )

                if test >= 0:
                    is_inside = True
                    break

            if is_inside:
                person_count += 1

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    2
                )

            else:
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    1
                )


    # =====================================================
    # 웹 상태 업데이트
    # =====================================================

    update_status(
        camera_id,
        camera_name,
        camera_location,
        person_count
    )


    # =====================================================
    # CCTV 화면 UI
    # =====================================================

    cv2.putText(
        frame,
        camera_name,
        (30, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    if person_count > 0:
        cv2.putText(
            frame,
            f"PEDESTRIAN: {person_count}",
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

        cv2.putText(
            frame,
            "C-ITS WARNING READY",
            (30, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

    else:
        cv2.putText(
            frame,
            "PEDESTRIAN: 0 (SAFE)",
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            3
        )

    cv2.putText(
        frame,
        "Q/ESC Exit | R Reset ROI",
        (
            30,
            frame.shape[0] - 20
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )


    # =====================================================
    # 웹 메모리 영상 갱신
    # =====================================================

    update_web_frame(
        frame
    )


    # =====================================================
    # 개발 확인용 OpenCV 화면
    # =====================================================

    cv2.imshow(
        window_name,
        frame
    )

    key = (
        cv2.waitKey(1)
        & 0xFF
    )

    if key in (
        ord("q"),
        ord("Q"),
        27
    ):
        print(
            "[종료] 프로그램을 종료합니다."
        )
        break

    elif key in (
        ord("r"),
        ord("R")
    ):
        print(
            "[안내] ROI를 다시 설정합니다."
        )

        new_roi = setup_roi(
            frame.copy(),
            ROI_FILE
        )

        if new_roi is not None:
            roi_polygon = new_roi

            print(
                "[완료] 새 ROI를 적용하고 CCTV 화면으로 돌아갑니다."
            )

            continue


# =========================================================
# 종료
# =========================================================

cv2.destroyAllWindows()

stream.stop()

print(
    "[완료] 프로그램이 정상 종료되었습니다."
)