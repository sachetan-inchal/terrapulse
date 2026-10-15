"""TerraPulse v2.0 Advanced Tools & Diagnostics Area.

Expandable laboratory for computer vision researchers and remote sensing engineers:
1. 🔬 SIFT & RANSAC Stitching Laboratory:
   - Multi-seam landmark reference lines canvas (emerald horizontal & cyan vertical reference lines)
   - Pairwise SIFT keypoints, Lowe's ratio matches, verified RANSAC inliers, reprojection error
   - Overlap alpha-blend slider & alternating checkerboard split view
2. 📐 Deep Learning Model Architecture Studio:
   - ResNet-18 U-Net semantic segmentation
   - DeepLabV3+ ASPP multi-scale receptive field analysis
   - NASA Prithvi-EO Vision Transformer (ViT) token activation inspector
3. 🔮 Future Earth Spatiotemporal World Model:
   - Multitemporal simulation roadmap & EarthTilePackage schema
"""

import streamlit as st
import cv2
import numpy as np

from src.data.state_manager import AppStateManager
from src.data.sentinel_explorer import ObservationData, StitchingLaboratoryData
from src.ui.tab_model_studio import render_tab_model_studio
from src.ui.tab_future_simulator import render_tab_future_simulator


def render_workspace_advanced():
    """Renders the expandable Advanced Tools & Diagnostics panel."""
    AppStateManager.init_state()

    st.markdown(
        """
        <div style="margin-top: 10px; margin-bottom: 14px;">
            <span class="tech-badge badge-cyan">SIFT / RANSAC Alignment</span>
            <span class="tech-badge badge-purple">Deep Learning Backbones</span>
            <span class="tech-badge badge-emerald">Spatiotemporal World Model</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    adv_tabs = st.tabs([
        "🔬 SIFT & RANSAC Stitching Lab",
        "📐 Deep Learning Model Architecture Studio",
        "🔮 Future Earth World Model"
    ])

    # =========================================================================
    # TAB 1: SIFT & RANSAC STITCHING LAB
    # =========================================================================
    with adv_tabs[0]:
        _render_stitching_lab()

    # =========================================================================
    # TAB 2: DEEP LEARNING MODEL STUDIO
    # =========================================================================
    with adv_tabs[1]:
        render_tab_model_studio()

    # =========================================================================
    # TAB 3: FUTURE EARTH WORLD MODEL
    # =========================================================================
    with adv_tabs[2]:
        render_tab_future_simulator()


def _render_stitching_lab():
    """Renders the intermediate feature matching and alignment laboratory."""
    active_mosaic: ObservationData = AppStateManager.ensure_primary_mosaic()

    if active_mosaic is None or active_mosaic.stitching_lab is None:
        st.info("ℹ️ Generate a combined satellite map in the **🌍 Explore** workspace to inspect intermediate stitching diagnostics.")
        return

    lab: StitchingLaboratoryData = active_mosaic.stitching_lab

    st.markdown(
        """
        <div class="telemetry-card" style="border-left: 3px solid #38bdf8; margin-bottom: 12px;">
            <div style="font-size: 0.95rem; font-weight: 600; color: #00f0ff;">
                Intermediate Feature-Based Alignment & Overlap Diagnostics
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                Demonstrates how visual landmarks (waterways, field edges, road corridors) are matched across 
                the 4 spatial quadrants to verify geometric registration accuracy before raster fusion.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    stitching_view_mode = st.radio(
        "Stitching Diagnostic View:",
        options=[
            "📐 2×2 Multi-Seam Landmark Reference Lines Canvas",
            "🔍 Pairwise SIFT Inlier Verification & Residual Diagnostics",
            "🎛️ Overlap Alpha-Blend & Checkerboard Split Comparison",
            "✨ Final Continuous Fused Square Mosaic"
        ],
        horizontal=True,
        index=0,
        key="rad_stitching_adv_view"
    )

    if "📐" in stitching_view_mode:
        if lab.multi_seam_canvas is not None:
            st.image(
                lab.multi_seam_canvas,
                caption="2×2 Quadrant Alignment Canvas: Emerald green reference lines bridge horizontal seams (NW ↔ NE, SW ↔ SE); Cyan reference lines bridge vertical seams (NW ↔ SW, NE ↔ SE).",
                use_container_width=True
            )
        elif lab.correspondence is not None:
            st.image(lab.correspondence.match_image_all, caption="Landmark Correspondence Lines Across Overlapping Swath", use_container_width=True)

    elif "🔍" in stitching_view_mode:
        if lab.correspondence is not None:
            corr = lab.correspondence
            c_k1, c_k2, c_cand, c_inl, c_rat, c_err = st.columns(6)
            c_k1.metric("Tile 1 Keypoints", f"{corr.num_kp1:,}")
            c_k2.metric("Tile 2 Keypoints", f"{corr.num_kp2:,}")
            c_cand.metric("Lowe's 0.75 Matches", corr.num_candidate_matches)
            c_inl.metric("Verified Inliers", corr.num_inliers)
            c_rat.metric("Inlier Ratio", f"{corr.inlier_ratio}%")
            c_err.metric("Reproj Error (Median)", f"{corr.median_reprojection_error} px")

            corr_filter = st.radio(
                "Display Filter:",
                options=["All Landmark Matches (Green: Inliers, Red: Outliers)", "Verified Inliers Only", "Rejected Outliers Only"],
                horizontal=True,
                key="rad_corr_filter_adv"
            )

            if "All" in corr_filter:
                st.image(corr.match_image_all, caption="Side-by-side landmark correspondence lines (Green: RANSAC verified | Red: Outliers)", use_container_width=True)
            elif "Inliers" in corr_filter:
                st.image(corr.match_image_inliers, caption="Verified Landmark Inliers Across Tile Boundary", use_container_width=True)
            else:
                st.image(corr.match_image_outliers, caption="Rejected Outlier Matches", use_container_width=True)

    elif "🎛️" in stitching_view_mode:
        if lab.correspondence is not None:
            corr = lab.correspondence
            col_ab_ctrl, col_ab_view = st.columns([1.2, 2.0])

            with col_ab_ctrl:
                ov_alpha = st.slider("Alpha Blend Overlap (%):", 0, 100, 50, key="sld_ov_alpha_adv", help="0% = Tile 1 only | 100% = Tile 2 only | 50% = Equal blend")
                st.markdown(
                    """
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 10px;">
                        Inspect edge continuity across the overlapping swath seam. 
                        Topographical features and roads remain aligned without ghosting.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_ab_view:
                ov_h, ov_w = corr.overlap_shape
                t1_ov = lab.tiles[0].reprojected_rgb[:ov_h, :ov_w]
                t2_ov = lab.tiles[1].reprojected_rgb[:ov_h, :ov_w]
                a_val = ov_alpha / 100.0
                dyn_blend = cv2.addWeighted(t1_ov, 1.0 - a_val, t2_ov, a_val, 0)
                st.image(dyn_blend, caption=f"Dynamic Overlap Blend ({100 - ov_alpha}% Tile 1 / {ov_alpha}% Tile 2)", use_container_width=True)

            st.markdown("#### 🏁 Alternating Checkerboard Split View")
            st.image(corr.checkerboard_comparison, caption="Alternating 32px Checkerboard Blocks: inspect linear feature continuity across square block borders", use_container_width=True)

    elif "✨" in stitching_view_mode:
        col_fn_view, col_fn_meta = st.columns([2.0, 1.2])
        with col_fn_view:
            show_seam_lines = st.checkbox("Show Seamline Cut Boundaries", value=False, key="chk_seam_adv")
            disp_raster = lab.seamline_preview if show_seam_lines else lab.merged_rgb
            st.image(disp_raster, caption=f"Stitched Continuous Bigger Square Mosaic ({active_mosaic.date_str}) [{lab.final_shape[1]}×{lab.final_shape[0]} px]", use_container_width=True)

        with col_fn_meta:
            st.markdown(
                f"""
                <div class="telemetry-card">
                    <div style="font-size: 0.72rem; color: #64748b; font-family: monospace; text-transform: uppercase;">Square Mosaic Telemetry</div>
                    <div style="font-size: 0.95rem; color: #38bdf8; font-weight: 700; margin-top: 4px;">4-Tile Fused Square</div>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 8px;">
                        • Total Dimensions: <strong>{lab.final_shape[1]} × {lab.final_shape[0]} px</strong><br>
                        • Coordinate System: <strong>{lab.crs}</strong><br>
                        • Total Mapped Area: <strong>{lab.coverage_km2} km²</strong><br>
                        • Overlap Fusion: <strong>Priority Valid Mask + Linear Feathering</strong><br>
                        • Contributing Tiles: <strong>{len(lab.tiles)} swaths</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
