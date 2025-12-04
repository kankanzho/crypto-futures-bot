"""
Auto Strategy Manager Module

Manages automatic strategy switching based on market conditions.
Implements safety checks, cooldown periods, and logging.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import threading

from .market_analyzer import MarketAnalyzer, MarketCondition
from .strategy_selector import StrategySelector


# Setup logging
logger = logging.getLogger(__name__)


class AutoStrategyManager:
    """
    Manages automatic strategy switching based on market analysis.
    
    Features:
    - Periodic market analysis
    - Automatic strategy selection
    - Safety checks (position status, cooldown, min duration)
    - Excessive switching protection
    - Comprehensive logging and statistics
    """
    
    def __init__(self, bot: Any, config: dict):
        """
        Initialize the AutoStrategyManager.
        
        Args:
            bot: Trading bot instance with methods:
                - get_current_strategy() -> str
                - set_strategy(name: str) -> bool
                - has_open_positions() -> bool
                - close_all_positions() -> bool
                - get_market_data() -> pd.DataFrame
            config: Configuration dictionary
        """
        self.bot = bot
        self.config = config
        
        # Initialize analyzers
        self.market_analyzer = MarketAnalyzer(config)
        self.strategy_selector = StrategySelector(config)
        
        # Get configuration
        auto_config = config.get('auto_strategy_switching', {})
        self.enabled = auto_config.get('enabled', True)
        self.check_interval = auto_config.get('check_interval', 300)  # 5 minutes
        self.min_strategy_duration = auto_config.get('min_strategy_duration', 1800)  # 30 minutes
        self.switch_cooldown = auto_config.get('switch_cooldown', 600)  # 10 minutes
        self.close_position_before_switch = auto_config.get('close_position_before_switch', False)
        self.score_threshold = auto_config.get('score_threshold', 70)
        self.dry_run = auto_config.get('dry_run', False)
        
        # State tracking
        self.current_strategy = None
        self.last_switch_time = None
        self.strategy_start_time = None
        self.last_check_time = None
        self.switch_history = []
        
        # Thread control
        self._running = False
        self._thread = None
        
        # Statistics file
        self.stats_file = Path('data/strategy_switches.json')
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize current strategy
        try:
            self.current_strategy = self.bot.get_current_strategy()
            self.strategy_start_time = datetime.now()
        except Exception as e:
            logger.warning(f"Could not get current strategy from bot: {e}")
            self.current_strategy = 'combined'
            self.strategy_start_time = datetime.now()
    
    def start(self):
        """Start the auto-switching manager in a background thread."""
        if not self.enabled:
            logger.info("Auto-strategy switching is disabled in config")
            return
        
        if self._running:
            logger.warning("AutoStrategyManager is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info(
            f"AutoStrategyManager started "
            f"(check_interval={self.check_interval}s, dry_run={self.dry_run})"
        )
    
    def stop(self):
        """Stop the auto-switching manager."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        
        logger.info("AutoStrategyManager stopped")
    
    def _run_loop(self):
        """Main loop for periodic market analysis and strategy switching."""
        # Wait 2 minutes on startup (warmup)
        logger.info("Warmup period: 2 minutes before first check")
        time.sleep(120)
        
        while self._running:
            try:
                self.analyze_and_switch()
                self.last_check_time = datetime.now()
            except Exception as e:
                logger.error(f"Error in auto-switching loop: {e}", exc_info=True)
            
            # Sleep until next check
            time.sleep(self.check_interval)
    
    def analyze_and_switch(self) -> bool:
        """
        Analyze market and switch strategy if needed.
        
        Returns:
            True if strategy was switched, False otherwise
        """
        try:
            # 1. Get market data
            market_data = self.bot.get_market_data()
            if market_data is None or len(market_data) == 0:
                logger.warning("Insufficient market data, skipping analysis")
                return False
            
            # 2. Analyze market condition
            market_condition = self.market_analyzer.analyze(market_data)
            self._log_market_analysis(market_condition)
            
            # 3. Select best strategy
            recommended_strategy, score = self.strategy_selector.select_best(market_condition)
            all_scores = self.strategy_selector.score_all_strategies(market_condition)
            self._log_strategy_selection(all_scores, recommended_strategy, score)
            
            # 4. Check if switch is needed
            if self._should_switch(recommended_strategy, score):
                return self._execute_switch(recommended_strategy, market_condition, score)
            else:
                logger.info("No strategy switch needed")
                return False
                
        except Exception as e:
            logger.error(f"Error in analyze_and_switch: {e}", exc_info=True)
            return False
    
    def _should_switch(self, recommended_strategy: str, score: float) -> bool:
        """
        Determine if strategy switch should occur.
        
        Args:
            recommended_strategy: Recommended strategy name
            score: Compatibility score
            
        Returns:
            True if switch should occur
        """
        reasons = []
        
        # Check 1: Different from current strategy
        if recommended_strategy == self.current_strategy:
            logger.info(f"Recommended strategy '{recommended_strategy}' is already active")
            return False
        reasons.append("✅ Different strategy recommended")
        
        # Check 2: Minimum strategy duration
        if self.strategy_start_time:
            duration = (datetime.now() - self.strategy_start_time).total_seconds()
            if duration < self.min_strategy_duration:
                remaining = self.min_strategy_duration - duration
                logger.info(
                    f"Minimum duration not met. "
                    f"Current: {duration/60:.1f} min, "
                    f"Required: {self.min_strategy_duration/60:.1f} min "
                    f"(remaining: {remaining/60:.1f} min)"
                )
                return False
        reasons.append("✅ Minimum duration met")
        
        # Check 3: Score threshold
        if score < self.score_threshold:
            logger.info(
                f"Score {score:.1f} below threshold {self.score_threshold}"
            )
            return False
        reasons.append(f"✅ Score {score:.1f} above threshold {self.score_threshold}")
        
        # Check 4: Cooldown period
        if self.last_switch_time:
            time_since_switch = (datetime.now() - self.last_switch_time).total_seconds()
            if time_since_switch < self.switch_cooldown:
                remaining = self.switch_cooldown - time_since_switch
                logger.info(
                    f"Cooldown period active. "
                    f"Remaining: {remaining/60:.1f} min"
                )
                return False
        reasons.append("✅ Cooldown period passed")
        
        # Check 5: Open positions
        has_positions = self.bot.has_open_positions()
        if has_positions and not self.close_position_before_switch:
            logger.info("Open positions exist, switch postponed")
            return False
        elif has_positions:
            reasons.append("⚠️ Will close positions before switch")
        else:
            reasons.append("✅ No open positions")
        
        # Check 6: Excessive switching protection
        if self._is_excessive_switching():
            logger.warning(
                "Excessive switching detected (>3 switches in 1 hour). "
                "Switching to 'combined' strategy and pausing auto-switching."
            )
            # Force switch to combined strategy
            if self.current_strategy != 'combined':
                self._execute_switch('combined', None, 100, force=True)
            return False
        reasons.append("✅ No excessive switching")
        
        # Log decision
        logger.info("Strategy Switch Decision:")
        for reason in reasons:
            logger.info(f"  {reason}")
        
        return True
    
    def _execute_switch(
        self, 
        new_strategy: str, 
        market_condition: Optional[MarketCondition],
        score: float,
        force: bool = False
    ) -> bool:
        """
        Execute strategy switch.
        
        Args:
            new_strategy: New strategy to switch to
            market_condition: Current market condition (None if forced)
            score: Compatibility score
            force: Force switch bypassing some checks
            
        Returns:
            True if switch was successful
        """
        old_strategy = self.current_strategy
        
        # Close positions if needed
        if not force and self.close_position_before_switch:
            if self.bot.has_open_positions():
                logger.info("Closing all positions before strategy switch...")
                if self.dry_run:
                    logger.info("[DRY RUN] Would close all positions")
                else:
                    success = self.bot.close_all_positions()
                    if not success:
                        logger.error("Failed to close positions, aborting switch")
                        return False
                    # Wait a moment for positions to close
                    time.sleep(2)
        
        # Execute switch
        if self.dry_run:
            logger.info(f"[DRY RUN] Would switch strategy: {old_strategy} → {new_strategy}")
            success = True
        else:
            success = self.bot.set_strategy(new_strategy)
        
        if success:
            # Update state
            self.current_strategy = new_strategy
            self.strategy_start_time = datetime.now()
            self.last_switch_time = datetime.now()
            
            # Record in history
            switch_record = {
                'timestamp': datetime.now().isoformat(),
                'from_strategy': old_strategy,
                'to_strategy': new_strategy,
                'market_condition': {
                    'volatility': market_condition.volatility if market_condition else 'N/A',
                    'trend': market_condition.trend if market_condition else 'N/A',
                    'volume': market_condition.volume if market_condition else 'N/A',
                } if market_condition else None,
                'score': score,
                'forced': force,
                'dry_run': self.dry_run
            }
            self.switch_history.append(switch_record)
            
            # Save to file
            self._save_switch_record(switch_record)
            
            # Log success
            logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}SUCCESS - Strategy switched: {old_strategy} → {new_strategy}")
            if market_condition:
                logger.info(
                    f"  Market: Volatility={market_condition.volatility}, "
                    f"Trend={market_condition.trend}, "
                    f"Volume={market_condition.volume}"
                )
            logger.info(f"  Score: {score:.1f}")
            logger.info(f"  Next check: {(datetime.now() + timedelta(seconds=self.check_interval)).strftime('%H:%M:%S')}")
            
            return True
        else:
            logger.error(f"Failed to switch strategy to {new_strategy}")
            return False
    
    def _is_excessive_switching(self) -> bool:
        """
        Check if there have been too many switches recently.
        
        Returns:
            True if more than 3 switches in the last hour
        """
        if len(self.switch_history) < 3:
            return False
        
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_switches = [
            s for s in self.switch_history
            if datetime.fromisoformat(s['timestamp']) > one_hour_ago
        ]
        
        return len(recent_switches) >= 3
    
    def _log_market_analysis(self, condition: MarketCondition):
        """Log market analysis results."""
        logger.info("=" * 60)
        logger.info("Market Analysis:")
        logger.info(f"  Volatility: {condition.volatility}")
        
        if condition.metrics:
            logger.info(
                f"    ATR: {condition.metrics.get('atr', 0):.6f}, "
                f"ATR%: {condition.metrics.get('atr_pct', 0):.2f}%, "
                f"BB Width: {condition.metrics.get('bb_width', 0):.2f}%"
            )
        
        logger.info(f"  Trend: {condition.trend}")
        if condition.metrics:
            logger.info(
                f"    ADX: {condition.metrics.get('adx', 0):.1f}, "
                f"EMA Up: {condition.metrics.get('ema_aligned_up', False)}, "
                f"EMA Down: {condition.metrics.get('ema_aligned_down', False)}"
            )
        
        logger.info(f"  Volume: {condition.volume}")
        if condition.metrics:
            logger.info(
                f"    Ratio: {condition.metrics.get('volume_ratio', 0):.2f}x average"
            )
    
    def _log_strategy_selection(self, all_scores, recommended, score):
        """Log strategy selection results."""
        logger.info("-" * 60)
        logger.info("Strategy Selection:")
        
        # Log top 3 strategies
        for i, strategy_score in enumerate(all_scores[:3], 1):
            marker = "⭐ BEST" if strategy_score.name == recommended else ""
            logger.info(f"  {i}. {strategy_score.name}: {strategy_score.score:.1f} points {marker}")
            for reason in strategy_score.reasons[:2]:  # Show first 2 reasons
                logger.info(f"      - {reason}")
        
        # Show current strategy score if not in top 3
        current_in_top3 = any(s.name == self.current_strategy for s in all_scores[:3])
        if not current_in_top3:
            current_score = next((s for s in all_scores if s.name == self.current_strategy), None)
            if current_score:
                logger.info(f"  ... Current ({self.current_strategy}): {current_score.score:.1f} points")
        
        # Log duration if strategy is active
        if self.strategy_start_time:
            duration_min = (datetime.now() - self.strategy_start_time).total_seconds() / 60
            logger.info(f"  Current strategy: {self.current_strategy} (used for {duration_min:.1f} min)")
    
    def _save_switch_record(self, record: dict):
        """Save switch record to JSON file."""
        try:
            # Load existing records
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {'switches': []}
            
            # Add new record
            data['switches'].append(record)
            
            # Save
            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving switch record: {e}")
    
    def get_statistics(self) -> dict:
        """
        Get statistics about strategy switches.
        
        Returns:
            Dict with statistics
        """
        if not self.switch_history:
            return {
                'total_switches': 0,
                'current_strategy': self.current_strategy,
                'strategy_duration_minutes': 0
            }
        
        # Calculate time per strategy
        time_per_strategy = {}
        for i, switch in enumerate(self.switch_history):
            strategy = switch['from_strategy']
            
            # Calculate duration
            start_time = datetime.fromisoformat(switch['timestamp'])
            if i + 1 < len(self.switch_history):
                end_time = datetime.fromisoformat(self.switch_history[i + 1]['timestamp'])
            else:
                end_time = datetime.now()
            
            duration_min = (end_time - start_time).total_seconds() / 60
            
            if strategy not in time_per_strategy:
                time_per_strategy[strategy] = 0
            time_per_strategy[strategy] += duration_min
        
        # Current strategy duration
        current_duration = 0
        if self.strategy_start_time:
            current_duration = (datetime.now() - self.strategy_start_time).total_seconds() / 60
        
        return {
            'total_switches': len(self.switch_history),
            'current_strategy': self.current_strategy,
            'strategy_duration_minutes': current_duration,
            'time_per_strategy': time_per_strategy,
            'last_switch_time': self.last_switch_time.isoformat() if self.last_switch_time else None,
            'switches_last_hour': len([
                s for s in self.switch_history
                if datetime.fromisoformat(s['timestamp']) > datetime.now() - timedelta(hours=1)
            ])
        }
