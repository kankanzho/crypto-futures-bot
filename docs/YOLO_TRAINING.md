# YOLO Training Guide
# YOLO 학습 가이드

Complete guide for training YOLO chart pattern detection model optimized for RTX 3050.

RTX 3050에 최적화된 YOLO 차트 패턴 탐지 모델 학습 완전 가이드

## 📋 Table of Contents / 목차

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Training Modes](#training-modes)
4. [GPU Setup](#gpu-setup)
5. [Troubleshooting](#troubleshooting)
6. [Expected Performance](#expected-performance)

---

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Training
```bash
python train_yolo_model.py
```

### Step 3: Select Mode
When prompted, select your training mode:
- **Quick Test**: 5 minutes (for testing)
- **Light**: 30 minutes (for development)
- **Full**: 1-1.5 hours (for production)

### Step 4: Test Model
```bash
python test_yolo_model.py
```

---

## 💻 System Requirements

### Minimum Requirements (최소 요구사항)

- **GPU**: NVIDIA GPU with 4GB+ VRAM (RTX 3050 or better)
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 5GB free space for dataset and models
- **CUDA**: CUDA 11.8 or newer

### Optimized For (최적화 대상)

- **GPU**: NVIDIA GeForce RTX 3050 (4GB VRAM)
- **CPU**: AMD Ryzen 7 3.2GHz (or equivalent)
- **RAM**: 16GB DDR4
- **OS**: Ubuntu 20.04+ / Windows 10+

---

## 🎯 Training Modes

### 1. Quick Test Mode (빠른 테스트)
- **Images**: 100
- **Epochs**: 5
- **Time**: ~5 minutes
- **Purpose**: Quick pipeline test

**When to use**: Testing the pipeline, debugging, quick experiments.

### 2. Light Mode (경량)
- **Images**: 500
- **Epochs**: 50
- **Time**: ~30 minutes
- **Purpose**: Development and iteration

**When to use**: Model development, hyperparameter tuning, feature testing.

### 3. Full Mode (완전)
- **Images**: 1000
- **Epochs**: 100
- **Time**: 1-1.5 hours
- **Purpose**: Production-ready model

**When to use**: Final training for deployment, production use.

### 4. Custom Mode (커스텀)
- **Images**: Your choice
- **Epochs**: Your choice
- **Time**: Varies
- **Purpose**: Specific requirements

**When to use**: Special requirements, research, experimentation.

---

## 🎮 GPU Setup

### Check GPU Availability

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
```

### Expected Output for RTX 3050
```
CUDA available: True
GPU name: NVIDIA GeForce RTX 3050
VRAM: 4.0 GB
```

### Install CUDA (if needed)

**Ubuntu:**
```bash
# Add NVIDIA package repositories
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update

# Install CUDA
sudo apt-get install cuda-11-8
```

**Windows:**
1. Download CUDA Toolkit from [NVIDIA website](https://developer.nvidia.com/cuda-downloads)
2. Install with default settings
3. Reboot system

---

## 🔧 Troubleshooting

### Issue 1: CUDA Out of Memory (CUDA 메모리 부족)

**Error:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**
1. Reduce batch size in `training/yolo_trainer.py`:
   ```python
   batch_size=8  # Instead of 16
   ```

2. Reduce image size:
   ```python
   imgsz=416  # Instead of 640
   ```

3. Disable cache:
   ```python
   cache=False
   ```

### Issue 2: No GPU Detected (GPU 감지 안 됨)

**Error:**
```
⚠️  No GPU detected! Training will be VERY slow on CPU.
```

**Solutions:**
1. Check NVIDIA driver installation:
   ```bash
   nvidia-smi
   ```

2. Reinstall PyTorch with CUDA:
   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. Verify CUDA installation:
   ```bash
   nvcc --version
   ```

### Issue 3: GPU Overheating (GPU 과열)

**Symptoms:**
- Training suddenly stops
- System becomes unresponsive
- GPU temperature > 85°C

**Solutions:**
1. Improve cooling:
   - Clean GPU fans
   - Improve case airflow
   - Reduce room temperature

2. Reduce GPU load:
   ```python
   batch_size=12  # Reduce from 16
   workers=4      # Reduce from 8
   ```

3. Limit GPU power:
   ```bash
   # Linux only
   sudo nvidia-smi -pl 50  # Limit to 50W
   ```

### Issue 4: Disk Space Error (디스크 공간 오류)

**Error:**
```
OSError: [Errno 28] No space left on device
```

**Solutions:**
1. Check disk space:
   ```bash
   df -h
   ```

2. Clean up space:
   ```bash
   # Remove old training runs
   rm -rf training/runs/old_*
   
   # Remove cached images (if cache=True)
   rm -rf training/dataset/cache/
   ```

3. Use smaller dataset:
   - Select "Quick Test" or "Light" mode

### Issue 5: Network Errors (네트워크 오류)

**Error:**
```
Failed to fetch data from Bybit API
```

**Solutions:**
1. Check internet connection

2. Retry with exponential backoff (automatically handled)

3. Use VPN if API is blocked in your region

---

## 📊 Expected Performance

### RTX 3050 Performance Metrics

#### Training Speed
- **Quick Test (100 images, 5 epochs)**: ~5 minutes
- **Light (500 images, 50 epochs)**: ~30 minutes
- **Full (1000 images, 100 epochs)**: ~1-1.5 hours

#### Batch Processing
- **Batch size**: 16 images
- **Time per epoch**: ~30-45 seconds (1000 images)
- **Images per second**: ~30-40 images/sec

#### Model Performance
- **Model size**: ~6 MB (YOLOv8n)
- **Inference speed**: ~5-10 ms per image
- **Expected mAP50**: 0.60-0.80 (with good labeling)

### Performance Comparison

| GPU Model | VRAM | Batch Size | Time (1000 imgs, 100 epochs) |
|-----------|------|------------|------------------------------|
| RTX 3050  | 4GB  | 16         | ~1-1.5 hours                |
| RTX 3060  | 12GB | 32         | ~45-60 minutes              |
| RTX 4090  | 24GB | 64         | ~20-30 minutes              |
| CPU only  | N/A  | 8          | ~10-15 hours                |

### Optimization Settings

For RTX 3050, we use:
```python
batch_size = 16        # Optimal for 4GB VRAM
imgsz = 640           # Standard YOLOv8 size
amp = True            # Use Tensor Cores
cache = True          # Cache in RAM (requires 16GB)
workers = 8           # Multi-core CPU utilization
patience = 20         # Early stopping
```

---

## 📈 Training Tips

### 1. Monitor GPU Usage
```bash
# Watch GPU stats in real-time
watch -n 1 nvidia-smi
```

### 2. Optimize for Your Hardware
- **Less VRAM**: Reduce `batch_size` to 8-12
- **More VRAM**: Increase `batch_size` to 24-32
- **Slow CPU**: Reduce `workers` to 4
- **Fast CPU**: Increase `workers` to 16

### 3. Improve Model Quality
1. Collect more diverse data
2. Improve labeling quality (use manual labeling)
3. Train for more epochs
4. Use data augmentation (built-in)

### 4. Save Costs
- Use "Quick Test" for development
- Use "Light" for most testing
- Use "Full" only for final production model

---

## 🔍 Monitoring Training

### Training Logs
Check real-time training progress:
```bash
tail -f training/training.log
```

### TensorBoard (Optional)
```bash
# Install tensorboard
pip install tensorboard

# Launch tensorboard
tensorboard --logdir training/runs

# Open browser to http://localhost:6006
```

### Watch Training Plots
Training automatically generates plots:
- `training/runs/chart_patterns/results.png` - Training curves
- `training/runs/chart_patterns/confusion_matrix.png` - Confusion matrix
- `training/runs/chart_patterns/val_batch*.jpg` - Validation predictions

---

## 📝 Next Steps

After training completes:

1. **Test the model**:
   ```bash
   python test_yolo_model.py
   ```

2. **Run backtest**:
   ```bash
   python run_backtest.py
   ```

3. **Start live trading** (paper trading first!):
   ```bash
   python bybit_yolo_bot.py
   ```

---

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs in `training/training.log`
3. Check YOLO documentation: https://docs.ultralytics.com/
4. Open an issue on GitHub

---

## ⚠️ Disclaimer

**Important**: This is a demo training pipeline with rule-based labeling. For production use:

1. Use real pattern detection algorithms or manual labeling
2. Validate model performance thoroughly
3. Test extensively before live trading
4. Start with paper trading
5. Never risk more than you can afford to lose

**The model trained with this pipeline is for educational purposes only.**

---

## 📚 Additional Resources

- **YOLOv8 Documentation**: https://docs.ultralytics.com/
- **PyTorch Documentation**: https://pytorch.org/docs/
- **CUDA Installation Guide**: https://docs.nvidia.com/cuda/
- **Bybit API Documentation**: https://bybit-exchange.github.io/docs/

---

*Last updated: 2025-12-05*
