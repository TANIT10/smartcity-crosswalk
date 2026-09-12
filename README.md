# Smart Crosswalk Safety System

스마트시티 환경을 가정하여 CCTV 영상에서 보행자를 감지하고, 차량이 횡단보도 100m 이내로 접근했을 때 경고를 제공하는 C-ITS 기반 안전 시뮬레이션 프로젝트입니다.

> 본 프로젝트는 실제 차량 제어 또는 실제 C-ITS 통신 시스템이 아닌 **포트폴리오용 웹 기반 시뮬레이션**입니다.

---

## 1. 프로젝트 개요

본 프로젝트는 CCTV 영상과 YOLOv8 객체 탐지 모델을 활용해 횡단보도 영역 내 보행자를 감지하고, 감지 결과를 웹 대시보드와 차량 접근 시뮬레이션에 연동하는 것을 목표로 합니다.

로컬 환경에서는 YouTube CCTV 스트림을 이용해 실시간 탐지를 수행하고, 배포 환경에서는 외부 스트리밍 서비스의 접근 제한을 고려하여 `sample.mp4`를 사용해 동일한 AI 탐지 흐름을 시연합니다.

---

## 2. 주요 기능

### CCTV 영상 처리
- 로컬 환경에서 YouTube CCTV 스트림 연결
- OpenCV 기반 실시간 영상 처리
- CCTV별 ROI(관심 영역) 저장 및 재사용
- CCTV 선택 및 전환 기능
- 배포 환경에서는 샘플 영상을 통한 동일 처리 흐름 시연

### AI 보행자 감지
- YOLOv8 기반 사람 객체 탐지
- 횡단보도 ROI 내부 보행자 판정
- ROI 내부 AI 감지 인원 계산
- AI 탐지 특성을 고려해 웹에서는 `최소 N명` 형태로 표시
- 탐지 인원이 0명이어도 안전을 단정하지 않고 `미감지 / MONITORING` 상태로 표시

### 차량 접근 시뮬레이션
- 차량이 횡단보도 200m 전방에서 출발
- 100m 경고 구간 진입 시 AI 보행자 탐지 결과 확인
- 보행자가 감지된 경우 C-ITS 안전 경고 표시
- 단계적인 차량 감속 시뮬레이션
- 횡단보도 정지선 전방 5m 지점에서 차량 정지

### 웹 대시보드
- CCTV 영상
- AI 감지 보행자 정보
- 차량과 횡단보도 사이 거리
- 차량 속도
- C-ITS 경고 상태
- 서버 연결 상태
- PC / 태블릿 / 모바일 반응형 UI
- 로컬에서는 `LIVE CCTV / LIVE`, 배포 환경에서는 `CCTV DEMO / DEMO`로 구분 표시

---

## 3. 시스템 동작 흐름

### 로컬 실행

```text
YouTube CCTV
    ↓
CamGear 영상 스트림
    ↓
OpenCV 영상 처리
    ↓
YOLOv8 사람 탐지
    ↓
횡단보도 ROI 내부 판정
    ↓
Flask API / MJPEG 영상 스트리밍
    ↓
React 웹 대시보드
    ↓
차량 접근 시뮬레이션
    ↓
100m 구간 보행자 감지 시 C-ITS 경고
```

### 배포 환경

```text
sample.mp4
    ↓
OpenCV 영상 처리
    ↓
YOLOv8 사람 탐지
    ↓
횡단보도 ROI 내부 판정
    ↓
Railway Flask Backend
    ↓
Vercel React Frontend
    ↓
웹 기반 C-ITS 안전 시뮬레이션
```

---

## 4. 배포 구조

프론트엔드와 백엔드를 분리해 배포했습니다.

```text
사용자 브라우저
      ↓
Vercel
React Frontend
      ↓
Railway
Flask + YOLOv8 Backend
      ↓
sample.mp4
```

### Frontend

Vercel

```text
https://smartcity-crosswalk.vercel.app
```

### Backend

Railway

```text
https://smartcity-crosswalk-production.up.railway.app
```

백엔드 루트 주소에 접속하면 서버 실행 여부를 확인할 수 있습니다.

```text
Smart CCTV Server is running!
```

> Railway 백엔드는 배포 플랜 및 서비스 활성화 상태에 따라 일시적으로 중지될 수 있습니다. 프론트엔드는 백엔드 연결 상태를 `SYSTEM ONLINE / OFFLINE`으로 표시합니다.

---

## 5. 로컬과 배포 환경의 차이

| 구분 | 로컬 환경 | 배포 환경 |
|---|---|---|
| 영상 소스 | YouTube CCTV 2개 테스트 소스 | `sample.mp4` 1개 |
| 카메라 선택 | `camera1`, `camera2` 전환 가능 | 단일 데모 영상 사용 |
| 화면 표시 | `LIVE CCTV / LIVE` | `CCTV DEMO / DEMO` |
| AI 탐지 | YOLOv8 | YOLOv8 |
| ROI | 카메라별 개별 ROI | 배포 샘플용 저장 ROI |
| Backend | Flask localhost | Railway |
| Frontend | Vite localhost | Vercel |
| 용도 | 실시간 CCTV 개발/시연 | 외부 접속 가능한 포트폴리오 데모 |

Railway 환경에서는 YouTube 영상 스트림 요청 시 외부 서비스의 요청 제한 및 봇 차단이 발생할 수 있어, 배포 버전에서는 샘플 영상을 사용하도록 분리했습니다.

### 로컬 다중 CCTV와 ROI 관리

로컬 환경에서는 테스트용 CCTV를 2개(`camera1`, `camera2`) 등록해 전환할 수 있습니다.

각 CCTV는 촬영 구도와 횡단보도 위치가 다르기 때문에 ROI 좌표도 개별적으로 관리합니다.

```text
camera1 → roi/camera1.json
camera2 → roi/camera2.json
```

카메라를 전환하면 해당 카메라에 저장된 ROI를 불러오며, 필요한 경우 해당 화면 기준으로 ROI를 다시 설정할 수 있습니다.

반면 배포 환경에서는 안정적인 포트폴리오 시연을 위해 `sample.mp4` 하나만 사용하는 단일 데모 구조로 구성했습니다. 따라서 배포 환경에서는 로컬처럼 여러 CCTV를 전환하지 않고, 샘플 영상과 저장된 ROI를 이용해 동일한 YOLO 탐지 및 경고 흐름을 보여줍니다.

---

### 외부 CCTV 스트림 의존성

로컬 실시간 테스트에는 공개 YouTube 라이브 CCTV 스트림을 사용합니다.

다만 외부 스트리밍 서비스 특성상 방송이 종료되거나 새 라이브 스트림으로 다시 시작될 경우 영상 URL이 변경될 수 있습니다. 이 경우 로컬 테스트 시 `cameras.json`의 CCTV URL을 최신 공개 스트림 주소로 갱신해야 합니다.

현재 로컬 테스트에 사용하는 공개 스트림은 외부 제공자가 관리하는 영상이므로, 프로젝트가 해당 CCTV 스트림의 지속적인 제공을 보장하지는 않습니다.

이러한 외부 의존성과 클라우드 환경의 YouTube 접근 제한을 분리하기 위해 배포 환경에서는 `sample.mp4`를 사용하도록 구성했습니다.

---

## 6. AI / ROI 판정 방식

YOLOv8에서 탐지한 사람 객체의 Bounding Box를 기준으로 다음 5개 지점을 확인합니다.

```text
왼쪽 위
오른쪽 위
왼쪽 아래
오른쪽 아래
중심점
```

5개 지점 중 하나 이상이 횡단보도 Polygon ROI 내부에 포함되면 해당 사람을 ROI 내부 보행자로 판정합니다.

이를 통해 객체 중심점 하나만 사용하는 방식보다 횡단보도 경계에 걸친 보행자를 더 유연하게 판정하도록 구현했습니다.

---

## 7. 배포 환경 최적화

배포 서버의 CPU 및 네트워크 부담을 줄이기 위해 로컬과 배포 환경의 처리 방식을 분리했습니다.

- 로컬 CCTV 스트림: 480p
- 로컬 YOLO 추론: `conf=0.15`, `imgsz=640`
- 배포 YOLO 추론: `conf=0.25`, `imgsz=480`
- 로컬 웹 영상 출력: 960 × 540
- 배포 웹 영상 출력: 640 × 360
- 배포 JPEG 품질 조정
- 배포 환경에서는 YOLO 탐지를 매 프레임이 아닌 일정 프레임 간격으로 수행
- 탐지를 수행하지 않는 중간 프레임에서는 직전 탐지 결과 재사용
- `sample.mp4` 종료 시 처음부터 자동 반복 재생
- 배포 환경에서 `/video_feed` 접속자가 없으면 `sample.mp4` 처리와 YOLO 추론을 중지
- 실제 영상 접속자가 생기면 AI 처리를 자동 재개

이를 통해 포트폴리오 사이트에 접속자가 없을 때 불필요한 AI 연산을 줄이도록 구성했습니다.

또한 로컬 촬영·테스트 환경에서는 야간, 군중 밀집, 작은 보행자 객체의 미탐을 줄이기 위해 배포 환경보다 높은 입력 크기와 낮은 confidence 기준을 사용합니다. 배포 환경은 서버 부담을 줄이기 위해 기존 경량 설정을 유지합니다.

---

## 8. 차량 접근 시뮬레이션

차량 시뮬레이션은 웹에서 시스템의 경고 흐름을 시각적으로 보여주기 위한 기능입니다.

```text
200m
 ↓
차량 출발
 ↓
100m
 ↓
AI 보행자 감지 결과 확인
 ↓
보행자 감지 시 경고
 ↓
단계적 감속
 ↓
5m
 ↓
정지
```

현재 거리 변화와 속도 값은 실제 차량의 제동거리, 노면 상태, 반응시간 등을 물리적으로 검증한 값이 아닙니다.

따라서 본 프로젝트의 차량 속도 및 감속 표현은 **안전 시스템의 동작 흐름을 보여주기 위한 시뮬레이션 값**입니다.

---

## 9. 100m 경고 구간을 설정한 이유

본 프로젝트의 100m 경고 구간은 실제 차량의 제동거리나 교통안전 기준을 검증해 산출한 값이 아니라, **보행자 감지 정보를 너무 이르지도 늦지도 않게 전달하기 위한 시뮬레이션 기준값**입니다.

100m를 기준으로 설정한 이유는 크게 세 가지입니다.

1. **제동 여유 확보**
   - 횡단보도 바로 앞에서 경고하면 급격한 감속이 필요할 수 있습니다.
   - 100m 전부터 보행자 정보를 전달해 운전자가 미리 상황을 인지하고 단계적으로 감속하는 흐름을 표현했습니다.

2. **보행자 정보의 최신성 유지**
   - 너무 먼 거리에서 경고하면 차량이 횡단보도에 도착하기 전에 보행자 위치나 상황이 바뀔 가능성이 커집니다.
   - 반대로 너무 가까운 거리에서 경고하면 대응 시간이 부족할 수 있습니다.
   - 따라서 100m를 보행자 정보의 유효성과 차량 대응 시간 사이의 균형을 보여주는 대표 시뮬레이션 값으로 사용했습니다.

3. **운전자의 인지와 경각심**
   - 지나치게 이른 경고는 실제 위험 구간에 도달하기 전에 집중력이 낮아질 수 있고, 너무 늦은 경고는 급격한 대응을 유발할 수 있습니다.
   - 횡단보도 접근 구간에서 경고가 발생하도록 해 전방 상황 인지와 감속 흐름을 함께 표현했습니다.

즉, 본 프로젝트에서는 **300m처럼 너무 이른 경고와 30m처럼 너무 늦은 경고 사이에서, 대응 시간과 보행자 정보의 유효성을 함께 보여주기 위한 대표적인 시뮬레이션 값으로 100m를 설정했습니다.**

실제 시스템에 적용할 경우에는 차량 속도, 운전자 또는 자율주행 시스템의 반응시간, 차량 제동 성능, 노면 상태, 기상 조건, 도로 경사, 센서 지연시간 등을 반영해 경고 거리를 별도로 산정해야 합니다.

---

## 10. 기술 스택

### AI / Computer Vision
- Python
- YOLOv8 (`yolov8n.pt`)
- Ultralytics
- OpenCV
- NumPy
- VidGear / CamGear

### Backend
- Flask
- Flask-CORS
- MJPEG Streaming

### Frontend
- React
- Vite
- JavaScript
- CSS

### Deployment
- GitHub
- Docker
- Railway
- Vercel

---

## 11. 주요 API

### 서버 상태 확인
```http
GET /
```

### 시스템 상태 조회
```http
GET /api/status
```

### CCTV 목록 조회
```http
GET /api/cameras
```

### CCTV 전환
```http
POST /api/switch_camera
```

> CCTV 전환 기능은 로컬 실시간 CCTV 환경에서 `camera1`, `camera2`를 전환하기 위해 사용합니다. 각 카메라는 별도의 ROI 파일을 사용합니다. 배포 데모에서는 `sample.mp4` 하나만 사용하므로 카메라 전환 기능을 사용하지 않습니다.

### CCTV 영상 스트림
```http
GET /video_feed
```

---

## 12. 프로젝트 구조

```text
smartcity-crosswalk
├─ main.py
├─ cameras.json
├─ requirements.txt
├─ Dockerfile
├─ sample.mp4
├─ yolov8n.pt
├─ roi
│  ├─ camera1.json
│  └─ camera2.json
└─ frontend
   ├─ src
   │  ├─ App.jsx
   │  └─ App.css
   ├─ public
   └─ package.json
```

> 로컬의 `camera1`, `camera2`는 각각 `roi/camera1.json`, `roi/camera2.json`을 사용합니다. 배포 환경에서는 `sample.mp4`와 저장된 ROI를 사용한 단일 데모 구조로 동작합니다.

---

## 13. 로컬 실행 방법

### Backend

프로젝트 루트에서 가상환경을 활성화합니다.

```cmd
.venv\Scripts\activate.bat
python main.py
```

기본 Backend 주소:

```text
http://127.0.0.1:5000
```

로컬에서 사용하는 공개 CCTV 스트림 주소는 `cameras.json`에서 관리합니다. 외부 라이브 방송이 종료되거나 URL이 변경된 경우 이 파일의 URL을 최신 주소로 갱신해야 합니다.

### Frontend

새 터미널에서 `frontend` 폴더로 이동합니다.

```cmd
cd frontend
npm run dev
```

기본 Frontend 주소:

```text
http://localhost:5173
```

로컬 환경에서는 `frontend/.env.local`을 사용해 React가 로컬 Flask 서버에 연결됩니다.

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
```

---

## 14. 배포 환경 변수

Vercel에서는 다음 환경변수를 사용합니다.

```env
VITE_API_BASE_URL=https://smartcity-crosswalk-production.up.railway.app
```

이를 통해 배포된 React 애플리케이션이 Railway Flask Backend API에 연결됩니다.

---

## 15. 프로젝트에서 고려한 점

### AI 오탐 / 미탐

객체 탐지 모델은 거리, 가림, 영상 품질, 사람 간 겹침 등에 따라 모든 사람을 항상 정확하게 탐지할 수 없습니다.

따라서 UI에서는 탐지 결과를 실제 인원으로 단정하지 않고 다음과 같이 표현합니다.

```text
최소 N명 감지
```

탐지 결과가 0명인 경우에도 `SAFE`라고 단정하지 않고 다음과 같이 표현합니다.

```text
AI 보행자 미감지
MONITORING
```

### 로컬 실시간 영상과 배포 데모 구분

로컬에서는 공개 YouTube CCTV 스트림을 사용하며, `camera1`, `camera2`처럼 여러 테스트 CCTV를 전환할 수 있습니다. 각 카메라는 화면 구도가 다르므로 개별 ROI 파일을 사용합니다.

외부 라이브 방송은 종료·재시작에 따라 URL이 변경될 수 있으므로 `cameras.json`을 통해 영상 소스를 분리 관리합니다.

배포 환경에서는 외부 영상 서비스의 접근 제한과 URL 변동성을 줄이기 위해 `sample.mp4` 하나만 사용하는 단일 데모 구조로 구성했습니다. 따라서 배포 화면에서는 `CCTV DEMO / DEMO`로 표시하고 카메라 전환을 사용하지 않습니다.

```text
로컬
LIVE CCTV / LIVE

배포
CCTV DEMO / DEMO
```

배포 환경의 샘플 영상을 실시간 CCTV라고 오해하지 않도록 UI에서 명확히 구분했습니다.

### 배포 환경 선택

YOLOv8 + OpenCV + MJPEG 영상 처리는 일반적인 정적 웹보다 서버 CPU 사용량이 높습니다.

저사양 무료 인스턴스 환경에서는 영상 처리 속도가 충분하지 않을 수 있음을 확인했고, 실시간에 가까운 데모 동작이 가능한 서버 환경을 기준으로 백엔드 배포 구조를 구성했습니다.

### 반응형 웹

PC 환경뿐 아니라 태블릿과 모바일에서도 대시보드의 핵심 정보가 확인되도록 반응형 UI를 적용했습니다.

---

## 16. 향후 개선 사항

- 차량 속도와 보행자 상태를 반영한 동적 경고거리 산정
- 카메라별 배포 영상 및 ROI 관리
- YOLO 모델 정확도 개선
- 객체 추적 기능 추가
- 보행자 이동 방향 분석
- 차량 실제 GPS 데이터 연동
- 실제 도로 센서 / C-ITS 데이터 연동
- 이벤트 로그 및 통계 저장
- 관리자용 CCTV 관리 기능
- WebSocket 기반 상태 전송
- 인증 및 사용자 관리 기능

---

## 17. 한계 및 주의사항

본 프로젝트는 포트폴리오 및 기술 시연을 목적으로 제작한 프로토타입입니다.

다음 기능은 실제 환경에서 검증되지 않았습니다.

- 실제 자동차 제동 제어
- 실제 차량과의 V2X 통신
- 실제 C-ITS 인프라 연동
- 실제 제동거리 계산
- 안전 인증이 필요한 판단 시스템

따라서 실제 교통 안전 장치나 차량 제어 시스템으로 사용할 수 없습니다.

---

## 18. 프로젝트 핵심 요약

```text
CCTV / Sample Video
        ↓
YOLOv8
        ↓
Crosswalk ROI
        ↓
Pedestrian Detection
        ↓
Flask API
        ↓
React Dashboard
        ↓
100m Warning Simulation
```

**Computer Vision + Backend + Frontend + Deployment를 하나의 흐름으로 연결하여 구현한 스마트 횡단보도 안전 시스템 시뮬레이션 프로젝트입니다.**
