"""
YOLO Training Pipeline
YOLO 학습 파이프라인

Complete automated training pipeline for chart pattern detection.
차트 패턴 탐지를 위한 완전 자동화 학습 파이프라인
"""

import os
import sys
import logging
from datetime import datetime

from training.data_collector import DataCollector
from training.auto_labeler import AutoLabeler
from training.dataset_preparer import DatasetPreparer
from training.yolo_trainer import YoloTrainer


# Configure logging
def setup_logging():
    """Setup logging to console and file"""
    log_dir = 'training'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'training.log')
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return log_file


def print_banner():
    """Print welcome banner"""
    print("=" * 80)
    print("🚀 YOLO Chart Pattern Training Pipeline")
    print("   차트 패턴 YOLO 학습 파이프라인")
    print("=" * 80)
    print()


def select_training_mode():
    """
    Let user select training mode
    학습 모드 선택
    
    Returns:
        Tuple of (num_images, epochs, mode_name)
    """
    print("Select training mode:")
    print("  1. Quick Test   - 100 images,  5 epochs  (~5 minutes)")
    print("  2. Light        - 500 images,  50 epochs (~30 minutes)")
    print("  3. Full         - 1000 images, 100 epochs (~1-1.5 hours)")
    print("  4. Custom")
    print()
    
    while True:
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            return 100, 5, "Quick Test"
        elif choice == '2':
            return 500, 50, "Light"
        elif choice == '3':
            return 1000, 100, "Full"
        elif choice == '4':
            try:
                num_images = int(input("Number of images: ").strip())
                epochs = int(input("Number of epochs: ").strip())
                return num_images, epochs, "Custom"
            except ValueError:
                print("Invalid input. Please enter numbers.")
                continue
        else:
            print("Invalid choice. Please enter 1-4.")


def main():
    """Main training pipeline"""
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    # Print banner
    print_banner()
    
    # Select training mode
    num_images, epochs, mode_name = select_training_mode()
    
    print()
    print("=" * 80)
    print(f"Starting {mode_name} Training Mode")
    print(f"  Images: {num_images}")
    print(f"  Epochs: {epochs}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    logger.info(f"Starting {mode_name} training mode")
    logger.info(f"Images: {num_images}, Epochs: {epochs}")
    
    try:
        # Step 1: Collect chart images
        print("📊 Step 1/4: Collecting chart images")
        print("-" * 80)
        
        collector = DataCollector()
        collected_count = collector.collect_images(target_count=num_images)
        
        if collected_count == 0:
            logger.error("No images collected. Aborting.")
            print("\n❌ Failed: No images collected")
            return False
        
        print(f"✅ Collected {collected_count} chart images\n")
        
        # Step 2: Auto-label patterns
        print("🏷️  Step 2/4: Auto-labeling patterns")
        print("-" * 80)
        
        labeler = AutoLabeler()
        pattern_stats = labeler.label_all_images()
        
        print("✅ Labeling complete!\n")
        
        # Step 3: Prepare dataset
        print("📂 Step 3/4: Preparing dataset")
        print("-" * 80)
        
        preparer = DatasetPreparer()
        class_names = labeler.get_class_names()
        
        success = preparer.prepare(class_names)
        
        if not success:
            logger.error("Dataset preparation failed. Aborting.")
            print("\n❌ Failed: Dataset preparation error")
            return False
        
        print("✅ Dataset prepared!\n")
        
        # Step 4: Train YOLO model
        print("🚀 Step 4/4: Training YOLO model")
        print("-" * 80)
        print(f"  Model: YOLOv8n")
        print(f"  Epochs: {epochs}")
        print(f"  Batch size: 16")
        print(f"  This may take a while... ☕")
        print()
        
        trainer = YoloTrainer(model_name='yolov8n.pt')
        
        data_yaml = os.path.join('training', 'dataset', 'data.yaml')
        
        best_weights = trainer.train(
            data_yaml=data_yaml,
            epochs=epochs,
            batch_size=16,
            patience=20
        )
        
        if not best_weights:
            logger.error("Training failed to produce weights. Aborting.")
            print("\n❌ Failed: Training error")
            return False
        
        # Deploy model
        deployed = trainer.deploy_model(best_weights)
        
        if not deployed:
            logger.error("Model deployment failed")
            print("\n⚠️  Warning: Model deployment failed")
        else:
            print(f"\n✅ Model deployed to: models/best_chart_patterns.pt")
        
        # Final summary
        print()
        print("=" * 80)
        print("🎉 Training Complete!")
        print("=" * 80)
        print()
        print("📁 Files created:")
        print(f"  - Model: models/best_chart_patterns.pt")
        print(f"  - Logs: {log_file}")
        print(f"  - Results: training/runs/chart_patterns/")
        print()
        print("▶️  Next steps:")
        print("  1. Test model: python test_yolo_model.py")
        print("  2. Run backtest: python run_backtest.py")
        print("  3. Start bot: python bybit_yolo_bot.py")
        print()
        
        logger.info("Training pipeline completed successfully!")
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        logger.warning("Training interrupted by user")
        return False
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        print(f"\n\n❌ Error: {e}")
        print(f"Check {log_file} for details")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
