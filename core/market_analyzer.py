"""
Market Analyzer Module

Analyzes market conditions including volatility, trend strength, and volume.
Provides classification of market conditions to enable optimal strategy selection.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional
import numpy as np
import pandas as pd


# Type definitions
VolatilityLevel = Literal['LOW', 'MEDIUM', 'HIGH']
TrendLevel = Literal['STRONG_UP', 'WEAK_UP', 'RANGING', 'WEAK_DOWN', 'STRONG_DOWN']
VolumeLevel = Literal['LOW', 'NORMAL', 'HIGH']


@dataclass
class MarketCondition:
    """
    Market condition data structure.
    
    Attributes:
        volatility: Volatility level (LOW, MEDIUM, HIGH)
        trend: Trend strength and direction
        volume: Volume level (LOW, NORMAL, HIGH)
        timestamp: Time of analysis
        metrics: Optional dict containing raw metric values
    """
    volatility: VolatilityLevel
    trend: TrendLevel
    volume: VolumeLevel
    timestamp: datetime
    metrics: Optional[dict] = None
    
    def __str__(self):
        """String representation for logging."""
        return (
            f"MarketCondition(volatility={self.volatility}, "
            f"trend={self.trend}, volume={self.volume})"
        )


class MarketAnalyzer:
    """
    Analyzes market conditions to classify volatility, trend, and volume.
    
    This analyzer computes various technical indicators and classifies
    market conditions to enable optimal strategy selection.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the MarketAnalyzer.
        
        Args:
            config: Configuration dict with analysis parameters
        """
        self.config = config or {}
        
        # Get analysis parameters from config
        market_analysis = self.config.get('market_analysis', {})
        self.volatility_period = market_analysis.get('volatility_period', 14)
        self.trend_period = market_analysis.get('trend_period', 14)
        self.volume_period = market_analysis.get('volume_period', 20)
        
    def analyze(self, df: pd.DataFrame) -> MarketCondition:
        """
        Analyze market conditions from OHLCV data.
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
                Index should be datetime
        
        Returns:
            MarketCondition object with classification results
        """
        if df is None or len(df) < max(self.volatility_period, self.trend_period, self.volume_period):
            raise ValueError("Insufficient data for market analysis")
        
        # Ensure DataFrame has required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # Calculate metrics
        volatility_metrics = self._measure_volatility(df)
        trend_metrics = self._measure_trend(df)
        volume_metrics = self._measure_volume(df)
        
        # Classify conditions
        volatility_level = self._classify_volatility(volatility_metrics)
        trend_level = self._classify_trend(trend_metrics)
        volume_level = self._classify_volume(volume_metrics)
        
        # Combine all metrics
        all_metrics = {
            **volatility_metrics,
            **trend_metrics,
            **volume_metrics
        }
        
        return MarketCondition(
            volatility=volatility_level,
            trend=trend_level,
            volume=volume_level,
            timestamp=datetime.now(),
            metrics=all_metrics
        )
    
    def _measure_volatility(self, df: pd.DataFrame) -> dict:
        """
        Measure market volatility using multiple indicators.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Dict with volatility metrics
        """
        # ATR (Average True Range) - absolute volatility
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.volatility_period).mean().iloc[-1]
        
        # Normalize ATR by current price
        current_price = df['close'].iloc[-1]
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
        
        # Bollinger Bandwidth - relative volatility
        sma = df['close'].rolling(window=self.volatility_period).mean()
        std = df['close'].rolling(window=self.volatility_period).std()
        bb_width = ((std * 2) / sma * 100).iloc[-1] if sma.iloc[-1] > 0 else 0
        
        # Recent N-period high/low range
        period = min(self.volatility_period, len(df))
        recent_high = df['high'].iloc[-period:].max()
        recent_low = df['low'].iloc[-period:].min()
        price_range_pct = ((recent_high - recent_low) / recent_low * 100) if recent_low > 0 else 0
        
        return {
            'atr': atr,
            'atr_pct': atr_pct,
            'bb_width': bb_width,
            'price_range_pct': price_range_pct
        }
    
    def _measure_trend(self, df: pd.DataFrame) -> dict:
        """
        Measure trend strength and direction.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Dict with trend metrics
        """
        # ADX (Average Directional Index) - trend strength
        adx = self._calculate_adx(df, self.trend_period)
        
        # EMA alignment (5, 20, 50)
        ema5 = df['close'].ewm(span=5, adjust=False).mean().iloc[-1]
        ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1] if len(df) >= 50 else ema20
        
        # Check EMA alignment
        ema_aligned_up = ema5 > ema20 > ema50
        ema_aligned_down = ema5 < ema20 < ema50
        
        # Linear regression slope
        period = min(self.trend_period, len(df))
        close_values = df['close'].iloc[-period:].values
        x = np.arange(len(close_values))
        
        # Calculate slope using least squares
        if len(x) > 1:
            slope, _ = np.polyfit(x, close_values, 1)
            # Normalize slope by price
            slope_pct = (slope / close_values[-1]) * 100 if close_values[-1] > 0 else 0
        else:
            slope_pct = 0
        
        return {
            'adx': adx,
            'ema5': ema5,
            'ema20': ema20,
            'ema50': ema50,
            'ema_aligned_up': ema_aligned_up,
            'ema_aligned_down': ema_aligned_down,
            'slope_pct': slope_pct
        }
    
    def _measure_volume(self, df: pd.DataFrame) -> dict:
        """
        Measure volume characteristics.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Dict with volume metrics
        """
        # Current volume vs average volume
        avg_volume = df['volume'].rolling(window=self.volume_period).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # VWAP (Volume Weighted Average Price)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
        current_price = df['close'].iloc[-1]
        price_vs_vwap = ((current_price - vwap) / vwap * 100) if vwap > 0 else 0
        
        return {
            'volume_ratio': volume_ratio,
            'avg_volume': avg_volume,
            'current_volume': current_volume,
            'vwap': vwap,
            'price_vs_vwap_pct': price_vs_vwap
        }
    
    def _calculate_adx(self, df: pd.DataFrame, period: int) -> float:
        """
        Calculate ADX (Average Directional Index).
        
        Args:
            df: OHLCV DataFrame
            period: Calculation period
            
        Returns:
            ADX value
        """
        # Calculate +DM and -DM
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Smooth the values
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX with zero-division protection
        di_sum = plus_di + minus_di
        # Avoid division by zero
        dx = 100 * np.abs(plus_di - minus_di) / di_sum.replace(0, np.nan)
        # Use exponential smoothing for ADX (more standard implementation)
        adx = dx.ewm(span=period, adjust=False).mean().iloc[-1]
        
        return adx if not np.isnan(adx) else 0.0
    
    def _classify_volatility(self, metrics: dict) -> VolatilityLevel:
        """
        Classify volatility level based on metrics.
        
        Args:
            metrics: Dict with volatility metrics
            
        Returns:
            VolatilityLevel (LOW, MEDIUM, HIGH)
        """
        # Use multiple indicators for classification
        atr_pct = metrics['atr_pct']
        bb_width = metrics['bb_width']
        price_range_pct = metrics['price_range_pct']
        
        # Score from 0-100 based on all indicators
        # ATR%: < 1% = low, 1-3% = medium, > 3% = high
        atr_score = min(100, (atr_pct / 3.0) * 100)
        
        # BB Width: < 5% = low, 5-15% = medium, > 15% = high
        bb_score = min(100, (bb_width / 15.0) * 100)
        
        # Price range: < 5% = low, 5-15% = medium, > 15% = high
        range_score = min(100, (price_range_pct / 15.0) * 100)
        
        # Average score
        volatility_score = (atr_score + bb_score + range_score) / 3
        
        # Classify
        if volatility_score < 33:
            return 'LOW'
        elif volatility_score < 66:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    def _classify_trend(self, metrics: dict) -> TrendLevel:
        """
        Classify trend strength and direction.
        
        Args:
            metrics: Dict with trend metrics
            
        Returns:
            TrendLevel
        """
        adx = metrics['adx']
        ema_aligned_up = metrics['ema_aligned_up']
        ema_aligned_down = metrics['ema_aligned_down']
        slope_pct = metrics['slope_pct']
        
        # Determine trend direction
        is_uptrend = slope_pct > 0
        is_downtrend = slope_pct < 0
        
        # ADX classification: < 20 = weak/ranging, 20-40 = moderate, > 40 = strong
        is_strong = adx > 40
        is_weak = adx < 20
        
        # Combine indicators
        if is_strong and is_uptrend and ema_aligned_up:
            return 'STRONG_UP'
        elif is_strong and is_downtrend and ema_aligned_down:
            return 'STRONG_DOWN'
        elif is_weak or abs(slope_pct) < 0.1:
            return 'RANGING'
        elif is_uptrend:
            return 'WEAK_UP'
        else:
            return 'WEAK_DOWN'
    
    def _classify_volume(self, metrics: dict) -> VolumeLevel:
        """
        Classify volume level.
        
        Args:
            metrics: Dict with volume metrics
            
        Returns:
            VolumeLevel (LOW, NORMAL, HIGH)
        """
        volume_ratio = metrics['volume_ratio']
        
        # Classification based on ratio to average
        if volume_ratio < 0.7:
            return 'LOW'
        elif volume_ratio < 1.5:
            return 'NORMAL'
        else:
            return 'HIGH'
