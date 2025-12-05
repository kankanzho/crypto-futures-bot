"""
Backtest Runner Script
백테스트 실행 스크립트

Entry point for running backtests on the YOLO trading strategy.
YOLO 트레이딩 전략 백테스트 실행을 위한 진입점
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

from backtest import Backtester

# Configure logging / 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to run backtest
    백테스트 실행 메인 함수
    """
    # Load environment variables / 환경 변수 로드
    load_dotenv()
    
    # Parse command line arguments / 명령줄 인수 파싱
    parser = argparse.ArgumentParser(
        description='Run backtest for crypto futures trading bot'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=os.getenv('BACKTEST_START_DATE', '2024-01-01'),
        help='Start date in YYYY-MM-DD format (default: 2024-01-01)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=os.getenv('BACKTEST_END_DATE', '2024-12-01'),
        help='End date in YYYY-MM-DD format (default: 2024-12-01)'
    )
    
    parser.add_argument(
        '--initial-capital',
        type=float,
        default=float(os.getenv('BACKTEST_INITIAL_CAPITAL', '10000')),
        help='Initial capital in USDT (default: 10000)'
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        default=os.getenv('SYMBOL', 'BTC/USDT:USDT'),
        help='Trading symbol (default: BTC/USDT:USDT)'
    )
    
    parser.add_argument(
        '--leverage',
        type=int,
        default=int(os.getenv('LEVERAGE', '3')),
        help='Trading leverage (default: 3)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='backtest_results',
        help='Output directory for results (default: backtest_results)'
    )
    
    args = parser.parse_args()
    
    # Display backtest configuration / 백테스트 설정 표시
    logger.info("=" * 80)
    logger.info("BACKTEST CONFIGURATION")
    logger.info("백테스트 설정")
    logger.info("=" * 80)
    logger.info(f"Start Date: {args.start_date}")
    logger.info(f"End Date: {args.end_date}")
    logger.info(f"Initial Capital: ${args.initial_capital:.2f} USDT")
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Leverage: {args.leverage}x")
    logger.info(f"Output Directory: {args.output_dir}")
    logger.info("=" * 80)
    
    try:
        # Validate dates / 날짜 검증
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        
        if start_date >= end_date:
            logger.error("Start date must be before end date")
            sys.exit(1)
        
        if end_date > datetime.now():
            logger.error("End date cannot be in the future")
            sys.exit(1)
        
        # Create backtester / 백테스터 생성
        backtester = Backtester(
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.initial_capital,
            symbol=args.symbol,
            leverage=args.leverage
        )
        
        # Run backtest / 백테스트 실행
        logger.info("\n🚀 Starting backtest...\n")
        metrics = backtester.run()
        
        # Display results / 결과 표시
        logger.info("\n" + "=" * 80)
        logger.info("BACKTEST RESULTS")
        logger.info("백테스트 결과")
        logger.info("=" * 80)
        logger.info(f"Initial Capital: ${metrics['initial_capital']:.2f} USDT")
        logger.info(f"Final Capital: ${metrics['final_capital']:.2f} USDT")
        logger.info(f"Total Return: ${metrics['total_return']:.2f} ({metrics['total_return_percent']:.2f}%)")
        logger.info("-" * 80)
        logger.info(f"Total Trades: {metrics['total_trades']}")
        logger.info(f"Winning Trades: {metrics['winning_trades']}")
        logger.info(f"Losing Trades: {metrics['losing_trades']}")
        logger.info(f"Win Rate: {metrics['win_rate']:.2f}%")
        logger.info(f"Average Trade PnL: ${metrics['avg_trade_pnl']:.2f}")
        logger.info(f"Avg Profit/Loss Ratio: {metrics['avg_profit_loss_ratio']:.2f}")
        logger.info("-" * 80)
        logger.info(f"Max Drawdown: ${metrics['max_drawdown']:.2f} ({metrics['max_drawdown_percent']:.2f}%)")
        logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info("=" * 80)
        
        # Save results / 결과 저장
        logger.info(f"\n💾 Saving results to {args.output_dir}...")
        backtester.save_results(output_dir=args.output_dir)
        
        logger.info("\n✅ Backtest completed successfully!")
        logger.info(f"📊 Check the {args.output_dir} directory for detailed results and reports")
        
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        logger.error("Please use YYYY-MM-DD format (e.g., 2024-01-01)")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
