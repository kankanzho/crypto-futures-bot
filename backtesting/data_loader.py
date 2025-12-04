"""
Data loader for backtesting.
Loads historical OHLCV data from Bybit API.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import time
from core.bybit_api import BybitAPI
from indicators.technical_indicators import calculate_all_indicators
from utils.logger import get_logger
from utils.helpers import datetime_to_timestamp

logger = get_logger()


class DataLoader:
    """Loads and prepares historical data for backtesting."""
    
    def __init__(self, api: Optional[BybitAPI] = None, testnet: bool = True):
        """
        Initialize data loader.
        
        Args:
            api: Bybit API client (creates new if None)
            testnet: Whether to use testnet
        """
        self.api = api or BybitAPI(testnet=testnet)
    
    def load_historical_data(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Load historical kline data.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1, 3, 5, 15, 30, 60, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Loading historical data for {symbol} from {start_date} to {end_date}")
        
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Convert to timestamps
        start_ts = datetime_to_timestamp(start_dt)
        end_ts = datetime_to_timestamp(end_dt)
        
        # Fetch data in chunks (Bybit limits to 200 candles per request)
        all_data = []
        current_start = start_ts
        
        while current_start < end_ts:
            # Fetch chunk
            klines = self.api.get_kline(
                symbol=symbol,
                interval=interval,
                limit=200,
                start_time=current_start,
                end_time=end_ts
            )
            
            if not klines:
                logger.warning(f"No data received for period starting {current_start}")
                break
            
            # Add to collection
            all_data.extend(klines)
            
            # Update start time for next chunk
            # Bybit returns data in reverse order (newest first)
            last_timestamp = int(klines[-1][0])
            current_start = last_timestamp + 1
            
            # Rate limiting
            time.sleep(0.1)
            
            logger.debug(f"Fetched {len(klines)} candles, total: {len(all_data)}")
        
        # Convert to DataFrame
        if not all_data:
            logger.error(f"No data loaded for {symbol}")
            return pd.DataFrame()
        
        df = self._convert_to_dataframe(all_data)
        
        logger.info(f"Loaded {len(df)} candles for {symbol}")
        
        return df
    
    def _convert_to_dataframe(self, klines: List) -> pd.DataFrame:
        """
        Convert Bybit kline data to DataFrame.
        
        Args:
            klines: List of kline data from Bybit
            
        Returns:
            DataFrame with OHLCV data
        """
        # Bybit kline format: [timestamp, open, high, low, close, volume, turnover]
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Convert types
        df['timestamp'] = pd.to_numeric(df['timestamp'])
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['turnover'] = pd.to_numeric(df['turnover'])
        
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Sort by timestamp (oldest first)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def prepare_data_for_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data by calculating all technical indicators.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicators added
        """
        logger.info("Calculating technical indicators")
        
        # Calculate all indicators
        df = calculate_all_indicators(df)
        
        # Drop rows with NaN values (initial periods where indicators can't be calculated)
        initial_len = len(df)
        df = df.dropna().reset_index(drop=True)
        
        logger.info(f"Data prepared: {len(df)} rows (dropped {initial_len - len(df)} rows with NaN)")
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> None:
        """
        Save DataFrame to CSV file.
        
        Args:
            df: DataFrame to save
            filename: Output filename
        """
        df.to_csv(filename, index=False)
        logger.info(f"Data saved to {filename}")
    
    def load_from_csv(self, filename: str) -> pd.DataFrame:
        """
        Load DataFrame from CSV file.
        
        Args:
            filename: Input filename
            
        Returns:
            DataFrame with data
        """
        df = pd.read_csv(filename)
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        logger.info(f"Data loaded from {filename}: {len(df)} rows")
        return df
