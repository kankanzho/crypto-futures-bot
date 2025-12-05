# Training Module
# 학습 모듈

This directory contains the YOLO training pipeline for chart pattern detection.

이 디렉토리에는 차트 패턴 탐지를 위한 YOLO 학습 파이프라인이 포함되어 있습니다.

## Quick Start

Run the training pipeline:
```bash
python train_yolo_model.py
```

For detailed instructions, see [docs/YOLO_TRAINING.md](../docs/YOLO_TRAINING.md)

## Modules

- **data_collector.py** - Collects chart images from Bybit API
- **auto_labeler.py** - Automatic pattern labeling
- **dataset_preparer.py** - Prepares YOLO dataset structure
- **yolo_trainer.py** - YOLO training engine

## Dataset Structure

```
dataset/
├── raw_images/          # Collected images
├── raw_labels/          # Generated labels
├── train/              # Training set
│   ├── images/
│   └── labels/
├── valid/              # Validation set
│   ├── images/
│   └── labels/
├── test/               # Test set
│   ├── images/
│   └── labels/
└── data.yaml           # YOLO configuration
```

## Outputs

- **runs/** - Training runs and results
- **training.log** - Training logs
- **../models/best_chart_patterns.pt** - Trained model (deployed)
