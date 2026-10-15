"""TerraPulse v2.0 Workspace 3: Compare.

Capabilities:
- Conditional Bi-Temporal Comparison (Only enabled when two valid observations exist)
- Honest availability warnings when secondary data is missing
- Common Spatial Grid Alignment & Geographic Boundary Harmonization
- Interactive Before-and-After Split Swipe Comparison Slider
- Calibrated Change Detection (ΔNDVI Vegetation Gain & Depletion Map)
- Real Provenance: True Acquisition Dates, Sensor Platforms, Cloud Covers, and Common Overlap %
"""

import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

from src.data.state_manager import AppStateManager
from src.data.sentinel_explorer import ObservationData, SentinelSceneMetadata


def composite_split_image(img_a: Image.Image, img_b: Image.Image, split_ratio: float = 0.5) -> Image.Image:
    """Creates a side-by-side composite split image with a vertical dividing line and badge."""
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

    # Cyan vertical divider line
    line_x = split_x
    draw.line([(line_x - 1, 0), (line_x - 1, h)], fill=(0, 240, 255), width=3)

    # Glowing center badge handle
    cy = h // 2
    r = 16
    draw.ellipse([(line_x - r, cy - r), (line_x + r, cy + r)], fill=(11, 15, 25), outline=(0, 240, 255), width=2)
    draw.text((line_x - 7, cy - 7), "↔", fill=(0, 240, 255))

    return out_img


def render_workspace_compare():
    """Renders the unified Compare workspace."""
    AppStateManager.init_state()

    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">↔️ Workspace 3: Bi-Temporal Observation Comparison & Change Detection</div>
            <div>
                <span class="tech-badge badge-cyan">Split-View Swipe Slider</span>
                <span class="tech-badge badge-purple">Spatial Grid Alignment</span>
                <span class="tech-badge badge-emerald">ΔNDVI Change Map</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        Compare two authentic satellite observations of the study area across different acquisition epochs.
        **Comparison is strictly conditional on valid data:** both scenes are aligned to a shared geographic coordinate grid,
        and change detection statistics are computed exclusively over the verified common spatial overlap.
        """
    )

    # 1. Fetch Primary Observation & Catalog Scenes from Shared State
    primary_obs: ObservationData = AppStateManager.get_active_observation()
    geocoded = AppStateManager.get_geocoded()
    discovered_scenes = AppStateManager.ensure_discovered_scenes()
    auto_4_scenes = AppStateManager.get_auto_4_scenes()
    auto_4_ids = set(s.id for s in auto_4_scenes)

    if primary_obs is None:
        st.warning("⚠️ No active observation found. Please select a location and generate imagery in the **🌍 Explore** workspace first.")
        return

    # Check for available secondary scenes
    # Exclude contributing tiles to avoid comparing an image with itself
    other_scenes = [s for s in discovered_scenes if s.id not in auto_4_ids and s.date_str != primary_obs.date_str]

    # If all scenes share the same date, fall back to any other distinct scene ID
    if not other_scenes:
        other_scenes = [s for s in discovered_scenes if s.id != primary_obs.id]

    # -------------------------------------------------------------------------
    # CONDITIONAL CHECK: ARE 2 SUITABLE OBSERVATIONS AVAILABLE?
    # -------------------------------------------------------------------------
    if not other_scenes:
        st.markdown(
            f"""
            <div class="telemetry-card" style="border-left: 3px solid #fbbf24; margin-top: 10px;">
                <div style="font-size: 1.0rem; font-weight: 700; color: #fbbf24;">
                    ⚠️ Single Observation Archive Notice
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px; line-height: 1.5;">
                    The current query criteria for <strong>{geocoded['name']}</strong> contains only 1 distinct observation epoch. 
                    Temporal comparison requires at least <strong>two authentic observations</strong> of the same geographic region.
                </div>
                <div style="font-size: 0.8rem; color: #f1f5f9; margin-top: 10px;">
                    <strong>Recommended Actions:</strong>
                    <ul style="margin-top: 4px; padding-left: 20px;">
                        <li>Return to <strong>🌍 Explore</strong> and change the <em>Historical Epoch / Archive Period</em> to <code>Full Archive (2016–Present)</code>.</li>
                        <li>Or increase the <em>Max Cloud Cover</em> slider to include earlier historical overpasses.</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.info("💡 Single-observation analysis remains fully functional in the **🌿 Analyze** and **🧠 Investigate** workspaces.")
        return

    # -------------------------------------------------------------------------
    # 2. SELECT SECONDARY OBSERVATION (t0 vs t1)
    # -------------------------------------------------------------------------
    st.markdown("### 📅 Select Comparison Observation Pair")

    scene_options = {
        f"📅 {s.date_str} (Cloud: {s.cloud_cover:.1f}%) — {s.platform} [{s.id[:28]}...]": s.id
        for s in other_scenes
    }

    col_t0, col_t1 = st.columns(2)

    with col_t0:
        st.markdown(
            f"""
            <div class="telemetry-card" style="padding: 10px 14px; margin-bottom: 8px;">
                <div style="font-size: 0.72rem; color: #38bdf8; font-family: monospace; text-transform: uppercase;">
                    Epoch t0 (Baseline / Historical)
                </div>
                <div style="font-size: 0.85rem; color: #f1f5f9; font-weight: 600; margin-top: 4px;">
                    Select secondary observation below:
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        selected_t0_label = st.selectbox(
            "Secondary Observation (t0):",
            options=list(scene_options.keys()),
            index=0,
            key="sel_t0_compare"
        )
        selected_t0_id = scene_options[selected_t0_label]

    with col_t1:
        st.markdown(
            f"""
            <div class="telemetry-card" style="padding: 10px 14px; margin-bottom: 8px;">
                <div style="font-size: 0.72rem; color: #34d399; font-family: monospace; text-transform: uppercase;">
                    Epoch t1 (Recent / Active Mosaic)
                </div>
                <div style="font-size: 0.85rem; color: #f1f5f9; font-weight: 600; margin-top: 4px;">
                    Date: <strong>{primary_obs.date_str}</strong> (Cloud: {primary_obs.cloud_cover:.1f}%)
                </div>
                <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 2px;">
                    Platform: {primary_obs.platform} | Source: Active Combined Map
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Harmonize and Run Comparison
    cur_comp = AppStateManager.get_comparison_result()
    needs_run = (cur_comp is None or cur_comp.get("scene_t0", {}).get("id") != selected_t0_id)

    if st.button("⚖️ Harmonize Grids & Run Change Detection", key="btn_run_comparison_action", use_container_width=True) or not needs_run:
        if needs_run:
            with st.spinner("Aligning geographic coordinate grids and computing ΔNDVI change..."):
                ok, msg, res = AppStateManager.run_temporal_comparison(selected_t0_id)
                if not ok:
                    st.error(f"Comparison failed: {msg}")
                    return
                cur_comp = res

    if cur_comp is None:
        st.info("Click **'⚖️ Harmonize Grids & Run Change Detection'** above to process the bi-temporal comparison.")
        return

    meta = cur_comp["meta"]
    obs_t0 = cur_comp["obs_t0"]
    obs_t1 = cur_comp["obs_t1"]
    crop_t0 = cur_comp["crop_t0"]
    crop_t1 = cur_comp["crop_t1"]
    delta_ndvi = cur_comp["delta_ndvi"]

    # -------------------------------------------------------------------------
    # 3. HARMONIZATION QUALITY & COMMON FOOTPRINT METRICS
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📊 Harmonized Grid & Alignment Telemetry")

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Baseline Epoch (t0)", obs_t0.date_str, f"Cloud: {obs_t0.cloud_cover:.1f}%")
    col_m2.metric("Recent Epoch (t1)", obs_t1.date_str, f"Cloud: {obs_t1.cloud_cover:.1f}%")
    col_m3.metric("Common Spatial Overlap", f"{meta['overlap_pct']}%", f"{meta['target_shape'][1]}×{meta['target_shape'][0]} px")
    col_m4.metric("Canopy Gain (Blue)", f"{meta['vegetation_gain_pct']}%", "Healthy growth")
    col_m5.metric("Canopy Loss (Red)", f"{meta['vegetation_loss_pct']}%", "Depleted canopy")

    # -------------------------------------------------------------------------
    # 4. INTERACTIVE SPLIT-VIEW SWIPE SLIDER
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🎚️ Interactive Before-and-After Swipe Split Slider")
    st.markdown(
        """
        Drag the slider boundary left and right to reveal the transition between the baseline pre-state ($t_0$)
        and the recent post-state ($t_1$). Observe ground changes such as construction, urban expansion, and vegetation shifts.
        """
    )

    split_pct = st.slider(
        "Swipe Boundary Position (% from left)",
        min_value=0, max_value=100, value=50, step=1,
        key="sld_swipe_boundary"
    )

    c_lbl1, c_lbl2 = st.columns(2)
    with c_lbl1:
        st.markdown(f"<span style='color: #00f0ff; font-weight: bold;'>PRE-STATE (t0): {obs_t0.date_str}</span>", unsafe_allow_html=True)
    with c_lbl2:
        st.markdown(f"<span style='color: #f43f5e; font-weight: bold; float: right;'>POST-STATE (t1): {obs_t1.date_str}</span>", unsafe_allow_html=True)

    img_a = Image.fromarray(crop_t0)
    img_b = Image.fromarray(crop_t1)
    split_composite = composite_split_image(img_a, img_b, split_ratio=split_pct / 100.0)
    st.image(split_composite, use_container_width=True)

    # -------------------------------------------------------------------------
    # 5. CHANGE DETECTION MAP (ΔNDVI: WHAT CHANGED?)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔍 Change Detection Analysis: What Changed?")

    col_cd_img, col_cd_meta = st.columns([2.0, 1.1])

    with col_cd_img:
        fig, ax = plt.subplots(figsize=(10, 5.8))
        fig.patch.set_facecolor('#070b14')
        ax.set_facecolor('#070b14')
        im = ax.imshow(delta_ndvi, cmap="coolwarm_r", vmin=-0.35, vmax=0.35)
        ax.set_title(
            f"ΔNDVI Vegetation Change ({obs_t0.date_str} → {obs_t1.date_str})\n"
            f"Canopy Gain: {meta['vegetation_gain_pct']}% | Canopy Loss: {meta['vegetation_loss_pct']}%",
            color="#00f0ff", fontsize=11, fontfamily='monospace'
        )
        ax.axis("off")
        cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
        cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
        cbar.set_label("ΔNDVI: Blue = Canopy Growth / Greening | Red = Canopy Depletion / Clearing", color="#94a3b8", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_cd_meta:
        st.markdown(
            f"""
            <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8;">
                <strong style="color: #38bdf8;">Change Detection Methodology:</strong><br>
                • Formula: <code>ΔNDVI = NDVI(t1) - NDVI(t0)</code><br>
                • Common Evaluation Mask: <strong>{meta['overlap_pct']}% spatial overlap</strong><br>
                • Depletion Threshold: <code>ΔNDVI < -0.15</code> (Red)<br>
                • Recovery Threshold: <code>ΔNDVI > +0.15</code> (Blue)<br>
                <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                <strong style="color: #f1f5f9;">Scientific Interpretation:</strong><br>
                Vegetation loss clusters typically correspond to new construction, seasonal agricultural harvesting, or forestry clearing.<br>
                Vegetation gain indicates seasonal monsoon green-up, afforestation, or crop canopy maturation.
            </div>
            """,
            unsafe_allow_html=True
        )
