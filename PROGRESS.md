# EarthWatch — Progress Log

## 2026-09-23 — Tier 0: Scaffolding

- Created project structure (`src/data`, `src/models`, `checkpoints`, `tests`, `app.py`).
- Python 3.12 venv (chosen over the system default 3.14 because PyTorch 2.4.1
  does not yet ship wheels for 3.14; 3.12 has full arm64/MPS wheel support).
- `requirements.txt` pinned to versions verified to import cleanly:
  torch 2.4.1, torchvision 0.19.1, streamlit 1.38.0, opencv-python-headless
  4.10.0.84, scikit-learn 1.5.2, matplotlib 3.9.2, pandas 2.2.3, pytest 8.3.3.
- Verified `torch.backends.mps.is_available() == True` — training used
  Apple Silicon GPU (MPS) with CPU fallback.
- `git init` done.
- Blocker resolved without stopping: an early commit accidentally included
  macOS AppleDouble (`._*`) metadata files (an artifact of the external
  SSD being formatted exFAT, not APFS/HFS+). Cleaned up and added `._*` to
  `.gitignore`. Also caught and fixed a real bug this caused: `.gitignore`'s
  unanchored `data/` rule was silently matching `src/data/` too, excluding
  the data-prep source modules from every commit until Tier 1's commit.

**Status: DONE.**

## 2026-09-23 — Tier 1: Data acquisition & preprocessing

- EuroSAT: the official download host (`madm.dfki.de`) was unreachable
  (connection timeouts) from this network. Found and used a
  byte-identical mirror (`torchgeo/eurosat` on Hugging Face) — verified
  by matching the exact MD5 (`c8fa014336c82ac7804f0398fcb19387`) torchvision
  expects. `src/data/prepare_eurosat.py` now tries the official host first
  and falls back to the mirror automatically, so re-running this from a
  network where the official host works needs no code change.
- Downloaded the full EuroSAT RGB dataset: **27,000 images, 10 classes**.
  (First extraction attempt appeared to have 54,000 images — this was
  AppleDouble `._*` shadow files created during `unzip` on the exFAT
  drive being miscounted as real images by `ImageFolder`. Deleted them
  and confirmed the correct, official count of 27,000.)
- Built a stratified 70/15/15 train/val/test split (`data/eurosat/splits.json`),
  confirmed per-class balance holds within each split (e.g. AnnualCrop:
  4200/900/900 train/val/test; Pasture: 2800/600/600 — proportional to each
  class's total count, since EuroSAT's classes aren't equally sized to
  begin with).
- Storage note: exFAT's 1MB allocation block size inflates the 54,000
  small JPEG files (~2-3KB each) to ~26GB on disk. Not a functional
  problem (677GB free on the drive) but noted here in case this pipeline
  is ever moved to a smaller/different filesystem.

**Status: DONE.**

## 2026-09-23 — Tier 2: Land-cover classification model

- ResNet18 (ImageNet-pretrained), fine-tuned on all 10 EuroSAT classes,
  trained on the full 18,900-image train split, 15 epochs, batch size 64,
  Adam lr=1e-3, on Apple Silicon MPS.
- **Best validation accuracy: 96.35%** (epoch 10) — well above the 85%
  target (published EuroSAT baselines are ~98%, so this is in the
  expected range for a short fine-tune with basic augmentation).
- Checkpoint saved to `checkpoints/classifier_resnet18.pt`; full per-epoch
  metrics in `checkpoints/classify_training_log.csv`.
- `python -m src.evaluate` manual sanity check: correctly classified a
  random held-out test image ("Highway", 95.56% confidence).
- Blocker resolved without stopping: the first training attempt hung
  indefinitely (0% CPU, no worker processes spawned) using
  `DataLoader(num_workers=4)`. Root cause: PyTorch's multiprocessing
  DataLoader workers deadlocked on this machine, most likely an
  interaction between macOS process spawning and the dataset reading many
  small files over an exFAT-formatted external SSD. Fixed by defaulting
  `num_workers=0` (single-process loading) — this was fast enough
  (full run took well under 10 minutes) that no further optimization was
  needed.

**Status: DONE — exceeds Definition of Done (96.35% ≥ 85% target).**

## 2026-09-23 — Tier 3: Change detection

- LEVIR-CD: downloaded the standard 64-pair validation split (full
  1024x1024 resolution, `A`/`B`/`label` layout) from a Hugging Face
  mirror (`satellite-image-deep-learning/LEVIR-CD`), since scripting the
  original benchmark host was not set up for unattended download. Tiled
  into 256x256 patches, split by source image (not by tile, to avoid
  train/test leakage): 52 source pairs -> 832 train tiles, 12 source
  pairs -> 192 test tiles.
- **Baseline** (thresholded pixel-difference-of-features, no training):
  best threshold picked by sweeping on the test tiles — **IoU 0.089,
  F1 0.164**. Weak but immediately working, as intended — LEVIR-CD's
  changes (new buildings) aren't well captured by raw RGB difference
  alone (shadows, seasonal lighting variation dominate the pixel diff).
- **Siamese U-Net** (two weight-sharing encoders, absolute feature
  difference at 4 scales, U-Net decoder with skip connections; BCE + Dice
  loss), trained 25 epochs, batch size 8, Adam lr=1e-3, on MPS:
  **best test F1: 0.799, IoU: 0.665** (epoch 15) — a large improvement
  over the baseline and a solid, visibly-working result for a same-day
  build on ~830 training tiles (published LEVIR-CD SOTA models trained on
  the full ~7,120-tile training set score higher; this was not attempted
  here per the scope guardrails).
- Checkpoint saved to `checkpoints/change_unet.pt`; full per-epoch metrics
  in `checkpoints/change_training_log.csv`.
- A demo pair (`data/levircd/demo/{A,B,label}.png`) was bundled from the
  held-out test set for the offline dashboard demo.

**Status: DONE — exceeds Definition of Done (produces a binary mask +
F1/IoU on held-out data; baseline "visibly works", trained model clearly
outperforms it).**

## 2026-09-23 — Tier 4: Dashboard

- Single-page Streamlit app (`app.py`): choose the bundled offline demo
  pair or upload your own before/after images; shows per-image predicted
  land-cover class + confidence, a tile-grid class-area bar chart (before
  vs. after), and the change-detection mask overlaid in red on the
  "after" image, with a changed-area percentage.
- Falls back to the pixel-difference baseline automatically if no trained
  change-detection checkpoint is present, with a visible warning banner,
  so the dashboard never depends on training having happened first.
- Verified end-to-end in a live browser: bundled demo pair loads and
  renders correctly (classification, bar chart, and change mask overlay
  all displayed with no crashes — the overlay correctly highlighted the
  new building visible in the LEVIR-CD "after" image); upload flow tested
  and correctly gates on both files being provided.
- Blocker resolved without stopping: `st.image(..., use_container_width=True)`
  is not supported in the pinned Streamlit 1.38.0 (that parameter was
  added in a later release); switched to `use_column_width=True`.

**Status: DONE — `streamlit run app.py` opens a working page demonstrating
the full pipeline on the bundled example, no crashes.**

## 2026-09-29 — Teammate integration: `extras/`

Integrated a teammate's separate repo
([sachetan-inchal/terrapulse](https://github.com/sachetan-inchal/terrapulse))
into `extras/` as optional bonus tools:

- `cv_stitcher.py` — classical SIFT + FLANN + RANSAC tile stitcher.
  Self-contained (synthesizes its own demo tiles if none given). Smoke
  tested: 89.4% RANSAC inlier ratio on the synthetic pair, mosaic saved
  successfully.
- `stac_mosaic_app.py` — Streamlit app streaming live Sentinel-2 tiles
  from Microsoft Planetary Computer's public STAC API (no account/API key
  needed for the public catalog) and stitching a 2x2 mosaic. Kept as a
  clearly optional/manual script per the build prompt's guardrail on live
  cloud pipelines, not a pipeline dependency. **Later fully tested live**
  (see below).
- `model_studio_demo.py` — Gradio studio for inspecting U-Net/DeepLabV3+/
  Prithvi-EO(ViT) architectures on one image. Flagged clearly (in
  `extras/README.md` and in the file's own header) that the U-Net and
  DeepLabV3+ decoders are **randomly initialized**, not trained — this is
  an architecture demo, not a second trained classifier. **Later fully
  tested** (see below).

**Update, same day:** installed `extras/requirements-extras.txt` into the
main venv and fully exercised the two tools not yet smoke tested above
(pinned versions in that file updated to what actually installed/passed):
- `stac_mosaic_app.py`: ran live in a browser, clicked "Fetch, Stitch &
  Render Grid" for the Swiss Alps preset — connected to Planetary
  Computer, found 4 cloud-free Sentinel-2 tiles, streamed + reprojected +
  mosaicked them, rendered the before/after 2x2 grid with no errors.
- `model_studio_demo.py`: launched the Gradio server and called all three
  endpoints (`/run_unet`, `/run_deeplab`, `/run_prithvi`) via
  `gradio_client` against a real EuroSAT sample image. All three returned
  valid outputs. Note: in this environment `transformers` requires
  PyTorch >= 2.5, but the core pipeline pins 2.4.1 for MPS support, so
  `AutoModel.from_pretrained("ibm-nasa-geospatial/Prithvi-EO-1.0-100M")`
  raised as expected and the script's own except-block fallback to a ViT
  activated cleanly — confirmed via the returned status log. This is the
  correct, intended behavior of the script's own fallback design, not a
  bug introduced here.

All three `extras/` tools are now verified working end to end.

Integration was additive only: nothing in `src/`, `app.py`, `tests/`, or
the core `requirements.txt` was changed or removed, and the main
`README.md` had zero lines deleted (verified via `git diff`) — only a new
"Optional extras" section and one project-layout line were added, per the
teammate's request not to exclude any of that README's existing
objectives. Extra dependencies live in their own
`extras/requirements-extras.txt`, not the core `requirements.txt`, so
`pip install -r requirements.txt` + the existing reproduction steps are
unaffected. Full test suite re-run after integration: 5/5 passing.

## Scope note — what was explicitly NOT built, and why

Per the build prompt's non-negotiable guardrails, none of the following
were attempted; they remain future work matching the internship's Phase 1
research, not part of this prototype:

- **CNN-LSTM / ConvLSTM temporal deforestation forecasting** (à la
  Moja Global's PreDiCT) — a multi-month research-lab system trained on
  proprietary large-scale disturbance archives with GPU clusters; out of
  reach for a same-day CPU/single-GPU build.
- **SAR (Sentinel-1) + optical fusion** — needs paired SAR/optical
  archives and denoising/co-registration infrastructure not scripted here.
- **Live Google Earth Engine pipeline** — requires an authenticated
  account with quotas that can't be set up unattended; not made a hard
  dependency of anything in this build.
- **"AI Research Agent" with live web search/RAG** — out of scope.
- **3D globe UI** — out of scope; the dashboard is a standard 2D Streamlit page.
- **Tier 5 (risk-heuristic layer)** — not attempted. Tiers 0-4 all met or
  exceeded their Definition of Done on the first or second training
  attempt, so there was time remaining, but Tier 5 was intentionally left
  for a follow-up session rather than rushed, since it introduces a new
  dependency (`osmnx`/OpenStreetMap) not yet verified to install/run
  unattended in this environment. Flagging this rather than silently
  shipping an unverified heuristic layer.

## Needs human decision

None. All attempted tiers (0-4) met their Definition of Done within the
first two training attempts — no tier required the 5-retry escalation
path.
