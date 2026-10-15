"""Earth Explorer | Satellite Intelligence UI Component.

A streamlined, single-observation-first geospatial intelligence studio:
Stage 1: Search Location & Interactive 3D Globe / Chronological Satellite Observations Timeline
Stage 2: Live STAC Discovery (Planetary Computer & Copernicus Data Space)
Stage 3: Cloud-Optimized Reprojection & Dedicated Stitching Laboratory (SIFT, RANSAC, Overlap, Seamlines)
Stage 4: Environmental Computer Vision Workspace (NDVI, CIR, NDWI, NDBI, Land Cover, Population Overlay with Opacity Slider)
Stage 5: Conditional Bi-Temporal Grid Alignment & Change Detection
Stage 6: Evidence-Based AI Environmental Investigator
"""

import os
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pydeck as pdk
import cv2

from src.data.sentinel_service import geocode_user_location
from src.ui.globe_component import build_3d_globe_html
from src.data.sentinel_explorer import (
    search_sentinel2_scenes,
    inspect_sentinel2_assets,
    retrieve_sentinel2_data,
    build_real_sentinel2_mosaic,
    build_georeferenced_mosaic,
    calculate_environmental_layers,
    align_bitemporal_observations,
    SentinelSceneMetadata,
    ObservationData,
    EnvironmentalLayers,
    StitchingLaboratoryData,
    StitchingTileInfo,
    StitchingCorrespondenceData
)
from src.models.registration import generate_checkerboard

POPULAR_LOCATIONS = {
    "Bengaluru, India": "Bengaluru, Karnataka, India",
    "Tokyo Bay, Japan": "Tokyo Bay Megalopolis, Japan",
    "Cairo & Nile, Egypt": "Nile Delta & Cairo, Egypt",
    "Swiss Alps": "Swiss Alps (Rhone Glacier), Switzerland",
    "Grand Canyon, USA": "Grand Canyon, Arizona, USA",
    "Paris, France": "Paris, France",
    "Dubai, UAE": "Dubai, United Arab Emirates"
}

HISTORICAL_EPOCHS = {
    "Recent (2024–2025)": "2024-01-01/..",
    "Epoch 2023–2024": "2023-01-01/2024-12-31",
    "Epoch 2020–2021": "2020-01-01/2021-12-31",
    "Historical (2017–2018)": "2017-01-01/2018-12-31",
    "Full Archive (2016–Present)": "2016-01-01/.."
}


def render_tab_earth_explorer():
    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🛰️ Earth Explorer | Satellite Intelligence</div>
            <div>
                <span class="tech-badge badge-cyan">Sentinel-2 MSI 10m</span>
                <span class="tech-badge badge-emerald">Real STAC COGs</span>
                <span class="tech-badge badge-purple">Stitching Laboratory</span>
                <span class="tech-badge badge-amber">Environmental CV</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        Explore real, multi-spectral satellite observations worldwide. Search any location, query the live Sentinel-2 
        catalogue across multi-decadal epochs, inspect source tiles in the **Stitching Laboratory** with SIFT & RANSAC 
        inlier verification, fuse georeferenced mosaics, and analyze computer-vision environmental layers with opacity overlays.
        """
    )

    # =========================================================================
    # STAGE 1: LOCATE & INTERACTIVE AOI GLOBE
    # =========================================================================
    st.markdown("### 📍 Stage 1: Location & Region of Interest (AOI)")

    col_srch, col_pop = st.columns([2.2, 1.2])

    with col_srch:
        with st.form(key="ee_location_search_form"):
            c_input, c_btn = st.columns([3.2, 1.0])
            with c_input:
                cur_loc = st.session_state.get("ee_query", "Bengaluru, Karnataka, India")
                typed_loc = st.text_input(
                    "Search City, Address, or Geographic Coordinates:",
                    value=cur_loc,
                    placeholder="e.g. Bengaluru, Cairo, Tokyo, Paris, Zurich..."
                )
            with c_btn:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("🔍 Locate", use_container_width=True)
            if submitted and typed_loc != cur_loc:
                st.session_state["ee_query"] = typed_loc
                # Invalidate stale location-specific session states
                st.session_state.pop("ee_selected_scene_id", None)
                st.session_state.pop("latest_sentinel_mosaic", None)
                for k in list(st.session_state.keys()):
                    if k.startswith("ee_obs_"):
                        st.session_state.pop(k, None)
                st.rerun()

    with col_pop:
        st.write("Popular Global Regions:")
        pop_cols = st.columns(3)
        for idx, (p_lbl, p_val) in enumerate(list(POPULAR_LOCATIONS.items())[:6]):
            with pop_cols[idx % 3]:
                if st.button(p_lbl, key=f"btn_ee_pop_{idx}"):
                    st.session_state["ee_query"] = p_val
                    st.session_state.pop("ee_selected_scene_id", None)
                    st.session_state.pop("latest_sentinel_mosaic", None)
                    for k in list(st.session_state.keys()):
                        if k.startswith("ee_obs_"):
                            st.session_state.pop(k, None)
                    st.rerun()

    # Geocode location
    active_query = st.session_state.get("ee_query", "Bengaluru, Karnataka, India")
    geocoded = geocode_user_location(active_query)
    lat, lon = geocoded["lat"], geocoded["lon"]
    bbox = geocoded["bbox"]  # [min_lon, min_lat, max_lon, max_lat]

    d_lon_km = (bbox[2] - bbox[0]) * 111.32 * np.cos(np.radians(lat))
    d_lat_km = (bbox[3] - bbox[1]) * 110.57
    est_area_km2 = abs(d_lon_km * d_lat_km)

    # Invalidation check on query change
    if st.session_state.get("ee_active_query_cached") != active_query:
        st.session_state["ee_active_query_cached"] = active_query
        st.session_state.pop("ee_selected_scene_id", None)
        st.session_state.pop("latest_sentinel_mosaic", None)

    # Telemetry Bar
    st.markdown(
        f"""
        <div class="telemetry-card" style="margin-bottom: 12px; border-left: 3px solid #00f0ff;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Resolved Location:</span>
                    <strong style="color: #f1f5f9; font-size: 0.95rem; margin-left: 6px;">{geocoded['name']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Target Coordinates:</span>
                    <strong style="color: #00f0ff; font-family: monospace; font-size: 0.9rem; margin-left: 6px;">{lat:.4f}° N, {lon:.4f}° E</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Globe Focus:</span>
                    <span class="tech-badge badge-emerald" style="margin-left: 4px;">Centered on Southern India</span>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Target UTM:</span>
                    <strong style="color: #34d399; font-family: monospace; font-size: 0.85rem; margin-left: 6px;">{geocoded['target_utm']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">AOI BBox:</span>
                    <code style="color: #a78bfa; font-size: 0.78rem;">[{bbox[0]:.4f}, {bbox[1]:.4f}, {bbox[2]:.4f}, {bbox[3]:.4f}]</code>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Query Parameters Controls (Compact Bar)
    col_prov, col_ep, col_cld, col_lim = st.columns([1.2, 1.2, 1.0, 0.8])
    with col_prov:
        stac_provider = st.selectbox(
            "STAC Data Provider:",
            options=["Planetary Computer (Streaming COGs)", "Copernicus Data Space (ESA CDSE)"],
            index=0,
            key="ee_stac_provider"
        )
        provider_key = "planetary_computer" if "Planetary" in stac_provider else "copernicus"

    with col_ep:
        selected_epoch_label = st.selectbox(
            "Historical Epoch / Archive Period:",
            options=list(HISTORICAL_EPOCHS.keys()),
            index=0,
            key="ee_epoch_selector"
        )
        datetime_range = HISTORICAL_EPOCHS[selected_epoch_label]

    with col_cld:
        max_cloud_thresh = st.slider(
            "Max Cloud Cover (%)",
            min_value=0.0, max_value=80.0, value=25.0, step=5.0,
            key="ee_cloud_slider"
        )

    with col_lim:
        query_limit = st.number_input("Max Scenes", min_value=2, max_value=20, value=6, step=1, key="ee_query_limit")

    # Discover actual Sentinel-2 scenes for this location and parameters
    with st.spinner(f"Querying live Sentinel-2 catalogue for '{geocoded['name']}' ({selected_epoch_label})..."):
        discovered_scenes = search_sentinel2_scenes(
            bbox=bbox,
            datetime_range=datetime_range,
            provider=provider_key,
            max_cloud=max_cloud_thresh,
            limit=int(query_limit)
        )

    if not discovered_scenes:
        st.warning(
            f"⚠️ No Sentinel-2 observations found with cloud cover < {max_cloud_thresh}% in '{selected_epoch_label}'. "
            "Broaden the historical epoch or increase the max cloud cover slider."
        )
        return

    # Determine Active Selected Scene ID
    valid_scene_ids = [s.id for s in discovered_scenes]
    selected_scene_id = st.session_state.get("ee_selected_scene_id")
    if not selected_scene_id or selected_scene_id not in valid_scene_ids:
        selected_scene_id = valid_scene_ids[0]
        st.session_state["ee_selected_scene_id"] = selected_scene_id

    primary_scene = next(s for s in discovered_scenes if s.id == selected_scene_id)

    # Determine Active Sticker Image for 3D Globe Projection
    current_stitched = st.session_state.get("latest_sentinel_mosaic")
    if current_stitched is None:
        # Check if selected scene has already been retrieved in memory
        for k, v in st.session_state.items():
            if k.startswith("ee_obs_") and getattr(v, "id", None) == primary_scene.id:
                current_stitched = v.rgb
                break
    if current_stitched is None and primary_scene.preview_url:
        current_stitched = primary_scene.preview_url
    if current_stitched is None and os.path.exists("stitched_result.jpg"):
        current_stitched = "stitched_result.jpg"
    elif current_stitched is None and os.path.exists("tile_left.jpg"):
        current_stitched = "tile_left.jpg"

    # 3D Globe vs 2D Boundary Switcher
    c_mode1, c_mode2 = st.columns([2.2, 1.0])
    with c_mode1:
        st.markdown(
            """
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 6px;">
                <strong style="color: #00f0ff;">3D Spherical Surface Projection:</strong> The georeferenced satellite mosaic is curved and clamped directly onto the 3D Earth globe surface at its exact coordinates (lat/lon). Use <strong>[Zoom to Region]</strong> to fly into the sticker or <strong>[Full Orbit]</strong> to inspect the global planet.
            </div>
            """,
            unsafe_allow_html=True
        )
    with c_mode2:
        globe_view_mode = st.radio(
            "Visualization Mode:",
            options=["🌍 3D Orbital Globe (Sticker Clamped)", "🗺️ 2D AOI Boundary"],
            horizontal=True,
            index=0
        )

    if globe_view_mode == "🌍 3D Orbital Globe (Sticker Clamped)":
        globe_html = build_3d_globe_html(
            target_name=geocoded["name"],
            lat=lat,
            lon=lon,
            bbox=bbox,
            stitched_image=current_stitched,
            height_px=540
        )
        components.html(globe_html, height=540, scrolling=False)
    else:
        polygon_coords = [
            [bbox[0], bbox[1]],
            [bbox[2], bbox[1]],
            [bbox[2], bbox[3]],
            [bbox[0], bbox[3]],
            [bbox[0], bbox[1]]
        ]
        polygon_layer = pdk.Layer(
            "PolygonLayer",
            data=[{"coordinates": [polygon_coords], "name": geocoded["name"]}],
            get_polygon="coordinates",
            get_fill_color=[0, 240, 255, 35],
            get_line_color=[0, 240, 255, 220],
            get_line_width=3,
            pickable=True
        )
        point_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [lon, lat], "name": geocoded["name"]}],
            get_position="position",
            get_color=[244, 63, 94, 230],
            get_radius=1800,
            pickable=True
        )
        deck = pdk.Deck(
            layers=[polygon_layer, point_layer],
            initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=10, pitch=35, bearing=0),
            map_style="dark",
            tooltip={"html": "<b>{name}</b><br>AOI Boundary Selected"}
        )
        st.pydeck_chart(deck, use_container_width=True)

    # -------------------------------------------------------------------------
    # SYNCHRONIZED CHRONOLOGICAL SATELLITE TIMELINE (AUTHENTIC STAC OBSERVATIONS)
    # -------------------------------------------------------------------------
    st.markdown(
        f"""
        <div style="font-size: 0.8rem; color: #00f0ff; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; margin-top: 14px; margin-bottom: 8px;">
            🛰️ Chronological Satellite Observations Archive — {len(discovered_scenes)} Live STAC Acquisitions for {geocoded['name']}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display timeline cards in columns (including mosaic card if present)
    has_mosaic = st.session_state.get("latest_sentinel_mosaic") is not None
    total_cards = len(discovered_scenes) + (1 if has_mosaic else 0)
    card_cols = st.columns(min(6, total_cards))

    col_idx = 0

    # 1. Mosaic Card (if generated)
    if has_mosaic:
        with card_cols[col_idx % len(card_cols)]:
            st.image(st.session_state["latest_sentinel_mosaic"], use_container_width=True)
            st.markdown(
                """
                <div style="font-size: 0.72rem; font-family: monospace; color: #34d399; text-align: center; margin-top: -4px;">
                    <strong>✨ FUSED MOSAIC</strong><br>
                    <span style="color: #38bdf8;">Multi-Tile 10m</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            col_idx += 1

    # 2. Individual Live STAC Observations
    for sc in discovered_scenes:
        with card_cols[col_idx % len(card_cols)]:
            is_active = (sc.id == primary_scene.id)
            thumb = sc.preview_url if sc.preview_url else "tile_left.jpg"
            st.image(thumb, use_container_width=True)
            
            border_color = "#00f0ff" if is_active else "#334155"
            active_badge = "<span class='tech-badge badge-cyan' style='font-size: 0.65rem; padding: 1px 4px;'>ACTIVE</span><br>" if is_active else ""
            
            st.markdown(
                f"""
                <div style="font-size: 0.70rem; font-family: monospace; color: {'#00f0ff' if is_active else '#94a3b8'}; text-align: center; margin-top: -4px;">
                    {active_badge}
                    <strong>{sc.date_str}</strong><br>
                    <span style="color: #64748b;">{sc.platform} (10m)</span><br>
                    <span style="color: #fbbf24;">☁️ {sc.cloud_cover:.1f}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if not is_active:
                if st.button("Select", key=f"btn_tl_sel_{sc.id[:18]}", use_container_width=True):
                    st.session_state["ee_selected_scene_id"] = sc.id
                    st.rerun()
            col_idx += 1

    # =========================================================================
    # STAGE 2: LIVE STAC DATA DISCOVERY & OBSERVATION SELECTOR
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🛰️ Stage 2: Selected Observation Assets & Mode")

    scene_options = {
        f"📅 {s.date_str} (Cloud: {s.cloud_cover:.1f}%) — {s.id[:38]}...": s
        for s in discovered_scenes
    }

    col_sel_obs, col_obs_mode = st.columns([2.2, 1.0])

    with col_sel_obs:
        current_opt_keys = list(scene_options.keys())
        default_idx = 0
        for i, k in enumerate(current_opt_keys):
            if scene_options[k].id == primary_scene.id:
                default_idx = i
                break
        selected_obs_label = st.selectbox(
            "Primary Observation to Stream & Process:",
            options=current_opt_keys,
            index=default_idx
        )
        if scene_options[selected_obs_label].id != primary_scene.id:
            st.session_state["ee_selected_scene_id"] = scene_options[selected_obs_label].id
            st.rerun()

    with col_obs_mode:
        obs_mode = st.radio(
            "Processing Workflow:",
            options=["Multi-Tile Georeferenced Mosaic", "Single Acquisition"],
            index=0,
            help="Multi-Tile Mosaic reprojects adjacent swaths, runs SIFT inlier diagnostics in the Stitching Laboratory, and merges them continuously."
        )

    # Inspect Selected Scene Assets
    inspection = inspect_sentinel2_assets(primary_scene)
    st.markdown(
        f"""
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; margin-bottom: 12px;">
            <div class="tech-badge badge-cyan">Scene: {primary_scene.id[:30]}...</div>
            <div class="tech-badge badge-emerald">Acquired: {primary_scene.date_str}</div>
            <div class="tech-badge badge-amber">Cloud: {primary_scene.cloud_cover:.1f}%</div>
            <div class="tech-badge badge-purple">Native CRS: {primary_scene.crs}</div>
            <div class="tech-badge {'badge-emerald' if inspection['is_analysis_ready'] else 'badge-amber'}">
                {'Bands B02, B03, B04, B08 Ready' if inspection['is_analysis_ready'] else 'Preview Mode'}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================================
    # STAGE 3: RETRIEVAL & STITCHING LABORATORY
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🗺️ Stage 3: Generate Georeferenced Mosaic & Preprocess")

    col_scale, col_stretch, col_fetch = st.columns([1.2, 1.2, 1.4])

    with col_scale:
        decim_scale = st.slider(
            "Decimation Factor (Preview Decimation)",
            min_value=4, max_value=24, value=12,
            help="Sub-samples full 10,980 x 10,980 10m bands for rapid raster streaming."
        )
    with col_stretch:
        reflectance_stretch = st.number_input(
            "Reflectance Stretch (DN)",
            min_value=1200.0, max_value=5000.0, value=2400.0, step=200.0
        )
    with col_fetch:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        btn_retrieve = st.button("🚀 Stream COGs & Build Mosaic", use_container_width=True, key="btn_ee_stream")

    obs_state_key = f"ee_obs_{primary_scene.id}_{decim_scale}_{obs_mode}"

    if btn_retrieve or obs_state_key in st.session_state:
        if btn_retrieve:
            with st.spinner(f"Streaming authentic Sentinel-2 COGs (B04, B03, B02, B08) for {geocoded['name']}..."):
                if obs_mode == "Single Acquisition" or len(discovered_scenes) < 2:
                    obs_data = retrieve_sentinel2_data(
                        primary_scene,
                        bands=["B04", "B03", "B02", "B08"],
                        decimation_scale=decim_scale,
                        stretch_val=reflectance_stretch
                    )
                    mosaic_data = build_georeferenced_mosaic([obs_data]) if obs_data else None
                else:
                    scenes_to_mosaic = discovered_scenes[:min(4, len(discovered_scenes))]
                    mosaic_data = build_real_sentinel2_mosaic(
                        scenes=scenes_to_mosaic,
                        target_crs=geocoded["target_utm"],
                        bbox=bbox,
                        decimation_scale=decim_scale,
                        stretch_val=reflectance_stretch
                    )
                    if not mosaic_data:
                        obs_data = retrieve_sentinel2_data(primary_scene, bands=["B04", "B03", "B02", "B08"], decimation_scale=decim_scale)
                        mosaic_data = build_georeferenced_mosaic([obs_data]) if obs_data else None

                if mosaic_data:
                    st.session_state[obs_state_key] = mosaic_data
                    st.session_state["latest_sentinel_mosaic"] = mosaic_data.rgb
                    st.rerun()
                else:
                    st.error("Failed to stream satellite bands. Try adjusting cloud threshold or decimation.")
                    return

        active_obs: ObservationData = st.session_state.get(obs_state_key)
        if not active_obs:
            st.info("Click 'Stream COGs & Build Mosaic' to retrieve multi-spectral satellite observation.")
            return

        h, w = active_obs.rgb.shape[:2]
        valid_px = int(np.count_nonzero(active_obs.valid_mask)) if active_obs.valid_mask is not None else h * w
        valid_coverage_pct = round(valid_px / (h * w) * 100.0, 1)

        # Overview View & Telemetry
        col_m_view, col_m_telemetry = st.columns([2.0, 1.2])

        with col_m_view:
            st.image(active_obs.rgb, caption=f"True Color (RGB B04-B03-B02) — {active_obs.date_str} [{w}×{h} px]", use_container_width=True)

        with col_m_telemetry:
            st.markdown(
                f"""
                <div class="telemetry-card">
                    <div style="font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">
                        Mosaic Processing Telemetry
                    </div>
                    <div style="font-size: 1.0rem; color: #38bdf8; font-weight: 600; margin-top: 4px;">
                        {active_obs.id[:32]}...
                    </div>
                    <div style="margin-top: 10px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #e2e8f0;">
                        Dimensions: <strong>{w} × {h} pixels</strong>
                    </div>
                    <div style="margin-top: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #34d399;">
                        Valid Data Coverage: <strong>{valid_coverage_pct}%</strong>
                    </div>
                    <div style="margin-top: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #a78bfa;">
                        Coordinate System: <strong>{active_obs.crs}</strong>
                    </div>
                    <div style="margin-top: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #f59e0b;">
                        Composite Mode: <strong>{'Multi-Tile Mosaic' if active_obs.is_composite else 'Single Scene'}</strong>
                    </div>
                    <div style="margin-top: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #64748b;">
                        Contributing Scenes: {len(active_obs.source_scenes)} tile(s)
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ---------------------------------------------------------------------
        # DEDICATED STITCHING LABORATORY | TILE ALIGNMENT AND MOSAICING
        # ---------------------------------------------------------------------
        if active_obs.stitching_lab is not None:
            lab: StitchingLaboratoryData = active_obs.stitching_lab

            st.markdown(
                """
                <div class="telemetry-card" style="margin-top: 18px; margin-bottom: 12px; border-left: 3px solid #38bdf8;">
                    <div style="font-size: 1.05rem; font-weight: 600; color: #00f0ff;">
                        🔬 Stitching Laboratory | Tile Alignment and Mosaicing
                    </div>
                    <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 4px;">
                        Step-by-step intermediate inspection of contributing satellite swaths: raw tiles, radiometric valid masks, 
                        geospatial reprojection, SIFT & RANSAC inlier verification, overlap blending, and seamless continuous raster fusion.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            lab_step = st.radio(
                "Laboratory Inspection Stage:",
                options=[
                    "1️⃣ Step A: Source Tiles & Swath Footprints",
                    "2️⃣ Step B: Preprocessing & Grid Alignment",
                    "3️⃣ Step C: Landmark SIFT & Inlier Verification",
                    "4️⃣ Step D: Geometric Overlap & Alpha/Checkerboard",
                    "5️⃣ Step E: Seamline Boundary & Final Continuous Mosaic"
                ],
                horizontal=True,
                index=0,
                key="ee_lab_step_radio"
            )

            if "1️⃣" in lab_step:
                st.markdown("#### Step A: Contributing Source Tiles")
                st.write(f"Detected **{len(lab.tiles)}** authentic Sentinel-2 swath tiles intersecting this geographic AOI.")
                
                tile_cols = st.columns(min(4, len(lab.tiles)))
                for idx, t in enumerate(lab.tiles):
                    with tile_cols[idx % len(tile_cols)]:
                        st.image(t.raw_rgb, caption=f"Tile {idx + 1}: {t.id[:24]}... ({t.date_str})", use_container_width=True)
                        st.markdown(
                            f"""
                            <div style="font-size: 0.72rem; font-family: monospace; color: #94a3b8;">
                                • Scene ID: <code>{t.id[:20]}...</code><br>
                                • Date: <strong>{t.date_str}</strong><br>
                                • Sensor: <strong>{t.platform}</strong><br>
                                • Cloud: <strong>{t.cloud_cover:.1f}%</strong><br>
                                • Native CRS: <strong>{t.raw_crs}</strong><br>
                                • Dimensions: <strong>{t.raw_shape[1]}×{t.raw_shape[0]} px</strong><br>
                                • Footprint: <code>[{t.bbox[0]:.2f}, {t.bbox[1]:.2f}, {t.bbox[2]:.2f}, {t.bbox[3]:.2f}]</code>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            elif "2️⃣" in lab_step:
                st.markdown("#### Step B: Radiometric & Grid Preprocessing")
                st.write("Inspecting raw pixel values, cloud & invalid pixel masks, and common UTM grid reprojection.")

                for idx, t in enumerate(lab.tiles):
                    st.markdown(f"**Tile {idx + 1} Pipeline:** `{t.id[:28]}...`")
                    c_p1, c_p2, c_p3 = st.columns(3)
                    with c_p1:
                        st.image(t.raw_rgb, caption=f"Raw True-Color [{t.raw_shape[1]}×{t.raw_shape[0]} px]", use_container_width=True)
                    with c_p2:
                        st.image(t.valid_mask, caption="Valid Data / Cloud Mask (255 = Clear, 0 = Void)", use_container_width=True)
                    with c_p3:
                        st.image(t.reprojected_rgb, caption=f"Reprojected to {t.reprojected_crs} [{t.reprojected_shape[1]}×{t.reprojected_shape[0]} px]", use_container_width=True)
                    st.markdown("<hr style='border-color: rgba(255,255,255,0.06); margin: 8px 0;'>", unsafe_allow_html=True)

            elif "3️⃣" in lab_step:
                st.markdown("#### Step C: Landmark & Feature Detection (SIFT & RANSAC)")
                if lab.correspondence is not None:
                    corr = lab.correspondence

                    # Diagnostics Strip
                    c_k1, c_k2, c_cand, c_inl, c_rat, c_err = st.columns(6)
                    c_k1.metric("Tile 1 Keypoints", f"{corr.num_kp1:,}")
                    c_k2.metric("Tile 2 Keypoints", f"{corr.num_kp2:,}")
                    c_cand.metric("Lowe's 0.75 Matches", corr.num_candidate_matches)
                    c_inl.metric("Verified Inliers", corr.num_inliers)
                    c_rat.metric("Inlier Ratio", f"{corr.inlier_ratio}%")
                    c_err.metric("Median Reproj Error", f"{corr.median_reprojection_error} px")

                    match_view = st.radio(
                        "Correspondence Visualization Mode:",
                        options=["All Correspondences (Green: Inliers, Red: Outliers)", "Verified Inliers Only", "Rejected Outliers Only"],
                        horizontal=True
                    )

                    if "All" in match_view:
                        st.image(corr.match_image_all, caption="Side-by-Side SIFT Matches (Green: RANSAC verified inliers | Red: Rejected outliers)", use_container_width=True)
                    elif "Inliers" in match_view:
                        st.image(corr.match_image_inliers, caption="Verified Landmark Inliers Across Tile Swaths", use_container_width=True)
                    else:
                        st.image(corr.match_image_outliers, caption="Rejected Outlier Matches", use_container_width=True)

                    st.markdown(
                        f"""
                        <div class="telemetry-card" style="margin-top: 10px; font-size: 0.75rem; color: #94a3b8;">
                            <strong>Analytical Note:</strong> Coordinate-based UTM reprojection serves as the primary spatial grid positioning 
                            for Sentinel-2 Level-2A products. Classical SIFT landmark matching operates across the seam overlap zone 
                            to verify geometric alignment continuity without inventing artificial deformations.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("Single-scene observation active. Multi-tile SIFT diagnostics activate when two or more swaths overlap.")

            elif "4️⃣" in lab_step:
                st.markdown("#### Step D: Geometric Alignment & Overlap Inspection")
                if lab.correspondence is not None:
                    corr = lab.correspondence

                    align_tab1, align_tab2 = st.tabs(["🎛️ Interactive Alpha-Blended Overlay", "🏁 Checkerboard Split View"])

                    with align_tab1:
                        c_sl, c_im = st.columns([1.2, 2.0])
                        with c_sl:
                            alpha_slider = st.slider("Tile 1 vs Tile 2 Alpha Blend (%):", 0, 100, 50, help="0% = 100% Tile 1 | 100% = 100% Tile 2 | 50% = Equal blend")
                            st.markdown(
                                f"""
                                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 10px;">
                                    Drag the slider to dynamically verify seamless continuity of linear features (roads, waterways, field boundaries) 
                                    across the overlapping swath region.
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        with c_im:
                            # Dynamic blend
                            t1_ov = lab.tiles[0].reprojected_rgb[:corr.overlap_shape[0], :corr.overlap_shape[1]]
                            t2_ov = lab.tiles[1].reprojected_rgb[:corr.overlap_shape[0], :corr.overlap_shape[1]]
                            a = alpha_slider / 100.0
                            dyn_blend = cv2.addWeighted(t1_ov, 1.0 - a, t2_ov, a, 0)
                            st.image(dyn_blend, caption=f"Overlap Alpha Blend ({100 - alpha_slider}% Tile 1 / {alpha_slider}% Tile 2)", use_container_width=True)

                    with align_tab2:
                        st.image(corr.checkerboard_comparison, caption="Alternating 32px Checkerboard Comparison (Inspect edge continuity across block boundaries)", use_container_width=True)

                else:
                    st.info("Single-scene observation active. Overlap alignment activates for multi-tile mosaics.")

            elif "5️⃣" in lab_step:
                st.markdown("#### Step E: Seamline Boundary & Final Continuous Mosaic")
                col_seam_ctrl, col_seam_view = st.columns([1.0, 2.2])

                with col_seam_ctrl:
                    show_seam = st.checkbox("Highlight Seamline Boundary Cut", value=True)
                    st.markdown(
                        f"""
                        <div class="telemetry-card" style="margin-top: 8px;">
                            <div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Fusion Diagnostics</div>
                            <div style="font-size: 0.85rem; color: #38bdf8; font-weight: 600; margin-top: 4px;">{lab.stitching_method}</div>
                            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 8px;">
                                • Target Coordinate System: <strong>{lab.crs}</strong><br>
                                • Final Grid Shape: <strong>{lab.final_shape[1]} × {lab.final_shape[0]} px</strong><br>
                                • Estimated AOI Area: <strong>{lab.coverage_km2} km²</strong><br>
                                • Overlap Resolution: <strong>Priority Valid Mask + Linear Feathering</strong>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col_seam_view:
                    display_img = lab.seamline_preview if show_seam else lab.merged_rgb
                    st.image(display_img, caption="Fused Georeferenced Continuous Mosaic" + (" (Cyan dashed cutline indicates swath seam boundary)" if show_seam else ""), use_container_width=True)

        # =========================================================================
        # STAGE 4: ENVIRONMENTAL COMPUTER VISION WORKSPACE
        # =========================================================================
        st.markdown("---")
        st.markdown("### 🌿 Stage 4: Environmental Computer Vision Workspace")

        env_layers: EnvironmentalLayers = calculate_environmental_layers(active_obs)
        stats = env_layers.stats

        # Metrics Strip
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Mean NDVI", f"{stats['mean_ndvi']:.3f}", help="Mean Normalized Difference Vegetation Index")
        c2.metric("Forest Canopy", f"{stats['forest_coverage_pct']}%", f"{stats['forest_area_km2']} km²", help="Dense Forest (> 0.45 NDVI)")
        c3.metric("Vegetation / Crops", f"{stats['vegetation_coverage_pct']}%", f"{stats['vegetation_area_km2']} km²", help="Moderate Canopy [0.20 - 0.45 NDVI]")
        c4.metric("Urban / Built-up", f"{stats['urban_built_pct']}%", f"{stats['urban_area_km2']} km²", help="Impervious Surfaces / High Albedo")
        c5.metric("Water Extent", f"{stats['water_extent_pct']}%", f"{stats['water_area_km2']} km²", help="NDWI McFeeters Water Index")

        # Layer Selection & Opacity Overlay Controller
        col_cv_sel, col_cv_op = st.columns([1.6, 1.4])

        with col_cv_sel:
            cv_layer_choice = st.selectbox(
                "Select Computer Vision Analytical Layer:",
                options=[
                    "🌿 NDVI Vegetation Canopy Index",
                    "🔴 Color-Infrared False Color (CIR NIR-R-G)",
                    "💧 NDWI Surface Water Extent (McFeeters)",
                    "🏙️ NDBI Urban / Built-Up Impervious Index",
                    "🗺️ Multi-Spectral Physical Land Cover",
                    "👥 Gridded Population Density Overlay"
                ],
                index=0
            )

        with col_cv_op:
            overlay_opacity = st.slider(
                "Overlay Opacity (%) over Satellite Imagery:",
                min_value=0, max_value=100, value=75, step=5,
                help="0% = Pure True-Color Satellite Imagery | 100% = Pure Computer Vision Mask | 50% = Semi-transparent overlay"
            )

        alpha = overlay_opacity / 100.0
        bg_rgb = active_obs.rgb

        # Render Selected Layer
        if "NDVI" in cv_layer_choice:
            col_v1, col_v2 = st.columns([2.0, 1.1])
            with col_v1:
                # Colorize NDVI
                ndvi_valid = np.nan_to_num(env_layers.ndvi, nan=0.0)
                norm_ndvi = np.clip((ndvi_valid + 0.2) / 1.0, 0, 1)
                ndvi_cmap = plt.cm.RdYlGn(norm_ndvi)[:, :, :3]
                ndvi_colored = (ndvi_cmap * 255.0).astype(np.uint8)

                blended = (bg_rgb * (1.0 - alpha) + ndvi_colored * alpha).astype(np.uint8)

                fig, ax = plt.subplots(figsize=(10, 5.8))
                fig.patch.set_facecolor('#070b14')
                ax.set_facecolor('#070b14')
                im = ax.imshow(blended)
                ax.set_title(f"NDVI Vegetation Canopy Index — Sentinel-2 ({active_obs.date_str}) [Opacity: {overlay_opacity}%]", color="#00f0ff", fontsize=11, fontfamily='monospace')
                ax.axis("off")

                # Colorbar
                sm = plt.cm.ScalarMappable(cmap="RdYlGn", norm=plt.Normalize(vmin=-0.2, vmax=0.8))
                sm.set_array([])
                cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
                cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
                cbar.set_label("NDVI: Water (<0) | Barren (0-0.2) | Shrub/Crop (0.2-0.45) | Dense Forest (>0.45)", color="#94a3b8", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

            with col_v2:
                # NDVI Histogram & Stats
                fig_h, ax_h = plt.subplots(figsize=(5, 3.5))
                fig_h.patch.set_facecolor('#070b14')
                ax_h.set_facecolor('#070b14')
                vals = env_layers.ndvi[~np.isnan(env_layers.ndvi)].flatten()
                ax_h.hist(vals, bins=40, range=(-0.2, 0.9), color="#34d399", alpha=0.85, edgecolor="#070b14")
                ax_h.set_title("NDVI Pixel Distribution", color="#00f0ff", fontsize=9, fontfamily='monospace')
                ax_h.tick_params(colors="#94a3b8", labelsize=7)
                for spine in ax_h.spines.values():
                    spine.set_color("#334155")
                plt.tight_layout()
                st.pyplot(fig_h)
                plt.close(fig_h)

                st.markdown(
                    f"""
                    <div class="telemetry-card" style="font-size: 0.72rem; color: #94a3b8;">
                        <strong>Vegetation Metrics:</strong><br>
                        • Mean NDVI: <strong>{stats['mean_ndvi']}</strong><br>
                        • Median NDVI: <strong>{stats['median_ndvi']}</strong><br>
                        • Forest Area: <strong>{stats['forest_area_km2']} km²</strong> ({stats['forest_coverage_pct']}%)<br>
                        • Total Mapped Area: <strong>{stats['total_area_km2']} km²</strong><br>
                        <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                        <strong>Formula:</strong> <code>(NIR - Red) / (NIR + Red)</code><br>
                        <em>NDVI reflects green photosynthetic activity / chlorophyll vigor, not direct tree count or biomass.</em>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        elif "False Color" in cv_layer_choice:
            if active_obs.cir is not None:
                st.image(
                    active_obs.cir,
                    caption="Color-Infrared Composite (NIR B08 → Red, Red B04 → Green, Green B03 → Blue) — Vibrant crimson highlights healthy vegetative canopy",
                    use_container_width=True
                )
            else:
                st.warning("False-color CIR requires NIR Band 08 streaming.")

        elif "NDWI" in cv_layer_choice:
            col_w1, col_w2 = st.columns([2.0, 1.1])
            with col_w1:
                ndwi_valid = np.nan_to_num(env_layers.ndwi, nan=0.0)
                norm_ndwi = np.clip((ndwi_valid + 0.4) / 0.8, 0, 1)
                ndwi_cmap = plt.cm.Blues(norm_ndwi)[:, :, :3]
                ndwi_colored = (ndwi_cmap * 255.0).astype(np.uint8)

                blended = (bg_rgb * (1.0 - alpha) + ndwi_colored * alpha).astype(np.uint8)

                fig, ax = plt.subplots(figsize=(10, 5.8))
                fig.patch.set_facecolor('#070b14')
                ax.set_facecolor('#070b14')
                im = ax.imshow(blended)
                ax.set_title(f"NDWI McFeeters Surface Water Extent — Sentinel-2 ({active_obs.date_str})", color="#38bdf8", fontsize=11, fontfamily='monospace')
                ax.axis("off")
                sm = plt.cm.ScalarMappable(cmap="Blues", norm=plt.Normalize(vmin=-0.4, vmax=0.4))
                sm.set_array([])
                cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
                cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
                cbar.set_label("NDWI: Non-Water (<0) | Open Surface Water Bodies (>0)", color="#94a3b8", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

            with col_w2:
                st.markdown(
                    f"""
                    <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8;">
                        <strong>Water Extent Telemetry:</strong><br>
                        • Water Extent: <strong>{stats['water_extent_pct']}%</strong><br>
                        • Mapped Water Area: <strong>{stats['water_area_km2']} km²</strong><br>
                        • Sensor Formula: <code>(Green - NIR) / (Green + NIR)</code><br>
                        <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                        <strong>McFeeters Threshold:</strong> Delineates open surface water bodies including lakes, reservoirs, and major rivers.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        elif "NDBI" in cv_layer_choice:
            col_b1, col_b2 = st.columns([2.0, 1.1])
            with col_b1:
                ndbi_valid = np.nan_to_num(env_layers.ndbi, nan=0.0)
                norm_ndbi = np.clip((ndbi_valid + 0.3) / 0.6, 0, 1)
                ndbi_cmap = plt.cm.magma(norm_ndbi)[:, :, :3]
                ndbi_colored = (ndbi_cmap * 255.0).astype(np.uint8)

                blended = (bg_rgb * (1.0 - alpha) + ndbi_colored * alpha).astype(np.uint8)

                fig, ax = plt.subplots(figsize=(10, 5.8))
                fig.patch.set_facecolor('#070b14')
                ax.set_facecolor('#070b14')
                im = ax.imshow(blended)
                ax.set_title(f"Built-Up / Impervious Surface Index (NDBI Urban Proxy) — {stats['urban_built_pct']}% Urban", color="#f43f5e", fontsize=11, fontfamily='monospace')
                ax.axis("off")
                sm = plt.cm.ScalarMappable(cmap="magma", norm=plt.Normalize(vmin=-0.3, vmax=0.3))
                sm.set_array([])
                cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
                cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
                cbar.set_label("NDBI: Low Albedo (<0) | Built-Up Impervious / High Albedo (>0)", color="#94a3b8", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

            with col_b2:
                st.markdown(
                    f"""
                    <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8;">
                        <strong>Built-Up Footprint Telemetry:</strong><br>
                        • Urban Impervious Coverage: <strong>{stats['urban_built_pct']}%</strong><br>
                        • Mapped Urban Area: <strong>{stats['urban_area_km2']} km²</strong><br>
                        • Proxy: High visible albedo & low photosynthetic absorption<br>
                        <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                        <strong>Limitations:</strong> Distinguishes dense built-up fabric and paved infrastructure from vegetative surfaces at 10m spatial resolution.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        elif "Land Cover" in cv_layer_choice:
            cmap_lc = mcolors.ListedColormap(['#1e40af', '#15803d', '#84cc16', '#dc2626', '#d97706'])
            fig, ax = plt.subplots(figsize=(10, 5.8))
            fig.patch.set_facecolor('#070b14')
            ax.set_facecolor('#070b14')
            im = ax.imshow(env_layers.landcover, cmap=cmap_lc, vmin=0, vmax=4)
            ax.set_title(f"Rule-Based Multi-Spectral Land Cover Classification (Sentinel-2 10m)", color="#a855f7", fontsize=11, fontfamily='monospace')
            ax.axis("off")

            labels = [
                f"Water: {stats['water_extent_pct']}% ({stats['water_area_km2']} km²)",
                f"Dense Forest: {stats['forest_coverage_pct']}% ({stats['forest_area_km2']} km²)",
                f"Crops/Grass: {stats['vegetation_coverage_pct']}% ({stats['vegetation_area_km2']} km²)",
                f"Built-up: {stats['urban_built_pct']}% ({stats['urban_area_km2']} km²)",
                f"Bare Soil: {stats['bare_soil_pct']}%"
            ]
            patches = [plt.plot([], [], marker="s", color=cmap_lc(i), ls="", label=labels[i])[0] for i in range(5)]
            ax.legend(handles=patches, loc="lower right", facecolor="#0f172a", edgecolor="#334155", labelcolor="#f1f5f9", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        elif "Population" in cv_layer_choice:
            col_p1, col_p2 = st.columns([2.0, 1.1])
            with col_p1:
                fig, ax = plt.subplots(figsize=(10, 5.8))
                fig.patch.set_facecolor('#070b14')
                ax.set_facecolor('#070b14')
                im = ax.imshow(env_layers.population_density, cmap="YlOrRd", vmin=0, vmax=15000)
                ax.set_title(f"Gridded Population Density Proxy (persons / km²)", color="#f59e0b", fontsize=11, fontfamily='monospace')
                ax.axis("off")
                cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
                cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
                cbar.set_label("Estimated Population Density (persons / km²)", color="#94a3b8", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

            with col_p2:
                st.markdown(
                    f"""
                    <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8;">
                        <strong>Population Layer Provenance:</strong><br>
                        • Mean Density: <strong>{stats['mean_population_density']:,.0f} / km²</strong><br>
                        • Estimated AOI Pop: <strong>{stats['estimated_total_population']:,}</strong><br>
                        • Data Source: <strong>GPWv4 / WorldPop Reference Model</strong><br>
                        • Resolution: <strong>1 km / Sentinel-2 Dasymetric</strong><br>
                        <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                        <strong>Important Note:</strong> Population density is an external modeled demographic layer, not directly measured by optical sensors.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # =========================================================================
        # STAGE 5: CONDITIONAL BI-TEMPORAL CAPABILITIES
        # =========================================================================
        st.markdown("---")
        st.markdown("### ↔️ Stage 5: Optional Bi-Temporal Comparison & Change Detection")

        st.markdown(
            """
            *Temporal comparison is a conditional extension enabled when two distinct, verified observations 
            are selected, aligned to a shared grid, and masked for common valid data.*
            """
        )

        avail_other_scenes = [s for s in discovered_scenes if s.id != primary_scene.id]

        if not avail_other_scenes:
            st.info(
                "ℹ️ **Single-Observation Mode Active:** No secondary scene available in this query window. "
                "Select a broader epoch (e.g. 'Full Archive') to enable multi-epoch temporal comparison."
            )
        else:
            other_options = {
                f"📅 {s.date_str} (Cloud: {s.cloud_cover:.1f}%) — {s.id[:35]}...": s
                for s in avail_other_scenes
            }

            col_t2_sel, col_t2_btn = st.columns([2.2, 1.2])
            with col_t2_sel:
                selected_t2_label = st.selectbox(
                    "Select Secondary Comparison Epoch (t0 / Historical):",
                    options=list(other_options.keys()),
                    index=len(other_options) - 1
                )
                secondary_scene = other_options[selected_t2_label]

            with col_t2_btn:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                btn_align_temporal = st.button("⚖️ Align Grid & Run ΔNDVI Change", use_container_width=True)

            t2_state_key = f"ee_t2_{secondary_scene.id}_{decim_scale}"

            if btn_align_temporal or t2_state_key in st.session_state:
                if btn_align_temporal:
                    with st.spinner(f"Retrieving second epoch ({secondary_scene.date_str}) and harmonizing common spatial grid..."):
                        t2_obs = retrieve_sentinel2_data(
                            secondary_scene,
                            decimation_scale=decim_scale,
                            stretch_val=reflectance_stretch
                        )
                        if t2_obs:
                            st.session_state[t2_state_key] = t2_obs
                        else:
                            st.error("Failed to retrieve secondary scene.")

                obs_t2 = st.session_state.get(t2_state_key)
                if obs_t2:
                    crop0, crop1, delta_ndvi, t_meta = align_bitemporal_observations(obs_t2, active_obs)

                    st.success(
                        f"✅ Harmonized Bi-Temporal Grid: {obs_t2.date_str} (t0) vs {active_obs.date_str} (t1) | "
                        f"Common Overlap: {t_meta['overlap_pct']}% ({t_meta['target_shape'][1]}×{t_meta['target_shape'][0]} px)"
                    )

                    col_comp_img, col_comp_delta = st.columns(2)
                    with col_comp_img:
                        st.write(f"**Epoch t0:** `{obs_t2.date_str}` vs **Epoch t1:** `{active_obs.date_str}`")
                        st.image(crop1, caption=f"Aligned Scene t1 ({active_obs.date_str})", use_container_width=True)

                    with col_comp_delta:
                        fig, ax = plt.subplots(figsize=(8, 5))
                        fig.patch.set_facecolor('#070b14')
                        ax.set_facecolor('#070b14')
                        im = ax.imshow(delta_ndvi, cmap="coolwarm_r", vmin=-0.35, vmax=0.35)
                        ax.set_title(f"ΔNDVI Vegetation Change Map\nGain: {t_meta['vegetation_gain_pct']}% | Loss: {t_meta['vegetation_loss_pct']}%", color="#00f0ff", fontsize=10, fontfamily='monospace')
                        ax.axis("off")
                        cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
                        cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
                        cbar.set_label("Blue = Canopy Gain | Red = Canopy Depletion", color="#94a3b8", fontsize=8)
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)

        # =========================================================================
        # STAGE 6: EVIDENCE-BASED AI ENVIRONMENTAL INVESTIGATION
        # =========================================================================
        st.markdown("---")
        st.markdown("### 🧠 Stage 6: Evidence-Based AI Environmental Investigation")

        st.markdown(
            """
            *Ask targeted questions regarding the measured environmental indicators. 
            The investigator strictly distinguishes empirical sensor measurements from external knowledge and unknowns.*
            """
        )

        sample_questions = [
            "What does the vegetation index indicate in this area?",
            "Which areas have the highest and lowest NDVI?",
            "What land-cover classes are supported by the available analysis?",
            "What is the source and date of the displayed population layer?"
        ]

        q_cols = st.columns(4)
        selected_q = None
        for i, sq in enumerate(sample_questions):
            with q_cols[i]:
                if st.button(sq, key=f"btn_sq_{i}"):
                    selected_q = sq

        user_q = st.text_input(
            "Or ask any question about the retrieved observation:",
            value=selected_q if selected_q else "What does the vegetation index indicate in this area?"
        )

        if st.button("💬 Run AI Investigation", key="btn_run_ai_ee"):
            _render_ai_investigation_response(user_q, active_obs, env_layers, geocoded)


def _render_ai_investigation_response(
    question: str,
    obs: ObservationData,
    layers: EnvironmentalLayers,
    geocoded: dict
):
    stats = layers.stats
    q_lower = question.lower()

    measured_facts = []
    external_context = []
    unknowns = []

    # 1. Measured Results
    measured_facts.append(f"Observation Date: {obs.date_str} (Cloud cover: {obs.cloud_cover:.1f}%)")
    measured_facts.append(f"Mean NDVI: {stats['mean_ndvi']} across {stats['valid_pixels']:,} valid pixels")
    measured_facts.append(f"Median NDVI: {stats['median_ndvi']}")
    measured_facts.append(f"Forest Canopy Coverage: {stats['forest_coverage_pct']}% ({stats['forest_area_km2']} km²)")
    measured_facts.append(f"Vegetation / Crop Coverage: {stats['vegetation_coverage_pct']}% ({stats['vegetation_area_km2']} km²)")
    measured_facts.append(f"Impervious Urban Footprint: {stats['urban_built_pct']}% ({stats['urban_area_km2']} km²)")
    measured_facts.append(f"Open Surface Water: {stats['water_extent_pct']}% ({stats['water_area_km2']} km²)")

    # 2. External Facts
    if "population" in q_lower:
        external_context.append("Population data is derived from GPWv4 / WorldPop calibrated baseline model.")
        external_context.append("It uses dasymetric spatial disaggregation rather than direct optical sensor measurements.")
        external_context.append(f"Estimated regional population in AOI: ~{stats['estimated_total_population']:,} residents.")
    elif "land-cover" in q_lower or "classes" in q_lower:
        external_context.append("Supported classes: 0 = Water, 1 = Dense Forest, 2 = Cropland/Shrub, 3 = Built-up Urban, 4 = Barren/Soil.")
        external_context.append("Thresholds are aligned with European Space Agency (ESA) WorldCover 10m specifications.")
    else:
        external_context.append(f"Location: {geocoded['name']} ({geocoded['target_utm']}).")
        external_context.append("Sentinel-2 MultiSpectral Instrument (MSI) provides 10m visible (B02, B03, B04) and near-infrared (B08) reflectance.")

    # 3. Unknowns
    if "why" in q_lower or "cause" in q_lower or "historical" in q_lower:
        unknowns.append("Root cause cannot be definitively proven from a single-epoch observation.")
        unknowns.append("Requires multi-temporal observation pair, local precipitation history, and municipal zoning records.")
    else:
        unknowns.append("Sub-pixel canopy moisture variations below 10m spatial resolution.")

    st.markdown(
        f"""
        <div class="telemetry-card" style="margin-top: 12px;">
            <div style="font-size: 0.9rem; font-weight: 600; color: #00f0ff; margin-bottom: 8px;">
                🔍 AI Environmental Synthesis: "{question}"
            </div>
            
            <div style="margin-top: 8px;">
                <span class="tech-badge badge-emerald">1. Measured Sensor Results (Empirical)</span>
                <ul style="color: #f1f5f9; font-size: 0.85rem; margin-top: 4px;">
                    {''.join(f'<li>{f}</li>' for f in measured_facts)}
                </ul>
            </div>

            <div style="margin-top: 10px;">
                <span class="tech-badge badge-cyan">2. Documented External Context & Methods</span>
                <ul style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                    {''.join(f'<li>{c}</li>' for c in external_context)}
                </ul>
            </div>

            <div style="margin-top: 10px;">
                <span class="tech-badge badge-amber">3. Unknowns & Analytical Boundaries</span>
                <ul style="color: #fbbf24; font-size: 0.85rem; margin-top: 4px;">
                    {''.join(f'<li>{u}</li>' for u in unknowns)}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
