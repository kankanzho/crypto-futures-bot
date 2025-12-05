"""
YOLO Trainer for Chart Patterns
차트 패턴 YOLO 학습 엔진

Optimized for NVIDIA RTX 3050 (4GB VRAM).
NVIDIA RTX 3050 (4GB VRAM)에 최적화
"""

import os
import logging
import shutil
from typing import Optional
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class YoloTrainer:
    """
    YOLO training engine optimized for RTX 3050
    RTX 3050에 최적화된 YOLO 학습 엔진
    """
    
    def __init__(self, model_name: str = 'yolov8n.pt'):
        """
        Initialize YOLO trainer
        
        Args:
            model_name: Base model to use (yolov8n.pt for nano model)
        """
        self.model_name = model_name
        self.model = None
        
        # Check GPU availability
        self.device = self._check_gpu()
        
        logger.info(f"YoloTrainer initialized")
        logger.info(f"  Base model: {model_name}")
        logger.info(f"  Device: {self.device}")
    
    def _check_gpu(self) -> str:
        """
        Check GPU availability and return device string
        GPU 사용 가능 여부 확인 및 디바이스 문자열 반환
        
        Returns:
            Device string ('0' for GPU, 'cpu' for CPU)
        """
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"✅ GPU detected: {gpu_name}")
            logger.info(f"  VRAM: {vram_gb:.1f} GB")
            
            # Check if it's RTX 3050
            if '3050' in gpu_name:
                logger.info(f"  🎯 RTX 3050 detected - using optimized settings")
            
            return '0'
        else:
            logger.warning(f"⚠️  No GPU detected! Training will be VERY slow on CPU.")
            logger.warning(f"   Consider using a machine with CUDA-capable GPU.")
            return 'cpu'
    
    def load_model(self):
        """
        Load YOLO model
        YOLO 모델 로드
        """
        try:
            self.model = YOLO(self.model_name)
            logger.info(f"Loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def train(
        self,
        data_yaml: str,
        epochs: int = 100,
        batch_size: int = 16,
        imgsz: int = 640,
        patience: int = 20,
        project: str = 'training/runs',
        name: str = 'chart_patterns',
        pretrained: bool = True,
        amp: bool = True,
        cache: bool = True,
        workers: int = 8
    ) -> Optional[str]:
        """
        Train YOLO model with RTX 3050 optimized settings
        RTX 3050 최적화 설정으로 YOLO 모델 학습
        
        Args:
            data_yaml: Path to data.yaml file
            epochs: Number of training epochs
            batch_size: Batch size (16 recommended for 4GB VRAM)
            imgsz: Input image size
            patience: Early stopping patience
            project: Project directory
            name: Run name
            pretrained: Use pretrained weights
            amp: Use Automatic Mixed Precision (Tensor Cores)
            cache: Cache images in RAM (recommended with 16GB RAM)
            workers: Number of worker threads (8 for Ryzen 7)
        
        Returns:
            Path to best model weights or None if failed
        """
        if self.model is None:
            self.load_model()
        
        logger.info(f"🚀 Starting YOLO training")
        logger.info(f"  Model: {self.model_name}")
        logger.info(f"  Epochs: {epochs}")
        logger.info(f"  Batch size: {batch_size}")
        logger.info(f"  Image size: {imgsz}")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  AMP: {amp} (Tensor Core acceleration)")
        logger.info(f"  Cache: {cache}")
        logger.info(f"  Workers: {workers}")
        
        try:
            # Train model
            results = self.model.train(
                data=data_yaml,
                epochs=epochs,
                imgsz=imgsz,
                batch=batch_size,
                device=self.device,
                patience=patience,
                amp=amp,
                cache=cache,
                workers=workers,
                project=project,
                name=name,
                pretrained=pretrained,
                verbose=True,
                plots=True,
                save=True,
                save_period=10  # Save checkpoint every 10 epochs
            )
            
            # Get path to best weights
            best_weights = os.path.join(project, name, 'weights', 'best.pt')
            
            if os.path.exists(best_weights):
                logger.info(f"✅ Training complete!")
                logger.info(f"  Best weights: {best_weights}")
                return best_weights
            else:
                logger.error(f"Training completed but best weights not found at {best_weights}")
                return None
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return None
    
    def deploy_model(
        self,
        weights_path: str,
        deploy_path: str = 'models/best_chart_patterns.pt'
    ) -> bool:
        """
        Deploy trained model to production location
        학습된 모델을 프로덕션 위치에 배포
        
        Args:
            weights_path: Path to trained weights
            deploy_path: Deployment path
        
        Returns:
            True if deployment successful
        """
        try:
            # Create models directory if it doesn't exist
            os.makedirs(os.path.dirname(deploy_path), exist_ok=True)
            
            # Copy weights to deployment location
            shutil.copy2(weights_path, deploy_path)
            
            logger.info(f"✅ Model deployed to: {deploy_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy model: {e}")
            return False
    
    def validate(self, data_yaml: str, weights_path: str = None):
        """
        Validate model on test set
        테스트 세트에서 모델 검증
        
        Args:
            data_yaml: Path to data.yaml file
            weights_path: Path to weights (optional)
        """
        try:
            if weights_path:
                model = YOLO(weights_path)
            elif self.model:
                model = self.model
            else:
                logger.error("No model available for validation")
                return
            
            logger.info(f"🔍 Validating model...")
            
            results = model.val(
                data=data_yaml,
                device=self.device,
                verbose=True
            )
            
            logger.info(f"✅ Validation complete!")
            
            # Log metrics if available
            if hasattr(results, 'box'):
                metrics = results.box
                if hasattr(metrics, 'map50'):
                    logger.info(f"  mAP50: {metrics.map50:.3f}")
                if hasattr(metrics, 'map'):
                    logger.info(f"  mAP50-95: {metrics.map:.3f}")
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")


if __name__ == "__main__":
    # Test the trainer
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    trainer = YoloTrainer()
    trainer._check_gpu()
