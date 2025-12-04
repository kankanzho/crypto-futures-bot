"""
WebSocket client for real-time market data from Bybit.
"""

import json
import threading
from typing import Callable, Dict, List, Optional
import time
from pybit.unified_trading import WebSocket
from utils.logger import get_logger

logger = get_logger()


class BybitWebSocket:
    """WebSocket client for Bybit market data."""
    
    def __init__(self, testnet: bool = True):
        """
        Initialize WebSocket client.
        
        Args:
            testnet: Whether to use testnet
        """
        self.testnet = testnet
        self.ws = None
        self.is_connected = False
        self.callbacks: Dict[str, List[Callable]] = {}
        self.subscribed_symbols: List[str] = []
        
        logger.info(f"WebSocket client initialized (Testnet: {testnet})")
    
    def connect(self) -> None:
        """Connect to WebSocket."""
        try:
            self.ws = WebSocket(
                testnet=self.testnet,
                channel_type="linear"
            )
            
            self.is_connected = True
            logger.info("WebSocket connected")
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            self.is_connected = False
    
    def disconnect(self) -> None:
        """Disconnect WebSocket."""
        if self.ws:
            try:
                self.ws.exit()
                self.is_connected = False
                logger.info("WebSocket disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting WebSocket: {e}")
    
    def subscribe_kline(
        self,
        symbol: str,
        interval: str,
        callback: Callable[[Dict], None]
    ) -> None:
        """
        Subscribe to kline/candlestick updates.
        
        Args:
            symbol: Trading symbol
            interval: Kline interval (1, 3, 5, 15, 30, 60, etc.)
            callback: Callback function to handle updates
        """
        if not self.is_connected:
            logger.warning("WebSocket not connected")
            return
        
        try:
            topic = f"kline.{interval}.{symbol}"
            
            # Store callback
            if topic not in self.callbacks:
                self.callbacks[topic] = []
            self.callbacks[topic].append(callback)
            
            # Subscribe
            self.ws.subscribe(
                topic=topic,
                callback=self._handle_kline_message
            )
            
            if symbol not in self.subscribed_symbols:
                self.subscribed_symbols.append(symbol)
            
            logger.info(f"Subscribed to kline: {symbol} {interval}")
            
        except Exception as e:
            logger.error(f"Error subscribing to kline: {e}")
    
    def subscribe_ticker(
        self,
        symbol: str,
        callback: Callable[[Dict], None]
    ) -> None:
        """
        Subscribe to ticker updates.
        
        Args:
            symbol: Trading symbol
            callback: Callback function to handle updates
        """
        if not self.is_connected:
            logger.warning("WebSocket not connected")
            return
        
        try:
            topic = f"tickers.{symbol}"
            
            # Store callback
            if topic not in self.callbacks:
                self.callbacks[topic] = []
            self.callbacks[topic].append(callback)
            
            # Subscribe
            self.ws.subscribe(
                topic=topic,
                callback=self._handle_ticker_message
            )
            
            if symbol not in self.subscribed_symbols:
                self.subscribed_symbols.append(symbol)
            
            logger.info(f"Subscribed to ticker: {symbol}")
            
        except Exception as e:
            logger.error(f"Error subscribing to ticker: {e}")
    
    def _handle_kline_message(self, message: Dict) -> None:
        """
        Handle kline message.
        
        Args:
            message: Kline message from WebSocket
        """
        try:
            topic = message.get('topic', '')
            
            if topic in self.callbacks:
                for callback in self.callbacks[topic]:
                    callback(message)
                    
        except Exception as e:
            logger.error(f"Error handling kline message: {e}")
    
    def _handle_ticker_message(self, message: Dict) -> None:
        """
        Handle ticker message.
        
        Args:
            message: Ticker message from WebSocket
        """
        try:
            topic = message.get('topic', '')
            
            if topic in self.callbacks:
                for callback in self.callbacks[topic]:
                    callback(message)
                    
        except Exception as e:
            logger.error(f"Error handling ticker message: {e}")
    
    def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
        """
        if not self.is_connected:
            return
        
        try:
            self.ws.unsubscribe(topic=topic)
            
            if topic in self.callbacks:
                del self.callbacks[topic]
            
            logger.info(f"Unsubscribed from: {topic}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
    
    def get_subscribed_symbols(self) -> List[str]:
        """
        Get list of subscribed symbols.
        
        Returns:
            List of subscribed symbols
        """
        return self.subscribed_symbols.copy()
