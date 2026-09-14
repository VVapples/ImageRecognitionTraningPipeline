# YOLO11s Sim-to-Real Training Pipeline

this README is mostle abot what is in /train_space.

This repository contains an automated, two-stage training script (`train_pipeline.py`) designed to bridge the domain gap between highly-controlled synthetic data and noisy, real-world camera sensor data using YOLO11s.

**RUN THIS ENTIRE FOLDER INSIDE A SSD AND NOT HDD**

## 🚀 Approach: Mitigating Catastrophic Forgetting

1. **Phase 1 (Simulation Training):** Trains the model heavily on generated/synthetic images to learn the fundamental geometry, shape, and features of the objects. Uses high data augmentation to mimic environmental variations.
2. **Phase 2 (Real-World Fine-Tuning):** Uses a carefully constrained learning environment (lower learning rate, smooth cosine decay, and backbone freezing) along with a **"mix-back" strategy** (combining the tiny real dataset with a subset of synthetic data) to adapt the model to the target camera's lens and color profile without un-learning the synthetic geometry.

---

## 📁 Dataset Arrangement

You must physically arrange your dataset into two distinct sets using the standard YOLO directory structure. 

### 1. Directory Structure


```

```text
README.md generated successfully.

```text
datasets/
├── phase1_sim/
│   ├── images/
│   │   ├── train/  # ~8100 generated objects + 2000 generated backgrounds
│   │   └── val/    # ~929 generated objects
│   └── labels/
│       ├── train/  # YOLO format .txt files (empty .txt for backgrounds)
│       └── val/
│
├── phase2_mixed/
│   ├── images/
│   │   ├── train/  # 224 real images + ~300 synthetic "mix-back" images + ~50 backgrounds
│   │   └── val/    # ONLY the 20 real images from the actual deployment camera
│   └── labels/
│       ├── train/
│       └── val/

```

*Note: For images containing only background (no objects), you must provide a `.txt` label file with the exact same name as the image, but leave the text file completely empty. This teaches the model to suppress false positives.*

### 2. YAML Configuration Files

Create two YAML files (e.g., in your project root) pointing to these directories.

**`phase1_sim_dataset.yaml`**

```yaml
path: /absolute/or/relative/path/to/datasets/phase1_sim
train: images/train
val: images/val

nc: 1  # Replace with your number of classes
names: ['your_object_class_name']

```

**`phase2_mixed_dataset.yaml`**

```yaml
path: /absolute/or/relative/path/to/datasets/phase2_mixed
train: images/train
val: images/val

nc: 1  # Replace with your number of classes
names: ['your_object_class_name']

```

---

## ⚙️ Installation & Usage

### Prerequisites

Make sure you have Python 3.8+ installed, then install the Ultralytics package:

```bash
pip install ultralytics

```

### Running the Pipeline

1. Open `train_pipeline.py`.
2. Update the directory configuration block at the top of the script to point to the YAML files you just created:
```python
DATASET_PHASE_1 = "phase1_sim_dataset.yaml"
DATASET_PHASE_2 = "phase2_mixed_dataset.yaml"

```


3. Run the script:
```bash
python train_pipeline.py

```



### Customizing Parameters

Inside `train_pipeline.py`, you can modify hyperparameters directly in the `model.train()` calls. Key variables you may need to tweak for your specific hardware:

* **`batch`**: Set to `16`, `32`, or `-1` (AutoBatch) depending on your GPU VRAM (e.g., RTX 2070 Super).
* **`epochs`** & **`patience`**: Controls early stopping.
* **`freeze`** (in Phase 2): Default is `10`. Increase if the model still suffers from catastrophic forgetting, decrease if it struggles to learn the new camera profile at all.

---

## 📊 Outputs & Checkpoints

The script handles the transition between phases automatically. It takes the "best" weights from Phase 1 and sets them as the starting point for Phase 2.

All training metrics, confusion matrices, F1 curves, and weights are saved in your defined output directory (default is `runs/yolo_training/`).

* Phase 1 weights: `runs/yolo_training/phase1_sim/weights/best.pt`
* **Final Deployable Model:** `runs/yolo_training/phase2_real/weights/best.pt`

## Datastructe/Parameters

- Step 1
  - Imageset
    - Train : 8100 gen
    - Train : 2000 gen bg
    - Val   : 929 gen
  - Parameters
    - Model      : yolo11s.pt
    - Epochs     : 150
    - patience   : 20
    - Batch size : -1
    - Lr0        : 0.01
    - mosaic     : 1.0
    - mizup      : 0.1
    - hsv_h      : 0.015
    - hsv_s      : 0.7
    - hsv_v      : 0.4
- Step 2
  - Imageset
    - Train : 189   diff_cam
    - Train : 35    real_cam
    - Train : 275   gen
    - Train : 50    gen bg
    - Val   : 20    real_cam
  - Parameters
    - Model         : (best.pt from Step 1)
    - Epochs        : 50
    - warmup_epochs : 5
    - lr0           : 0.0005
    - freeze        : 10
    - mosaic        : 0.5
    - mixup         : 0.0
    - cos_lr        : True
