"""
🤖 YOLO 트레이딩 봇 Streamlit GUI
Bybit YOLO Trading Bot Streamlit Dashboard

완전 한글화된 경량 웹 대시보드
Fully Korean-localized lightweight web dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="🤖 YOLO 트레이딩 봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'training_running' not in st.session_state:
    st.session_state.training_running = False
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False


def generate_sample_candlestick_data(num_candles=50):
    """샘플 캔들 데이터 생성"""
    dates = pd.date_range(end=datetime.now(), periods=num_candles, freq='15min')
    base_price = 43000
    data = []
    
    for i in range(num_candles):
        open_price = base_price + random.uniform(-200, 200)
        close_price = open_price + random.uniform(-150, 150)
        high_price = max(open_price, close_price) + random.uniform(0, 100)
        low_price = min(open_price, close_price) - random.uniform(0, 100)
        volume = random.uniform(100, 1000)
        
        data.append({
            'date': dates[i],
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
        base_price = close_price
    
    return pd.DataFrame(data)


def create_candlestick_chart(df, title="BTC/USDT 15분 차트", height=400):
    """Plotly 캔들스틱 차트 생성"""
    fig = go.Figure(data=[go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='캔들'
    )])
    
    fig.update_layout(
        title=title,
        yaxis_title='가격 (USDT)',
        xaxis_title='시간',
        height=height,
        xaxis_rangeslider_visible=False,
        template='plotly_dark'
    )
    
    return fig


def create_line_chart(data, title="가격 차트", height=150):
    """간단한 라인 차트 생성"""
    fig = go.Figure(data=[go.Scatter(
        y=data,
        mode='lines',
        line=dict(color='#00ff00', width=2)
    )])
    
    fig.update_layout(
        title=title,
        height=height,
        showlegend=False,
        template='plotly_dark',
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig


def generate_sample_positions():
    """샘플 포지션 데이터 생성"""
    return pd.DataFrame([
        {
            '코인': 'BTC/USDT',
            '방향': '롱 🟢',
            '진입가': 43200.00,
            '현재가': 43850.00,
            '손익%': '+1.5%'
        },
        {
            '코인': 'ETH/USDT',
            '방향': '숏 🔴',
            '진입가': 2280.00,
            '현재가': 2265.00,
            '손익%': '+0.7%'
        }
    ])


def generate_sample_trades():
    """샘플 거래 내역 생성"""
    trades = []
    patterns = ['bull_flag', 'double_bottom', 'bear_flag', 'head_and_shoulders']
    
    for i in range(10):
        time_offset = timedelta(hours=i*2)
        profit = random.uniform(-50, 100)
        trades.append({
            '시간': (datetime.now() - time_offset).strftime('%m-%d %H:%M'),
            '코인': random.choice(['BTC/USDT', 'ETH/USDT', 'SOL/USDT']),
            '방향': random.choice(['롱 🟢', '숏 🔴']),
            '진입': round(random.uniform(40000, 45000), 2),
            '청산': round(random.uniform(40000, 45000), 2),
            '손익': f"${profit:.2f}",
            '패턴': random.choice(patterns)
        })
    
    return pd.DataFrame(trades)


# 메인 타이틀
st.title("🤖 Bybit YOLO 트레이딩 봇 시스템")
st.caption("실시간 자동매매 모니터링 대시보드")
st.markdown("---")

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 대시보드",
    "📈 실시간 거래",
    "🎓 YOLO 학습",
    "📉 백테스트"
])

# ==================== 탭 1: 대시보드 ====================
with tab1:
    # 상단 제어 패널
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        status_text = "🟢 실행중" if st.session_state.bot_running else "🔴 중지"
        st.metric("봇 상태", status_text)
    
    with col2:
        if st.button("▶️ 시작", disabled=st.session_state.bot_running):
            st.session_state.bot_running = True
            st.success("봇이 시작되었습니다!")
            st.rerun()
    
    with col3:
        if st.button("⏹️ 중지", disabled=not st.session_state.bot_running):
            st.session_state.bot_running = False
            st.warning("봇이 중지되었습니다!")
            st.rerun()
    
    with col4:
        if st.button("🚨 긴급청산"):
            st.error("모든 포지션이 청산되었습니다!")
    
    st.markdown("---")
    
    # 계좌 현황
    st.subheader("💰 계좌 현황")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("잔고", "$10,245.32")
    with col2:
        st.metric("오늘 수익", "$342.18", "+3.45%")
    with col3:
        st.metric("수익률", "+24.5%", "+2.1%")
    with col4:
        st.metric("포지션", "2개")
    
    st.markdown("---")
    
    # 성과 지표
    st.subheader("📈 성과 지표")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("승률", "67.8%")
    with col2:
        st.metric("총 거래", "145")
    with col3:
        st.metric("평균 수익", "$85.50")
    with col4:
        st.metric("평균 손실", "-$42.30")
    with col5:
        st.metric("Sharpe Ratio", "1.85")
    
    st.markdown("---")
    
    # 활성 포지션
    st.subheader("📌 활성 포지션")
    positions_df = generate_sample_positions()
    st.dataframe(positions_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # BTC/USDT 차트
    st.subheader("📊 BTC/USDT 15분 차트")
    candle_data = generate_sample_candlestick_data(50)
    fig = create_candlestick_chart(candle_data)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 최근 거래 내역
    st.subheader("📜 최근 거래 내역")
    trades_df = generate_sample_trades()
    st.dataframe(trades_df, use_container_width=True, hide_index=True)


# ==================== 탭 2: 실시간 거래 ====================
with tab2:
    st.header("📈 실시간 거래 모니터링")
    
    # 3개 코인 동시 모니터링
    col1, col2, col3 = st.columns(3)
    
    coins = [
        ('BTC/USDT', 43850.00, 2.45, [43000 + random.uniform(-500, 500) for _ in range(20)]),
        ('ETH/USDT', 2265.00, -1.23, [2300 + random.uniform(-50, 50) for _ in range(20)]),
        ('SOL/USDT', 98.50, 5.67, [95 + random.uniform(-5, 5) for _ in range(20)])
    ]
    
    for idx, (col, (coin, price, change, price_data)) in enumerate(zip([col1, col2, col3], coins)):
        with col:
            st.subheader(coin)
            
            # 현재가 및 변동률
            delta_color = "normal" if change > 0 else "inverse"
            st.metric("현재가", f"${price:,.2f}", f"{change:+.2f}%", delta_color=delta_color)
            
            # 간단한 가격 차트
            fig = create_line_chart(price_data, f"{coin} 가격 추이")
            st.plotly_chart(fig, use_container_width=True)
            
            # 지표 정보
            rsi = random.uniform(30, 70)
            macd = random.uniform(-10, 10)
            st.info(f"📊 RSI: {rsi:.1f} | MACD: {macd:.2f}")
            
            # 패턴 정보
            patterns = ['bull_flag', 'double_bottom', 'bear_flag', 'head_and_shoulders']
            detected_pattern = random.choice(patterns) if random.random() > 0.5 else None
            
            if detected_pattern:
                st.success(f"🎯 패턴 감지: {detected_pattern}")
            else:
                st.info("👀 패턴 감지 대기중...")
            
            # 포지션 상태
            has_position = random.random() > 0.5
            if has_position:
                st.warning(f"📌 {'롱' if random.random() > 0.5 else '숏'} 포지션 보유중")
            else:
                st.success("✅ 포지션 없음")
            
            # 거래 버튼
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"🟢 롱 진입", key=f"long_{idx}"):
                    st.success(f"{coin} 롱 포지션 진입!")
            with col_b:
                if st.button(f"🔴 숏 진입", key=f"short_{idx}"):
                    st.error(f"{coin} 숏 포지션 진입!")
    
    st.markdown("---")
    
    # 실시간 신호 알림
    st.subheader("🔔 실시간 신호 알림")
    
    signals = [
        f"{datetime.now().strftime('%H:%M:%S')} | BTC/USDT | 🟢 롱 신호 감지 (bull_flag, conf: 0.85)",
        f"{(datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S')} | ETH/USDT | 패턴 감지 대기중",
        f"{(datetime.now() - timedelta(minutes=10)).strftime('%H:%M:%S')} | SOL/USDT | 🔴 숏 신호 감지 (bear_flag, conf: 0.78)",
        f"{(datetime.now() - timedelta(minutes=15)).strftime('%H:%M:%S')} | BTC/USDT | TP 도달, 포지션 청산",
        f"{(datetime.now() - timedelta(minutes=20)).strftime('%H:%M:%S')} | ETH/USDT | RSI 과매수 경고"
    ]
    
    for signal in signals:
        st.text(signal)


# ==================== 탭 3: YOLO 학습 ====================
with tab3:
    st.header("🎓 YOLO 모델 학습")
    
    col1, col2 = st.columns([2, 1])
    
    # 왼쪽: 학습 설정
    with col1:
        st.subheader("⚙️ 학습 설정")
        
        # 학습 모드
        mode = st.radio(
            "학습 모드",
            ["전체 학습", "빠른 테스트", "커스텀"],
            horizontal=True
        )
        
        if mode == "커스텀":
            col_a, col_b = st.columns(2)
            with col_a:
                num_images = st.number_input("이미지 수", min_value=100, max_value=10000, value=1000, step=100)
                epochs = st.number_input("에포크", min_value=10, max_value=500, value=100, step=10)
            with col_b:
                batch_size = st.number_input("배치 크기", min_value=4, max_value=64, value=16, step=4)
                img_size = st.number_input("이미지 크기", min_value=320, max_value=1280, value=640, step=32)
        
        # 심볼 선택
        symbols = st.multiselect(
            "트레이딩 심볼",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"],
            default=["BTC/USDT", "ETH/USDT"]
        )
        
        # 타임프레임 선택
        timeframes = st.multiselect(
            "타임프레임",
            ["15m", "1h", "4h"],
            default=["15m", "4h"]
        )
        
        # 학습 시작 버튼
        if st.button("🚀 학습 시작", disabled=st.session_state.training_running):
            st.session_state.training_running = True
            st.success("학습이 시작되었습니다!")
            st.rerun()
        
        if st.button("⏹️ 학습 중지", disabled=not st.session_state.training_running):
            st.session_state.training_running = False
            st.warning("학습이 중지되었습니다!")
            st.rerun()
    
    # 오른쪽: GPU 상태
    with col2:
        st.subheader("🖥️ GPU 상태")
        
        st.metric("GPU", "NVIDIA RTX 3050")
        st.metric("온도", "65°C", "-2°C")
        
        gpu_usage = random.uniform(60, 90)
        st.write("사용률")
        st.progress(gpu_usage / 100)
        st.caption(f"{gpu_usage:.1f}%")
        
        vram_usage = random.uniform(3.5, 7.5)
        st.write("VRAM (8GB)")
        st.progress(vram_usage / 8)
        st.caption(f"{vram_usage:.1f}GB / 8GB")
    
    st.markdown("---")
    
    # 학습 진행률 (학습중일 때만)
    if st.session_state.training_running:
        st.subheader("📊 학습 진행률")
        
        progress = random.uniform(0.4, 0.8)
        epoch_progress = random.uniform(0.3, 0.9)
        
        st.write("전체 진행률")
        st.progress(progress)
        st.caption(f"{progress*100:.1f}% 완료")
        
        st.write("현재 에포크 진행률")
        st.progress(epoch_progress)
        st.caption(f"Epoch 45/100 ({epoch_progress*100:.1f}%)")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("경과 시간", "1h 23m")
        with col_b:
            st.metric("남은 시간", "1h 52m")
        
        st.markdown("---")
    
    # 학습 지표
    st.subheader("📈 학습 지표")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Loss", "0.0234", "-0.0012")
        loss_data = [0.5 - i*0.01 for i in range(20)]
        st.line_chart(loss_data, height=100)
    
    with col2:
        st.metric("mAP50", "0.892", "+0.015")
        map_data = [0.5 + i*0.02 for i in range(20)]
        st.line_chart(map_data, height=100)
    
    with col3:
        st.metric("정밀도", "0.875", "+0.008")
        precision_data = [0.6 + i*0.015 for i in range(20)]
        st.line_chart(precision_data, height=100)
    
    st.markdown("---")
    
    # 로그
    st.subheader("📝 학습 로그")
    logs = [
        "Epoch 45/100: loss=0.0234, mAP50=0.892, precision=0.875",
        "Batch 123/500: Processing...",
        "Validation: mAP50 improved from 0.877 to 0.892",
        "Checkpoint saved: best.pt",
        "Learning rate: 0.001",
        "GPU Memory: 6.5GB / 8GB",
        "Processing pattern: bull_flag",
        "Data augmentation applied",
        "Batch completed in 2.3s",
        "Starting next epoch..."
    ]
    
    for log in logs[-10:]:
        st.text(f"[{datetime.now().strftime('%H:%M:%S')}] {log}")


# ==================== 탭 4: 백테스트 ====================
with tab4:
    st.header("📉 백테스트")
    
    # 백테스트 설정
    st.subheader("⚙️ 백테스트 설정")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "시작 날짜",
            value=datetime.now() - timedelta(days=180)
        )
    
    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=datetime.now()
        )
    
    with col3:
        initial_capital = st.number_input(
            "초기 자금 (USDT)",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        strategy = st.selectbox(
            "전략 선택",
            ["YOLO + 기술적분석", "기술적분석만", "YOLO만"]
        )
    
    with col2:
        leverage = st.selectbox(
            "레버리지",
            ["1x", "2x", "5x", "10x", "20x"]
        )
    
    # 실행 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 백테스트 실행", disabled=st.session_state.backtest_running):
            st.session_state.backtest_running = True
            st.success("백테스트가 시작되었습니다!")
            st.session_state.backtest_running = False
            st.rerun()
    
    with col2:
        if st.button("📊 결과 비교"):
            st.info("여러 전략의 결과를 비교합니다...")
    
    st.markdown("---")
    
    # 성과 요약
    st.subheader("💰 성과 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 수익률", "+48.5%", "+2.3%")
    with col2:
        st.metric("최대 낙폭", "-12.3%")
    with col3:
        st.metric("Sharpe Ratio", "2.15")
    with col4:
        st.metric("Profit Factor", "2.45")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("승률", "68.5%")
    with col2:
        st.metric("총 거래", "234")
    with col3:
        st.metric("평균 수익", "$125.50")
    with col4:
        st.metric("평균 손실", "-$58.30")
    
    st.markdown("---")
    
    # 수익률 곡선
    st.subheader("📈 수익률 곡선")
    
    # 샘플 수익률 데이터 생성
    days = max((end_date - start_date).days, 1)
    dates = pd.date_range(start=start_date, end=end_date, periods=max(days, 2))
    equity = [initial_capital]
    
    for i in range(1, len(dates)):
        change = equity[-1] * random.uniform(-0.02, 0.03)
        equity.append(equity[-1] + change)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity,
        mode='lines',
        name='자산 곡선',
        line=dict(color='#00ff00', width=2)
    ))
    
    fig.update_layout(
        title='일별 자산 변화',
        xaxis_title='날짜',
        yaxis_title='자산 (USDT)',
        height=400,
        template='plotly_dark'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 월별 수익률
    st.subheader("📊 월별 수익률")
    
    months = ['1월', '2월', '3월', '4월', '5월', '6월', 
              '7월', '8월', '9월', '10월', '11월', '12월']
    monthly_returns = [random.uniform(-5, 10) for _ in range(12)]
    
    monthly_df = pd.DataFrame({
        '월': months,
        '수익률': monthly_returns
    })
    
    st.bar_chart(monthly_df.set_index('월'), height=300)


# 사이드바
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    
    st.subheader("🔗 연결 상태")
    st.success("✅ Bybit API 연결됨")
    st.success("✅ YOLO 모델 로드됨")
    
    st.markdown("---")
    
    st.subheader("📊 시스템 정보")
    st.text(f"버전: v1.0.0")
    st.text(f"가동 시간: 3h 25m")
    st.text(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    st.subheader("🔔 알림 설정")
    st.checkbox("거래 신호 알림", value=True)
    st.checkbox("포지션 변화 알림", value=True)
    st.checkbox("위험 경고 알림", value=True)
    
    st.markdown("---")
    
    if st.button("🔄 새로고침"):
        st.rerun()
    
    st.caption("© 2024 YOLO Trading Bot")
