"""
YOLO 트레이딩 봇 - Streamlit GUI
바이비트 YOLO 트레이딩 봇의 통합 웹 인터페이스
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random

# 페이지 설정
st.set_page_config(
    page_title="YOLO 트레이딩 봇",
    page_icon="🤖",
    layout="wide"
)

# 세션 상태 초기화
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# 예시 데이터 생성 함수
def get_account_data():
    """계좌 정보 예시 데이터"""
    return {
        'balance': 10245.32,
        'profit_pct': 3.45,
        'positions_count': 2,
        'total_trades': 156,
        'winning_trades': 106,
        'losing_trades': 50,
        'avg_profit': 45.23,
        'avg_loss': -28.67,
        'sharpe_ratio': 1.42
    }

def get_active_positions():
    """활성 포지션 예시 데이터"""
    return pd.DataFrame([
        {
            '코인': 'BTC/USDT',
            '방향': '롱',
            '진입가': 43850.00,
            '현재가': 44508.75,
            '손익%': '+1.5%',
            '손익': '+98.81 USDT',
            '청산가': 41232.50
        },
        {
            '코인': 'ETH/USDT',
            '방향': '숏',
            '진입가': 2285.50,
            '현재가': 2269.45,
            '손익%': '+0.7%',
            '손익': '+32.10 USDT',
            '청산가': 2399.78
        }
    ])

def get_recent_trades():
    """최근 거래 내역 예시 데이터"""
    return pd.DataFrame([
        {
            '시간': '2024-12-05 14:23',
            '코인': 'BTC/USDT',
            '방향': '롱',
            '진입가': 43200.00,
            '청산가': 43850.00,
            '손익%': '+1.5%',
            '손익': '+75.00 USDT'
        },
        {
            '시간': '2024-12-05 12:15',
            '코인': 'ETH/USDT',
            '방향': '숏',
            '진입가': 2310.00,
            '청산가': 2285.50,
            '손익%': '+1.1%',
            '손익': '+24.50 USDT'
        },
        {
            '시간': '2024-12-05 10:42',
            '코인': 'SOL/USDT',
            '방향': '롱',
            '진입가': 98.50,
            '청산가': 96.80,
            '손익%': '-1.7%',
            '손익': '-17.00 USDT'
        }
    ])

def create_candlestick_chart():
    """BTC/USDT 캔들스틱 차트 생성"""
    # 예시 캔들스틱 데이터
    dates = pd.date_range(end=datetime.now(), periods=50, freq='15min')
    base_price = 43850
    
    data = []
    for i, date in enumerate(dates):
        open_price = base_price + random.uniform(-200, 200)
        close_price = open_price + random.uniform(-150, 150)
        high_price = max(open_price, close_price) + random.uniform(0, 100)
        low_price = min(open_price, close_price) - random.uniform(0, 100)
        
        data.append({
            'date': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price
        })
        base_price = close_price
    
    df = pd.DataFrame(data)
    
    fig = go.Figure(data=[go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='BTC/USDT'
    )])
    
    fig.update_layout(
        title='BTC/USDT 15분 차트',
        yaxis_title='가격 (USDT)',
        xaxis_title='시간',
        height=400,
        template='plotly_dark'
    )
    
    return fig

def create_coin_chart(symbol, base_price):
    """코인별 미니 차트 생성"""
    dates = pd.date_range(end=datetime.now(), periods=30, freq='5min')
    prices = [base_price + random.uniform(-base_price*0.02, base_price*0.02) for _ in range(30)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        line=dict(color='#00ff00' if prices[-1] > prices[0] else '#ff0000', width=2),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False),
        template='plotly_dark'
    )
    
    return fig

def create_training_chart(metric_name, epochs=50):
    """학습 지표 차트 생성"""
    x = list(range(1, epochs + 1))
    
    if metric_name == 'Loss':
        y = [2.5 - (i * 0.04) + random.uniform(-0.1, 0.1) for i in range(epochs)]
        color = '#ff6b6b'
    elif metric_name == 'mAP50':
        y = [0.3 + (i * 0.012) + random.uniform(-0.02, 0.02) for i in range(epochs)]
        color = '#4ecdc4'
    else:  # Precision
        y = [0.4 + (i * 0.01) + random.uniform(-0.02, 0.02) for i in range(epochs)]
        color = '#95e1d3'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title=metric_name,
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        template='plotly_dark'
    )
    
    return fig

def create_equity_curve():
    """백테스트 수익률 곡선 차트"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='D')
    initial = 10000
    equity = [initial]
    
    for _ in range(len(dates) - 1):
        change = equity[-1] * random.uniform(-0.02, 0.03)
        equity.append(equity[-1] + change)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity,
        mode='lines',
        line=dict(color='#00ff00', width=2),
        fill='tozeroy',
        name='수익률'
    ))
    
    fig.update_layout(
        title='수익률 곡선',
        yaxis_title='자산 (USDT)',
        xaxis_title='날짜',
        height=400,
        template='plotly_dark'
    )
    
    return fig

def create_monthly_returns():
    """월별 수익률 차트"""
    months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월']
    returns = [random.uniform(-5, 15) for _ in range(11)]
    colors = ['#00ff00' if r > 0 else '#ff0000' for r in returns]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months,
        y=returns,
        marker_color=colors
    ))
    
    fig.update_layout(
        title='월별 수익률',
        yaxis_title='수익률 (%)',
        xaxis_title='월',
        height=400,
        template='plotly_dark'
    )
    
    return fig

# 메인 타이틀
st.title("🤖 YOLO 트레이딩 봇")
st.caption(f"마지막 업데이트: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 대시보드",
    "📈 실시간 거래",
    "🎓 YOLO 학습",
    "📉 백테스트"
])

# ===== 탭 1: 대시보드 =====
with tab1:
    st.header("대시보드")
    
    # 봇 제어 버튼
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("▶️ 시작", use_container_width=True, type="primary"):
            st.session_state.bot_running = True
            st.success("봇이 시작되었습니다!")
    with col2:
        if st.button("⏸️ 중지", use_container_width=True):
            st.session_state.bot_running = False
            st.warning("봇이 중지되었습니다.")
    with col3:
        if st.button("🚨 긴급 청산", use_container_width=True, type="secondary"):
            st.error("모든 포지션이 청산되었습니다!")
    with col4:
        st.checkbox("자동 새로고침", value=st.session_state.auto_refresh, key='auto_refresh')
    
    st.divider()
    
    # 계좌 현황
    account = get_account_data()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 잔고", f"${account['balance']:,.2f}", f"{account['profit_pct']:+.2f}%")
    with col2:
        win_rate = (account['winning_trades'] / account['total_trades'] * 100)
        st.metric("🎯 승률", f"{win_rate:.1f}%", f"{account['winning_trades']}/{account['total_trades']}")
    with col3:
        st.metric("📊 활성 포지션", account['positions_count'], "2개")
    with col4:
        st.metric("📈 Sharpe 비율", f"{account['sharpe_ratio']:.2f}", "+0.12")
    
    st.divider()
    
    # 성과 지표
    st.subheader("성과 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 거래", account['total_trades'])
    with col2:
        st.metric("평균 수익", f"${account['avg_profit']:.2f}")
    with col3:
        st.metric("평균 손실", f"${account['avg_loss']:.2f}")
    with col4:
        profit_factor = abs(account['avg_profit'] / account['avg_loss'])
        st.metric("Profit Factor", f"{profit_factor:.2f}")
    
    st.divider()
    
    # 활성 포지션과 차트
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("활성 포지션")
        positions_df = get_active_positions()
        st.dataframe(positions_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("BTC/USDT 차트")
        st.plotly_chart(create_candlestick_chart(), use_container_width=True)
    
    st.divider()
    
    # 최근 거래 내역
    st.subheader("최근 거래 내역")
    trades_df = get_recent_trades()
    st.dataframe(trades_df, use_container_width=True, hide_index=True)

# ===== 탭 2: 실시간 거래 =====
with tab2:
    st.header("실시간 거래")
    
    # 3개 코인 동시 모니터링
    coins = [
        {'symbol': 'BTC/USDT', 'price': 43850.00, 'change': 2.34, 'rsi': 58.5, 'macd': 'BULLISH'},
        {'symbol': 'ETH/USDT', 'price': 2285.50, 'change': -1.23, 'rsi': 45.2, 'macd': 'BEARISH'},
        {'symbol': 'SOL/USDT', 'price': 98.75, 'change': 4.56, 'rsi': 67.8, 'macd': 'BULLISH'}
    ]
    
    for coin in coins:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.subheader(coin['symbol'])
                change_color = "🟢" if coin['change'] > 0 else "🔴"
                st.write(f"{change_color} ${coin['price']:,.2f} ({coin['change']:+.2f}%)")
            
            with col2:
                st.metric("RSI", f"{coin['rsi']:.1f}")
            
            with col3:
                st.metric("MACD", coin['macd'])
            
            with col4:
                if st.button(f"청산", key=f"close_{coin['symbol']}"):
                    st.success(f"{coin['symbol']} 포지션 청산!")
            
            # 미니 차트
            st.plotly_chart(create_coin_chart(coin['symbol'], coin['price']), use_container_width=True)
        
        st.divider()
    
    # 실시간 신호 알림
    st.subheader("실시간 신호 알림")
    signal_log = [
        "🟢 14:23 - BTC/USDT: Bull Flag 패턴 감지 (신뢰도 85%)",
        "🔴 13:45 - ETH/USDT: Bear Flag 패턴 감지 (신뢰도 78%)",
        "🟢 13:12 - SOL/USDT: Ascending Triangle 패턴 감지 (신뢰도 72%)",
        "⚠️ 12:55 - BTC/USDT: RSI 과매수 구간 진입",
        "🟢 12:30 - ETH/USDT: Double Bottom 패턴 완성"
    ]
    
    for log in signal_log:
        st.text(log)

# ===== 탭 3: YOLO 학습 =====
with tab3:
    st.header("YOLO 학습")
    
    col1, col2 = st.columns([1, 1])
    
    # 학습 설정
    with col1:
        st.subheader("학습 설정")
        
        mode = st.selectbox(
            "학습 모드",
            ["전체 학습", "빠른 학습", "커스텀"]
        )
        
        if mode == "커스텀":
            images = st.slider("이미지 개수", 100, 10000, 1000, 100)
            epochs = st.slider("에포크", 10, 200, 50, 10)
            batch = st.slider("배치 크기", 8, 64, 16, 8)
        else:
            images = 1000 if mode == "전체 학습" else 500
            epochs = 50 if mode == "전체 학습" else 25
            batch = 16
            st.info(f"이미지: {images}, 에포크: {epochs}, 배치: {batch}")
        
        st.multiselect(
            "학습 심볼",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"],
            default=["BTC/USDT", "ETH/USDT"]
        )
        
        st.multiselect(
            "타임프레임",
            ["5m", "15m", "1h", "4h"],
            default=["15m", "4h"]
        )
        
        if st.button("🚀 학습 시작", use_container_width=True, type="primary"):
            st.success("학습이 시작되었습니다!")
    
    # GPU 상태
    with col2:
        st.subheader("GPU 상태")
        
        st.write("**GPU:** NVIDIA GeForce RTX 3050")
        st.write("**온도:** 62°C")
        
        st.progress(0.45, text="GPU 사용률: 45%")
        st.progress(0.38, text="VRAM 사용: 3.0GB / 8GB")
    
    st.divider()
    
    # 학습 진행률
    st.subheader("학습 진행률")
    col1, col2 = st.columns(2)
    
    with col1:
        st.progress(0.65, text="전체 진행률: 65%")
    with col2:
        st.progress(0.32, text="에포크 16/50 (32%)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("경과 시간", "1시간 23분")
    with col2:
        st.metric("남은 시간", "약 48분")
    
    st.divider()
    
    # 학습 지표 차트
    st.subheader("학습 지표")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.plotly_chart(create_training_chart('Loss'), use_container_width=True)
    with col2:
        st.plotly_chart(create_training_chart('mAP50'), use_container_width=True)
    with col3:
        st.plotly_chart(create_training_chart('Precision'), use_container_width=True)
    
    st.divider()
    
    # 학습 로그
    st.subheader("학습 로그")
    log_text = """
[14:23:45] Epoch 16/50
[14:23:46] Loss: 0.482, mAP50: 0.745, Precision: 0.812
[14:23:47] Training on 1000 images, validating on 200 images
[14:23:50] Best model saved at epoch 15
[14:23:51] GPU Memory: 3.2GB / 8GB (40%)
    """
    st.text_area("", log_text, height=150, disabled=True)

# ===== 탭 4: 백테스트 =====
with tab4:
    st.header("백테스트")
    
    col1, col2 = st.columns([1, 2])
    
    # 백테스트 설정
    with col1:
        st.subheader("백테스트 설정")
        
        start_date = st.date_input(
            "시작 날짜",
            datetime(2024, 1, 1)
        )
        
        end_date = st.date_input(
            "종료 날짜",
            datetime(2024, 12, 1)
        )
        
        initial_capital = st.number_input(
            "초기 자금 (USDT)",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000
        )
        
        strategy = st.selectbox(
            "전략",
            ["YOLO + 기술적 분석", "YOLO 전용", "기술적 분석 전용"]
        )
        
        leverage = st.slider("레버리지", 1, 20, 10)
        
        if st.button("🚀 백테스트 실행", use_container_width=True, type="primary"):
            st.success("백테스트가 완료되었습니다!")
    
    # 성과 요약
    with col2:
        st.subheader("성과 요약")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 수익률", "+24.5%", "+$2,450")
        with col2:
            st.metric("승률", "62.2%", "+5.2%")
        with col3:
            st.metric("MDD", "-8.5%", "양호")
        with col4:
            st.metric("총 거래", "45", "")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sharpe 비율", "1.42", "+0.18")
        with col2:
            st.metric("Profit Factor", "1.85", "")
        with col3:
            st.metric("평균 수익", "$54.44", "")
        with col4:
            st.metric("평균 손실", "$-29.42", "")
    
    st.divider()
    
    # 수익률 곡선
    st.subheader("수익률 곡선")
    st.plotly_chart(create_equity_curve(), use_container_width=True)
    
    st.divider()
    
    # 월별 수익률
    st.subheader("월별 수익률")
    st.plotly_chart(create_monthly_returns(), use_container_width=True)

# 자동 새로고침
if st.session_state.auto_refresh:
    time.sleep(5)
    st.rerun()
