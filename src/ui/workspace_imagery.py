"""TerraPulse v2.0 Workspace 2: Imagery.

Capabilities:
- Real Sentinel-2 L2A STAC Observation Retrieval (Planetary Computer & Copernicus)
- Configurable acquisition epoch, cloud cover filter, and decimation
- Chronological observation cards with native Streamlit safe rendering (no raw HTML bugs)
- Instant selection & synchronization with shared application state
- Expandable Source & Metadata section (traceability, scene ID, asset URLs, spectral bands, CRS, limitations)
- Automated 2×2 Spatial Quadrant Detection (NW, NE, SW, SE)
- Georeferenced 2×2 Mosaic Generation
- Expandable Intermediate Stitching Process Visualizer:
  * Source tiles & bounding boxes
  * Reprojection & common grid alignment
  * Feature correspondence lines & RANSAC inlier filtering
  * Final fused mosaic with geodetic transform
"""

import streamlit as st
import numpy as np
import cv2

from src.data.state_manager import AppStateManager, HISTORICAL_EPOCHS
from src.data.sentinel_explorer import (
    ObservationData,
    StitchingLaboratoryData
)


def render_workspace_imagery():
    """Renders the unified Imagery workspace."""
    AppStateManager.init_state()

    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🛰️ Workspace 2: Satellite Imagery & 2×2 Mosaicking</div>
            <div>
                <span class="tech-badge badge-blue">Real STAC Catalogue</span>
                <span class="tech-badge badge-emerald">10m Multi-Spectral</span>
                <span class="tech-badge badge-purple">Cross-UTM Reprojection</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        Browse authentic Sentinel-2 Level-2A observations intersecting the study area.
        Select an individual swath to inspect or combine four adjacent quadrant tiles (NW, NE, SW, SE)
        into a continuous, georeferenced square mosaic aligned to a common coordinate grid.
        """
    )

    geocoded = AppStateManager.get_geocoded()

    # -------------------------------------------------------------------------
    # 1. STAC QUERY FILTERS
    # -------------------------------------------------------------------------
    col_prov, col_ep, col_cld, col_dec = st.columns([1.2, 1.2, 1.0, 0.8])
    with col_prov:
        prov_opt = ["Planetary Computer (Streaming COGs)", "Copernicus Data Space (ESA CDSE)"]
        cur_prov = st.session_state.get(AppStateManager.KEY_STAC_PROVIDER, prov_opt[0])
        idx_prov = prov_opt.index(cur_prov) if cur_prov in prov_opt else 0
        new_prov = st.selectbox("Satellite Provider:", options=prov_opt, index=idx_prov, key="sel_prov_imagery")
        if new_prov != cur_prov:
            st.session_state[AppStateManager.KEY_STAC_PROVIDER] = new_prov
            st.session_state.pop(AppStateManager.KEY_DISCOVERED_SCENES, None)
            st.rerun()

    with col_ep:
        epoch_opts = list(HISTORICAL_EPOCHS.keys())
        cur_epoch = st.session_state.get(AppStateManager.KEY_EPOCH_LABEL, epoch_opts[0])
        idx_epoch = epoch_opts.index(cur_epoch) if cur_epoch in epoch_opts else 0
        new_epoch = st.selectbox("Acquisition Epoch / Date Range:", options=epoch_opts, index=idx_epoch, key="sel_epoch_imagery")
        if new_epoch != cur_epoch:
            st.session_state[AppStateManager.KEY_EPOCH_LABEL] = new_epoch
            st.session_state.pop(AppStateManager.KEY_DISCOVERED_SCENES, None)
            st.rerun()

    with col_cld:
        cur_cloud = float(st.session_state.get(AppStateManager.KEY_MAX_CLOUD, 25.0))
        new_cloud = st.slider("Max Cloud Cover (%)", min_value=0.0, max_value=80.0, value=cur_cloud, step=5.0, key="sld_cloud_imagery")
        if new_cloud != cur_cloud:
            st.session_state[AppStateManager.KEY_MAX_CLOUD] = new_cloud
            st.session_state.pop(AppStateManager.KEY_DISCOVERED_SCENES, None)
            st.rerun()

    with col_dec:
        cur_dec = int(st.session_state.get(AppStateManager.KEY_DECIMATION, 12))
        new_dec = st.slider("Decimation", min_value=4, max_value=24, value=cur_dec, step=2, key="sld_dec_imagery", help="Sampling factor for responsive COG streaming.")
        if new_dec != cur_dec:
            st.session_state[AppStateManager.KEY_DECIMATION] = new_dec
            st.session_state.pop(AppStateManager.KEY_PRIMARY_MOSAIC, None)
            st.rerun()

    # -------------------------------------------------------------------------
    # 2. DISCOVER SCENES & PRIMARY MOSAIC
    # -------------------------------------------------------------------------
    with st.spinner(f"Querying authentic Sentinel-2 archive for '{geocoded['name']}'..."):
        discovered_scenes = AppStateManager.ensure_discovered_scenes()

    if not discovered_scenes:
        st.warning(
            f"⚠️ No Sentinel-2 observations found with cloud cover < {new_cloud}% in '{new_epoch}'. "
            "Please broaden the date range or increase the max cloud cover slider."
        )
        return

    auto_4_scenes = AppStateManager.get_auto_4_scenes()
    with st.spinner("Preparing georeferenced mosaic..."):
        active_mosaic = AppStateManager.ensure_primary_mosaic()

    cur_sel_id = st.session_state.get(AppStateManager.KEY_PRIMARY_OBS_ID, "mosaic")

    # -------------------------------------------------------------------------
    # 3. CHRONOLOGICAL SATELLITE OBSERVATIONS (SAFE NATIVE RENDERING)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown(f"### 🗓️ Satellite Observations Archive ({len(discovered_scenes)} acquisitions found)")
    st.caption("Select any observation card below to update all downstream maps, environmental CV layers, and AI investigations.")

    total_cards = len(discovered_scenes) + (1 if active_mosaic else 0)
    card_cols = st.columns(min(6, total_cards))
    col_idx = 0

    # 1. Mosaic Card
    if active_mosaic is not None:
        with card_cols[col_idx % len(card_cols)]:
            is_active_mosaic = (cur_sel_id == "mosaic")
            with st.container(border=True):
                st.image(active_mosaic.rgb, use_container_width=True)
                if is_active_mosaic:
                    st.markdown(":blue[**● ACTIVE 2×2 MOSAIC**]")
                else:
                    st.markdown(":green[**FUSED 2×2 MOSAIC**]")
                st.caption(f"Date: {active_mosaic.date_str}")
                st.caption(f"Cloud: {active_mosaic.cloud_cover:.1f}% | 10m")
                if st.button("Select Mosaic", key="btn_sel_mosaic_img_tab", use_container_width=True, disabled=is_active_mosaic):
                    AppStateManager.set_selected_observation_id("mosaic")
                    st.rerun()
            col_idx += 1

    # 2. Individual Discovered Scenes
    auto_4_ids = set(s.id for s in auto_4_scenes)
    for sc in discovered_scenes[:11]:
        with card_cols[col_idx % len(card_cols)]:
            is_selected = (cur_sel_id == sc.id)
            is_quad = (sc.id in auto_4_ids)
            thumb = sc.preview_url if sc.preview_url else "tile_left.jpg"
            with st.container(border=True):
                st.image(thumb, use_container_width=True)
                if is_selected:
                    st.markdown(":blue[**● ACTIVE SCENE**]")
                elif is_quad:
                    st.markdown(":orange[**QUADRANT TILE**]")
                else:
                    st.markdown("**OBSERVATION**")

                st.caption(f"Date: **{sc.date_str}**")
                st.caption(f"{sc.platform} | ☁️ {sc.cloud_cover:.1f}%")
                if st.button("Select Scene", key=f"btn_sel_sc_{col_idx}_{sc.id[:12]}", use_container_width=True, disabled=is_selected):
                    AppStateManager.set_selected_observation_id(sc.id)
                    st.rerun()
            col_idx += 1

    # -------------------------------------------------------------------------
    # 4. ACTIVE OBSERVATION SOURCE & METADATA (TRACEABILITY)
    # -------------------------------------------------------------------------
    st.markdown("---")
    active_obs = AppStateManager.get_active_observation()

    with st.expander("🔍 Selected Observation Source & Full Metadata (Provenance)", expanded=True):
        if active_obs is not None:
            m_c1, m_c2, m_c3 = st.columns([1.5, 1.5, 1.5])
            with m_c1:
                st.markdown("**Identification & Catalog:**")
                st.markdown(f"• **Product / Scene ID:** `{active_obs.id}`")
                st.markdown(f"• **Data Provider:** {new_prov}")
                st.markdown(f"• **Acquisition Date:** {active_obs.date_str}")
                st.markdown(f"• **Obs Mode:** {'2×2 Spatial Mosaic' if active_obs.is_composite else 'Single Scene Swath'}")
            with m_c2:
                st.markdown("**Spatial & Sensor Specifications:**")
                st.markdown(f"• **Spatial Resolution:** 10m Ground Sample Distance")
                st.markdown(f"• **Spectral Bands:** B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)")
                st.markdown(f"• **Coordinate System:** `{active_obs.crs}`")
                st.markdown(f"• **Cloud Cover:** {active_obs.cloud_cover:.1f}%")
            with m_c3:
                st.markdown("**Processing & Limitations:**")
                st.markdown("• **Operations Applied:** Cross-UTM Reprojection, Bilinear Sampling, Contrast Stretch")
                st.markdown("• **Atmospheric Processing:** Level-2A Bottom-Of-Atmosphere (BOA) Surface Reflectance")
                st.markdown(f"• **Geographic Extent:** `[{active_obs.bbox[0]:.2f}, {active_obs.bbox[1]:.2f}, {active_obs.bbox[2]:.2f}, {active_obs.bbox[3]:.2f}]`")
                st.markdown("• **Limitations:** Decimated preview for real-time interaction; invalid zero-data pixels masked out.")

    # -------------------------------------------------------------------------
    # 5. 2×2 SPATIAL QUADRANT TILES & MOSAIC ENGINE
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🧩 2×2 Spatial Quadrants (Coverage of AOI)")
    st.caption("Adjacent orbital swaths automatically detected to form continuous multi-swath coverage over the study area.")

    q_labels = ["North-West (Tile 1)", "North-East (Tile 2)", "South-West (Tile 3)", "South-East (Tile 4)"]
    q_cols = st.columns(4)
    for idx, sc in enumerate(auto_4_scenes[:4]):
        with q_cols[idx]:
            parts = sc.id.split('_')
            tc = [p for p in parts if p.startswith('T') and len(p) == 6]
            code = tc[0] if tc else sc.id[:12]
            with st.container(border=True):
                st.markdown(f"**{q_labels[idx]}**")
                st.markdown(f"`{code}`")
                st.caption(f"Acquired: {sc.date_str}")
                st.caption(f"Cloud: {sc.cloud_cover:.1f}% | {sc.platform}")

    # -------------------------------------------------------------------------
    # 6. EXPANDABLE INTERMEDIATE STITCHING PROCESS VISUALIZER
    # -------------------------------------------------------------------------
    with st.expander("🛠️ Intermediate Mosaicking Process Visualizer (Step-by-Step)", expanded=False):
        st.markdown(
            """
            This visualizer shows genuine intermediate raster outputs generated during the 2×2 mosaicking pipeline:
            reprojection, grid alignment, seamline verification, and feature correspondence analysis.
            """
        )

        stitching_lab = active_mosaic.stitching_lab if active_mosaic else None

        if stitching_lab and len(stitching_lab.tiles) >= 2:
            st_tab1, st_tab2, st_tab3, st_tab4 = st.tabs([
                "1. Source Tiles & Projections",
                "2. Grid Alignment & Seamlines",
                "3. Feature Correspondence & RANSAC",
                "4. Final Fused Mosaic"
            ])

            with st_tab1:
                st.markdown("#### Input Satellite Swaths Before & After UTM Reprojection")
                tile_cols = st.columns(min(4, len(stitching_lab.tiles)))
                for t_idx, tile in enumerate(stitching_lab.tiles):
                    with tile_cols[t_idx]:
                        st.image(tile.raw_rgb, caption=f"Tile {t_idx+1}: {tile.id[:14]}... ({tile.raw_crs})", use_container_width=True)
                        st.caption(f"Shape: {tile.raw_shape} px | Cloud: {tile.cloud_cover:.1f}%")

            with st_tab2:
                st.markdown("#### Multi-Swath Seamlines & Valid Data Masks")
                c_seam, c_info = st.columns([2.0, 1.0])
                with c_seam:
                    if stitching_lab.multi_seam_canvas is not None:
                        st.image(stitching_lab.multi_seam_canvas, caption="Combined 4-Tile Seamlines (Green Crosshairs) and Tile Placement", use_container_width=True)
                    else:
                        st.image(stitching_lab.seamline_preview, caption="Tile Overlap Boundary Seamline", use_container_width=True)
                with c_info:
                    st.markdown("**Alignment Metadata:**")
                    st.markdown(f"• **Target CRS:** `{stitching_lab.crs}`")
                    st.markdown(f"• **Mosaic Dimensions:** {stitching_lab.final_shape[1]} × {stitching_lab.final_shape[0]} px")
                    st.markdown(f"• **Area Covered:** {stitching_lab.coverage_km2:,} km²")
                    st.markdown(f"• **Blending:** Priority Valid Mask + Linear Feathering")

            with st_tab3:
                st.markdown("#### SIFT & RANSAC Landmark Verification Across Overlap")
                if stitching_lab.correspondence is not None:
                    corr = stitching_lab.correspondence
                    st.markdown(
                        f"""
                        • **Keypoints Detected:** {corr.num_kp1:,} (Tile 1) & {corr.num_kp2:,} (Tile 2)  
                        • **Matches Found:** {corr.num_candidate_matches:,} candidate pairs  
                        • **RANSAC Inliers:** **{corr.num_inliers:,} ({corr.inlier_ratio:.1f}%)**  
                        • **Median Reprojection Error:** {corr.median_reprojection_error:.2f} px  
                        """
                    )
                    st.image(corr.match_image_all, caption="Landmark Correspondence Lines (Green: Verified Inliers | Red: Outliers)", use_container_width=True)
                else:
                    st.info("Feature correspondence analysis requires at least 2 tiles with overlapping boundaries.")

            with st_tab4:
                st.markdown("#### Final Georeferenced Continuous Mosaic")
                if active_mosaic is not None:
                    st.image(active_mosaic.rgb, caption=f"Fused Square Mosaic for {geocoded['name']} ({active_mosaic.date_str})", use_container_width=True)
                    st.success(f"✓ Georeferenced mosaic successfully built across {len(auto_4_scenes)} adjacent swaths.")
        else:
            st.info("Intermediate stitching laboratory data is loading or requires at least 2 adjacent swaths.")
