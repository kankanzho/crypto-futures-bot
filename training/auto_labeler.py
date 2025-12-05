"""
Auto Labeler for YOLO Training
자동 패턴 라벨링

Rule-based automatic pattern labeling for chart images.
규칙 기반 차트 이미지 자동 패턴 라벨링
"""

import os
import random
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

import cv2
from tqdm import tqdm

logger = logging.getLogger(__name__)


class AutoLabeler:
    """
    Automatic labeling system for chart patterns
    차트 패턴 자동 라벨링 시스템
    """
    
    # Pattern class definitions
    PATTERNS = [
        'bull_flag',
        'double_bottom',
        'inverse_head_and_shoulders',
        'ascending_triangle',
        'bullish_engulfing',
        'bear_flag',
        'double_top',
        'head_and_shoulders',
        'descending_triangle',
        'bearish_engulfing'
    ]
    
    def __init__(
        self,
        images_dir: str = 'training/dataset/raw_images',
        labels_dir: str = 'training/dataset/raw_labels'
    ):
        """
        Initialize auto labeler
        
        Args:
            images_dir: Directory containing images
            labels_dir: Directory to save labels
        """
        self.images_dir = images_dir
        self.labels_dir = labels_dir
        os.makedirs(labels_dir, exist_ok=True)
        
        # Create class mapping
        self.class_to_id = {pattern: idx for idx, pattern in enumerate(self.PATTERNS)}
        self.id_to_class = {idx: pattern for pattern, idx in self.class_to_id.items()}
        
        logger.info(f"AutoLabeler initialized")
        logger.info(f"  Classes: {len(self.PATTERNS)}")
        logger.info(f"  Images: {images_dir}")
        logger.info(f"  Labels: {labels_dir}")
    
    def generate_label_for_image(
        self,
        image_path: str,
        pattern_probability: float = 0.5
    ) -> List[Tuple[int, float, float, float, float]]:
        """
        Generate YOLO format labels for an image
        이미지에 대한 YOLO 형식 라벨 생성
        
        ⚠️  WARNING: This is a DEMO labeler that generates RANDOM patterns!
        ⚠️  경고: 이것은 랜덤 패턴을 생성하는 데모 라벨러입니다!
        
        This rule-based labeler creates completely random pattern labels
        without any actual chart analysis. It is designed ONLY for:
        - Testing the training pipeline
        - Demonstrating the workflow
        - Educational purposes
        
        For PRODUCTION use, you MUST:
        - Implement real pattern detection algorithms, OR
        - Use manual labeling by experts, OR
        - Collect pre-labeled datasets
        
        Models trained with random labels will NOT detect real patterns!
        
        이 규칙 기반 라벨러는 실제 차트 분석 없이 완전히 랜덤한 패턴
        라벨을 생성합니다. 오직 다음 용도로만 설계되었습니다:
        - 학습 파이프라인 테스트
        - 워크플로우 시연
        - 교육 목적
        
        프로덕션 사용을 위해서는 반드시:
        - 실제 패턴 탐지 알고리즘 구현, 또는
        - 전문가에 의한 수동 라벨링, 또는
        - 사전 라벨링된 데이터셋 수집
        
        랜덤 라벨로 학습된 모델은 실제 패턴을 탐지하지 못합니다!
        
        Args:
            image_path: Path to image file
            pattern_probability: Probability of pattern existing in image
        
        Returns:
            List of (class_id, x_center, y_center, width, height) tuples
            All values are normalized to [0, 1]
        """
        labels = []
        
        # Get image dimensions
        image = cv2.imread(image_path)
        if image is None:
            logger.warning(f"Could not read image: {image_path}")
            return labels
        
        height, width = image.shape[:2]
        
        # ⚠️  RANDOM LABELING - NOT REAL PATTERN DETECTION
        # Decide if pattern exists (demo logic)
        if random.random() < pattern_probability:
            # Randomly select 1-2 patterns
            num_patterns = random.randint(1, 2)
            
            for _ in range(num_patterns):
                # Random pattern class
                class_id = random.randint(0, len(self.PATTERNS) - 1)
                
                # Generate bounding box (centered with some variation)
                # x_center, y_center are in [0.3, 0.7] range (middle of image)
                x_center = random.uniform(0.3, 0.7)
                y_center = random.uniform(0.3, 0.7)
                
                # Width and height as fraction of image
                box_width = random.uniform(0.2, 0.5)
                box_height = random.uniform(0.2, 0.4)
                
                labels.append((class_id, x_center, y_center, box_width, box_height))
        
        return labels
    
    def save_label_file(
        self,
        image_filename: str,
        labels: List[Tuple[int, float, float, float, float]]
    ):
        """
        Save labels to YOLO format text file
        YOLO 형식 텍스트 파일로 라벨 저장
        
        YOLO format: class_id x_center y_center width height
        All values normalized to [0, 1]
        
        Args:
            image_filename: Name of image file
            labels: List of label tuples
        """
        # Create label filename (replace image extension with .txt)
        label_filename = os.path.splitext(image_filename)[0] + '.txt'
        label_path = os.path.join(self.labels_dir, label_filename)
        
        with open(label_path, 'w') as f:
            for class_id, x, y, w, h in labels:
                f.write(f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
    
    def label_all_images(self, pattern_probability: float = 0.5) -> Dict[str, int]:
        """
        Label all images in the images directory
        이미지 디렉토리의 모든 이미지 라벨링
        
        Args:
            pattern_probability: Probability of pattern in each image
        
        Returns:
            Dictionary with pattern distribution statistics
        """
        # Get all image files
        image_files = [
            f for f in os.listdir(self.images_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        
        if not image_files:
            logger.warning(f"No images found in {self.images_dir}")
            return {}
        
        logger.info(f"🏷️  Starting auto-labeling")
        logger.info(f"  Images to label: {len(image_files)}")
        logger.info(f"  Pattern probability: {pattern_probability}")
        
        # Statistics
        pattern_counts = defaultdict(int)
        total_labels = 0
        images_with_patterns = 0
        
        for image_file in tqdm(image_files, desc="Labeling images"):
            image_path = os.path.join(self.images_dir, image_file)
            
            # Generate labels
            labels = self.generate_label_for_image(image_path, pattern_probability)
            
            # Save labels
            self.save_label_file(image_file, labels)
            
            # Update statistics
            if labels:
                images_with_patterns += 1
                total_labels += len(labels)
                
                for class_id, _, _, _, _ in labels:
                    pattern_name = self.id_to_class[class_id]
                    pattern_counts[pattern_name] += 1
        
        logger.info(f"✅ Labeling complete!")
        logger.info(f"  Images processed: {len(image_files)}")
        logger.info(f"  Images with patterns: {images_with_patterns}")
        logger.info(f"  Total labels: {total_labels}")
        
        # Print pattern distribution
        if pattern_counts:
            logger.info(f"\n  Pattern distribution:")
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_labels) * 100 if total_labels > 0 else 0
                logger.info(f"    - {pattern}: {count} ({percentage:.1f}%)")
        
        return dict(pattern_counts)
    
    def get_class_names(self) -> List[str]:
        """
        Get list of class names
        클래스 이름 목록 가져오기
        
        Returns:
            List of pattern names
        """
        return self.PATTERNS.copy()


if __name__ == "__main__":
    # Test the labeler
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    labeler = AutoLabeler()
    stats = labeler.label_all_images()
    print(f"Pattern statistics: {stats}")
