# EarthWatch — Progress Log

## 2026-09-23 — Tier 0: Scaffolding

- Created project structure (`src/data`, `src/models`, `checkpoints`, `tests`, `app.py`).
- Python 3.12 venv (chosen over the system default 3.14 because PyTorch 2.4.1
  does not yet ship wheels for 3.14; 3.12 has full arm64/MPS wheel support).
- `requirements.txt` pinned to versions verified to import cleanly:
  torch 2.4.1, torchvision 0.19.1, streamlit 1.38.0, opencv-python-headless
  4.10.0.84, scikit-learn 1.5.2, matplotlib 3.9.2, pandas 2.2.3.
- Verified `torch.backends.mps.is_available() == True` — training will use
  Apple Silicon GPU (MPS) with CPU fallback.
- `git init` done.

**Status: DONE.** Moving to Tier 1 (data acquisition).
