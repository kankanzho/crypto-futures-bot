"""
Parameter optimizer for strategy backtesting.
Performs grid search to find optimal parameters.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from itertools import product
from loguru import logger

from ..strategies.base_strategy import BaseStrategy
from .backtest_engine import BacktestEngine


class StrategyOptimizer:
    """Optimizer for strategy parameters using grid search."""
    
    def __init__(self, strategy_class, initial_capital: float,
                 commission: float = 0.0006, slippage: float = 0.0005,
                 leverage: int = 1):
        """
        Initialize optimizer.
        
        Args:
            strategy_class: Strategy class to optimize
            initial_capital: Initial capital for backtests
            commission: Commission rate
            slippage: Slippage estimate
            leverage: Leverage multiplier
        """
        self.strategy_class = strategy_class
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.leverage = leverage
        
        self.results: List[Dict[str, Any]] = []
        
        logger.info(f"Optimizer initialized for {strategy_class.__name__}")
    
    def optimize(self, data: Dict[str, pd.DataFrame],
                param_ranges: Dict[str, List[Any]],
                stop_loss_config: Dict[str, Any],
                take_profit_config: Dict[str, Any],
                position_size_config: Dict[str, Any],
                metric: str = 'sharpe_ratio') -> Dict[str, Any]:
        """
        Perform grid search optimization.
        
        Args:
            data: Historical data
            param_ranges: Dictionary of parameter name -> list of values to test
            stop_loss_config: Stop loss configuration
            take_profit_config: Take profit configuration
            position_size_config: Position sizing configuration
            metric: Metric to optimize ('sharpe_ratio', 'total_return', 'win_rate', etc.)
            
        Returns:
            Best parameters and results
        """
        logger.info(f"Starting optimization with metric: {metric}")
        
        # Generate all parameter combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))
        
        total_combinations = len(combinations)
        logger.info(f"Testing {total_combinations} parameter combinations")
        
        best_score = float('-inf')
        best_params = None
        best_results = None
        
        # Test each combination
        for i, combination in enumerate(combinations):
            # Create parameter dictionary
            params = dict(zip(param_names, combination))
            
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{total_combinations}")
            
            # Create strategy with these parameters
            strategy = self.strategy_class(params)
            
            # Run backtest
            engine = BacktestEngine(
                strategy,
                self.initial_capital,
                self.commission,
                self.slippage,
                self.leverage
            )
            
            try:
                results = engine.run(
                    data,
                    stop_loss_config,
                    take_profit_config,
                    position_size_config
                )
                
                # Get metric score
                score = results.get(metric, float('-inf'))
                
                # Store results
                result_entry = {
                    'parameters': params.copy(),
                    'score': score,
                    'metric': metric,
                    **results
                }
                self.results.append(result_entry)
                
                # Update best if better
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    best_results = results.copy()
                    
            except Exception as e:
                logger.error(f"Error testing parameters {params}: {e}")
                continue
        
        logger.info(f"Optimization complete. Best {metric}: {best_score:.2f}")
        logger.info(f"Best parameters: {best_params}")
        
        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'best_results': best_results,
            'all_results': self.results
        }
    
    def get_optimization_summary(self) -> pd.DataFrame:
        """
        Get summary of optimization results as DataFrame.
        
        Returns:
            DataFrame with all tested parameters and results
        """
        if not self.results:
            return pd.DataFrame()
        
        # Flatten results for DataFrame
        flat_results = []
        for result in self.results:
            entry = result['parameters'].copy()
            entry['score'] = result['score']
            entry['total_return'] = result.get('total_return', 0)
            entry['sharpe_ratio'] = result.get('sharpe_ratio', 0)
            entry['win_rate'] = result.get('win_rate', 0)
            entry['max_drawdown_pct'] = result.get('max_drawdown_pct', 0)
            entry['total_trades'] = result.get('total_trades', 0)
            
            flat_results.append(entry)
        
        df = pd.DataFrame(flat_results)
        return df.sort_values('score', ascending=False)
    
    def plot_optimization_results(self, param1: str, param2: str = None,
                                  metric: str = 'sharpe_ratio'):
        """
        Plot optimization results.
        
        Args:
            param1: First parameter to plot
            param2: Second parameter for 2D heatmap (optional)
            metric: Metric to visualize
        """
        import matplotlib.pyplot as plt
        
        df = self.get_optimization_summary()
        
        if param2 is None:
            # 1D plot
            plt.figure(figsize=(10, 6))
            plt.plot(df[param1], df[metric], 'o-')
            plt.xlabel(param1)
            plt.ylabel(metric)
            plt.title(f'{metric} vs {param1}')
            plt.grid(True)
            plt.show()
        else:
            # 2D heatmap
            pivot = df.pivot(index=param1, columns=param2, values=metric)
            
            plt.figure(figsize=(10, 8))
            plt.imshow(pivot, cmap='RdYlGn', aspect='auto')
            plt.colorbar(label=metric)
            plt.xlabel(param2)
            plt.ylabel(param1)
            plt.title(f'{metric} Optimization')
            plt.xticks(range(len(pivot.columns)), pivot.columns)
            plt.yticks(range(len(pivot.index)), pivot.index)
            plt.show()


class WalkForwardOptimizer:
    """Walk-forward optimization to test robustness."""
    
    def __init__(self, strategy_class, initial_capital: float,
                 in_sample_ratio: float = 0.6):
        """
        Initialize walk-forward optimizer.
        
        Args:
            strategy_class: Strategy class to optimize
            initial_capital: Initial capital
            in_sample_ratio: Ratio of data to use for in-sample optimization
        """
        self.strategy_class = strategy_class
        self.initial_capital = initial_capital
        self.in_sample_ratio = in_sample_ratio
        
        logger.info("Walk-forward optimizer initialized")
    
    def optimize(self, data: Dict[str, pd.DataFrame],
                param_ranges: Dict[str, List[Any]],
                stop_loss_config: Dict[str, Any],
                take_profit_config: Dict[str, Any],
                position_size_config: Dict[str, Any],
                n_splits: int = 3) -> Dict[str, Any]:
        """
        Perform walk-forward optimization.
        
        Args:
            data: Historical data
            param_ranges: Parameter ranges to test
            stop_loss_config: Stop loss configuration
            take_profit_config: Take profit configuration
            position_size_config: Position sizing configuration
            n_splits: Number of walk-forward windows
            
        Returns:
            Walk-forward results
        """
        logger.info(f"Starting walk-forward optimization with {n_splits} splits")
        
        # Calculate split points
        first_symbol = list(data.keys())[0]
        total_length = len(data[first_symbol])
        split_size = total_length // n_splits
        
        results = []
        
        for i in range(n_splits):
            logger.info(f"Processing split {i+1}/{n_splits}")
            
            # Calculate in-sample and out-of-sample ranges
            start_idx = i * split_size
            end_idx = start_idx + split_size
            
            in_sample_end = start_idx + int(split_size * self.in_sample_ratio)
            
            # Split data
            in_sample_data = {}
            out_sample_data = {}
            
            for symbol, df in data.items():
                in_sample_data[symbol] = df.iloc[start_idx:in_sample_end]
                out_sample_data[symbol] = df.iloc[in_sample_end:end_idx]
            
            # Optimize on in-sample data
            optimizer = StrategyOptimizer(
                self.strategy_class,
                self.initial_capital
            )
            
            opt_results = optimizer.optimize(
                in_sample_data,
                param_ranges,
                stop_loss_config,
                take_profit_config,
                position_size_config
            )
            
            # Test on out-of-sample data
            best_params = opt_results['best_parameters']
            strategy = self.strategy_class(best_params)
            
            engine = BacktestEngine(strategy, self.initial_capital)
            oos_results = engine.run(
                out_sample_data,
                stop_loss_config,
                take_profit_config,
                position_size_config
            )
            
            results.append({
                'split': i + 1,
                'in_sample_results': opt_results['best_results'],
                'out_sample_results': oos_results,
                'parameters': best_params
            })
        
        logger.info("Walk-forward optimization complete")
        return {
            'splits': results,
            'n_splits': n_splits
        }
