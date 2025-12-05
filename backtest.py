"""
Backtesting Module for Hybrid Crypto Futures Trading Bot
하이브리드 암호화폐 선물 트레이딩 봇 백테스트 모듈

Provides backtesting functionality to test trading strategies on historical data.
과거 데이터로 트레이딩 전략을 테스트하는 백테스트 기능 제공
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import ccxt
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Import from main bot
from bybit_yolo_bot import BybitYoloBot

# Configure logging / 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Backtester:
    """
    Backtesting engine for YOLO trading strategy
    YOLO 트레이딩 전략 백테스트 엔진
    """
    
    def __init__(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0,
        symbol: str = 'BTC/USDT:USDT',
        leverage: int = 3
    ):
        """
        Initialize backtester
        백테스터 초기화
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            initial_capital: Initial capital in USDT
            symbol: Trading symbol
            leverage: Trading leverage
        """
        load_dotenv()
        
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.symbol = symbol
        self.leverage = leverage
        
        # Trading records / 거래 기록
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []
        
        # Initialize exchange for data fetching / 데이터 가져오기용 거래소 초기화
        self._initialize_exchange()
        
        # Initialize bot for strategy logic / 전략 로직용 봇 초기화
        self.bot = BybitYoloBot()
        
        logger.info(f"Backtester initialized: {start_date} to {end_date}")
        logger.info(f"Initial capital: ${initial_capital:.2f} USDT")
    
    def _initialize_exchange(self):
        """
        Initialize exchange for historical data fetching
        과거 데이터 가져오기를 위한 거래소 초기화
        """
        try:
            api_key = os.getenv('BYBIT_API_KEY')
            api_secret = os.getenv('BYBIT_API_SECRET')
            
            # For backtesting, we only need public data access
            # 백테스트는 공개 데이터만 필요
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                }
            })
            
            self.exchange.load_markets()
            logger.info("Exchange initialized for backtesting")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise
    
    def load_historical_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load historical OHLCV data for both timeframes
        두 타임프레임의 과거 OHLCV 데이터 로드
        
        Returns:
            Tuple of (main_df, trend_df) DataFrames
        """
        try:
            logger.info("Loading historical data...")
            
            # Convert dates to milliseconds / 날짜를 밀리초로 변환
            start_ms = int(self.start_date.timestamp() * 1000)
            end_ms = int(self.end_date.timestamp() * 1000)
            
            # Fetch main timeframe data (15m)
            # 메인 타임프레임 데이터 가져오기 (15m)
            main_ohlcv = []
            current_ms = start_ms
            
            while current_ms < end_ms:
                data = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe=self.bot.main_timeframe,
                    since=current_ms,
                    limit=1000
                )
                
                if not data:
                    break
                
                main_ohlcv.extend(data)
                current_ms = data[-1][0] + 1
                
                # Rate limiting / 레이트 제한
                self.exchange.sleep(self.exchange.rateLimit)
            
            main_df = pd.DataFrame(
                main_ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            main_df['timestamp'] = pd.to_datetime(main_df['timestamp'], unit='ms')
            main_df.set_index('timestamp', inplace=True)
            main_df = main_df[~main_df.index.duplicated(keep='first')]
            
            # Fetch trend timeframe data (4h)
            # 트렌드 타임프레임 데이터 가져오기 (4h)
            trend_ohlcv = []
            current_ms = start_ms
            
            while current_ms < end_ms:
                data = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe=self.bot.trend_timeframe,
                    since=current_ms,
                    limit=1000
                )
                
                if not data:
                    break
                
                trend_ohlcv.extend(data)
                current_ms = data[-1][0] + 1
                
                # Rate limiting / 레이트 제한
                self.exchange.sleep(self.exchange.rateLimit)
            
            trend_df = pd.DataFrame(
                trend_ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            trend_df['timestamp'] = pd.to_datetime(trend_df['timestamp'], unit='ms')
            trend_df.set_index('timestamp', inplace=True)
            trend_df = trend_df[~trend_df.index.duplicated(keep='first')]
            
            logger.info(f"Loaded {len(main_df)} candles for {self.bot.main_timeframe}")
            logger.info(f"Loaded {len(trend_df)} candles for {self.bot.trend_timeframe}")
            
            return main_df, trend_df
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            raise
    
    def simulate_trade(
        self,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size_usdt: float,
        entry_time: datetime,
        future_data: pd.DataFrame
    ) -> Dict:
        """
        Simulate a single trade execution and outcome
        단일 거래 실행 및 결과 시뮬레이션
        
        Args:
            side: 'long' or 'short'
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            position_size_usdt: Position size in USDT
            entry_time: Entry timestamp
            future_data: Future price data after entry
        
        Returns:
            Trade result dictionary
        """
        try:
            # Calculate position size with leverage
            # 레버리지를 적용한 포지션 크기 계산
            # position_size_usdt = margin/collateral used
            # notional_value = total position value with leverage
            notional_value = position_size_usdt * self.leverage
            position_size = notional_value / entry_price
            
            # Simulate price movement to find exit
            # 가격 움직임 시뮬레이션하여 청산 찾기
            exit_price = None
            exit_time = None
            exit_reason = None
            
            for idx, row in future_data.iterrows():
                if side == 'long':
                    # Check if stop loss hit / 손절가 도달 확인
                    if row['low'] <= stop_loss:
                        exit_price = stop_loss
                        exit_time = idx
                        exit_reason = 'stop_loss'
                        break
                    # Check if take profit hit / 목표가 도달 확인
                    elif row['high'] >= take_profit:
                        exit_price = take_profit
                        exit_time = idx
                        exit_reason = 'take_profit'
                        break
                else:  # short
                    # Check if stop loss hit / 손절가 도달 확인
                    if row['high'] >= stop_loss:
                        exit_price = stop_loss
                        exit_time = idx
                        exit_reason = 'stop_loss'
                        break
                    # Check if take profit hit / 목표가 도달 확인
                    elif row['low'] <= take_profit:
                        exit_price = take_profit
                        exit_time = idx
                        exit_reason = 'take_profit'
                        break
            
            # If no exit found, use last price (force close)
            # 청산 없으면 마지막 가격 사용 (강제 청산)
            if exit_price is None:
                exit_price = future_data.iloc[-1]['close']
                exit_time = future_data.index[-1]
                exit_reason = 'end_of_backtest'
            
            # Calculate PnL / 손익 계산
            # PnL is calculated on the full notional position size
            # PnL 계산은 전체 명목 포지션 크기로 수행
            if side == 'long':
                pnl = (exit_price - entry_price) * position_size
            else:  # short
                pnl = (entry_price - exit_price) * position_size
            
            # PnL percentage is relative to margin (position_size_usdt), not notional
            # PnL 퍼센트는 명목가가 아닌 마진(position_size_usdt)에 상대적
            pnl_percent = (pnl / position_size_usdt) * 100
            
            trade_result = {
                'entry_time': entry_time,
                'exit_time': exit_time,
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position_size': position_size,
                'position_size_usdt': position_size_usdt,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'exit_reason': exit_reason
            }
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Failed to simulate trade: {e}")
            raise
    
    def run(self) -> Dict:
        """
        Run backtest simulation
        백테스트 시뮬레이션 실행
        
        Returns:
            Performance metrics dictionary
        """
        try:
            logger.info("=" * 80)
            logger.info("Starting backtest...")
            logger.info("=" * 80)
            
            # Load historical data / 과거 데이터 로드
            main_df, trend_df = self.load_historical_data()
            
            # Ensure we have enough data for indicators
            # 지표 계산에 충분한 데이터 확인
            if len(main_df) < 200 or len(trend_df) < 200:
                raise ValueError("Insufficient data for indicators (need at least 200 candles)")
            
            # Iterate through time periods / 시간대별 반복
            # Track the last exit time to prevent immediate re-entry
            # 마지막 청산 시간을 추적하여 즉시 재진입 방지
            last_exit_index = -1
            
            # Start from index 200 to have enough data for indicators
            # 지표 계산을 위해 인덱스 200부터 시작
            for i in range(200, len(main_df)):
                current_time = main_df.index[i]
                
                # Skip if we just exited a trade (prevent immediate re-entry)
                # 거래를 막 청산한 경우 건너뛰기 (즉시 재진입 방지)
                if i <= last_exit_index:
                    continue
                
                # Get data up to current point / 현재 시점까지 데이터 가져오기
                main_subset = main_df.iloc[:i+1]
                trend_subset = trend_df[trend_df.index <= current_time]
                
                # Ensure we have enough trend data / 충분한 트렌드 데이터 확인
                if len(trend_subset) < 200:
                    continue
                
                # Calculate indicators / 지표 계산
                try:
                    indicators = self.bot.calculate_indicators(
                        main_subset.tail(200).copy(),
                        trend_subset.tail(200).copy()
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate indicators at {current_time}: {e}")
                    continue
                
                # Generate chart and detect patterns (simplified for backtest)
                # 차트 생성 및 패턴 탐지 (백테스트용 간소화)
                # Note: In real backtest, you might want to skip YOLO detection
                # to speed up simulation, or use cached pattern data
                # 실제 백테스트에서는 YOLO 탐지를 건너뛰거나
                # 캐시된 패턴 데이터를 사용하여 시뮬레이션 속도 향상
                
                try:
                    chart_image = self.bot.generate_chart_image(main_subset.tail(50).copy())
                    patterns = self.bot.detect_pattern(chart_image)
                except Exception as e:
                    logger.warning(f"Failed to detect patterns at {current_time}: {e}")
                    patterns = []
                
                # Use funding rate = 0 for simplicity in backtest
                # 백테스트 간소화를 위해 펀딩 비율 = 0 사용
                funding_rate = 0.0
                
                # Check long conditions / 롱 조건 확인
                should_long, long_reason = self.bot.check_long_conditions(
                    indicators, patterns, funding_rate
                )
                
                if should_long:
                    # Calculate position details / 포지션 세부사항 계산
                    entry_price = indicators['current_price']
                    stop_loss, take_profit = self.bot.calculate_sl_tp(
                        entry_price,
                        indicators['atr'],
                        'long'
                    )
                    
                    # Simulate trade / 거래 시뮬레이션
                    future_data = main_df.iloc[i+1:]
                    if len(future_data) > 0:
                        trade_result = self.simulate_trade(
                            side='long',
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            position_size_usdt=self.bot.position_size_usdt,
                            entry_time=current_time,
                            future_data=future_data
                        )
                        
                        # Update capital / 자본 업데이트
                        self.current_capital += trade_result['pnl']
                        self.trades.append(trade_result)
                        
                        logger.info(f"LONG trade: {trade_result['entry_time']} -> {trade_result['exit_time']}")
                        logger.info(f"PnL: ${trade_result['pnl']:.2f} ({trade_result['pnl_percent']:.2f}%)")
                        logger.info(f"Capital: ${self.current_capital:.2f}")
                        
                        # Update last exit index to prevent immediate re-entry
                        # 즉시 재진입 방지를 위해 마지막 청산 인덱스 업데이트
                        exit_idx = main_df.index.get_loc(trade_result['exit_time'])
                        last_exit_index = exit_idx
                
                else:
                    # Check short conditions / 숏 조건 확인
                    should_short, short_reason = self.bot.check_short_conditions(
                        indicators, patterns, funding_rate
                    )
                    
                    if should_short:
                        # Calculate position details / 포지션 세부사항 계산
                        entry_price = indicators['current_price']
                        stop_loss, take_profit = self.bot.calculate_sl_tp(
                            entry_price,
                            indicators['atr'],
                            'short'
                        )
                        
                        # Simulate trade / 거래 시뮬레이션
                        future_data = main_df.iloc[i+1:]
                        if len(future_data) > 0:
                            trade_result = self.simulate_trade(
                                side='short',
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                position_size_usdt=self.bot.position_size_usdt,
                                entry_time=current_time,
                                future_data=future_data
                            )
                            
                            # Update capital / 자본 업데이트
                            self.current_capital += trade_result['pnl']
                            self.trades.append(trade_result)
                            
                            logger.info(f"SHORT trade: {trade_result['entry_time']} -> {trade_result['exit_time']}")
                            logger.info(f"PnL: ${trade_result['pnl']:.2f} ({trade_result['pnl_percent']:.2f}%)")
                            logger.info(f"Capital: ${self.current_capital:.2f}")
                            
                            # Update last exit index to prevent immediate re-entry
                            # 즉시 재진입 방지를 위해 마지막 청산 인덱스 업데이트
                            exit_idx = main_df.index.get_loc(trade_result['exit_time'])
                            last_exit_index = exit_idx
                
                # Record equity / 자산 기록
                self.equity_curve.append({
                    'timestamp': current_time,
                    'equity': self.current_capital
                })
            
            # Calculate performance metrics / 성과 지표 계산
            metrics = self.calculate_metrics()
            
            logger.info("=" * 80)
            logger.info("Backtest completed!")
            logger.info("=" * 80)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise
    
    def calculate_metrics(self) -> Dict:
        """
        Calculate performance metrics
        성과 지표 계산
        
        Returns:
            Dictionary of performance metrics
        """
        try:
            if len(self.trades) == 0:
                logger.warning("No trades executed during backtest")
                return {
                    'total_trades': 0,
                    'total_return': 0.0,
                    'total_return_percent': 0.0,
                    'max_drawdown': 0.0,
                    'max_drawdown_percent': 0.0,
                    'sharpe_ratio': 0.0,
                    'win_rate': 0.0,
                    'avg_profit_loss_ratio': 0.0,
                    'avg_trade_pnl': 0.0,
                    'winning_trades': 0,
                    'losing_trades': 0
                }
            
            # Total return / 총 수익률
            total_return = self.current_capital - self.initial_capital
            total_return_percent = (total_return / self.initial_capital) * 100
            
            # Win rate / 승률
            winning_trades = [t for t in self.trades if t['pnl'] > 0]
            losing_trades = [t for t in self.trades if t['pnl'] <= 0]
            win_rate = (len(winning_trades) / len(self.trades)) * 100
            
            # Average profit/loss ratio / 평균 손익비
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            avg_loss = abs(np.mean([t['pnl'] for t in losing_trades])) if losing_trades else 0
            avg_profit_loss_ratio = avg_win / avg_loss if avg_loss != 0 else 0
            
            # Max drawdown / 최대 낙폭
            equity_values = [e['equity'] for e in self.equity_curve]
            peak = equity_values[0]
            max_drawdown = 0
            
            for value in equity_values:
                if value > peak:
                    peak = value
                drawdown = peak - value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            max_drawdown_percent = (max_drawdown / self.initial_capital) * 100 if self.initial_capital > 0 else 0
            
            # Sharpe ratio / 샤프 비율
            # Simplified calculation using trade returns
            # 거래 수익률을 사용한 간소화된 계산
            if len(self.trades) > 1:
                returns = [t['pnl_percent'] for t in self.trades]
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return) if std_return != 0 else 0
            else:
                sharpe_ratio = 0.0
            
            # Average trade PnL / 평균 거래 손익
            avg_trade_pnl = np.mean([t['pnl'] for t in self.trades])
            
            metrics = {
                'total_trades': len(self.trades),
                'total_return': total_return,
                'total_return_percent': total_return_percent,
                'max_drawdown': max_drawdown,
                'max_drawdown_percent': max_drawdown_percent,
                'sharpe_ratio': sharpe_ratio,
                'win_rate': win_rate,
                'avg_profit_loss_ratio': avg_profit_loss_ratio,
                'avg_trade_pnl': avg_trade_pnl,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'initial_capital': self.initial_capital,
                'final_capital': self.current_capital
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            raise
    
    def save_results(self, output_dir: str = 'backtest_results'):
        """
        Save backtest results to files
        백테스트 결과를 파일로 저장
        
        Args:
            output_dir: Directory to save results
        """
        try:
            # Create output directory / 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save trades to CSV / 거래 내역 CSV로 저장
            if self.trades:
                trades_df = pd.DataFrame(self.trades)
                trades_file = os.path.join(output_dir, f'trades_{timestamp}.csv')
                trades_df.to_csv(trades_file, index=False)
                logger.info(f"Trades saved to {trades_file}")
            
            # Save equity curve to CSV / 자산 곡선 CSV로 저장
            if self.equity_curve:
                equity_df = pd.DataFrame(self.equity_curve)
                equity_file = os.path.join(output_dir, f'equity_{timestamp}.csv')
                equity_df.to_csv(equity_file, index=False)
                logger.info(f"Equity curve saved to {equity_file}")
            
            # Save metrics to JSON / 지표 JSON으로 저장
            metrics = self.calculate_metrics()
            metrics_file = os.path.join(output_dir, f'metrics_{timestamp}.json')
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=4, default=str)
            logger.info(f"Metrics saved to {metrics_file}")
            
            # Generate markdown report / 마크다운 리포트 생성
            self.generate_report(output_dir, timestamp, metrics)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def generate_report(self, output_dir: str, timestamp: str, metrics: Dict):
        """
        Generate markdown backtest report
        마크다운 백테스트 리포트 생성
        
        Args:
            output_dir: Output directory
            timestamp: Timestamp for filename
            metrics: Performance metrics
        """
        try:
            report_file = os.path.join(output_dir, f'report_{timestamp}.md')
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# Backtest Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## Test Period\n\n")
                f.write(f"- **Start Date:** {self.start_date.strftime('%Y-%m-%d')}\n")
                f.write(f"- **End Date:** {self.end_date.strftime('%Y-%m-%d')}\n")
                f.write(f"- **Symbol:** {self.symbol}\n\n")
                
                f.write(f"## Capital\n\n")
                f.write(f"- **Initial Capital:** ${metrics['initial_capital']:.2f} USDT\n")
                f.write(f"- **Final Capital:** ${metrics['final_capital']:.2f} USDT\n")
                f.write(f"- **Total Return:** ${metrics['total_return']:.2f} ({metrics['total_return_percent']:.2f}%)\n\n")
                
                f.write(f"## Performance Metrics\n\n")
                f.write(f"| Metric | Value |\n")
                f.write(f"|--------|-------|\n")
                f.write(f"| Total Trades | {metrics['total_trades']} |\n")
                f.write(f"| Winning Trades | {metrics['winning_trades']} |\n")
                f.write(f"| Losing Trades | {metrics['losing_trades']} |\n")
                f.write(f"| Win Rate | {metrics['win_rate']:.2f}% |\n")
                f.write(f"| Average Trade PnL | ${metrics['avg_trade_pnl']:.2f} |\n")
                f.write(f"| Avg Profit/Loss Ratio | {metrics['avg_profit_loss_ratio']:.2f} |\n")
                f.write(f"| Max Drawdown | ${metrics['max_drawdown']:.2f} ({metrics['max_drawdown_percent']:.2f}%) |\n")
                f.write(f"| Sharpe Ratio | {metrics['sharpe_ratio']:.2f} |\n\n")
                
                f.write(f"## Strategy Configuration\n\n")
                f.write(f"- **Main Timeframe:** {self.bot.main_timeframe}\n")
                f.write(f"- **Trend Timeframe:** {self.bot.trend_timeframe}\n")
                f.write(f"- **Position Size:** ${self.bot.position_size_usdt} USDT\n")
                f.write(f"- **Leverage:** {self.leverage}x\n")
                f.write(f"- **ATR SL Multiplier:** {self.bot.atr_sl_multiplier}x\n")
                f.write(f"- **ATR TP Multiplier:** {self.bot.atr_tp_multiplier}x\n")
                f.write(f"- **YOLO Confidence:** {self.bot.yolo_confidence}\n\n")
                
                f.write(f"## Trade Summary\n\n")
                if self.trades:
                    f.write(f"### Recent Trades (Last 10)\n\n")
                    f.write(f"| Entry Time | Side | Entry | Exit | PnL | PnL % | Reason |\n")
                    f.write(f"|------------|------|-------|------|-----|-------|--------|\n")
                    
                    for trade in self.trades[-10:]:
                        f.write(f"| {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} | "
                               f"{trade['side'].upper()} | "
                               f"${trade['entry_price']:.2f} | "
                               f"${trade['exit_price']:.2f} | "
                               f"${trade['pnl']:.2f} | "
                               f"{trade['pnl_percent']:.2f}% | "
                               f"{trade['exit_reason']} |\n")
                
            logger.info(f"Report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
