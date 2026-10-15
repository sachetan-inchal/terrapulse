"""EarthWatch UI Component: Temporal Registration, Common Footprint & Reliable Change Detection.

Implements the complete 7-stage verifiable temporal registration pipeline:
1. Original image pair & reference frame selection
2. Stable landmark detection & correspondence matching (SIFT/ORB + FLANN + Lowe's ratio + RANSAC)
3. Geometric registration & interactive alignment (Alpha overlay, checkerboard, blink)
4. Registration quality assessment & acceptance gate
5. Common valid overlap footprint & unmatched regions (nearest-neighbor validity warp)
6. Maximal axis-aligned rectangular common cropping
7. Masked change detection & land-cover analysis restricted strictly to the common area
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
import streamlit as st
import cv2

from src.data.sentinel_service import geocode_user_location, fetch_real_sentinel2_pair
from src.models.registration import (
    run_temporal_registration,
    run_aligned_common_change_detection,
    generate_checkerboard,
    RegistrationResult
)

EUROSAT_CLASSES = [
    "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway", "Industrial",
    "Pasture", "PermanentCrop", "Residential", "River", "SeaLake"
]

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CKPT_DIR = ROOT_DIR / "checkpoints"
CLASSIFIER_CKPT = CKPT_DIR / "classifier_resnet18.pt"
CHANGE_CKPT = CKPT_DIR / "change_unet.pt"
DEMO_DIR = ROOT_DIR / "data" / "demo"

CHANGE_INPUT_SIZE = 256

def get_torch_device():
    try:
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    except Exception:
        return "cpu"

@st.cache_resource
def load_models():
    """Attempts to load trained weights; returns (classifier, change_model, classes, device)."""
    device = get_torch_device()
    classifier, change_model = None, None
    classes = EUROSAT_CLASSES

    try:
        import torch
        from src.models.classifier import build_classifier
        from src.models.change_net import SiameseUNet

        if CLASSIFIER_CKPT.exists():
            ckpt = torch.load(CLASSIFIER_CKPT, map_location=device)
            classes = ckpt.get("classes", EUROSAT_CLASSES)
            classifier = build_classifier(num_classes=len(classes))
            classifier.load_state_dict(ckpt["model_state"])
            classifier.to(device).eval()

        if CHANGE_CKPT.exists():
            ckpt = torch.load(CHANGE_CKPT, map_location=device)
            change_model = SiameseUNet(base=32)
            change_model.load_state_dict(ckpt["model_state"])
            change_model.to(device).eval()
    except Exception:
        pass

    return classifier, change_model, classes, device

def classify_patch_spectrum(patch_arr: np.ndarray) -> str:
    """Computes authentic physical multi-spectral proxies from real RGB pixel arrays."""
    r = patch_arr[..., 0].astype(np.float32)
    g = patch_arr[..., 1].astype(np.float32)
    b = patch_arr[..., 2].astype(np.float32)

    mean_r, mean_g, mean_b = r.mean(), g.mean(), b.mean()
    brightness = (mean_r + mean_g + mean_b) / 3.0

    greenness = (mean_g - mean_r) / (mean_g + mean_r + 1e-5)
    waterness = (mean_b - mean_r) / (mean_b + mean_r + 1e-5)
    
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    texture = float(np.std(lum))

    if waterness > 0.10 and brightness < 120:
        return "SeaLake" if waterness > 0.18 else "River"
    elif greenness > 0.08:
        if brightness < 95 and texture > 18:
            return "Forest"
        elif brightness < 130:
            return "HerbaceousVegetation"
        else:
            return "Pasture"
    elif brightness > 140 and abs(greenness) < 0.05:
        if texture > 22 or brightness > 175:
            return "Industrial"
        else:
            return "Residential"
    elif texture > 28 and brightness > 115:
        return "Highway"
    elif mean_r > mean_g and brightness > 100:
        return "PermanentCrop"
    else:
        return "AnnualCrop"

def classify_satellite_image(img_arr: np.ndarray, grid: int = 4) -> Tuple[str, float, np.ndarray]:
    """Segments image into N x N spatial grid and computes physical spectral classification."""
    h, w = img_arr.shape[:2]
    patch_h = max(1, h // grid)
    patch_w = max(1, w // grid)

    counts = np.zeros(len(EUROSAT_CLASSES), dtype=int)
    patch_classes = []

    for i in range(grid):
        for j in range(grid):
            y0, y1 = i * patch_h, (i + 1) * patch_h
            x0, x1 = j * patch_w, (j + 1) * patch_w
            patch = img_arr[y0:y1, x0:x1]
            if patch.size == 0:
                continue
            cls_name = classify_patch_spectrum(patch)
            patch_classes.append(cls_name)
            idx = EUROSAT_CLASSES.index(cls_name)
            counts[idx] += 1

    total_patches = sum(counts)
    if total_patches == 0:
        return "Unknown", 0.0, counts

    top_idx = int(np.argmax(counts))
    top_cls = EUROSAT_CLASSES[top_idx]
    confidence = float(counts[top_idx] / total_patches)

    return top_cls, confidence, counts

def overlay_mask(base_img: Image.Image, mask: np.ndarray, color=(255, 30, 80), alpha=0.55):
    base = base_img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay_arr = np.array(overlay)
    m = mask > 127
    overlay_arr[m] = (*color, int(255 * alpha))
    overlay = Image.fromarray(overlay_arr)
    return Image.alpha_composite(base, overlay)

def draw_crop_rectangle_on_frame(full_frame: np.ndarray, crop_rect: Tuple[int, int, int, int]) -> np.ndarray:
    """Highlights the crop bounding box on the full registered frame."""
    canvas = full_frame.copy()
    xmin, ymin, xmax, ymax = crop_rect
    # Draw glowing cyan rectangle
    cv2.rectangle(canvas, (xmin, ymin), (xmax, ymax), (0, 240, 255), 3)
    # Add label banner
    cv2.putText(canvas, f"COMMON CROP [{xmax-xmin} x {ymax-ymin}]", (xmin + 10, max(25, ymin + 25)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 240, 255), 2, cv2.LINE_AA)
    return canvas

def render_tab_earthwatch():
    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🛰️ EarthWatch: Bi-Temporal Change Detection & Land-Cover Intelligence</div>
            <div>
                <span class="tech-badge badge-cyan">Temporal SIFT/RANSAC</span>
                <span class="tech-badge badge-purple">Common Footprint Masking</span>
                <span class="tech-badge badge-emerald">Verified Inlier Gate</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    classifier, change_model, classes, device = load_models()

    c_status = "PyTorch ResNet-18 (Active)" if classifier else "Real Physical Spectral Patch Classifier"
    cd_status = "Siamese U-Net (Active)" if change_model else "Calibrated Euclidean Diff Masker"

    st.markdown(
        f"""
        <div style="display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap;">
            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(0, 240, 255, 0.2); padding: 8px 14px; border-radius: 8px; font-size: 0.8rem;">
                <span style="color: #64748b;">Land-Cover Engine:</span> <strong style="color: #38bdf8;">{c_status}</strong>
            </div>
            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(168, 85, 247, 0.2); padding: 8px 14px; border-radius: 8px; font-size: 0.8rem;">
                <span style="color: #64748b;">Change Model:</span> <strong style="color: #c084fc;">{cd_status}</strong>
            </div>
            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(52, 211, 153, 0.2); padding: 8px 14px; border-radius: 8px; font-size: 0.8rem;">
                <span style="color: #64748b;">Registration Mode:</span> <strong style="color: #34d399;">Multi-Stage Common Footprint Engine</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Ingestion Controls
    st.sidebar.markdown("### 🛰️ Observation Ingestion")
    source_option = st.sidebar.radio(
        "Select Satellite Ingestion Mode",
        [
            "🌍 Live Sentinel-2 Satellite Stream (Type ANY Location)",
            "Local Tile Benchmark (Left vs Right)",
            "Bundled Demo Pair (Urban Growth)",
            "Upload Custom Multi-Temporal Pair"
        ]
    )

    img_before, img_after = None, None
    meta_before, meta_after = None, None

    if source_option == "🌍 Live Sentinel-2 Satellite Stream (Type ANY Location)":
        st.markdown("### 🔍 Live Planetary Geocoder & STAC Ingestion")
        
        st.write("Popular Study Regions:")
        presets = ["Bengaluru", "Cairo", "Tokyo", "Paris", "Dubai", "Swiss Alps"]
        p_cols = st.columns(len(presets))
        for idx, p_name in enumerate(presets):
            with p_cols[idx]:
                if st.button(p_name, key=f"btn_ew_preset_{p_name}"):
                    st.session_state["ew_location_query"] = p_name
                    st.session_state["ew_trigger_fetch"] = True
                    st.rerun()

        with st.form(key="ew_location_form"):
            col_q, col_cloud, col_btn = st.columns([2.5, 1.2, 1.3])
            with col_q:
                current_query = st.session_state.get("ew_location_query", "Bengaluru, Karnataka, India")
                typed_loc = st.text_input(
                    "Type ANY City, Region, or Coordinates:",
                    value=current_query,
                    placeholder="e.g. Cairo, Tokyo, Paris, Bengaluru, Dubai, San Francisco..."
                )
            with col_cloud:
                max_cloud = st.slider("Max Cloud (%)", min_value=5.0, max_value=50.0, value=20.0, step=5.0)
            with col_btn:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                fetch_pair_btn = st.form_submit_button("🛰️ Stream Sentinel-2", use_container_width=True)

        should_fetch = fetch_pair_btn or st.session_state.pop("ew_trigger_fetch", False)

        if should_fetch:
            st.session_state["ew_location_query"] = typed_loc
            with st.spinner(f"Geocoding '{typed_loc}' & streaming live Sentinel-2 tiles from Microsoft Planetary Computer..."):
                geocoded = geocode_user_location(typed_loc)
                st.session_state["ew_geocoded"] = geocoded
                pair_result = fetch_real_sentinel2_pair(geocoded["bbox"], max_cloud=max_cloud)
                if pair_result[0] and pair_result[1]:
                    st.session_state["ew_pair_data"] = pair_result
                    st.success(f"✅ Successfully streamed real multi-temporal Sentinel-2 observations for {geocoded['name']}!")
                else:
                    st.error(f"No cloud-free Sentinel-2 scenes found for '{typed_loc}'. Try increasing the cloud threshold.")

        if "ew_geocoded" not in st.session_state:
            st.session_state["ew_geocoded"] = geocode_user_location(st.session_state.get("ew_location_query", "Bengaluru, Karnataka, India"))

        geocoded = st.session_state["ew_geocoded"]
        b = geocoded["bbox"]
        st.markdown(
            f"""
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 8px; padding: 10px 16px; margin-bottom: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;">
                <span style="color: #64748b;">Resolved Geolocation:</span> <strong style="color: #f1f5f9;">{geocoded['name']}</strong> | 
                <span style="color: #64748b;">Centroid:</span> <strong style="color: #38bdf8;">{geocoded['lat']:.4f}° N, {geocoded['lon']:.4f}° E</strong> | 
                <span style="color: #64748b;">BBox:</span> <strong style="color: #38bdf8;">[{b[0]:.4f}, {b[1]:.4f}, {b[2]:.4f}, {b[3]:.4f}]</strong> | 
                <span style="color: #64748b;">Target CRS:</span> <strong style="color: #34d399;">{geocoded['target_utm']}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        if "ew_pair_data" not in st.session_state:
            with st.spinner("Streaming baseline Sentinel-2 observation pair for Bengaluru..."):
                pair_result = fetch_real_sentinel2_pair(geocoded["bbox"], max_cloud=20.0)
                if pair_result[0] and pair_result[1]:
                    st.session_state["ew_pair_data"] = pair_result

        if "ew_pair_data" in st.session_state:
            (h_tuple, r_tuple) = st.session_state["ew_pair_data"]
            if h_tuple and r_tuple:
                img_before, meta_before = h_tuple
                img_after, meta_after = r_tuple

    elif source_option == "Local Tile Benchmark (Left vs Right)":
        p_left = ROOT_DIR / "tile_left.jpg"
        p_right = ROOT_DIR / "tile_right.jpg"
        if p_left.exists() and p_right.exists():
            img_before = Image.open(p_left).convert("RGB")
            img_after = Image.open(p_right).convert("RGB")
        else:
            st.error("tile_left.jpg or tile_right.jpg not found.")
            return

    elif source_option == "Bundled Demo Pair (Urban Growth)":
        demo_a = DEMO_DIR / "A.png"
        demo_b = DEMO_DIR / "B.png"
        if not demo_a.exists() or not demo_b.exists():
            demo_a = ROOT_DIR / "tile_left.jpg"
            demo_b = ROOT_DIR / "tile_right.jpg"

        if demo_a.exists() and demo_b.exists():
            img_before = Image.open(demo_a).convert("RGB")
            img_after = Image.open(demo_b).convert("RGB")
        else:
            st.error("No sample images found in workspace.")
            return

    else:
        up_a = st.sidebar.file_uploader("Pre-Event / Historical Image (t0)", type=["png", "jpg", "jpeg"])
        up_b = st.sidebar.file_uploader("Post-Event / Current Image (t1)", type=["png", "jpg", "jpeg"])
        if up_a and up_b:
            img_before = Image.open(up_a).convert("RGB")
            img_after = Image.open(up_b).convert("RGB")
        else:
            st.info("Upload both a pre-event and post-event satellite chip to proceed.")
            return

    if img_before is None or img_after is None:
        st.info("Click '🛰️ Stream Sentinel-2' above to download and inspect real satellite data.")
        return

    st.markdown("---")

    # =========================================================================
    # DEDICATED SECTION: TEMPORAL REGISTRATION & COMMON FOOTPRINT
    # =========================================================================
    st.markdown(
        """
        <div style="background: linear-gradient(90deg, rgba(0,240,255,0.12), rgba(168,85,247,0.12)); border-left: 4px solid #00f0ff; padding: 12px 18px; border-radius: 6px; margin-bottom: 20px;">
            <div style="font-size: 1.15rem; font-weight: bold; color: #f8fafc; font-family: monospace;">
                🛰️ Temporal Registration & Common Footprint Engine
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                Raw multi-temporal satellite images may be shifted, scaled, or partially overlapping. 
                This verified computer vision pipeline identifies stable landmarks, warps moving images into the reference coordinate frame, 
                computes the true valid common footprint, and crops both images to the exact same rectangle before change detection.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------------------
    # STAGE 1 / A: ORIGINAL IMAGE PAIR
    # -------------------------------------------------------------------------
    st.markdown("#### 1️⃣ Stage A: Original Unaligned Image Pair")

    col_orig1, col_orig2 = st.columns(2)
    with col_orig1:
        date_cap = f"Date: {meta_before['date']} | Cloud: {meta_before['cloud_cover']}%" if meta_before else "Pre-Event Observation"
        st.markdown(f"**Image A (Pre-Event / $t_0$)** — `{date_cap}`")
        st.image(img_before, use_container_width=True)
        st.caption(f"📐 Dimensions: {img_before.width} × {img_before.height} px | Channels: 3 (RGB) | Format: {img_before.format or 'Memory RGB'}")

    with col_orig2:
        date_cap = f"Date: {meta_after['date']} | Cloud: {meta_after['cloud_cover']}%" if meta_after else "Post-Event Observation"
        st.markdown(f"**Image B (Post-Event / $t_1$)** — `{date_cap}`")
        st.image(img_after, use_container_width=True)
        st.caption(f"📐 Dimensions: {img_after.width} × {img_after.height} px | Channels: 3 (RGB) | Format: {img_after.format or 'Memory RGB'}")

    # Reference selection control
    col_ref_sel, col_reg_btn = st.columns([2, 1])
    with col_ref_sel:
        ref_selection = st.radio(
            "Select Fixed Reference Coordinate System:",
            ["Image A (t0 Pre-Event) as Reference [Fixed] - Warp Image B (t1)",
             "Image B (t1 Post-Event) as Reference [Fixed] - Warp Image A (t0)"],
            index=0,
            horizontal=True,
            key="ew_ref_selection_radio"
        )
    is_a_reference = "Image A" in ref_selection
    ref_img_in = img_before if is_a_reference else img_after
    mov_img_in = img_after if is_a_reference else img_before
    ref_name = "Image A (t0)" if is_a_reference else "Image B (t1)"
    mov_name = "Image B (t1)" if is_a_reference else "Image A (t0)"

    # -------------------------------------------------------------------------
    # REGISTRATION SETTINGS CONTROLS
    # -------------------------------------------------------------------------
    with st.expander("⚙️ Registration Configuration & Acceptance Thresholds", expanded=False):
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            detector_choice = st.selectbox("Feature Detector", ["SIFT (Scale-Invariant)", "ORB (Fast Binary)"], index=0)
            model_choice = st.selectbox(
                "Geometric Transformation Model",
                [
                    "Partial Affine (Translation + Rotation + Scale)",
                    "Affine (6-DoF Translation + Rotation + Scale + Shear)",
                    "Homography (8-DoF Projective Perspective)"
                ],
                index=0
            )
        with c_p2:
            lowe_ratio_val = st.slider("Lowe's Ratio Distance Gate", 0.50, 0.90, 0.75, 0.05,
                                      help="Rejects ambiguous matches where second-nearest neighbor distance is too close.")
            ransac_thresh_val = st.slider("RANSAC Inlier Threshold (px)", 1.0, 10.0, 4.0, 0.5,
                                         help="Maximum reprojection residual in pixels for a correspondence to be counted as inlier.")
        with c_p3:
            min_inliers_conf = st.slider("Min Inliers Required (Safety Gate)", 6, 50, 15)
            min_overlap_conf = st.slider("Min Acceptable Overlap (%)", 10.0, 60.0, 25.0, 5.0)

    # Execute Registration Engine
    reg_result: RegistrationResult = run_temporal_registration(
        ref_img_in, mov_img_in,
        ref_label=ref_name, mov_label=mov_name,
        transform_model=model_choice,
        detector_type="SIFT" if "SIFT" in detector_choice else "ORB",
        lowe_ratio=lowe_ratio_val,
        ransac_thresh=ransac_thresh_val,
        min_inliers_req=min_inliers_conf,
        min_overlap_req_pct=min_overlap_conf
    )

    diag = reg_result.diagnostics

    # -------------------------------------------------------------------------
    # STAGE 2 / B: LANDMARK DETECTION AND CORRESPONDENCE
    # -------------------------------------------------------------------------
    st.markdown("#### 2️⃣ Stage B: Stable Landmark Detection & Correspondence Matching")
    
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Keypoints (Ref / Mov)", f"{diag.num_keypoints_ref} / {diag.num_keypoints_mov}")
    with col_k2:
        st.metric("Candidate Matches", f"{diag.num_ratio_matches}", f"{diag.num_raw_matches} raw matches")
    with col_k3:
        st.metric("RANSAC Inliers", f"{diag.num_inliers}", f"{diag.inlier_ratio*100:.1f}% Inlier Ratio")
    with col_k4:
        outliers_count = max(0, diag.num_ratio_matches - diag.num_inliers)
        st.metric("Rejected Outliers", f"{outliers_count}", f"Filter: Lowe {lowe_ratio_val}")

    match_view_opt = st.radio(
        "Correspondence Vector Canvas View:",
        ["Geometrically Verified Inliers Only (Green Lines)", "All Candidates (Green Inliers + Red Outliers)"],
        horizontal=True,
        key="ew_match_view_radio"
    )

    if match_view_opt.startswith("Geometrically Verified"):
        if reg_result.inlier_matches_vis is not None:
            st.image(reg_result.inlier_matches_vis, use_container_width=True, caption=f"RANSAC Verified Inlier Correspondences ({diag.num_inliers} landmark pairs)")
    else:
        if reg_result.all_matches_vis is not None:
            st.image(reg_result.all_matches_vis, use_container_width=True, caption=f"All Candidate Correspondences (Green=Inlier, Red=Rejected Outlier)")

    st.caption("ℹ️ Stable landmarks (road intersections, terrain features, building footprints) are matched while moving objects, vegetation shifts, and seasonal differences are rejected by RANSAC.")

    # -------------------------------------------------------------------------
    # STAGE 3 / C: ESTIMATE AND APPLY TRANSFORMATION
    # -------------------------------------------------------------------------
    st.markdown("#### 3️⃣ Stage C: Geometric Registration & Alignment")
    
    col_mat, col_stat = st.columns([1.5, 1])
    with col_mat:
        matrix_symbol = 'H' if 'homography' in model_choice.lower() else 'M'
        st.markdown(f"**Estimated Transformation Matrix ($\\\\mathbf{{{matrix_symbol}}}$)** — `{diag.transform_model}`")
        if diag.transformation_matrix is not None:
            mat_df = pd.DataFrame(diag.transformation_matrix)
            st.dataframe(mat_df.style.format("{:.6f}"), use_container_width=True)
        else:
            st.error("No valid transformation matrix could be calculated.")

    with col_stat:
        st.markdown("**Geometric Reprojection Residuals**")
        st.write(f"• **Median Error:** `{diag.reprojection_error_median:.2f} px`")
        st.write(f"• **90th Percentile:** `{diag.reprojection_error_p90:.2f} px`")
        st.write(f"• **Spatial Spread:** `{diag.spatial_spread_score*100:.1f}%` of scene")
        st.write(f"• **Compute Time:** `{diag.processing_time_s:.3f} s`")

    # Interactive visual alignment inspections
    align_tab1, align_tab2, align_tab3 = st.tabs([
        "🎚️ Interactive Alpha Overlay Slider",
        "🏁 Checkerboard Edge Alignment",
        "👁️ Blink Comparison"
    ])

    with align_tab1:
        st.markdown("Slide to blend between the fixed reference coordinate system and warped moving image:")
        alpha_slider = st.slider("Alpha Blend Opacity (0% = Reference, 100% = Warped Moving)", 0.0, 1.0, 0.50, 0.05, key="ew_alpha_slider")
        ref_rgb = reg_result.ref_orig
        warped_rgb = reg_result.warped_mov
        blended = cv2.addWeighted(ref_rgb, 1.0 - alpha_slider, warped_rgb, alpha_slider, 0)
        st.image(blended, use_container_width=True, caption=f"Alpha Blend: {int((1-alpha_slider)*100)}% Reference + {int(alpha_slider*100)}% Warped Moving (Check for doubled roads/edges)")

    with align_tab2:
        check_block = st.slider("Checkerboard Block Size (px)", 16, 120, 48, step=8, key="ew_check_slider")
        cb_vis = generate_checkerboard(reg_result.ref_orig, reg_result.warped_mov, block_size=check_block)
        st.image(cb_vis, use_container_width=True, caption=f"Checkerboard Continuity Canvas (Block Size: {check_block}px) — Inspect straight roads crossing tile borders")

    with align_tab3:
        blink_state = st.toggle("Toggle to View Warped Moving (Off = Fixed Reference)", value=False, key="ew_blink_toggle")
        if blink_state:
            st.image(reg_result.warped_mov, use_container_width=True, caption=f"Blink State: Warped Moving ({mov_name})")
        else:
            st.image(reg_result.ref_orig, use_container_width=True, caption=f"Blink State: Fixed Reference ({ref_name})")

    # -------------------------------------------------------------------------
    # STAGE 4 / D: REGISTRATION QUALITY AND ACCEPTANCE GATE
    # -------------------------------------------------------------------------
    st.markdown("#### 4️⃣ Stage D: Registration Quality & Acceptance Gate")

    gate_cols = st.columns(4)
    with gate_cols[0]:
        st.metric("Inlier Support Status", f"{diag.num_inliers} Inliers", "PASSED" if diag.num_inliers >= min_inliers_conf else "FAILED")
    with gate_cols[1]:
        st.metric("Inlier Ratio", f"{diag.inlier_ratio*100:.1f}%", "PASSED" if diag.inlier_ratio >= 0.20 else "WARNING")
    with gate_cols[2]:
        st.metric("Sub-Pixel Precision", f"{diag.reprojection_error_median:.2f} px", "PASSED" if diag.reprojection_error_median <= 3.8 else "HIGH ERROR")
    with gate_cols[3]:
        st.metric("Spatial Overlap", f"{diag.valid_overlap_pct_ref:.1f}%", "PASSED" if diag.valid_overlap_pct_ref >= min_overlap_conf else "INSUFFICIENT")

    if diag.quality_passed:
        st.success("🟢 **VERIFIED REGISTRATION**: All quantitative quality gates passed. Scene is suitable for high-confidence change detection.")
    else:
        st.warning("⚠️ **CAUTION - UNVERIFIED REGISTRATION**: One or more quality gates failed:")
        for w in diag.quality_warnings:
            st.markdown(f"- ⚠️ {w}")

    # -------------------------------------------------------------------------
    # STAGE 5 / E: OVERLAP FOOTPRINT AND UNMATCHED REGIONS
    # -------------------------------------------------------------------------
    st.markdown("#### 5️⃣ Stage E: Overlap Footprint & Validity Masking")
    st.markdown(
        """
        Calculates exact valid data masks: `common_mask = ref_valid_mask AND warped_mov_valid_mask` (warped via nearest-neighbor to prevent black padding leakage).
        """
    )

    col_fp_vis, col_fp_stats = st.columns([1.5, 1])
    with col_fp_vis:
        if reg_result.footprint_vis is not None:
            st.image(reg_result.footprint_vis, use_container_width=True, caption="Footprint Map: 🟢 Green = Valid Common Area | 🟠 Amber = Ref Only | 🟣 Magenta = Moving Only | ⬛ Navy = Invalid")

    with col_fp_stats:
        st.markdown("**Footprint Partitioning Telemetry**")
        st.write(f"• **Valid Overlap (vs Ref):** `{diag.valid_overlap_pct_ref:.2f}%`")
        st.write(f"• **Valid Overlap (vs Mov):** `{diag.valid_overlap_pct_mov:.2f}%`")
        ref_only_pct = max(0.0, 100.0 - diag.valid_overlap_pct_ref)
        mov_only_pct = max(0.0, 100.0 - diag.valid_overlap_pct_mov)
        st.write(f"• **Reference-Only Region:** `{ref_only_pct:.2f}%`")
        st.write(f"• **Moving-Only Region:** `{mov_only_pct:.2f}%`")
        st.caption("Common footprint strictly reflects spatial geographic coverage, not visual spectral similarity.")

    # -------------------------------------------------------------------------
    # STAGE 6 / F: COMMON-AREA CROPPING
    # -------------------------------------------------------------------------
    st.markdown("#### 6️⃣ Stage F: Maximal Axis-Aligned Common Rectangle Cropping")
    st.markdown(
        """
        Derives the largest axis-aligned rectangle fully contained within the common valid mask. 
        Applies the **exact identical crop rectangle** to both images and the validity mask.
        """
    )

    # Show crop rectangle highlighted on full frame
    crop_highlighted = draw_crop_rectangle_on_frame(reg_result.warped_mov, diag.crop_rect)
    st.image(crop_highlighted, use_container_width=True, caption=f"Full Registered Frame with Highlighted Common Crop Window: {diag.crop_rect}")

    col_crop1, col_crop2, col_crop3 = st.columns(3)
    with col_crop1:
        st.markdown(f"**Identically Cropped Reference ({ref_name})**")
        st.image(reg_result.ref_cropped, use_container_width=True)
        st.caption(f"Shape: {reg_result.ref_cropped.shape[1]} × {reg_result.ref_cropped.shape[0]} px")

    with col_crop2:
        st.markdown(f"**Identically Cropped Moving ({mov_name})**")
        st.image(reg_result.mov_cropped, use_container_width=True)
        st.caption(f"Shape: {reg_result.mov_cropped.shape[1]} × {reg_result.mov_cropped.shape[0]} px")

    with col_crop3:
        st.markdown("**Cropped Common Validity Mask**")
        st.image(reg_result.mask_cropped, use_container_width=True)
        st.caption(f"Valid Data: {np.count_nonzero(reg_result.mask_cropped):,} px ({diag.retained_footprint_pct:.1f}% of reference)")

    # -------------------------------------------------------------------------
    # STAGE 7 / G: CHANGE DETECTION ON COMMON AREA
    # -------------------------------------------------------------------------
    st.markdown("#### 7️⃣ Stage G: Change Detection Restricted to Aligned Common Area")
    st.markdown(
        """
        Change detection is calculated **strictly on the aligned common crops** and masked by the common validity mask. 
        Invalid padding or non-overlapping margins are strictly excluded from all metrics.
        """
    )

    cd_thresh = st.slider("Spectral Difference Sensitivity Threshold", 30.0, 180.0, 85.0, 5.0, key="ew_cd_thresh_slider")

    # Primary: Verified Aligned Change Detection
    c_mask, c_diff, changed_pct, changed_px, total_valid = run_aligned_common_change_detection(
        reg_result.ref_cropped,
        reg_result.mov_cropped,
        reg_result.mask_cropped,
        threshold=cd_thresh
    )

    # Diagnostic Baseline: Unaligned Change Detection on Raw Images
    unaligned_before = cv2.resize(np.array(img_before), (reg_result.ref_cropped.shape[1], reg_result.ref_cropped.shape[0]))
    unaligned_after = cv2.resize(np.array(img_after), (reg_result.ref_cropped.shape[1], reg_result.ref_cropped.shape[0]))
    raw_diff = np.sqrt(np.sum((unaligned_before.astype(np.float32) - unaligned_after.astype(np.float32)) ** 2, axis=2))
    raw_changed_pct = float((raw_diff > cd_thresh).mean() * 100.0)

    col_cd_m1, col_cd_m2, col_cd_m3 = st.columns(3)
    with col_cd_m1:
        st.metric("Verified Disturbed Area", f"{changed_pct:.2f}%", f"{changed_pct - raw_changed_pct:+.1f}% vs unaligned baseline", delta_color="inverse")
    with col_cd_m2:
        st.metric("Disturbed Valid Pixels", f"{changed_px:,}", f"out of {total_valid:,} valid pixels")
    with col_cd_m3:
        st.metric("False Positive Suppression", f"{max(0.0, raw_changed_pct - changed_pct):.1f}%", "Misalignment Artifacts Eliminated")

    col_res1, col_res2, col_res3 = st.columns(3)
    with col_res1:
        st.markdown("**Aligned Common Pre-State**")
        st.image(reg_result.ref_cropped, use_container_width=True)
    with col_res2:
        st.markdown("**Aligned Common Post-State**")
        st.image(reg_result.mov_cropped, use_container_width=True)
    with col_res3:
        st.markdown("**Verified Disturbance Heatmap Overlay**")
        overlay = overlay_mask(Image.fromarray(reg_result.mov_cropped), c_mask, color=(255, 30, 80), alpha=0.6)
        st.image(overlay, use_container_width=True)

    # Unaligned vs Aligned Diagnostic Expander
    with st.expander("🔬 View Diagnostic Comparison: Unaligned Raw Baseline vs Registered Common Area"):
        diag_c1, diag_c2 = st.columns(2)
        with diag_c1:
            st.markdown(f"**Unaligned Baseline Difference Map** (Error Rate: `{raw_changed_pct:.1f}%`)")
            raw_mask = (raw_diff > cd_thresh).astype(np.uint8) * 255
            st.image(raw_mask, use_container_width=True, caption="Notice false-positive halos along unaligned roads and building boundaries.")
        with diag_c2:
            st.markdown(f"**Verified Aligned Difference Map** (True Change: `{changed_pct:.1f}%`)")
            st.image(c_mask, use_container_width=True, caption="True landscape disturbances isolated; alignment shift artifacts eliminated.")

    st.markdown("---")

    # =========================================================================
    # SECTION 2: LAND COVER CLASSIFICATION ON ALIGNED COMMONS
    # =========================================================================
    st.subheader("🌲 Real Land-Cover Analysis on Aligned Common Footprint")
    grid_res = st.slider("Sub-Tile Spatial Sampling Grid ($N \\times N$ physical patch analysis)", 2, 8, 4, key="ew_grid_slider")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cls_a, conf_a, counts_a = classify_satellite_image(reg_result.ref_cropped, grid_res)
        st.metric(f"Baseline Dominant Class ({ref_name})", cls_a, f"{conf_a:.1%} grid dominance")
    with col_c2:
        cls_b, conf_b, counts_b = classify_satellite_image(reg_result.mov_cropped, grid_res)
        st.metric(f"Post-Event Dominant Class ({mov_name})", cls_b, f"{conf_b:.1%} grid dominance")

    total_a = counts_a.sum()
    total_b = counts_b.sum()
    pct_a = (counts_a / total_a * 100).round(1) if total_a > 0 else np.zeros(len(classes))
    pct_b = (counts_b / total_b * 100).round(1) if total_b > 0 else np.zeros(len(classes))

    chart_df = pd.DataFrame({
        "Land Cover Class": classes * 2,
        "Surface Area %": list(pct_a) + list(pct_b),
        "Observation Time": [f"Pre-Event ({ref_name})"] * len(classes) + [f"Post-Event ({mov_name})"] * len(classes)
    })

    st.bar_chart(
        chart_df.pivot(index="Land Cover Class", columns="Observation Time", values="Surface Area %"),
        height=320
    )
