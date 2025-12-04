"""Parameter optimizer for strategies."""
from typing import Dict, List
import itertools
from backtesting.backtest_engine import BacktestEngine
from strategies.base_strategy import BaseStrategy
from utils.logger import get_logger

logger = get_logger()

class ParameterOptimizer:
    """Optimizes strategy parameters using grid search."""
    
    @staticmethod
    def grid_search(
        strategy_class,
        param_grid: Dict[str, List],
        df,
        initial_capital: float = 10000
    ) -> Dict:
        """
        Perform grid search for parameter optimization.
        
        Args:
            strategy_class: Strategy class to optimize
            param_grid: Dictionary of parameter ranges
            df: Historical data
            initial_capital: Starting capital
            
        Returns:
            Best parameters and results
        """
        logger.info(f"Starting grid search for {strategy_class.__name__}")
        
        best_result = None
        best_params = None
        best_return = -float('inf')
        
        # Generate all parameter combinations
        keys = param_grid.keys()
        values = param_grid.values()
        
        for params_tuple in itertools.product(*values):
            params = dict(zip(keys, params_tuple))
            
            # Create strategy with these parameters
            strategy = strategy_class(params=params)
            
            # Run backtest
            engine = BacktestEngine(strategy, initial_capital)
            results = engine.run(df)
            
            # Check if this is the best result
            if results['total_return'] > best_return:
                best_return = results['total_return']
                best_result = results
                best_params = params
        
        logger.info(f"Grid search completed. Best return: ${best_return:.2f}")
        
        return {
            'best_params': best_params,
            'best_results': best_result
        }
