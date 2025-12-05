# YOLO 트레이딩 봇 GUI 사용 가이드
# YOLO Trading Bot GUI User Guide

바이비트 YOLO 트레이딩 봇의 Streamlit 기반 웹 인터페이스입니다.
Streamlit-based web interface for the Bybit YOLO Trading Bot.

## 🚀 빠른 시작 (Quick Start)

### 1. 의존성 설치 (Install Dependencies)

```bash
pip install -r requirements.txt
```

### 2. GUI 실행 (Run GUI)

**방법 1: 런처 스크립트 사용 (Using Launcher Script)**
```bash
python run_gui.py
```

**방법 2: Streamlit 직접 실행 (Direct Streamlit Run)**
```bash
streamlit run gui/streamlit_app.py
```

### 3. 브라우저 접속 (Access Browser)

자동으로 브라우저가 열리며, 수동으로는 다음 주소로 접속:
Browser opens automatically, or manually navigate to:

```
http://localhost:8501
```

## 📊 기능 (Features)

### 탭 1: 📊 대시보드 (Dashboard)

**봇 제어 (Bot Control)**
- ▶️ **시작**: 트레이딩 봇 시작
- ⏸️ **중지**: 트레이딩 봇 중지
- 🚨 **긴급 청산**: 모든 포지션 즉시 청산
- ✅ **자동 새로고침**: 5초마다 자동 업데이트

**계좌 현황 (Account Status)**
- 💰 잔고 (Balance)
- 🎯 승률 (Win Rate)
- 📊 활성 포지션 (Active Positions)
- 📈 Sharpe 비율 (Sharpe Ratio)

**성과 지표 (Performance Metrics)**
- 총 거래 수 (Total Trades)
- 평균 수익 (Average Profit)
- 평균 손실 (Average Loss)
- Profit Factor

**차트 및 테이블 (Charts & Tables)**
- BTC/USDT 15분 캔들스틱 차트
- 활성 포지션 테이블
- 최근 거래 내역

### 탭 2: 📈 실시간 거래 (Real-time Trading)

**3개 코인 동시 모니터링 (Monitor 3 Coins)**
- BTC/USDT
- ETH/USDT
- SOL/USDT

**각 코인별 정보 (Per Coin Information)**
- 현재가 및 변동률 (Current Price & Change)
- RSI 지표
- MACD 신호
- 실시간 차트 (Real-time Chart)
- 청산 버튼 (Close Position Button)

**실시간 신호 알림 (Real-time Signal Alerts)**
- 패턴 감지 로그
- RSI 경고
- MACD 신호

### 탭 3: 🎓 YOLO 학습 (YOLO Training)

**학습 설정 (Training Settings)**
- 학습 모드 선택 (전체/빠른/커스텀)
- 이미지 개수 조절
- 에포크 수 조절
- 배치 크기 조절
- 학습 심볼 선택 (BTC/ETH/SOL/BNB)
- 타임프레임 선택 (5m/15m/1h/4h)

**GPU 상태 (GPU Status)**
- GPU 모델명 (RTX 3050)
- 온도 (Temperature)
- GPU 사용률 (Utilization)
- VRAM 사용량 (VRAM Usage)

**학습 진행률 (Training Progress)**
- 전체 진행률 바
- 에포크 진행률 바
- 경과 시간 (Elapsed Time)
- 남은 시간 (Remaining Time)

**학습 지표 차트 (Training Metrics)**
- Loss 차트
- mAP50 차트
- Precision 차트

**학습 로그 (Training Log)**
- 실시간 학습 로그 출력

### 탭 4: 📉 백테스트 (Backtest)

**백테스트 설정 (Backtest Settings)**
- 시작 날짜 (Start Date)
- 종료 날짜 (End Date)
- 초기 자금 (Initial Capital)
- 전략 선택 (Strategy Selection)
- 레버리지 설정 (Leverage)

**성과 요약 (Performance Summary)**
- 총 수익률 (Total Return)
- 승률 (Win Rate)
- 최대 손실폭 (Max Drawdown)
- 총 거래 수 (Total Trades)
- Sharpe 비율 (Sharpe Ratio)
- Profit Factor
- 평균 수익 (Average Profit)
- 평균 손실 (Average Loss)

**차트 (Charts)**
- 수익률 곡선 (Equity Curve)
- 월별 수익률 (Monthly Returns)

## 🎨 사용자 인터페이스 (User Interface)

### 레이아웃 (Layout)
- **Wide Mode**: 전체 화면 활용
- **Multi-Column**: 2-4개 컬럼으로 정보 분할
- **반응형 디자인**: 다양한 화면 크기 지원

### 색상 테마 (Color Theme)
- **Dark Theme**: Plotly 다크 테마 사용
- **상승**: 녹색 (#00ff00)
- **하락**: 빨간색 (#ff0000)

### 아이콘 (Icons)
- 🤖 봇 (Bot)
- 📊 대시보드 (Dashboard)
- 📈 상승 (Up)
- 📉 하락 (Down)
- 🎓 학습 (Training)
- 💰 자금 (Money)
- 🎯 목표 (Target)
- 🚨 경고 (Alert)

## ⚙️ 설정 (Configuration)

### 포트 변경 (Change Port)

`run_gui.py` 파일에서 포트 번호 변경:
```python
"--server.port=8501"  # 원하는 포트로 변경
```

### 자동 새로고침 간격 (Auto-refresh Interval)

`gui/streamlit_app.py` 파일의 551-554줄에서 조절:
```python
# 자동 새로고침 (5초마다)
if st.session_state.auto_refresh:
    import time
    time.sleep(5)  # 초 단위로 변경
    st.rerun()
```

## 📱 모바일 접속 (Mobile Access)

### 로컬 네트워크에서 접속 (Access from Local Network)

1. 서버의 IP 주소 확인:
```bash
# Linux/Mac
ifconfig | grep inet

# Windows
ipconfig
```

2. 모바일 브라우저에서 접속:
```
http://[서버_IP]:8501
```

예: `http://192.168.1.100:8501`

### 외부 네트워크 접속 (External Access)

보안을 위해 외부 접속은 권장하지 않습니다. 필요한 경우:
1. 포트 포워딩 설정
2. HTTPS 설정 (SSL/TLS)
3. 인증 추가

## 🔧 문제 해결 (Troubleshooting)

### Streamlit 실행 오류

**증상**: "Streamlit이 설치되지 않았습니다" 오류

**해결**:
```bash
pip install streamlit plotly
```

### 포트 사용 중 오류

**증상**: "Port 8501 is already in use"

**해결**:
```bash
# 다른 포트로 실행
streamlit run gui/streamlit_app.py --server.port=8502
```

### 차트 표시 안 됨

**증상**: 차트가 표시되지 않음

**해결**:
```bash
# Plotly 재설치
pip install --upgrade plotly
```

### 한글 깨짐

**증상**: 한글이 깨져서 보임

**해결**:
- 브라우저 인코딩을 UTF-8로 설정
- 최신 브라우저 사용 (Chrome, Firefox, Edge)

## 💡 팁 (Tips)

### 성능 최적화 (Performance)
1. 자동 새로고침은 필요시에만 활성화
2. 여러 탭을 동시에 열지 않기
3. 오래된 브라우저 탭 닫기

### 데이터 보기 (Viewing Data)
1. 테이블 컬럼 정렬 가능
2. 테이블 CSV 다운로드 가능
3. 차트 확대/축소 가능
4. 차트 PNG 다운로드 가능

### 멀티 세션 (Multi-Session)
- 여러 브라우저/탭에서 동시 접속 가능
- 각 세션은 독립적인 상태 유지

## 📝 참고 사항 (Notes)

### 현재 버전 (Current Version)
- 예시 데이터 사용 (Example Data)
- 실제 봇 연동은 추후 구현 예정
- UI/UX 프로토타입

### 향후 계획 (Future Plans)
- [ ] 실제 봇 API 연동
- [ ] 실시간 WebSocket 데이터
- [ ] 사용자 인증 시스템
- [ ] 알림 시스템
- [ ] 거래 이력 저장
- [ ] 설정 파일 지원

## 📞 지원 (Support)

문제 발생 시 GitHub Issues에 보고해주세요.
For issues, please report on GitHub Issues.

## 📄 라이선스 (License)

MIT License - 자세한 내용은 LICENSE 파일 참조
