# EarthWatch — Satellite Land-Cover & Change Detection Prototype

CCVR Internship — Team 37 — Phase 2 build.

An end-to-end computer-vision pipeline that:
1. Classifies land cover from Sentinel-2-derived imagery (EuroSAT),
2. Detects change between two time points of the same location (LEVIR-CD),
3. Serves both through a local Streamlit dashboard.

See [PROGRESS.md](PROGRESS.md) for what was actually built, achieved metrics,
and what was explicitly scoped out (and why).

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12 is required (not the system default on newer machines) because
PyTorch does not yet ship wheels for the newest Python releases. On Apple
Silicon, PyTorch will automatically use the MPS GPU backend if available.

## Reproducing the pipeline

```bash
# 1. Download EuroSAT (auto-downloads from the official host, falls back
#    to a byte-identical Hugging Face mirror if that host is unreachable)
#    and build a stratified 70/15/15 train/val/test split.
python -m src.data.prepare_eurosat

# 2. Train the land-cover classifier (ResNet18, ImageNet-pretrained,
#    fine-tuned on EuroSAT's 10 classes).
python -m src.train_classify --epochs 15 --batch-size 64

# 3. Sanity-check a single prediction.
python -m src.evaluate

# 4. LEVIR-CD change detection. The val split (64 full-resolution 1024x1024
#    pairs) is downloaded manually from a Hugging Face mirror of the
#    official dataset (see src/data/prepare_levircd.py docstring for the
#    URL) into data/levircd/val_extracted/{A,B,label}, then tiled:
python -m src.data.prepare_levircd

# baseline: thresholded pixel-difference, no training required
python -m src.train_change --mode baseline

# trained: Siamese U-Net
python -m src.train_change --mode unet --epochs 25 --batch-size 8

# 5. Launch the dashboard (works fully offline on a bundled demo pair).
streamlit run app.py
```

## Project layout

```
earthwatch/
  data/               # downloaded datasets (gitignored)
  src/
    data/             # dataset download + preprocessing scripts
    models/           # model definitions (ResNet18 classifier, Siamese U-Net)
    train_classify.py
    train_change.py
    evaluate.py
  checkpoints/         # saved model weights (gitignored; metrics logged as CSV)
  app.py               # Streamlit dashboard
  tests/               # unit tests for data shapes, model forward pass
  PROGRESS.md
  README.md
```

## Tech stack

PyTorch + torchvision, OpenCV, NumPy, scikit-learn, Streamlit, matplotlib.
CPU/MPS only — no cloud training clusters required.
