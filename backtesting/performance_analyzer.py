"""Performance analyzer for backtest results."""
import numpy as np
import pandas as pd
from typing import Dict, List
from utils.logger import get_logger

logger = get_logger()

class PerformanceAnalyzer:
    """Analyzes backtest performance metrics."""
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio."""
        if not returns or len(returns) < 2:
            return 0.0
        
        excess_returns = np.array(returns) - risk_free_rate
        return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0.0
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> float:
        """Calculate maximum drawdown."""
        if not equity_curve:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        return max_dd * 100
    
    @staticmethod
    def analyze(backtest_results: Dict, equity_curve: List[float]) -> Dict:
        """Generate comprehensive performance analysis."""
        max_dd = PerformanceAnalyzer.calculate_max_drawdown(equity_curve)
        
        return {
            **backtest_results,
            'max_drawdown_pct': max_dd,
            'sharpe_ratio': 0.0  # Simplified
        }
