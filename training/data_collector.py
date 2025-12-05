"""
Data Collector for YOLO Training
차트 이미지 자동 수집

Collects chart images from Bybit API for YOLO training.
바이비트 API에서 YOLO 학습을 위한 차트 이미지 수집
"""

import os
import io
import logging
from typing import List, Tuple
from datetime import datetime

import ccxt
import numpy as np
import pandas as pd
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import mplfinance as mpf
from tqdm import tqdm

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collects chart images from Bybit API
    바이비트 API에서 차트 이미지 수집
    """
    
    def __init__(self, output_dir: str = 'training/dataset/raw_images'):
        """
        Initialize data collector
        
        Args:
            output_dir: Directory to save collected images
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize exchange (no API key needed for public data)
        self.exchange = ccxt.bybit({
            'enableRateLimit': True
        })
        
        logger.info(f"DataCollector initialized. Output: {output_dir}")
    
    def generate_chart_image(self, df: pd.DataFrame) -> np.ndarray:
        """
        Generate candlestick chart image from OHLCV data
        OHLCV 데이터에서 캔들스틱 차트 이미지 생성
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            OpenCV image array (BGR format)
        """
        try:
            # Create clean candlestick chart style
            mc = mpf.make_marketcolors(
                up='g', down='r',
                edge='inherit',
                wick='inherit',
                volume='inherit'
            )
            style = mpf.make_mpf_style(marketcolors=mc, gridstyle='', y_on_right=False)
            
            # Create figure in memory
            fig, axes = mpf.plot(
                df,
                type='candle',
                style=style,
                volume=False,
                axisoff=True,
                returnfig=True,
                figsize=(10, 6)
            )
            
            # Save to BytesIO buffer
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
            buffer.seek(0)
            
            # Convert to PIL Image
            pil_image = Image.open(buffer)
            
            # Convert to OpenCV format (BGR)
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Close figure to free memory
            plt.close(fig)
            
            return opencv_image
            
        except Exception as e:
            logger.error(f"Failed to generate chart image: {e}")
            raise
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data
        과거 OHLCV 데이터 가져오기
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT:USDT')
            timeframe: Timeframe (e.g., '15m', '1h')
            limit: Number of candles to fetch
        
        Returns:
            OHLCV DataFrame
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol} {timeframe}: {e}")
            raise
    
    def collect_images(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None,
        target_count: int = 1000,
        window_size: int = 50
    ) -> int:
        """
        Collect chart images using sliding window
        슬라이딩 윈도우를 사용하여 차트 이미지 수집
        
        Args:
            symbols: List of trading pairs
            timeframes: List of timeframes
            target_count: Target number of images to collect
            window_size: Number of candles per chart
        
        Returns:
            Number of images collected
        """
        if symbols is None:
            symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        if timeframes is None:
            timeframes = ['15m', '1h']
        
        logger.info(f"📊 Starting data collection")
        logger.info(f"  Symbols: {symbols}")
        logger.info(f"  Timeframes: {timeframes}")
        logger.info(f"  Target: {target_count} images")
        logger.info(f"  Window size: {window_size} candles")
        
        collected = 0
        
        with tqdm(total=target_count, desc="Collecting images") as pbar:
            for symbol in symbols:
                for timeframe in timeframes:
                    if collected >= target_count:
                        break
                    
                    try:
                        # Fetch more data for sliding window
                        # Calculate how many candles we need
                        candles_needed = window_size + (target_count // (len(symbols) * len(timeframes)))
                        
                        logger.info(f"  Fetching {symbol} ({timeframe})...")
                        df = self.fetch_historical_data(
                            symbol,
                            timeframe,
                            limit=min(candles_needed, 1000)  # API limit
                        )
                        
                        # Generate images with sliding window
                        step_size = max(1, window_size // 10)  # 10% overlap
                        
                        for i in range(0, len(df) - window_size, step_size):
                            if collected >= target_count:
                                break
                            
                            # Extract window
                            window_df = df.iloc[i:i + window_size].copy()
                            
                            # Generate chart image
                            image = self.generate_chart_image(window_df)
                            
                            # Save image
                            filename = f"{symbol.replace('/', '_').replace(':', '_')}_{timeframe}_{i}_{collected:04d}.png"
                            filepath = os.path.join(self.output_dir, filename)
                            cv2.imwrite(filepath, image)
                            
                            collected += 1
                            pbar.update(1)
                        
                    except Exception as e:
                        logger.error(f"Error collecting from {symbol} {timeframe}: {e}")
                        continue
        
        logger.info(f"✅ Collected {collected} chart images")
        return collected


if __name__ == "__main__":
    # Test the collector
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = DataCollector()
    count = collector.collect_images(target_count=10)
    print(f"Collected {count} images")
