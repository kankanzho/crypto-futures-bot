"""
Streamlit dashboard for monitoring and controlling the trading bot.
Run with: streamlit run src/gui/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import load_config, load_strategy_config, format_price, format_percentage
from exchange import BybitClient
from strategies import RSIStrategy, MACDStrategy, BollingerStrategy, EMACrossStrategy


# Page configuration
st.set_page_config(
    page_title="Crypto Futures Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive {
        color: #00ff00;
    }
    .negative {
        color: #ff0000;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_configurations():
    """Load bot configurations."""
    try:
        config = load_config()
        strategy_config = load_strategy_config()
        return config, strategy_config
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        return None, None


def create_candlestick_chart(df: pd.DataFrame, indicators: dict = None):
    """Create candlestick chart with indicators."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('Price', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC'
        ),
        row=1, col=1
    )
    
    # Add indicators if provided
    if indicators:
        if 'ema_fast' in indicators:
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['ema_fast'], 
                          name='EMA Fast', line=dict(color='blue', width=1)),
                row=1, col=1
            )
        if 'ema_slow' in indicators:
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['ema_slow'],
                          name='EMA Slow', line=dict(color='red', width=1)),
                row=1, col=1
            )
        if 'bb_upper' in indicators:
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['bb_upper'],
                          name='BB Upper', line=dict(color='gray', width=1, dash='dash')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['bb_lower'],
                          name='BB Lower', line=dict(color='gray', width=1, dash='dash')),
                row=1, col=1
            )
    
    # Volume
    colors = ['red' if close < open else 'green' 
              for close, open in zip(df['close'], df['open'])]
    fig.add_trace(
        go.Bar(x=df.index, y=df['volume'], name='Volume',
               marker_color=colors),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        template='plotly_dark'
    )
    
    return fig


def create_equity_curve(equity_data: list, timestamps: list):
    """Create equity curve chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=equity_data,
        mode='lines',
        name='Equity',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Time',
        yaxis_title='Equity ($)',
        height=400,
        template='plotly_dark'
    )
    
    return fig


def main():
    """Main dashboard function."""
    
    # Title
    st.title("📈 Crypto Futures Trading Bot Dashboard")
    
    # Load configurations
    config, strategy_config = load_configurations()
    
    if config is None:
        st.error("Failed to load configuration. Please check config files.")
        return
    
    # Sidebar - Controls
    st.sidebar.header("🎛️ Controls")
    
    # Bot status
    bot_status = st.sidebar.selectbox(
        "Bot Status",
        ["Stopped", "Running", "Paused"]
    )
    
    if bot_status == "Stopped":
        if st.sidebar.button("▶️ Start Bot", key="start"):
            st.sidebar.success("Bot started!")
    elif bot_status == "Running":
        if st.sidebar.button("⏸️ Pause Bot", key="pause"):
            st.sidebar.warning("Bot paused")
        if st.sidebar.button("⏹️ Stop Bot", key="stop"):
            st.sidebar.error("Bot stopped")
    
    if st.sidebar.button("🚨 Emergency Stop", key="emergency"):
        st.sidebar.error("EMERGENCY STOP ACTIVATED")
    
    st.sidebar.divider()
    
    # Strategy selection
    st.sidebar.header("📊 Strategy")
    
    available_strategies = ["RSI", "MACD", "Bollinger Bands", "EMA Crossover"]
    selected_strategy = st.sidebar.selectbox("Select Strategy", available_strategies)
    
    # Strategy parameters (example for RSI)
    if selected_strategy == "RSI":
        st.sidebar.subheader("RSI Parameters")
        rsi_period = st.sidebar.slider("Period", 5, 30, 14)
        rsi_oversold = st.sidebar.slider("Oversold", 10, 40, 30)
        rsi_overbought = st.sidebar.slider("Overbought", 60, 90, 70)
    
    st.sidebar.divider()
    
    # Risk management
    st.sidebar.header("🛡️ Risk Management")
    risk_per_trade = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 2.0, 0.5)
    max_positions = st.sidebar.slider("Max Positions", 1, 10, 4)
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Charts", "💼 Positions", "📜 History"])
    
    with tab1:
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Equity",
                value="$10,250.00",
                delta="$250.00 (2.5%)"
            )
        
        with col2:
            st.metric(
                label="Today's P&L",
                value="$125.50",
                delta="1.25%"
            )
        
        with col3:
            st.metric(
                label="Win Rate",
                value="58.5%",
                delta="3.5%"
            )
        
        with col4:
            st.metric(
                label="Open Positions",
                value="2/4",
                delta=None
            )
        
        st.divider()
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Performance Metrics")
            metrics_df = pd.DataFrame({
                'Metric': [
                    'Total Return',
                    'Sharpe Ratio',
                    'Max Drawdown',
                    'Profit Factor',
                    'Total Trades',
                    'Avg Win',
                    'Avg Loss'
                ],
                'Value': [
                    '12.5%',
                    '1.85',
                    '-5.2%',
                    '2.3',
                    '45',
                    '$45.20',
                    '-$19.80'
                ]
            })
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("📈 Equity Curve")
            # Sample equity curve
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            equity = [10000 + i*10 + (i**2)*0.5 for i in range(30)]
            fig = create_equity_curve(equity, dates)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Active coins
        st.subheader("💰 Active Coins")
        
        coins_data = []
        for coin in config['trading']['coins']:
            if coin.get('enabled', False):
                coins_data.append({
                    'Symbol': coin['symbol'],
                    'Allocation': f"{coin['allocation']*100}%",
                    'Leverage': f"{coin['leverage']}x",
                    'Status': '✅ Active'
                })
        
        coins_df = pd.DataFrame(coins_data)
        st.dataframe(coins_df, hide_index=True, use_container_width=True)
    
    with tab2:
        # Charts tab
        st.subheader("📈 Market Charts")
        
        # Symbol selection
        active_symbols = [c['symbol'] for c in config['trading']['coins'] if c.get('enabled')]
        selected_symbol = st.selectbox("Select Symbol", active_symbols)
        
        # Timeframe selection
        timeframe = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "1h", "4h", "1d"])
        
        # Sample chart data
        st.info("Chart data would be loaded from exchange here")
        
        # Create sample DataFrame
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1min')
        sample_df = pd.DataFrame({
            'open': [50000 + i*10 for i in range(100)],
            'high': [50100 + i*10 for i in range(100)],
            'low': [49900 + i*10 for i in range(100)],
            'close': [50050 + i*10 for i in range(100)],
            'volume': [100 + i for i in range(100)]
        }, index=dates)
        
        fig = create_candlestick_chart(sample_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Indicator values
        st.subheader("📊 Current Indicators")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("RSI", "45.2", "-5.3")
        with col2:
            st.metric("MACD", "125.5", "+12.3")
        with col3:
            st.metric("ATR", "850.2", "+25.1")
    
    with tab3:
        # Positions tab
        st.subheader("💼 Open Positions")
        
        # Sample positions
        positions_data = [
            {
                'Symbol': 'BTCUSDT',
                'Side': 'Long',
                'Size': '0.1',
                'Entry': '$50,000',
                'Current': '$50,500',
                'P&L': '$50.00',
                'P&L %': '+1.0%'
            },
            {
                'Symbol': 'ETHUSDT',
                'Side': 'Short',
                'Size': '1.5',
                'Entry': '$3,000',
                'Current': '$2,950',
                'P&L': '$75.00',
                'P&L %': '+1.67%'
            }
        ]
        
        if positions_data:
            positions_df = pd.DataFrame(positions_data)
            
            # Color code P&L
            def color_pnl(val):
                if isinstance(val, str) and '%' in val:
                    num = float(val.strip('%+'))
                    color = 'green' if num > 0 else 'red' if num < 0 else 'gray'
                    return f'color: {color}'
                return ''
            
            styled_df = positions_df.style.applymap(color_pnl, subset=['P&L %'])
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
            
            # Position management
            st.subheader("Position Management")
            col1, col2 = st.columns(2)
            
            with col1:
                pos_to_close = st.selectbox("Select position to close", 
                                           [p['Symbol'] for p in positions_data])
            with col2:
                if st.button("Close Position"):
                    st.success(f"Position {pos_to_close} closed successfully")
        else:
            st.info("No open positions")
    
    with tab4:
        # History tab
        st.subheader("📜 Trade History")
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Sample trade history
        history_data = [
            {
                'Time': '2024-01-15 10:30',
                'Symbol': 'BTCUSDT',
                'Side': 'Long',
                'Entry': '$49,500',
                'Exit': '$50,000',
                'Size': '0.1',
                'P&L': '$50.00',
                'P&L %': '+1.01%'
            },
            {
                'Time': '2024-01-15 14:20',
                'Symbol': 'ETHUSDT',
                'Side': 'Short',
                'Entry': '$3,100',
                'Exit': '$3,050',
                'Size': '1.0',
                'P&L': '$50.00',
                'P&L %': '+1.61%'
            },
            {
                'Time': '2024-01-14 09:15',
                'Symbol': 'SOLUSDT',
                'Side': 'Long',
                'Entry': '$100',
                'Exit': '$98',
                'Size': '5.0',
                'P&L': '-$10.00',
                'P&L %': '-2.00%'
            }
        ]
        
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, hide_index=True, use_container_width=True)
        
        # Download button
        csv = history_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Trade History",
            data=csv,
            file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.divider()
    st.markdown("""
        <div style='text-align: center; color: gray;'>
        <small>Crypto Futures Trading Bot v1.0 | ⚠️ Trading involves risk. Use at your own discretion.</small>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
