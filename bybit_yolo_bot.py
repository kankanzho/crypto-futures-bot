"""
Hybrid Crypto Futures Trading Bot
하이브리드 암호화폐 선물 트레이딩 봇

Combines YOLOv8 chart pattern recognition with technical analysis
for automated futures trading on Bybit.

YOLOv8 차트 패턴 인식과 기술적 분석을 결합한
바이비트 선물 자동 거래 봇
"""

import os
import io
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import ccxt
import numpy as np
import pandas as pd
import cv2
from PIL import Image
import mplfinance as mpf
import matplotlib.pyplot as plt
from ultralytics import YOLO
from dotenv import load_dotenv

# Configure logging / 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BybitYoloBot:
    """
    Hybrid trading bot combining YOLO pattern detection and technical analysis
    YOLO 패턴 탐지와 기술적 분석을 결합한 하이브리드 트레이딩 봇
    """
    
    def __init__(self):
        """
        Initialize the bot with YOLO model and Bybit API
        YOLO 모델과 바이비트 API로 봇 초기화
        """
        # Load environment variables / 환경 변수 로드
        load_dotenv()
        
        # Trading parameters / 트레이딩 파라미터
        self.symbol = os.getenv('SYMBOL', 'BTC/USDT:USDT')
        self.position_size_usdt = float(os.getenv('POSITION_SIZE_USDT', '50'))
        self.atr_sl_multiplier = float(os.getenv('ATR_SL_MULTIPLIER', '2.0'))
        self.atr_tp_multiplier = float(os.getenv('ATR_TP_MULTIPLIER', '4.0'))
        self.yolo_confidence = float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', '0.7'))
        self.funding_rate_threshold = float(os.getenv('FUNDING_RATE_THRESHOLD', '0.0003'))
        self.main_timeframe = os.getenv('MAIN_TIMEFRAME', '15m')
        self.trend_timeframe = os.getenv('TREND_TIMEFRAME', '4h')
        
        # Pattern definitions / 패턴 정의
        self.bullish_patterns = [
            'bull_flag', 'double_bottom', 'inverse_head_and_shoulders',
            'ascending_triangle', 'bullish_engulfing'
        ]
        self.bearish_patterns = [
            'bear_flag', 'double_top', 'head_and_shoulders',
            'descending_triangle', 'bearish_engulfing'
        ]
        
        # Initialize YOLO model / YOLO 모델 초기화
        self._load_yolo_model()
        
        # Initialize Bybit API / 바이비트 API 초기화
        self._initialize_exchange()
        
        logger.info(f"Bot initialized for {self.symbol}")
        logger.info(f"Main timeframe: {self.main_timeframe}, Trend timeframe: {self.trend_timeframe}")
    
    def _load_yolo_model(self):
        """
        Load YOLO model with fallback
        YOLO 모델 로드 (폴백 포함)
        """
        try:
            # Try loading custom model / 커스텀 모델 로드 시도
            model_path = os.path.join('models', 'best_chart_patterns.pt')
            if os.path.exists(model_path):
                self.yolo_model = YOLO(model_path)
                logger.info(f"Loaded custom YOLO model: {model_path}")
            else:
                # Fallback to pretrained model / 사전 학습된 모델로 폴백
                self.yolo_model = YOLO('yolov8n.pt')
                logger.warning("Custom model not found, using YOLOv8n pretrained model")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            # Use pretrained as fallback / 폴백으로 사전 학습 모델 사용
            self.yolo_model = YOLO('yolov8n.pt')
            logger.info("Using YOLOv8n pretrained model as fallback")
    
    def _initialize_exchange(self):
        """
        Initialize Bybit exchange connection with ccxt
        ccxt를 사용한 바이비트 거래소 연결 초기화
        """
        try:
            api_key = os.getenv('BYBIT_API_KEY')
            api_secret = os.getenv('BYBIT_API_SECRET')
            
            if not api_key or not api_secret:
                raise ValueError("Bybit API credentials not found in environment variables")
            
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,  # Enable rate limiting / 레이트 리미트 활성화
                'options': {
                    'defaultType': 'future',  # Use futures / 선물 사용
                }
            })
            
            # Test connection / 연결 테스트
            self.exchange.load_markets()
            logger.info("Bybit API initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bybit API: {e}")
            raise
    
    def fetch_ohlcv_multi_timeframe(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch OHLCV data for both main and trend timeframes
        메인 및 트렌드 타임프레임의 OHLCV 데이터 가져오기
        
        Returns:
            Tuple of (main_df, trend_df) DataFrames
        """
        try:
            # Fetch main timeframe (15m) - 200 candles for indicators
            # 메인 타임프레임 (15m) - 지표 계산을 위한 200개 캔들
            main_ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.main_timeframe,
                limit=200
            )
            main_df = pd.DataFrame(
                main_ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            main_df['timestamp'] = pd.to_datetime(main_df['timestamp'], unit='ms')
            main_df.set_index('timestamp', inplace=True)
            
            # Fetch trend timeframe (4h) - 200 candles for EMA 200
            # 트렌드 타임프레임 (4h) - EMA 200 계산을 위한 200개 캔들
            trend_ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.trend_timeframe,
                limit=200
            )
            trend_df = pd.DataFrame(
                trend_ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            trend_df['timestamp'] = pd.to_datetime(trend_df['timestamp'], unit='ms')
            trend_df.set_index('timestamp', inplace=True)
            
            logger.info(f"Fetched {len(main_df)} candles for {self.main_timeframe}")
            logger.info(f"Fetched {len(trend_df)} candles for {self.trend_timeframe}")
            
            return main_df, trend_df
            
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data: {e}")
            raise
    
    def calculate_indicators(self, main_df: pd.DataFrame, trend_df: pd.DataFrame) -> Dict:
        """
        Calculate technical indicators
        기술적 지표 계산
        
        Args:
            main_df: Main timeframe DataFrame (15m)
            trend_df: Trend timeframe DataFrame (4h)
        
        Returns:
            Dictionary containing indicator values
        """
        indicators = {}
        
        try:
            # Calculate EMA 200 on trend timeframe (4h)
            # 트렌드 타임프레임에서 EMA 200 계산 (4h)
            trend_df['ema_200'] = trend_df['close'].ewm(span=200, adjust=False).mean()
            indicators['ema_200'] = trend_df['ema_200'].iloc[-1]
            
            # Calculate RSI on main timeframe (15m)
            # 메인 타임프레임에서 RSI 계산 (15m)
            delta = main_df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            main_df['rsi'] = 100 - (100 / (1 + rs))
            indicators['rsi'] = main_df['rsi'].iloc[-1]
            
            # Calculate ATR on main timeframe (15m)
            # 메인 타임프레임에서 ATR 계산 (15m)
            high_low = main_df['high'] - main_df['low']
            high_close = np.abs(main_df['high'] - main_df['close'].shift())
            low_close = np.abs(main_df['low'] - main_df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            main_df['atr'] = true_range.rolling(14).mean()
            indicators['atr'] = main_df['atr'].iloc[-1]
            
            # Get current price / 현재 가격 가져오기
            indicators['current_price'] = main_df['close'].iloc[-1]
            
            logger.info(f"Indicators calculated - Price: {indicators['current_price']:.2f}, "
                       f"EMA200: {indicators['ema_200']:.2f}, RSI: {indicators['rsi']:.2f}, "
                       f"ATR: {indicators['atr']:.2f}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            raise
    
    def fetch_funding_rate(self) -> float:
        """
        Fetch current funding rate from Bybit
        바이비트에서 현재 펀딩 비율 가져오기
        
        Returns:
            Current funding rate as a decimal
        """
        try:
            # Fetch funding rate / 펀딩 비율 가져오기
            ticker = self.exchange.fetch_ticker(self.symbol)
            
            # Get funding rate from ticker info
            # 티커 정보에서 펀딩 비율 가져오기
            funding_rate = ticker.get('info', {}).get('fundingRate', 0)
            
            if funding_rate:
                funding_rate = float(funding_rate)
                logger.info(f"Current funding rate: {funding_rate:.6f}")
                return funding_rate
            else:
                logger.warning("Funding rate not available, using 0")
                return 0.0
                
        except Exception as e:
            logger.warning(f"Failed to fetch funding rate: {e}, using 0")
            return 0.0
    
    def generate_chart_image(self, df: pd.DataFrame) -> np.ndarray:
        """
        Generate candlestick chart image in memory (no disk I/O)
        메모리 내에서 캔들스틱 차트 이미지 생성 (디스크 I/O 없음)
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            OpenCV image array (BGR format)
        """
        try:
            # Take last 50 candles for chart / 차트를 위한 마지막 50개 캔들
            chart_data = df.tail(50).copy()
            
            # Create clean candlestick chart style
            # 깔끔한 캔들스틱 차트 스타일 생성
            mc = mpf.make_marketcolors(
                up='g', down='r',
                edge='inherit',
                wick='inherit',
                volume='inherit'
            )
            style = mpf.make_mpf_style(marketcolors=mc, gridstyle='', y_on_right=False)
            
            # Create figure in memory / 메모리에 그림 생성
            fig, axes = mpf.plot(
                chart_data,
                type='candle',
                style=style,
                volume=False,  # No volume chart / 볼륨 차트 없음
                axisoff=True,  # No axes / 축 없음
                returnfig=True,
                figsize=(10, 6)
            )
            
            # Save to BytesIO buffer instead of file
            # 파일 대신 BytesIO 버퍼에 저장
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
            buffer.seek(0)
            
            # Convert to PIL Image / PIL 이미지로 변환
            pil_image = Image.open(buffer)
            
            # Convert to OpenCV format (BGR) / OpenCV 형식으로 변환 (BGR)
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Close figure to free memory / 메모리 해제를 위해 그림 닫기
            plt.close(fig)
            
            logger.info(f"Generated chart image with shape: {opencv_image.shape}")
            
            return opencv_image
            
        except Exception as e:
            logger.error(f"Failed to generate chart image: {e}")
            raise
    
    def detect_pattern(self, image: np.ndarray) -> List[Dict]:
        """
        Run YOLO detection on chart image
        차트 이미지에서 YOLO 탐지 실행
        
        Args:
            image: OpenCV image array (BGR format)
        
        Returns:
            List of detected patterns with confidence scores
        """
        try:
            # Run YOLO inference / YOLO 추론 실행
            results = self.yolo_model(image, verbose=False)
            
            detected_patterns = []
            
            # Process results / 결과 처리
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    confidence = float(box.conf[0])
                    
                    # Filter by confidence threshold / 신뢰도 임계값으로 필터링
                    if confidence > self.yolo_confidence:
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id] if hasattr(result, 'names') else f"class_{class_id}"
                        
                        detected_patterns.append({
                            'pattern': class_name,
                            'confidence': confidence
                        })
                        
                        logger.info(f"Detected pattern: {class_name} (confidence: {confidence:.2f})")
            
            if not detected_patterns:
                logger.info("No patterns detected above confidence threshold")
            
            return detected_patterns
            
        except Exception as e:
            logger.error(f"Failed to detect patterns: {e}")
            return []
    
    def check_long_conditions(
        self,
        indicators: Dict,
        patterns: List[Dict],
        funding_rate: float
    ) -> Tuple[bool, str]:
        """
        Check if long entry conditions are met
        롱 진입 조건 확인
        
        Returns:
            Tuple of (should_enter, reason)
        """
        reasons = []
        
        # Check trend: Price > EMA 200 (uptrend)
        # 트렌드 확인: 가격 > EMA 200 (상승 추세)
        if indicators['current_price'] <= indicators['ema_200']:
            return False, "Price below EMA 200 (not in uptrend)"
        reasons.append("✓ Price above EMA 200 (uptrend)")
        
        # Check for bullish pattern / 강세 패턴 확인
        bullish_pattern_found = False
        for pattern in patterns:
            if pattern['pattern'] in self.bullish_patterns:
                bullish_pattern_found = True
                reasons.append(f"✓ Bullish pattern detected: {pattern['pattern']} ({pattern['confidence']:.2f})")
                break
        
        if not bullish_pattern_found:
            return False, "No bullish pattern detected"
        
        # Check RSI: Not overbought / RSI 확인: 과매수 아님
        if indicators['rsi'] >= 70:
            return False, f"RSI too high (overbought): {indicators['rsi']:.2f}"
        reasons.append(f"✓ RSI not overbought: {indicators['rsi']:.2f}")
        
        # Check funding rate / 펀딩 비율 확인
        if abs(funding_rate) >= self.funding_rate_threshold:
            return False, f"Funding rate too high: {funding_rate:.6f}"
        reasons.append(f"✓ Funding rate acceptable: {funding_rate:.6f}")
        
        return True, " | ".join(reasons)
    
    def check_short_conditions(
        self,
        indicators: Dict,
        patterns: List[Dict],
        funding_rate: float
    ) -> Tuple[bool, str]:
        """
        Check if short entry conditions are met
        숏 진입 조건 확인
        
        Returns:
            Tuple of (should_enter, reason)
        """
        reasons = []
        
        # Check trend: Price < EMA 200 (downtrend)
        # 트렌드 확인: 가격 < EMA 200 (하락 추세)
        if indicators['current_price'] >= indicators['ema_200']:
            return False, "Price above EMA 200 (not in downtrend)"
        reasons.append("✓ Price below EMA 200 (downtrend)")
        
        # Check for bearish pattern / 약세 패턴 확인
        bearish_pattern_found = False
        for pattern in patterns:
            if pattern['pattern'] in self.bearish_patterns:
                bearish_pattern_found = True
                reasons.append(f"✓ Bearish pattern detected: {pattern['pattern']} ({pattern['confidence']:.2f})")
                break
        
        if not bearish_pattern_found:
            return False, "No bearish pattern detected"
        
        # Check RSI: Not oversold / RSI 확인: 과매도 아님
        if indicators['rsi'] <= 30:
            return False, f"RSI too low (oversold): {indicators['rsi']:.2f}"
        reasons.append(f"✓ RSI not oversold: {indicators['rsi']:.2f}")
        
        # Check funding rate / 펀딩 비율 확인
        if abs(funding_rate) >= self.funding_rate_threshold:
            return False, f"Funding rate too high: {funding_rate:.6f}"
        reasons.append(f"✓ Funding rate acceptable: {funding_rate:.6f}")
        
        return True, " | ".join(reasons)
    
    def calculate_position_size(self, price: float) -> float:
        """
        Calculate position size based on fixed USDT amount
        고정 USDT 금액을 기반으로 포지션 크기 계산
        
        Args:
            price: Current market price
        
        Returns:
            Position size in base currency units
        """
        try:
            # Validate price is positive / 가격이 양수인지 검증
            if price <= 0:
                raise ValueError(f"Invalid price: {price}. Price must be positive.")
            
            # Position size = USDT amount / Price
            # 포지션 크기 = USDT 금액 / 가격
            position_size = self.position_size_usdt / price
            
            # Get market info for precision / 정밀도를 위한 시장 정보 가져오기
            market = self.exchange.market(self.symbol)
            
            # Round to market precision / 시장 정밀도로 반올림
            if 'precision' in market and 'amount' in market['precision']:
                precision = market['precision']['amount']
                if precision:
                    position_size = round(position_size, precision)
            
            logger.info(f"Calculated position size: {position_size} (${self.position_size_usdt} USDT)")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            raise
    
    def calculate_sl_tp(
        self,
        entry_price: float,
        atr: float,
        side: str
    ) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels
        손절가와 목표가 계산
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            side: 'long' or 'short'
        
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        try:
            if side == 'long':
                # Long: SL below entry, TP above entry
                # 롱: 진입가 아래 손절, 진입가 위 목표
                stop_loss = entry_price - (atr * self.atr_sl_multiplier)
                take_profit = entry_price + (atr * self.atr_tp_multiplier)
            else:  # short
                # Short: SL above entry, TP below entry
                # 숏: 진입가 위 손절, 진입가 아래 목표
                stop_loss = entry_price + (atr * self.atr_sl_multiplier)
                take_profit = entry_price - (atr * self.atr_tp_multiplier)
            
            logger.info(f"{side.upper()} SL/TP - Entry: {entry_price:.2f}, "
                       f"SL: {stop_loss:.2f}, TP: {take_profit:.2f}")
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Failed to calculate SL/TP: {e}")
            raise
    
    def has_open_position(self) -> Tuple[bool, Optional[Dict]]:
        """
        Check if there is an active position for the symbol
        해당 심볼의 활성 포지션이 있는지 확인
        
        Returns:
            Tuple of (has_position, position_info)
            - has_position: True if active position exists
            - position_info: Position details or None
        """
        try:
            # Fetch all positions / 모든 포지션 가져오기
            positions = self.exchange.fetch_positions([self.symbol])
            
            # Find position for our symbol / 우리 심볼의 포지션 찾기
            for position in positions:
                # Check if position has size (not zero) / 포지션 크기 확인 (0이 아닌지)
                # Note: For some exchanges, contracts can be negative for short positions
                # 일부 거래소에서는 숏 포지션의 contracts가 음수일 수 있음
                contracts = float(position.get('contracts', 0))
                
                # Check for both long and short positions (contracts != 0)
                # 롱과 숏 포지션 모두 확인 (contracts != 0)
                if contracts != 0:
                    # Active position found / 활성 포지션 발견
                    position_info = {
                        'symbol': position.get('symbol'),
                        'side': position.get('side'),  # 'long' or 'short'
                        'contracts': contracts,
                        'entry_price': float(position.get('entryPrice', 0)),
                        'unrealized_pnl': float(position.get('unrealizedPnl', 0)),
                        'percentage': float(position.get('percentage', 0)),
                        'leverage': float(position.get('leverage', 1)),
                        'liquidation_price': position.get('liquidationPrice'),
                        'margin_type': position.get('marginMode', 'cross'),
                    }
                    
                    logger.info(f"Active position found: {position_info['side']} "
                               f"{position_info['contracts']} contracts at "
                               f"${position_info['entry_price']:.2f}")
                    
                    return True, position_info
            
            # No active position / 활성 포지션 없음
            return False, None
            
        except Exception as e:
            logger.error(f"Failed to check position: {e}")
            # Return False on error to be safe / 에러 시 안전하게 False 반환
            return False, None
    
    def get_position_info(self) -> Optional[Dict]:
        """
        Get detailed information about current position
        현재 포지션의 상세 정보 조회
        
        Returns:
            Dictionary with position details or None if no position
        """
        try:
            has_position, position_info = self.has_open_position()
            
            if not has_position:
                logger.info("No active position")
                return None
            
            # Get current market price for PnL calculation
            # PnL 계산을 위한 현재 시장 가격 가져오기
            ticker = self.exchange.fetch_ticker(self.symbol)
            current_price = float(ticker['last'])
            
            # Add current price and calculate additional metrics
            # 현재 가격 추가 및 추가 지표 계산
            position_info['current_price'] = current_price
            
            # Calculate PnL percentage if not already provided
            # PnL 퍼센트 계산 (제공되지 않은 경우)
            if position_info['entry_price'] > 0:
                if position_info['side'] == 'long':
                    pnl_percent = ((current_price - position_info['entry_price']) / 
                                  position_info['entry_price']) * 100
                else:  # short
                    pnl_percent = ((position_info['entry_price'] - current_price) / 
                                  position_info['entry_price']) * 100
                
                position_info['pnl_percent_calculated'] = pnl_percent
            
            return position_info
            
        except Exception as e:
            logger.error(f"Failed to get position info: {e}")
            return None
    
    def monitor_position(self):
        """
        Monitor and log active position status
        활성 포지션 모니터링 및 로깅
        """
        try:
            position_info = self.get_position_info()
            
            if not position_info:
                logger.info("No position to monitor")
                return
            
            # Log position details / 포지션 세부사항 로깅
            logger.info("=" * 60)
            logger.info("📊 POSITION STATUS / 포지션 상태")
            logger.info("=" * 60)
            logger.info(f"Symbol: {position_info['symbol']}")
            logger.info(f"Side: {position_info['side'].upper()}")
            logger.info(f"Size: {position_info['contracts']} contracts")
            logger.info(f"Entry Price: ${position_info['entry_price']:.2f}")
            logger.info(f"Current Price: ${position_info['current_price']:.2f}")
            logger.info(f"Unrealized PnL: ${position_info['unrealized_pnl']:.2f}")
            
            if 'pnl_percent_calculated' in position_info:
                pnl_pct = position_info['pnl_percent_calculated']
                emoji = "🟢" if pnl_pct > 0 else "🔴" if pnl_pct < 0 else "⚪"
                logger.info(f"PnL Percentage: {emoji} {pnl_pct:.2f}%")
            
            logger.info(f"Leverage: {position_info['leverage']}x")
            
            if position_info['liquidation_price']:
                logger.info(f"Liquidation Price: ${position_info['liquidation_price']:.2f}")
            
            logger.info("=" * 60)
            
            # Risk alerts / 리스크 알림
            if 'pnl_percent_calculated' in position_info:
                pnl_pct = position_info['pnl_percent_calculated']
                
                if pnl_pct < -10:
                    logger.warning("⚠️  WARNING: Position is down more than 10%!")
                elif pnl_pct < -5:
                    logger.warning("⚠️  CAUTION: Position is down more than 5%")
                elif pnl_pct > 10:
                    logger.info("💰 Position is up more than 10% - consider taking profits")
            
        except Exception as e:
            logger.error(f"Failed to monitor position: {e}")
    
    def close_position_manually(self, reason: str = "Manual close"):
        """
        Manually close the current position
        수동으로 현재 포지션 청산
        
        Args:
            reason: Reason for closing the position
        """
        try:
            has_position, position_info = self.has_open_position()
            
            if not has_position:
                logger.info("No active position to close")
                return
            
            logger.info(f"Closing position: {reason}")
            logger.info(f"Position: {position_info['side']} {position_info['contracts']} contracts")
            
            # Determine the opposite side to close position
            # 포지션 청산을 위한 반대 방향 결정
            close_side = 'sell' if position_info['side'] == 'long' else 'buy'
            
            # Create market order to close position
            # 포지션 청산을 위한 시장가 주문 생성
            order = self.exchange.create_order(
                symbol=self.symbol,
                type='market',
                side=close_side,
                amount=position_info['contracts'],
                params={'reduceOnly': True}  # Ensure it only closes, not opens new position
            )
            
            logger.info(f"✅ Position closed successfully!")
            logger.info(f"Close order ID: {order.get('id')}")
            logger.info(f"Reason: {reason}")
            
            # Log final PnL if available / 최종 PnL 로깅 (가능한 경우)
            if position_info.get('unrealized_pnl'):
                logger.info(f"Final PnL: ${position_info['unrealized_pnl']:.2f}")
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return None
    
    def execute_trade(
        self,
        side: str,
        amount: float,
        stop_loss: float,
        take_profit: float
    ) -> Optional[Dict]:
        """
        Execute trade with stop loss and take profit
        손절가와 목표가를 포함한 거래 실행
        
        Args:
            side: 'buy' or 'sell'
            amount: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
        
        Returns:
            Order info dictionary or None if failed
        """
        try:
            # Place market order / 시장가 주문 실행
            order = self.exchange.create_order(
                symbol=self.symbol,
                type='market',
                side=side,
                amount=amount,
                params={
                    'stopLoss': {
                        'triggerPrice': stop_loss,
                        'type': 'market'
                    },
                    'takeProfit': {
                        'triggerPrice': take_profit,
                        'type': 'market'
                    }
                }
            )
            
            logger.info(f"✅ {side.upper()} order executed successfully!")
            logger.info(f"Order ID: {order.get('id')}")
            logger.info(f"Amount: {amount}")
            logger.info(f"Stop Loss: {stop_loss:.2f}")
            logger.info(f"Take Profit: {take_profit:.2f}")
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return None
    
    def run(self):
        """
        Main bot loop with position management
        포지션 관리를 포함한 메인 봇 루프
        """
        logger.info("=" * 80)
        logger.info("Starting Hybrid Crypto Futures Trading Bot")
        logger.info("하이브리드 암호화폐 선물 트레이딩 봇 시작")
        logger.info("=" * 80)
        
        iteration = 0
        
        # Get position check interval from environment or use default
        # 환경 변수에서 포지션 확인 간격 가져오기 또는 기본값 사용
        position_check_interval = int(os.getenv('POSITION_CHECK_INTERVAL', '30'))
        
        while True:
            try:
                iteration += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                # Step 1: Check for existing position
                # 단계 1: 기존 포지션 확인
                has_position, position_info = self.has_open_position()
                
                if has_position:
                    # Position exists - monitor only, skip new entries
                    # 포지션 존재 - 모니터링만 하고 새 진입 건너뛰기
                    logger.info("⏸️  Active position exists, skipping new entry evaluation")
                    self.monitor_position()
                    
                    logger.info(f"\n💤 Sleeping for {position_check_interval} seconds...")
                    time.sleep(position_check_interval)
                    continue
                
                # Step 2: No position - proceed with entry evaluation
                # 단계 2: 포지션 없음 - 진입 조건 평가 진행
                logger.info("✅ No active position - evaluating entry conditions")
                
                # Step 3: Fetch multi-timeframe OHLCV data
                # 단계 3: 다중 타임프레임 OHLCV 데이터 가져오기
                main_df, trend_df = self.fetch_ohlcv_multi_timeframe()
                
                # Step 4: Calculate indicators
                # 단계 4: 지표 계산
                indicators = self.calculate_indicators(main_df, trend_df)
                
                # Step 5: Fetch funding rate
                # 단계 5: 펀딩 비율 가져오기
                funding_rate = self.fetch_funding_rate()
                
                # Step 6: Generate chart image (in-memory)
                # 단계 6: 차트 이미지 생성 (메모리 내)
                chart_image = self.generate_chart_image(main_df)
                
                # Step 7: Detect patterns with YOLO
                # 단계 7: YOLO로 패턴 탐지
                patterns = self.detect_pattern(chart_image)
                
                # Step 8: Evaluate trading conditions
                # 단계 8: 거래 조건 평가
                
                # Check long conditions / 롱 조건 확인
                should_long, long_reason = self.check_long_conditions(
                    indicators, patterns, funding_rate
                )
                
                if should_long:
                    logger.info("🟢 LONG CONDITIONS MET!")
                    logger.info(f"Reason: {long_reason}")
                    
                    # Calculate position size / 포지션 크기 계산
                    position_size = self.calculate_position_size(indicators['current_price'])
                    
                    # Calculate SL/TP / 손절/목표 계산
                    stop_loss, take_profit = self.calculate_sl_tp(
                        indicators['current_price'],
                        indicators['atr'],
                        'long'
                    )
                    
                    # Execute trade / 거래 실행
                    self.execute_trade('buy', position_size, stop_loss, take_profit)
                    
                else:
                    # Check short conditions / 숏 조건 확인
                    should_short, short_reason = self.check_short_conditions(
                        indicators, patterns, funding_rate
                    )
                    
                    if should_short:
                        logger.info("🔴 SHORT CONDITIONS MET!")
                        logger.info(f"Reason: {short_reason}")
                        
                        # Calculate position size / 포지션 크기 계산
                        position_size = self.calculate_position_size(indicators['current_price'])
                        
                        # Calculate SL/TP / 손절/목표 계산
                        stop_loss, take_profit = self.calculate_sl_tp(
                            indicators['current_price'],
                            indicators['atr'],
                            'short'
                        )
                        
                        # Execute trade / 거래 실행
                        self.execute_trade('sell', position_size, stop_loss, take_profit)
                        
                    else:
                        logger.info("⏸️  No trading conditions met")
                        logger.info(f"Long: {long_reason}")
                        logger.info(f"Short: {short_reason}")
                
                # Step 9: Wait before next iteration
                # 단계 9: 다음 반복 전 대기
                sleep_time = 60
                logger.info(f"\n💤 Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  Bot stopped by user")
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)


if __name__ == "__main__":
    # Create and run bot / 봇 생성 및 실행
    bot = BybitYoloBot()
    bot.run()
