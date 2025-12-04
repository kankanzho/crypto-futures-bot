"""
Take profit management module.
Supports multi-level, risk/reward ratio, and dynamic take profit targets.
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from loguru import logger
from ..utils.indicators import calculate_volatility


class TakeProfitManager:
    """Manages take profit orders for positions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize take profit manager.
        
        Args:
            config: Take profit configuration
        """
        self.config = config
        self.tp_type = config.get('type', 'risk_reward')
        self.active_targets: Dict[str, Dict] = {}  # symbol -> TP info
        
        logger.info(f"Take profit manager initialized with type: {self.tp_type}")
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float, side: str,
                             market_data: Optional[pd.DataFrame] = None) -> List[Tuple[float, float]]:
        """
        Calculate take profit targets.
        
        Args:
            entry_price: Position entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            market_data: Market data for dynamic TP calculation
            
        Returns:
            List of (price, size) tuples representing TP levels
        """
        if self.tp_type == 'risk_reward':
            return self._calculate_risk_reward_tp(entry_price, stop_loss, side)
        elif self.tp_type == 'multi_level':
            return self._calculate_multi_level_tp(entry_price, side)
        elif self.tp_type == 'dynamic':
            return self._calculate_dynamic_tp(entry_price, side, market_data)
        else:
            logger.warning(f"Unknown TP type: {self.tp_type}, using risk_reward")
            return self._calculate_risk_reward_tp(entry_price, stop_loss, side)
    
    def _calculate_risk_reward_tp(self, entry_price: float, stop_loss: float, 
                                  side: str) -> List[Tuple[float, float]]:
        """
        Calculate take profit based on risk/reward ratio.
        
        Args:
            entry_price: Position entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            
        Returns:
            List of (price, size) tuples
        """
        ratio = self.config.get('ratio', 2.0)  # Default 2:1 R/R
        partial_exits = self.config.get('partial_exits', [])
        
        # Calculate risk
        risk = abs(entry_price - stop_loss)
        
        targets = []
        
        if partial_exits:
            # Multiple partial exits
            for exit in partial_exits:
                exit_ratio = exit.get('ratio', ratio)
                exit_size = exit.get('level', 1.0)
                
                if side == 'long':
                    tp_price = entry_price + (risk * exit_ratio)
                else:  # short
                    tp_price = entry_price - (risk * exit_ratio)
                
                targets.append((tp_price, exit_size))
        else:
            # Single take profit at specified ratio
            if side == 'long':
                tp_price = entry_price + (risk * ratio)
            else:  # short
                tp_price = entry_price - (risk * ratio)
            
            targets.append((tp_price, 1.0))
        
        logger.debug(f"Risk/reward TP targets: {targets}")
        return targets
    
    def _calculate_multi_level_tp(self, entry_price: float, side: str) -> List[Tuple[float, float]]:
        """
        Calculate multiple take profit levels based on percentage.
        
        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            
        Returns:
            List of (price, size) tuples
        """
        levels = self.config.get('levels', [])
        
        if not levels:
            # Default levels
            levels = [
                {'percentage': 0.02, 'exit_size': 0.33},
                {'percentage': 0.04, 'exit_size': 0.33},
                {'percentage': 0.06, 'exit_size': 0.34}
            ]
        
        targets = []
        
        for level in levels:
            percentage = level.get('percentage', 0.02)
            exit_size = level.get('exit_size', 0.33)
            
            if side == 'long':
                tp_price = entry_price * (1 + percentage)
            else:  # short
                tp_price = entry_price * (1 - percentage)
            
            targets.append((tp_price, exit_size))
        
        logger.debug(f"Multi-level TP targets: {targets}")
        return targets
    
    def _calculate_dynamic_tp(self, entry_price: float, side: str,
                             market_data: Optional[pd.DataFrame]) -> List[Tuple[float, float]]:
        """
        Calculate dynamic take profit based on market volatility.
        
        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            market_data: Market data for volatility calculation
            
        Returns:
            List of (price, size) tuples
        """
        base_target = self.config.get('base_target', 0.025)  # 2.5%
        max_target = self.config.get('max_target', 0.05)  # 5%
        volatility_multiplier = self.config.get('volatility_multiplier', 1.5)
        
        # Calculate volatility if data available
        if market_data is not None and len(market_data) >= 20:
            volatility = calculate_volatility(market_data['close'], period=20)
            current_vol = volatility.iloc[-1]
            
            if not pd.isna(current_vol):
                # Adjust target based on volatility
                target_percent = min(base_target * (1 + current_vol * volatility_multiplier), max_target)
            else:
                target_percent = base_target
        else:
            target_percent = base_target
        
        if side == 'long':
            tp_price = entry_price * (1 + target_percent)
        else:  # short
            tp_price = entry_price * (1 - target_percent)
        
        targets = [(tp_price, 1.0)]
        
        logger.debug(f"Dynamic TP target: {targets} (target%: {target_percent*100:.2f}%)")
        return targets
    
    def set_take_profit(self, symbol: str, entry_price: float, stop_loss: float, side: str,
                       market_data: Optional[pd.DataFrame] = None) -> List[Tuple[float, float]]:
        """
        Set take profit targets for a position.
        
        Args:
            symbol: Trading pair symbol
            entry_price: Position entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            market_data: Market data (for dynamic TP)
            
        Returns:
            List of (price, size) tuples
        """
        targets = self.calculate_take_profit(entry_price, stop_loss, side, market_data)
        
        self.active_targets[symbol] = {
            'targets': targets,
            'entry_price': entry_price,
            'side': side,
            'filled': [False] * len(targets)  # Track which levels have been filled
        }
        
        logger.info(f"Take profit set for {symbol}: {targets}")
        return targets
    
    def check_take_profit_hit(self, symbol: str, current_price: float) -> Optional[Tuple[int, float, float]]:
        """
        Check if any take profit level has been hit.
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            
        Returns:
            Tuple of (level_index, tp_price, exit_size) if hit, None otherwise
        """
        if symbol not in self.active_targets:
            return None
        
        tp_info = self.active_targets[symbol]
        targets = tp_info['targets']
        filled = tp_info['filled']
        side = tp_info['side']
        
        # Check each unfilled target
        for i, (tp_price, exit_size) in enumerate(targets):
            if not filled[i]:
                hit = False
                
                if side == 'long':
                    # Long TP hit when price rises above target
                    hit = current_price >= tp_price
                else:  # short
                    # Short TP hit when price drops below target
                    hit = current_price <= tp_price
                
                if hit:
                    filled[i] = True
                    logger.info(f"Take profit hit for {symbol} at level {i+1}: {tp_price}")
                    return (i, tp_price, exit_size)
        
        return None
    
    def get_remaining_targets(self, symbol: str) -> List[Tuple[float, float]]:
        """
        Get remaining unfilled take profit targets.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            List of remaining (price, size) tuples
        """
        if symbol not in self.active_targets:
            return []
        
        tp_info = self.active_targets[symbol]
        targets = tp_info['targets']
        filled = tp_info['filled']
        
        return [target for i, target in enumerate(targets) if not filled[i]]
    
    def all_targets_filled(self, symbol: str) -> bool:
        """
        Check if all take profit targets have been filled.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            True if all targets filled, False otherwise
        """
        if symbol not in self.active_targets:
            return True
        
        filled = self.active_targets[symbol]['filled']
        return all(filled)
    
    def remove_take_profit(self, symbol: str):
        """
        Remove take profit targets for a symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        if symbol in self.active_targets:
            del self.active_targets[symbol]
            logger.info(f"Take profit removed for {symbol}")
    
    def get_next_target(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Get the next unfilled take profit target.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            (price, size) tuple or None
        """
        if symbol not in self.active_targets:
            return None
        
        tp_info = self.active_targets[symbol]
        targets = tp_info['targets']
        filled = tp_info['filled']
        
        for i, target in enumerate(targets):
            if not filled[i]:
                return target
        
        return None
