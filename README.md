# Smart Crosswalk Safety System

스마트시티 환경을 가정하여 CCTV 영상에서 보행자를 감지하고, 차량이 횡단보도 100m 이내로 접근했을 때 경고를 제공하는 C-ITS 기반 안전 시뮬레이션 프로젝트입니다.

> 본 프로젝트는 실제 차량 제어 또는 실제 C-ITS 통신 시스템이 아닌 **포트폴리오용 웹 기반 시뮬레이션**입니다.

---

## 1. 프로젝트 개요

본 프로젝트는 CCTV 영상과 YOLO 객체 탐지 모델을 활용해 횡단보도 영역 내 보행자를 감지하고, 감지 결과를 웹 대시보드와 차량 접근 시뮬레이션에 연동하는 것을 목표로 합니다.

로컬 환경에서는 YouTube CCTV 스트림을 사용하여 실시간 탐지를 수행하고, 배포 환경에서는 외부 스트리밍 서비스의 접근 제한을 고려해 `sample.mp4`를 반복 재생하여 동일한 AI 탐지 흐름을 시연합니다.

---

## 2. 주요 기능

### 실시간 CCTV 영상 처리

- YouTube CCTV 영상 스트림 연결
- OpenCV 기반 영상 처리
- CCTV 영상 실시간 웹 출력
- CCTV 선택 및 영상 전환 기능
- CCTV별 ROI 영역 저장
- 로컬 환경에서 실시간 CCTV 기반 탐지 지원

### AI 보행자 감지

- YOLOv8 기반 사람 객체 탐지
- 횡단보도 ROI 내부 보행자 판정
- ROI 내부 AI 감지 인원 계산
- 객체 Bounding Box의 네 꼭짓점과 중심점 중 하나 이상이 ROI 내부에 포함되면 ROI 내부 객체로 판정
- AI 탐지 특성을 고려하여 웹에서는 `최소 N명` 형태로 표시
- 탐지되지 않은 경우에도 안전을 단정하지 않고 `AI 보행자 미감지` 상태로 표시

### 차량 접근 시뮬레이션

- 차량이 횡단보도 200m 전방에서 출발
- 100m 경고 구간 진입 시 AI 보행자 감지 결과 확인
- 보행자가 감지된 경우 C-ITS 안전 경고 표시
- 단계적인 차량 감속 시뮬레이션
- 횡단보도 정지선 전방에서 차량 정지
- 보행자가 감지되지 않은 경우에도 계속 주의 운전 상태 유지

### 웹 대시보드

- CCTV 영상
- AI 감지 보행자 정보
- 차량과 횡단보도 사이 거리
- 차량 속도
- C-ITS 경고 상태
- 서버 연결 상태
- PC / 태블릿 / 모바일 반응형 UI

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

프론트엔드와 백엔드를 분리하여 배포했습니다.

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

### Backend

Railway

```text
https://smartcity-crosswalk-production.up.railway.app
```

백엔드 루트 주소에 접속하면 서버 실행 여부를 확인할 수 있습니다.

```text
Smart CCTV Server is running!
```

### Frontend

Vercel에 React 프론트엔드를 배포하여 외부에서도 웹 대시보드를 사용할 수 있습니다.

```text
https://smartcity-crosswalk.vercel.app/
```

---

## 5. 로컬과 배포 환경의 차이

| 구분 | 로컬 환경 | 배포 환경 |
|---|---|---|
| 영상 소스 | YouTube CCTV | `sample.mp4` |
| AI 탐지 | YOLOv8 | YOLOv8 |
| ROI | CCTV별 저장 ROI | 저장된 ROI |
| Backend | Flask localhost | Railway |
| Frontend | Vite localhost | Vercel |
| 용도 | 실시간 CCTV 개발/시연 | 외부 접속 가능한 포트폴리오 데모 |

Railway 환경에서 YouTube 영상 스트림 요청 시 외부 서비스의 봇/요청 제한이 발생할 수 있어, 배포 버전에서는 샘플 영상을 사용하도록 분리했습니다.

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

5개 지점 중 하나 이상이 횡단보도 ROI 내부에 포함되면 해당 사람을 ROI 내부 보행자로 판정합니다.

이를 통해 객체 중심점 하나만 사용하는 방식보다 경계 부분에 걸쳐 있는 보행자를 보다 유연하게 판정하도록 구현했습니다.

---

## 7. 배포 환경 최적화

배포 서버의 CPU 및 네트워크 부담을 줄이기 위해 로컬과 배포 환경의 처리 방식을 일부 분리했습니다.

- 로컬 CCTV 스트림: 480p
- YOLO 추론 입력 크기: 480
- 로컬 웹 영상 출력: 960 × 540
- 배포 웹 영상 출력: 640 × 360
- 배포 JPEG 품질 조정
- 배포 환경에서는 YOLO 탐지를 매 프레임이 아닌 일정 프레임 간격으로 수행
- 탐지를 수행하지 않는 중간 프레임에서는 직전 탐지 결과를 재사용
- `sample.mp4` 종료 시 처음부터 자동 반복 재생

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

본 프로젝트의 100m 경고 구간은 실제 차량의 제동거리나 교통안전 기준을 검증하여 산출한 값이 아니라, **보행자 감지 정보를 너무 이르지도 늦지도 않게 전달하기 위한 시뮬레이션 기준값**입니다.

100m를 기준으로 설정한 이유는 크게 세 가지입니다.

1. **제동 여유 확보**
   - 횡단보도 바로 앞에서 경고하면 운전자가 급하게 감속해야 할 수 있습니다.
   - 100m 전부터 경고를 제공하면 보행자 정보를 미리 인지하고 단계적으로 속도를 줄이는 과정을 표현할 수 있습니다.
   - 즉, 급정거보다는 충분한 대응 시간을 제공하는 조기 경고 구간을 표현하기 위한 거리입니다.

2. **보행자 정보의 최신성 유지**
   - 너무 먼 거리에서 보행자 정보를 전달하면 차량이 횡단보도에 도착하기 전에 보행자가 이동하여 현재 상황과 달라질 가능성이 커집니다.
   - 반대로 너무 가까운 거리에서 경고하면 대응 시간이 부족할 수 있습니다.
   - 따라서 본 프로젝트에서는 100m를 현재 CCTV가 감지한 보행자 정보와 차량 접근 시점 사이의 균형을 보여주기 위한 기준으로 사용했습니다.

3. **운전자의 인지와 경각심**
   - 지나치게 이른 경고는 실제 위험 상황에 도달하기 전에 운전자의 집중력이 낮아질 수 있고, 너무 늦은 경고는 운전자를 당황하게 할 수 있습니다.
   - 본 시뮬레이션에서는 횡단보도에 접근하는 구간에서 경고를 제공하여, 운전자가 전방 상황을 인지하면서 감속하도록 하는 흐름을 표현했습니다.

즉, 본 프로젝트에서는 **300m처럼 너무 이른 경고와 30m처럼 너무 늦은 경고 사이에서, 안전한 대응 시간과 보행자 정보의 유효성을 함께 보여주기 위한 대표적인 시뮬레이션 값으로 100m를 설정했습니다.**

실제 시스템에 적용할 경우에는 차량 속도, 운전자 또는 자율주행 시스템의 반응시간, 차량 제동 성능, 노면 상태, 기상 조건, 도로 경사, 센서 지연시간 등을 반영하여 경고 거리를 별도로 산정해야 합니다.

---

## 10. 기술 스택

### AI / Computer Vision

- Python
- YOLOv8
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
- Lucide React

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

> CCTV 전환은 로컬 실시간 CCTV 환경을 중심으로 사용합니다. 배포 데모에서는 샘플 영상 기반으로 동작합니다.

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

---

## 13. 로컬 실행 방법

### Backend

프로젝트 루트에서 가상환경을 활성화합니다.

```cmd
.venv\Scripts\activate.bat
```

Flask / YOLO 프로그램을 실행합니다.

```cmd
python main.py
```

기본 Backend 주소:

```text
http://127.0.0.1:5000
```

### Frontend

새 터미널에서 `frontend` 폴더로 이동합니다.

```cmd
cd frontend
```

개발 서버를 실행합니다.

```cmd
npm run dev
```

기본 Frontend 주소:

```text
http://localhost:5173
```

로컬 환경에서는 `frontend/.env.local`을 사용하여 React가 로컬 Flask 서버에 연결됩니다.

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
```

---

## 14. 배포 환경 변수

Vercel에는 다음 환경변수를 설정합니다.

```env
VITE_API_BASE_URL=https://smartcity-crosswalk-production.up.railway.app
```

이를 통해 배포된 React 애플리케이션이 Railway의 Flask Backend API를 사용합니다.

---

## 15. 프로젝트에서 고려한 점

### AI 오탐 / 미탐

실제 객체 탐지 모델은 거리, 가림, 영상 품질, 사람 간 겹침 등에 따라 모든 사람을 항상 정확하게 탐지할 수 없습니다.

따라서 UI에서 탐지 결과를 실제 인원으로 단정하지 않고 다음과 같이 표현했습니다.

```text
최소 N명 감지
```

또한 탐지 결과가 0명인 경우에도 `SAFE`와 같이 안전을 단정하지 않고 AI가 현재 보행자를 감지하지 못한 상태임을 표시하도록 구성했습니다.

### 외부 영상 서비스 의존성

로컬에서는 YouTube CCTV 스트림을 사용할 수 있지만 클라우드 서버에서는 외부 영상 서비스의 요청 제한이나 봇 차단이 발생할 수 있습니다.

이를 고려해 배포 환경에서는 샘플 영상 기반 데모 모드를 별도로 구성했습니다.

### 반응형 웹

PC 환경뿐 아니라 태블릿과 모바일에서도 대시보드의 핵심 정보가 확인되도록 반응형 UI를 적용했습니다.

---

## 16. 향후 개선 사항

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
