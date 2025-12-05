"""
Dataset Preparer for YOLO Training
YOLO 데이터셋 구조화

Prepares dataset in YOLO format with train/valid/test splits.
train/valid/test 분할로 YOLO 형식 데이터셋 준비
"""

import os
import shutil
import random
import logging
from typing import Tuple
import yaml

logger = logging.getLogger(__name__)


class DatasetPreparer:
    """
    Prepares dataset for YOLO training
    YOLO 학습을 위한 데이터셋 준비
    """
    
    def __init__(
        self,
        raw_images_dir: str = 'training/dataset/raw_images',
        raw_labels_dir: str = 'training/dataset/raw_labels',
        dataset_root: str = 'training/dataset'
    ):
        """
        Initialize dataset preparer
        
        Args:
            raw_images_dir: Directory with raw images
            raw_labels_dir: Directory with raw labels
            dataset_root: Root directory for dataset
        """
        self.raw_images_dir = raw_images_dir
        self.raw_labels_dir = raw_labels_dir
        self.dataset_root = dataset_root
        
        self.train_images_dir = os.path.join(dataset_root, 'train', 'images')
        self.train_labels_dir = os.path.join(dataset_root, 'train', 'labels')
        self.valid_images_dir = os.path.join(dataset_root, 'valid', 'images')
        self.valid_labels_dir = os.path.join(dataset_root, 'valid', 'labels')
        self.test_images_dir = os.path.join(dataset_root, 'test', 'images')
        self.test_labels_dir = os.path.join(dataset_root, 'test', 'labels')
        
        logger.info(f"DatasetPreparer initialized")
        logger.info(f"  Source images: {raw_images_dir}")
        logger.info(f"  Source labels: {raw_labels_dir}")
        logger.info(f"  Dataset root: {dataset_root}")
    
    def clear_dataset_dirs(self):
        """
        Clear existing train/valid/test directories
        기존 train/valid/test 디렉토리 정리
        """
        dirs_to_clear = [
            self.train_images_dir,
            self.train_labels_dir,
            self.valid_images_dir,
            self.valid_labels_dir,
            self.test_images_dir,
            self.test_labels_dir
        ]
        
        for dir_path in dirs_to_clear:
            if os.path.exists(dir_path):
                # Remove all files in directory
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
    
    def split_dataset(
        self,
        train_ratio: float = 0.7,
        valid_ratio: float = 0.2,
        test_ratio: float = 0.1,
        seed: int = 42
    ) -> Tuple[int, int, int]:
        """
        Split dataset into train/valid/test sets
        데이터셋을 train/valid/test로 분할
        
        Args:
            train_ratio: Ratio for training set
            valid_ratio: Ratio for validation set
            test_ratio: Ratio for test set
            seed: Random seed for reproducibility
        
        Returns:
            Tuple of (train_count, valid_count, test_count)
        """
        # Validate ratios
        if not abs(train_ratio + valid_ratio + test_ratio - 1.0) < 0.001:
            raise ValueError(f"Ratios must sum to 1.0, got {train_ratio + valid_ratio + test_ratio}")
        
        # Get all image files
        image_files = [
            f for f in os.listdir(self.raw_images_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        
        if not image_files:
            logger.warning(f"No images found in {self.raw_images_dir}")
            return 0, 0, 0
        
        logger.info(f"📂 Preparing dataset")
        logger.info(f"  Total images: {len(image_files)}")
        logger.info(f"  Split ratio: {train_ratio:.0%} / {valid_ratio:.0%} / {test_ratio:.0%}")
        
        # Shuffle with seed
        random.seed(seed)
        random.shuffle(image_files)
        
        # Calculate split indices
        total = len(image_files)
        train_end = int(total * train_ratio)
        valid_end = train_end + int(total * valid_ratio)
        
        train_files = image_files[:train_end]
        valid_files = image_files[train_end:valid_end]
        test_files = image_files[valid_end:]
        
        # Clear existing files
        self.clear_dataset_dirs()
        
        # Copy files to respective directories
        train_count = self._copy_files(train_files, self.train_images_dir, self.train_labels_dir)
        valid_count = self._copy_files(valid_files, self.valid_images_dir, self.valid_labels_dir)
        test_count = self._copy_files(test_files, self.test_images_dir, self.test_labels_dir)
        
        logger.info(f"  Train: {train_count}")
        logger.info(f"  Valid: {valid_count}")
        logger.info(f"  Test: {test_count}")
        
        return train_count, valid_count, test_count
    
    def _copy_files(
        self,
        files: list,
        target_images_dir: str,
        target_labels_dir: str
    ) -> int:
        """
        Copy image and label files to target directories
        이미지와 라벨 파일을 타겟 디렉토리로 복사
        
        Args:
            files: List of image filenames
            target_images_dir: Target directory for images
            target_labels_dir: Target directory for labels
        
        Returns:
            Number of files copied
        """
        # Ensure target directories exist
        os.makedirs(target_images_dir, exist_ok=True)
        os.makedirs(target_labels_dir, exist_ok=True)
        
        copied = 0
        
        for image_file in files:
            # Copy image
            src_image = os.path.join(self.raw_images_dir, image_file)
            dst_image = os.path.join(target_images_dir, image_file)
            shutil.copy2(src_image, dst_image)
            
            # Copy label
            label_file = os.path.splitext(image_file)[0] + '.txt'
            src_label = os.path.join(self.raw_labels_dir, label_file)
            dst_label = os.path.join(target_labels_dir, label_file)
            
            if os.path.exists(src_label):
                shutil.copy2(src_label, dst_label)
            else:
                # Create empty label file if no label exists
                with open(dst_label, 'w') as f:
                    pass
            
            copied += 1
        
        return copied
    
    def create_data_yaml(
        self,
        class_names: list,
        yaml_path: str = None
    ):
        """
        Create data.yaml configuration file for YOLO
        YOLO를 위한 data.yaml 설정 파일 생성
        
        Args:
            class_names: List of class names
            yaml_path: Path to save YAML file (default: dataset_root/data.yaml)
        """
        if yaml_path is None:
            yaml_path = os.path.join(self.dataset_root, 'data.yaml')
        
        # Get absolute paths
        train_path = os.path.abspath(self.train_images_dir)
        valid_path = os.path.abspath(self.valid_images_dir)
        test_path = os.path.abspath(self.test_images_dir)
        
        # Create YAML configuration
        data_config = {
            'path': os.path.abspath(self.dataset_root),
            'train': train_path,
            'val': valid_path,
            'test': test_path,
            'nc': len(class_names),
            'names': class_names
        }
        
        # Save YAML file
        with open(yaml_path, 'w') as f:
            yaml.dump(data_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"✅ Created data.yaml at {yaml_path}")
        logger.info(f"  Classes: {len(class_names)}")
    
    def validate_dataset(self) -> bool:
        """
        Validate dataset structure and files
        데이터셋 구조 및 파일 검증
        
        Returns:
            True if dataset is valid
        """
        logger.info(f"🔍 Validating dataset...")
        
        errors = []
        
        # Check if directories exist
        required_dirs = [
            self.train_images_dir,
            self.train_labels_dir,
            self.valid_images_dir,
            self.valid_labels_dir,
            self.test_images_dir,
            self.test_labels_dir
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                errors.append(f"Missing directory: {dir_path}")
        
        # Check if data.yaml exists
        yaml_path = os.path.join(self.dataset_root, 'data.yaml')
        if not os.path.exists(yaml_path):
            errors.append(f"Missing data.yaml: {yaml_path}")
        
        # Check if images and labels match
        for split_name, images_dir, labels_dir in [
            ('train', self.train_images_dir, self.train_labels_dir),
            ('valid', self.valid_images_dir, self.valid_labels_dir),
            ('test', self.test_images_dir, self.test_labels_dir)
        ]:
            if os.path.exists(images_dir):
                image_files = [
                    f for f in os.listdir(images_dir)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                ]
                
                for image_file in image_files:
                    label_file = os.path.splitext(image_file)[0] + '.txt'
                    label_path = os.path.join(labels_dir, label_file)
                    
                    if not os.path.exists(label_path):
                        errors.append(f"Missing label for {split_name}/{image_file}")
        
        if errors:
            logger.error(f"❌ Dataset validation failed:")
            for error in errors[:10]:  # Show first 10 errors
                logger.error(f"  - {error}")
            if len(errors) > 10:
                logger.error(f"  ... and {len(errors) - 10} more errors")
            return False
        
        logger.info(f"✅ Dataset validation passed!")
        return True
    
    def prepare(
        self,
        class_names: list,
        train_ratio: float = 0.7,
        valid_ratio: float = 0.2,
        test_ratio: float = 0.1
    ) -> bool:
        """
        Full dataset preparation pipeline
        전체 데이터셋 준비 파이프라인
        
        Args:
            class_names: List of class names
            train_ratio: Training set ratio
            valid_ratio: Validation set ratio
            test_ratio: Test set ratio
        
        Returns:
            True if preparation successful
        """
        try:
            # Split dataset
            train_count, valid_count, test_count = self.split_dataset(
                train_ratio, valid_ratio, test_ratio
            )
            
            if train_count == 0:
                logger.error("No training data available")
                return False
            
            # Create data.yaml
            self.create_data_yaml(class_names)
            
            # Validate dataset
            if not self.validate_dataset():
                return False
            
            logger.info(f"✅ Dataset prepared successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare dataset: {e}")
            return False


if __name__ == "__main__":
    # Test the preparer
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    preparer = DatasetPreparer()
    
    # Example class names
    class_names = [
        'bull_flag', 'double_bottom', 'inverse_head_and_shoulders',
        'ascending_triangle', 'bullish_engulfing', 'bear_flag',
        'double_top', 'head_and_shoulders', 'descending_triangle',
        'bearish_engulfing'
    ]
    
    success = preparer.prepare(class_names)
    print(f"Preparation successful: {success}")
