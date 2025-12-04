"""
Notification system for the trading bot.
Handles pop-up notifications and sound alerts.
"""

from typing import Optional
from enum import Enum
import sys
from utils.logger import get_logger

logger = get_logger()


class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"


class NotificationManager:
    """Manages notifications for the trading bot."""
    
    def __init__(self, enable_sound: bool = True, enable_popup: bool = True):
        """
        Initialize the notification manager.
        
        Args:
            enable_sound: Whether to enable sound notifications
            enable_popup: Whether to enable popup notifications
        """
        self.enable_sound = enable_sound
        self.enable_popup = enable_popup
        self._sound_available = False
        
        # Try to import winsound (Windows) or other sound libraries
        try:
            if sys.platform == "win32":
                import winsound
                self._winsound = winsound
                self._sound_available = True
            else:
                # On Linux/Mac, we could use ossaudiodev or other libraries
                # For now, just log
                self._sound_available = False
        except ImportError:
            logger.warning("Sound notification not available on this platform")
            self._sound_available = False
    
    def notify(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        play_sound: bool = True
    ) -> None:
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            play_sound: Whether to play sound
        """
        # Log the notification
        log_message = f"{title}: {message}"
        
        if notification_type == NotificationType.ERROR:
            logger.error(log_message)
        elif notification_type == NotificationType.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Play sound if enabled
        if play_sound and self.enable_sound and self._sound_available:
            self._play_sound(notification_type)
        
        # Show popup if enabled (will be handled by GUI)
        if self.enable_popup:
            self._show_popup(title, message, notification_type)
    
    def _play_sound(self, notification_type: NotificationType) -> None:
        """
        Play a sound based on notification type.
        
        Args:
            notification_type: Type of notification
        """
        if not self._sound_available:
            return
        
        try:
            if sys.platform == "win32":
                # Windows system sounds
                sound_map = {
                    NotificationType.INFO: self._winsound.MB_ICONASTERISK,
                    NotificationType.SUCCESS: self._winsound.MB_OK,
                    NotificationType.WARNING: self._winsound.MB_ICONEXCLAMATION,
                    NotificationType.ERROR: self._winsound.MB_ICONHAND,
                    NotificationType.TRADE_ENTRY: self._winsound.MB_OK,
                    NotificationType.TRADE_EXIT: self._winsound.MB_ICONASTERISK,
                }
                
                sound = sound_map.get(notification_type, self._winsound.MB_OK)
                self._winsound.MessageBeep(sound)
        except Exception as e:
            logger.debug(f"Could not play sound: {e}")
    
    def _show_popup(
        self,
        title: str,
        message: str,
        notification_type: NotificationType
    ) -> None:
        """
        Show a popup notification.
        This will be handled by the GUI component.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
        """
        # Store notification for GUI to display
        # This is a placeholder - actual implementation will be in GUI
        pass
    
    def notify_trade_entry(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float
    ) -> None:
        """
        Notify about a trade entry.
        
        Args:
            symbol: Trading symbol
            side: Trade side (long/short)
            price: Entry price
            quantity: Position quantity
        """
        title = f"Trade Opened: {symbol}"
        message = f"{side.upper()} {quantity} @ ${price:.2f}"
        self.notify(title, message, NotificationType.TRADE_ENTRY)
    
    def notify_trade_exit(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        pnl: float,
        pnl_pct: float
    ) -> None:
        """
        Notify about a trade exit.
        
        Args:
            symbol: Trading symbol
            side: Trade side (long/short)
            price: Exit price
            quantity: Position quantity
            pnl: Profit/loss in USDT
            pnl_pct: Profit/loss percentage
        """
        title = f"Trade Closed: {symbol}"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        message = f"{side.upper()} {quantity} @ ${price:.2f} | PnL: {pnl_str} ({pnl_pct:+.2f}%)"
        
        notification_type = NotificationType.SUCCESS if pnl >= 0 else NotificationType.WARNING
        self.notify(title, message, notification_type)
    
    def notify_error(self, title: str, message: str) -> None:
        """
        Notify about an error.
        
        Args:
            title: Error title
            message: Error message
        """
        self.notify(title, message, NotificationType.ERROR)
    
    def notify_warning(self, title: str, message: str) -> None:
        """
        Notify about a warning.
        
        Args:
            title: Warning title
            message: Warning message
        """
        self.notify(title, message, NotificationType.WARNING)


# Global notification manager instance
_notification_manager = None


def get_notification_manager(
    enable_sound: bool = True,
    enable_popup: bool = True
) -> NotificationManager:
    """
    Get the global notification manager instance.
    
    Args:
        enable_sound: Whether to enable sound notifications
        enable_popup: Whether to enable popup notifications
        
    Returns:
        NotificationManager instance
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager(enable_sound, enable_popup)
    return _notification_manager
