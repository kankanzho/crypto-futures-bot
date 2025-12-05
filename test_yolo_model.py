"""
Test YOLO Model
YOLO 모델 테스트

Test the trained YOLO model on sample images.
학습된 YOLO 모델을 샘플 이미지에서 테스트
"""

import os
import sys
import random
import logging
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_test_images(test_dir: str = 'training/dataset/test/images') -> list:
    """
    Find test images in the test directory
    테스트 디렉토리에서 테스트 이미지 찾기
    
    Args:
        test_dir: Path to test images directory
    
    Returns:
        List of image paths
    """
    if not os.path.exists(test_dir):
        logger.error(f"Test directory not found: {test_dir}")
        return []
    
    image_files = [
        os.path.join(test_dir, f)
        for f in os.listdir(test_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    
    logger.info(f"Found {len(image_files)} test images")
    return image_files


def test_model_on_image(
    model: YOLO,
    image_path: str,
    output_dir: str = 'training/test_results',
    confidence: float = 0.5
):
    """
    Test model on a single image and save result
    단일 이미지에서 모델 테스트 및 결과 저장
    
    Args:
        model: YOLO model
        image_path: Path to test image
        output_dir: Directory to save results
        confidence: Confidence threshold
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not read image: {image_path}")
            return
        
        # Run detection
        results = model(image, conf=confidence, verbose=False)
        
        # Get image filename
        image_filename = os.path.basename(image_path)
        image_name = os.path.splitext(image_filename)[0]
        
        # Process results
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id] if hasattr(result, 'names') else f"class_{class_id}"
                
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                detections.append({
                    'class': class_name,
                    'confidence': conf,
                    'bbox': (int(x1), int(y1), int(x2), int(y2))
                })
        
        # Draw detections on image
        result_image = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class']
            conf = det['confidence']
            
            # Draw bounding box
            color = (0, 255, 0) if 'bull' in class_name or 'ascending' in class_name else (0, 0, 255)
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            label_y = max(y1 - 10, label_size[1])
            
            cv2.rectangle(
                result_image,
                (x1, label_y - label_size[1] - 5),
                (x1 + label_size[0], label_y),
                color,
                -1
            )
            cv2.putText(
                result_image,
                label,
                (x1, label_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        # Save result
        output_path = os.path.join(output_dir, f"{image_name}_result.png")
        cv2.imwrite(output_path, result_image)
        
        # Print results
        print(f"\n📸 Image: {image_filename}")
        if detections:
            print(f"  Detections: {len(detections)}")
            for det in detections:
                print(f"    - {det['class']}: {det['confidence']:.2f}")
        else:
            print(f"  No patterns detected")
        print(f"  Result saved: {output_path}")
        
        logger.info(f"Tested {image_filename}: {len(detections)} detections")
        
    except Exception as e:
        logger.error(f"Error testing image {image_path}: {e}")


def main():
    """Main test function"""
    print("=" * 80)
    print("🧪 YOLO Model Testing")
    print("   YOLO 모델 테스트")
    print("=" * 80)
    print()
    
    # Check if model exists
    model_path = 'models/best_chart_patterns.pt'
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        print(f"   Please train the model first using: python train_yolo_model.py")
        return False
    
    print(f"✅ Model found: {model_path}")
    
    # Load model
    print(f"Loading model...")
    try:
        model = YOLO(model_path)
        print(f"✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        logger.error(f"Failed to load model: {e}")
        return False
    
    print()
    
    # Find test images
    test_images = find_test_images()
    
    if not test_images:
        print("❌ No test images found")
        print("   Test images should be in: training/dataset/test/images/")
        return False
    
    print(f"✅ Found {len(test_images)} test images")
    print()
    
    # Select test mode
    print("Select test mode:")
    print("  1. Test on random image")
    print("  2. Test on multiple random images (5)")
    print("  3. Test on all images")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    print()
    
    # Process based on choice
    if choice == '1':
        # Test on 1 random image
        image_path = random.choice(test_images)
        print("Testing on 1 random image...")
        print("-" * 80)
        test_model_on_image(model, image_path)
        
    elif choice == '2':
        # Test on 5 random images
        num_samples = min(5, len(test_images))
        sample_images = random.sample(test_images, num_samples)
        
        print(f"Testing on {num_samples} random images...")
        print("-" * 80)
        
        for image_path in sample_images:
            test_model_on_image(model, image_path)
        
    elif choice == '3':
        # Test on all images
        print(f"Testing on all {len(test_images)} images...")
        print("-" * 80)
        
        for image_path in test_images:
            test_model_on_image(model, image_path)
    
    else:
        print("Invalid choice")
        return False
    
    print()
    print("=" * 80)
    print("✅ Testing complete!")
    print("=" * 80)
    print()
    print("📁 Results saved to: training/test_results/")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
