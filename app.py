"""EarthWatch dashboard: land-cover classification + change detection.

Run: streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from src.data.eurosat_dataset import IMAGENET_MEAN, IMAGENET_STD
from src.models.change_net import SiameseUNet
from src.models.classifier import build_classifier

ROOT = Path(__file__).resolve().parent
CKPT_DIR = ROOT / "checkpoints"
CLASSIFIER_CKPT = CKPT_DIR / "classifier_resnet18.pt"
CHANGE_CKPT = CKPT_DIR / "change_unet.pt"
DEMO_DIR = ROOT / "data" / "levircd" / "demo"

TILE = 64  # EuroSAT tile size the classifier was trained on
CHANGE_INPUT_SIZE = 256  # Siamese U-Net was trained at this resolution


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


@st.cache_resource
def load_classifier():
    device = get_device()
    if not CLASSIFIER_CKPT.exists():
        return None, None, device
    ckpt = torch.load(CLASSIFIER_CKPT, map_location=device)
    model = build_classifier(num_classes=len(ckpt["classes"]))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, ckpt["classes"], device


@st.cache_resource
def load_change_model():
    device = get_device()
    if not CHANGE_CKPT.exists():
        return None, device
    ckpt = torch.load(CHANGE_CKPT, map_location=device)
    model = SiameseUNet(base=32)
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, device


CLASSIFY_TF = transforms.Compose([
    transforms.Resize((TILE, TILE)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def classify_whole_image(model, classes, device, img: Image.Image):
    x = CLASSIFY_TF(img).unsqueeze(0).to(device)
    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)[0].cpu().numpy()
    top = probs.argmax()
    return classes[top], float(probs[top]), probs


def classify_tiles(model, classes, device, img: Image.Image, grid: int = 4):
    """Split the image into a grid of tiles, classify each, return class
    counts (used for the class-area bar chart) and a color-coded grid."""
    w, h = img.size
    tile_w, tile_h = w // grid, h // grid
    tf = transforms.Compose([
        transforms.Resize((TILE, TILE)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    batch = []
    for gy in range(grid):
        for gx in range(grid):
            crop = img.crop((gx * tile_w, gy * tile_h, (gx + 1) * tile_w, (gy + 1) * tile_h))
            batch.append(tf(crop))
    batch = torch.stack(batch).to(device)
    with torch.no_grad():
        preds = model(batch).argmax(1).cpu().numpy()
    counts = np.bincount(preds, minlength=len(classes))
    return counts


def run_change_detection(model, device, img_a: Image.Image, img_b: Image.Image):
    size = (CHANGE_INPUT_SIZE, CHANGE_INPUT_SIZE)
    a = img_a.resize(size)
    b = img_b.resize(size)
    tf = transforms.ToTensor()
    ta = tf(a).unsqueeze(0).to(device)
    tb = tf(b).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(ta, tb)
        prob = torch.sigmoid(logits)[0, 0].cpu().numpy()
    mask = (prob > 0.5).astype(np.uint8) * 255
    return mask, prob, a, b


def run_change_baseline(img_a: Image.Image, img_b: Image.Image, threshold=170):
    size = (CHANGE_INPUT_SIZE, CHANGE_INPUT_SIZE)
    a = np.asarray(img_a.resize(size).convert("RGB"), dtype=np.float32)
    b = np.asarray(img_b.resize(size).convert("RGB"), dtype=np.float32)
    diff = np.sqrt(((a - b) ** 2).sum(axis=2))
    mask = (diff > threshold).astype(np.uint8) * 255
    return mask, diff, Image.fromarray(a.astype(np.uint8)), Image.fromarray(b.astype(np.uint8))


def overlay_mask(base_img: Image.Image, mask: np.ndarray, color=(255, 0, 0), alpha=0.5):
    base = base_img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay_arr = np.array(overlay)
    m = mask > 127
    overlay_arr[m] = (*color, int(255 * alpha))
    overlay = Image.fromarray(overlay_arr)
    return Image.alpha_composite(base, overlay)


st.set_page_config(page_title="EarthWatch", layout="wide")
st.title("🛰️ EarthWatch — Land-Cover & Change Detection")
st.caption(
    "CCVR Internship prototype: EuroSAT land-cover classification (ResNet18) "
    "+ LEVIR-CD change detection (Siamese U-Net). Trained on CPU/MPS in-lab, "
    "no live satellite fetch — bundled demo imagery works fully offline."
)

classifier, classes, device = load_classifier()
change_model, _ = load_change_model()

if classifier is None:
    st.error(f"No classifier checkpoint found at {CLASSIFIER_CKPT}. Run "
             "`python -m src.train_classify` first.")
    st.stop()

st.sidebar.header("Input")
source = st.sidebar.radio("Image source", ["Bundled demo pair", "Upload my own"])

if source == "Bundled demo pair":
    if not DEMO_DIR.exists():
        st.error(f"Demo pair not found at {DEMO_DIR}. Run "
                 "`python -m src.data.prepare_levircd` first.")
        st.stop()
    img_before = Image.open(DEMO_DIR / "A.png").convert("RGB")
    img_after = Image.open(DEMO_DIR / "B.png").convert("RGB")
    st.sidebar.success("Using bundled LEVIR-CD demo pair (works fully offline).")
else:
    up_before = st.sidebar.file_uploader("Before image", type=["png", "jpg", "jpeg"])
    up_after = st.sidebar.file_uploader("After image", type=["png", "jpg", "jpeg"])
    if not (up_before and up_after):
        st.info("Upload both a 'before' and an 'after' image in the sidebar, "
                "or switch to the bundled demo pair.")
        st.stop()
    img_before = Image.open(up_before).convert("RGB")
    img_after = Image.open(up_after).convert("RGB")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Before")
    st.image(img_before, use_container_width=True)
with col2:
    st.subheader("After")
    st.image(img_after, use_container_width=True)

st.divider()
st.header("1. Land-cover classification")

grid = st.slider("Tile grid (N×N crops per image, for the area chart)", 2, 8, 4)

col1, col2 = st.columns(2)
with col1:
    cls, conf, _ = classify_whole_image(classifier, classes, device, img_before)
    st.metric("Before — predicted class", cls, f"{conf:.1%} confidence")
    counts_before = classify_tiles(classifier, classes, device, img_before, grid)
with col2:
    cls, conf, _ = classify_whole_image(classifier, classes, device, img_after)
    st.metric("After — predicted class", cls, f"{conf:.1%} confidence")
    counts_after = classify_tiles(classifier, classes, device, img_after, grid)

df = pd.DataFrame({
    "class": classes * 2,
    "area %": list(counts_before / counts_before.sum() * 100) + list(counts_after / counts_after.sum() * 100),
    "image": ["Before"] * len(classes) + ["After"] * len(classes),
})
st.bar_chart(df.pivot(index="class", columns="image", values="area %"))

st.divider()
st.header("2. Change detection")

if change_model is not None:
    mask, prob, a_resized, b_resized = run_change_detection(change_model, device, img_before, img_after)
    method = "Siamese U-Net (trained)"
else:
    st.warning("No trained change-detection checkpoint found; falling back to the "
               "pixel-difference baseline. Run `python -m src.train_change --mode unet` "
               "to train the U-Net.")
    mask, prob, a_resized, b_resized = run_change_baseline(img_before, img_after)
    method = "Pixel-difference baseline (untrained)"

changed_pct = (mask > 127).mean() * 100
st.caption(f"Method: {method}")
st.metric("Changed area", f"{changed_pct:.2f}%")

col1, col2, col3 = st.columns(3)
with col1:
    st.image(a_resized, caption="Before (resized)", use_container_width=True)
with col2:
    st.image(b_resized, caption="After (resized)", use_container_width=True)
with col3:
    st.image(overlay_mask(b_resized, mask), caption="Change mask overlay (red)", use_container_width=True)

st.caption(
    "Prototype scope: classification and change detection are trained on public, "
    "unattended-downloadable data (EuroSAT, LEVIR-CD). No live Sentinel/GEE fetch, "
    "no SAR fusion, no temporal forecasting — see PROGRESS.md for what is out of "
    "scope for this build and why."
)
