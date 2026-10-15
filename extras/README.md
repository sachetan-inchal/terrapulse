# extras/ — optional, exploratory bonus tools

These three scripts are contributed by a teammate (originally in
[sachetan-inchal/terrapulse](https://github.com/sachetan-inchal/terrapulse))
and integrated here as **optional add-ons**. They are kept separate from the
core pipeline (`src/`, `app.py`, `PROGRESS.md`'s Tier 0-4) on purpose:

- **They are not required** to install, reproduce, or run anything described
  in the main [README.md](../README.md). `pip install -r requirements.txt`
  (repo root) does not install their dependencies.
- Some of them have hard dependencies the main build prompt's guardrails
  explicitly kept optional/manual for the core pipeline — live cloud
  streaming, `rasterio`/GDAL, and a foundation-model download — so they
  live here, gated behind their own `pip install -r
  extras/requirements-extras.txt`.
- Nothing in the main pipeline imports or depends on anything in this
  directory. Deleting `extras/` entirely would not break Tiers 0-4 or the
  dashboard's Definition of Done.

Install their dependencies (separately from the main venv, if you prefer to
keep the core environment lean):

```bash
pip install -r extras/requirements-extras.txt
```

## `cv_stitcher.py` — classical feature-based tile stitcher

SIFT keypoint extraction, FLANN nearest-neighbor matching, Lowe's ratio
test, and RANSAC homography estimation to stitch two overlapping image
tiles into one mosaic. Self-contained: if no input tiles are given, it
synthesizes two overlapping demo tiles itself, so it runs with **zero
external data or network access**.

```bash
python extras/cv_stitcher.py               # generates its own demo tiles
python extras/cv_stitcher.py left.jpg right.jpg
```

**Verified:** ran end-to-end on the self-generated synthetic tiles — 322
Lowe's-ratio matches, 89.4% RANSAC inlier ratio, mosaic stitched and saved
successfully.

## `stac_mosaic_app.py` — live Sentinel-2 2x2 mosaic streamer

A Streamlit app that streams cloud-free Sentinel-2 L2A tiles directly from
Microsoft's public Planetary Computer STAC API (no account/API key
required for the public catalog), reprojects them into a shared UTM zone,
and stitches a 2x2 mosaic on the fly. This is a genuinely live, network-
dependent tool — consistent with the main build prompt's rule that any
live cloud-imagery pipeline must be a clearly optional/manual script, never
something the main pipeline depends on to run.

```bash
streamlit run extras/stac_mosaic_app.py
```

**Verified:** ran live end-to-end (Swiss Alps preset) — connected to
Planetary Computer, found 4 cloud-free Sentinel-2 tiles, streamed/
reprojected/mosaicked them, and rendered the before/after grid in the UI
with no errors.

## `model_studio_demo.py` — architecture playground (untrained)

A Gradio UI to poke at three segmentation/foundation-model architectures
(U-Net/ResNet18, DeepLabV3+/MobileNetV2, NASA Prithvi-EO/ViT) on a single
uploaded image chip. **Important caveat:** the U-Net and DeepLabV3+
decoders here are randomly initialized — only their encoders carry
ImageNet-pretrained weights. This tool shows what each architecture's
*output shape and activation pattern* looks like, not a trained land-cover
prediction. For an actual trained-and-evaluated classifier, see
[`../src/train_classify.py`](../src/train_classify.py) and its 96.35%
val-accuracy checkpoint (documented in [`../PROGRESS.md`](../PROGRESS.md)).

The Prithvi-EO weights download from Hugging Face on first run (~100M
params); if that model can't be fetched, it falls back to a small
ImageNet ViT so the tool still runs.

```bash
python extras/model_studio_demo.py
```

**Verified:** launched the Gradio server and called all three endpoints
(`/run_unet`, `/run_deeplab`, `/run_prithvi`) via `gradio_client` on a real
EuroSAT sample chip — all three returned valid output images with no
errors. In this environment `transformers` requires PyTorch >= 2.5 (we
pin 2.4.1 for the core pipeline's MPS support), so `AutoModel.from_pretrained`
for Prithvi-EO raised as expected and the script's own fallback kicked in
cleanly, confirmed by the returned log: *"Model Status: Operating via
Vision Transformer (ViT) Foundation Backbone."*
