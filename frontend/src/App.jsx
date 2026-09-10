import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:5000'

const IS_LOCAL_CCTV =
  API_BASE_URL.includes('127.0.0.1') ||
  API_BASE_URL.includes('localhost')

function App() {
  const [status, setStatus] = useState({
    cameraId: 'camera1',
    cameraName: '테스트 횡단보도',
    location: '테스트 지역',
    personCount: 0,
    danger: false,
  })

  const [distance, setDistance] = useState(200)
  const [speed, setSpeed] = useState(50)
  const [isRunning, setIsRunning] = useState(false)
  const [alertTriggered, setAlertTriggered] = useState(false)
  const [simulationFinished, setSimulationFinished] = useState(false)
  const [safePassed, setSafePassed] = useState(false)
  const [showSafePass, setShowSafePass] = useState(false)
  const [cameras, setCameras] = useState([])
  const [selectedCameraId, setSelectedCameraId] = useState('camera1')
  const [serverConnected, setServerConnected] = useState(false)

  const detectedCount = status.personCount ?? 0
  const hasDetectedPedestrian = detectedCount > 0

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/status`
        )

        if (!response.ok) {
          throw new Error('API 요청 실패')
        }

        const data = await response.json()

        setStatus(data)
        setServerConnected(true)
      } catch (error) {
        console.error(
          'CCTV 상태 불러오기 실패:',
          error
        )

        setServerConnected(false)
      }
    }

    fetchStatus()

    const interval = setInterval(
      fetchStatus,
      250
    )

    return () => {
      clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/cameras`
        )

        if (!response.ok) {
          throw new Error('CCTV 목록 요청 실패')
        }

        const data = await response.json()

        setCameras(data)

        if (data.length > 0) {
          setSelectedCameraId(data[0].id)
        }
      } catch (error) {
        console.error(
          'CCTV 목록 불러오기 실패:',
          error
        )
      }
    }

    fetchCameras()
  }, [])

  const startSimulation = () => {
    setDistance(200)
    setSpeed(50)
    setAlertTriggered(false)
    setSimulationFinished(false)
    setIsRunning(true)
    setSafePassed(false)
    setShowSafePass(false)
  }

  const resetSimulation = () => {
    setDistance(200)
    setSpeed(50)
    setAlertTriggered(false)
    setSimulationFinished(false)
    setIsRunning(false)
    setSafePassed(false)
    setShowSafePass(false)
  }

  useEffect(() => {
    if (!isRunning) {
      return
    }

    const timer = setInterval(() => {
      setDistance((currentDistance) => {
        const nextDistance = Math.max(
          currentDistance - 5,
          5
        )

        return nextDistance
      })
    }, 100)

    return () => {
      clearInterval(timer)
    }
  }, [isRunning])

  useEffect(() => {
    if (!isRunning) {
      return
    }

    if (
      distance <= 100 &&
      detectedCount === 0 &&
      !safePassed
    ) {
      setSafePassed(true)
      setShowSafePass(true)
    }

    if (distance <= 5) {
      setDistance(5)
      setSpeed(0)
      setIsRunning(false)
      setAlertTriggered(false)
      setSimulationFinished(true)

      return
    }

    if (
      distance <= 100 &&
      detectedCount > 0 &&
      !alertTriggered
    ) {
      setAlertTriggered(true)
    }

    if (alertTriggered) {
      if (distance <= 10) {
        setSpeed(10)
      } else if (distance <= 15) {
        setSpeed(20)
      } else if (distance <= 25) {
        setSpeed(30)
      } else if (distance <= 40) {
        setSpeed(35)
      } else if (distance <= 60) {
        setSpeed(40)
      } else if (distance <= 80) {
        setSpeed(45)
      } else if (distance <= 100) {
        setSpeed(50)
      }
    }
  }, [
    distance,
    isRunning,
    detectedCount,
    alertTriggered,
    safePassed,
  ])

  useEffect(() => {
    if (!showSafePass) {
      return
    }

    const timer = setTimeout(() => {
      setShowSafePass(false)
    }, 2000)

    return () => {
      clearTimeout(timer)
    }
  }, [showSafePass])

  const handleCameraChange = async (event) => {
    const newCameraId = event.target.value

    setSelectedCameraId(newCameraId)

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/switch_camera`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            cameraId: newCameraId,
          }),
        }
      )

      if (!response.ok) {
        throw new Error('CCTV 변경 요청 실패')
      }

      console.log(
        'CCTV 변경 요청 성공'
      )
    } catch (error) {
      console.error(
        'CCTV 변경 실패:',
        error
      )
    }
  }

  return (
    <div className="app">
      {alertTriggered && (
        <div className="alert-overlay">
          <div className="alert-box">
            <div className="alert-icon">
              ⚠
            </div>

            <div>
              <span className="alert-title">
                C-ITS SAFETY ALERT
              </span>

              <h2>
                전방 횡단보도 보행자 감지
              </h2>

              <p>
                100m 전방에서 보행자 최소 {detectedCount}명이 AI에 감지되었습니다.
                실제 인원은 더 많을 수 있으므로 감속 운전하세요.
              </p>
            </div>
          </div>
        </div>
      )}

      {showSafePass && !alertTriggered && (
        <div className="safe-pass-overlay">
          AI 보행자 미감지 · 계속 주의 운전
        </div>
      )}

      <header className="header">
        <div>
          <p className="eyebrow">
            SMART CITY · C-ITS SAFETY DEMO
          </p>

          <h1>
            Smart Crosswalk Safety System
          </h1>

          <p className="header-description">
            CCTV 보행자 인식과 차량 100m 사전 경고 시뮬레이션
          </p>
        </div>

        <div
          className={
            serverConnected
              ? 'system-badge'
              : 'system-badge offline'
          }
        >
          <span className="status-dot"></span>

          {serverConnected
            ? 'SYSTEM ONLINE'
            : 'SYSTEM OFFLINE'}
        </div>
      </header>

      <main className="dashboard">
        <section className="panel cctv-panel">
          <div className="panel-header">
            <div>
              <span className="panel-label">
                {IS_LOCAL_CCTV ? 'LIVE CCTV' : 'CCTV DEMO'}
              </span>

              <h2>
                {status.cameraName || '실시간 보행자 감지'}
              </h2>

              <p className="camera-location">
                {status.location || '위치 정보 없음'}
              </p>
            </div>

            <div className="cctv-header-right">
              <select
                className="camera-select"
                value={selectedCameraId}
                onChange={handleCameraChange}
              >
                {cameras.map((camera) => (
                  <option
                    key={camera.id}
                    value={camera.id}
                  >
                    {camera.name}
                  </option>
                ))}
              </select>

              <span className="live-badge">
                <span className="live-dot"></span>
                {IS_LOCAL_CCTV ? 'LIVE' : 'DEMO'}
              </span>
            </div>
          </div>

          <div className="cctv-view">
            <img
              src={`${API_BASE_URL}/video_feed`}
              alt={
                IS_LOCAL_CCTV
                  ? '실시간 CCTV'
                  : '샘플 CCTV 영상'
              }
              className="cctv-video"
            />

            <div className="video-overlay">
              <span>
                AI OBJECT DETECTION
              </span>
            </div>
          </div>
        </section>

        <section className="panel simulation-panel">
          <div className="panel-header">
            <div>
              <span className="panel-label">
                VEHICLE SIMULATION
              </span>

              <h2>
                차량 접근 시뮬레이션
              </h2>
            </div>

            <span className="demo-badge">
              DEMO
            </span>
          </div>

          <div className="navigation-demo">
            <div className="distance-info">
              <span>
                횡단보도까지
              </span>

              <strong>
                {distance}m
              </strong>

              {simulationFinished && (
                <div className="stopped-badge">
                  STOPPED · 안전 정지 완료
                </div>
              )}
            </div>

            <div className="road">
              <div className="road-line"></div>

              <div className="warning-line">
                <span>
                  100m WARNING ZONE
                </span>
              </div>

              <div className="distance-marker marker-200">
                200m
              </div>

              <div className="distance-marker marker-100">
                100m
              </div>

              <div className="stop-line">
                <span>
                  STOP LINE
                </span>
              </div>

              <div
                className={
                  simulationFinished
                    ? 'car stopped'
                    : alertTriggered
                      ? 'car braking'
                      : 'car'
                }
                style={{
                  top: `${78 - ((200 - distance) / 200) * 38}%`,
                }}
              >
                🚗

                {simulationFinished && (
                  <div className="brake-light"></div>
                )}
              </div>

              <div className="crosswalk">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
              </div>

              <div className="pedestrian-sign">
                🚸
              </div>
            </div>

            <div className="simulation-bottom">
              <div>
                <span>
                  현재 속도
                </span>

                <strong>
                  {speed} km/h
                </strong>
              </div>

              <button
                type="button"
                onClick={
                  isRunning
                    ? resetSimulation
                    : startSimulation
                }
              >
                {isRunning
                  ? '시뮬레이션 초기화'
                  : simulationFinished
                    ? '다시 시작'
                    : '시뮬레이션 시작'}
              </button>
            </div>
          </div>
        </section>
      </main>

      <section className="status-grid">
        <div className="status-card">
          <span>
            AI 감지 보행자
          </span>

          <strong>
            {hasDetectedPedestrian
              ? `최소 ${detectedCount}명`
              : '미감지'}
          </strong>

          <small>
            {hasDetectedPedestrian
              ? '실제 인원은 더 많을 수 있음'
              : '현재 AI가 탐지한 보행자 없음'}
          </small>
        </div>

        <div className="status-card">
          <span>
            현재 상태
          </span>

          <strong
            className={
              status.danger
                ? 'danger-text'
                : ''
            }
          >
            {status.danger
              ? 'WARNING'
              : 'MONITORING'}
          </strong>

          <small>
            {status.danger
              ? '보행자가 감지되었습니다.'
              : '현재 AI 탐지 없음 · 지속 모니터링'}
          </small>
        </div>

        <div className="status-card">
          <span>
            차량 거리
          </span>

          <strong>
            {distance}m
          </strong>

          <small>
            경고 기준 100m
          </small>
        </div>

        <div className="status-card">
          <span>
            C-ITS 경고
          </span>

          <strong
            className={
              alertTriggered
                ? 'danger-text'
                : ''
            }
          >
            {alertTriggered
              ? '경고 발생'
              : '대기'}
          </strong>

          <small>
            {alertTriggered
              ? `보행자 최소 ${detectedCount}명 감지`
              : '100m 진입 시 AI 탐지 결과 판정'}
          </small>
        </div>
      </section>
    </div>
  )
}

export default App
