"""Bi-Temporal Split Comparison Slider Component.

Provides pixel-aligned split slider and side-by-side extent comparison
for authentic multi-temporal satellite observations (Sentinel-2 & Landsat).
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import streamlit as st

from src.data.sentinel_service import geocode_user_location, fetch_real_sentinel2_pair

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def composite_split_image(img_a: Image.Image, img_b: Image.Image, split_ratio: float = 0.5) -> Image.Image:
    """Creates a side-by-side composite split image with a vertical dividing line."""
    # Resize both to same dimensions
    w, h = 800, 600
    a = img_a.resize((w, h)).convert("RGB")
    b = img_b.resize((w, h)).convert("RGB")

    split_x = int(w * split_ratio)

    arr_a = np.array(a)
    arr_b = np.array(b)

    out_arr = np.zeros_like(arr_a)
    out_arr[:, :split_x] = arr_a[:, :split_x]
    out_arr[:, split_x:] = arr_b[:, split_x:]

    out_img = Image.fromarray(out_arr)
    draw = ImageDraw.Draw(out_img)

    # Draw vertical divider line
    line_x = split_x
    draw.line([(line_x - 1, 0), (line_x - 1, h)], fill=(0, 240, 255), width=3)

    # Draw divider handle badge
    cy = h // 2
    r = 16
    draw.ellipse([(line_x - r, cy - r), (line_x + r, cy + r)], fill=(11, 15, 25), outline=(0, 240, 255), width=2)
    draw.text((line_x - 7, cy - 7), "↔", fill=(0, 240, 255))

    return out_img

def render_tab_split_slider():
    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">↔️ Bi-Temporal Observation Comparison Studio</div>
            <div>
                <span class="tech-badge badge-cyan">Split-View Slider</span>
                <span class="tech-badge badge-purple">Pixel-Aligned Comparison</span>
                <span class="tech-badge badge-emerald">Multi-Decadal Extent</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Compare multi-decadal satellite observations with an interactive horizontal split slider.
        Inspect ground-level urban expansion, forest depletion, infrastructure construction, and water boundary retreat.
        """
    )

    # 1. Observation Source Selection
    col_src, col_loc = st.columns([1, 2])
    with col_src:
        src_mode = st.radio(
            "Observation Imagery Source",
            [
                "Use Live Sentinel-2 Stream (From EarthWatch Tab)",
                "Local Tile Benchmark (Left vs Right)"
            ],
            key="split_slider_src_mode"
        )

    img_before, img_after = None, None
    label_a = "Historical Baseline (Pre-State)"
    label_b = "Recent Observation (Post-State)"

    if src_mode == "Use Live Sentinel-2 Stream (From EarthWatch Tab)":
        if "ew_pair_data" in st.session_state and st.session_state["ew_pair_data"][0]:
            (h_tuple, r_tuple) = st.session_state["ew_pair_data"]
            img_before, meta_a = h_tuple
            img_after, meta_b = r_tuple
            label_a = f"Epoch A ({meta_a['date']}) • {meta_a['id'][:20]}..."
            label_b = f"Epoch B ({meta_b['date']}) • {meta_b['id'][:20]}..."
            with col_loc:
                st.success(f"Loaded live Sentinel-2 observation pair for {st.session_state.get('ew_location_query', 'Study Region')}.")
        else:
            with col_loc:
                st.info("No live stream loaded yet. Type a location below or in the EarthWatch tab:")
                q = st.text_input("Enter City or Region:", value="Bengaluru, Karnataka, India", key="split_quick_loc")
                if st.button("🛰️ Stream Sentinel-2 Observation Pair", key="btn_split_stream"):
                    with st.spinner("Fetching Sentinel-2 observation pair..."):
                        loc = geocode_user_location(q)
                        pair = fetch_real_sentinel2_pair(loc["bbox"], max_cloud=20.0)
                        if pair[0] and pair[1]:
                            st.session_state["ew_pair_data"] = pair
                            st.session_state["ew_location_query"] = q
                            st.rerun()

    if img_before is None or img_after is None:
        p_left = ROOT_DIR / "tile_left.jpg"
        p_right = ROOT_DIR / "tile_right.jpg"
        if p_left.exists() and p_right.exists():
            img_before = Image.open(p_left).convert("RGB")
            img_after = Image.open(p_right).convert("RGB")
            label_a = "Benchmark Spatial Tile Left (10m Optical)"
            label_b = "Benchmark Spatial Tile Right (10m Optical)"

    if img_before is None or img_after is None:
        st.warning("Please load or stream satellite imagery to inspect the split comparison.")
        return

    # 2. Interactive Split Slider Control
    st.markdown("### 🎚️ Interactive Split-View Swipe Control")
    split_pct = st.slider(
        "Swipe Boundary Position (% from left)",
        min_value=0,
        max_value=100,
        value=50,
        step=1,
        help="Drag to reveal transition between pre-event and post-event satellite observations."
    )

    col_meta_a, col_meta_b = st.columns(2)
    with col_meta_a:
        st.markdown(f"<span style='color: #00f0ff; font-weight: bold;'>PRE-STATE: {label_a}</span>", unsafe_allow_html=True)
    with col_meta_b:
        st.markdown(f"<span style='color: #ff3366; font-weight: bold; float: right;'>POST-STATE: {label_b}</span>", unsafe_allow_html=True)

    # 3. Composite Image Display
    split_image = composite_split_image(img_before, img_after, split_ratio=split_pct / 100.0)
    st.image(split_image, use_container_width=True)

    # 4. Synchronized Side-by-Side Dual Extents
    with st.expander("🔍 View Side-by-Side Synchronized Raw Observations"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{label_a}**")
            st.image(img_before, use_container_width=True)
        with c2:
            st.markdown(f"**{label_b}**")
            st.image(img_after, use_container_width=True)
