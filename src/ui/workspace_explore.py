"""TerraPulse v2.0 Workspace 1: Explore.

Capabilities:
- Location Search & Geocoding (Popular cities + Global coordinates)
- Interactive 3D Orbital Globe with clamped georeferenced square mosaic
- 2D Bounding Box AOI Projection
- Live STAC Observation Discovery (Planetary Computer & Copernicus)
- Chronological Satellite Observations Timeline (100% unique keys)
- Automated 2x2 Spatial Quadrant Detection (NW, NE, SW, SE)
- Seamless Georeferenced Square Mosaic Generation
"""

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pydeck as pdk

from src.data.state_manager import AppStateManager, POPULAR_LOCATIONS, HISTORICAL_EPOCHS
from src.ui.globe_component import build_3d_globe_html


def render_workspace_explore():
    """Renders the unified Explore workspace."""
    AppStateManager.init_state()

    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🌍 Workspace 1: Explore & Discover</div>
            <div>
                <span class="tech-badge badge-cyan">Automated 2×2 Quadrant Finder</span>
                <span class="tech-badge badge-emerald">3D Orbital Globe</span>
                <span class="tech-badge badge-purple">Real STAC Catalogue</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        Search any global region to query live optical satellite observations.
        The platform **automatically detects 4 spatial quadrants** (NW, NE, SW, SE), harmonizes them onto a shared grid,
        and fuses them into a continuous georeferenced square mosaic displayed on the 3D globe.
        """
    )

    # -------------------------------------------------------------------------
    # 1. LOCATION SEARCH & POPULAR REGIONS
    # -------------------------------------------------------------------------
    col_srch, col_pop = st.columns([2.2, 1.2])

    current_geo = AppStateManager.get_geocoded()
    current_query = st.session_state.get(AppStateManager.KEY_LOCATION_QUERY, current_geo["name"])

    with col_srch:
        with st.form(key="tp2_location_search_form"):
            c_input, c_btn = st.columns([3.2, 1.0])
            with c_input:
                typed_loc = st.text_input(
                    "Search City, Address, or Geographic Coordinates:",
                    value=current_query,
                    placeholder="e.g. Bengaluru, Cairo, Tokyo, Paris, Zurich...",
                    help="Accepts city names, regions, or decimal coordinates (e.g. 12.9716, 77.5946)"
                )
            with c_btn:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("🔍 Locate", use_container_width=True)

            if submitted and typed_loc.strip() != current_query.strip():
                AppStateManager.set_location(typed_loc)
                st.rerun()

    with col_pop:
        st.write("Popular Global Regions:")
        pop_cols = st.columns(3)
        for idx, (p_lbl, p_val) in enumerate(list(POPULAR_LOCATIONS.items())[:6]):
            with pop_cols[idx % 3]:
                if st.button(p_lbl, key=f"btn_pop_explore_{idx}_{p_lbl[:4]}"):
                    AppStateManager.set_location(p_val)
                    st.rerun()

    # Re-fetch active geocoded info
    geocoded = AppStateManager.get_geocoded()
    lat, lon = geocoded["lat"], geocoded["lon"]
    bbox = geocoded["bbox"]

    # -------------------------------------------------------------------------
    # 2. TELEMETRY & COORDINATE BAR
    # -------------------------------------------------------------------------
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
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Target UTM Grid:</span>
                    <strong style="color: #34d399; font-family: monospace; font-size: 0.85rem; margin-left: 6px;">{geocoded['target_utm']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Estimated Area:</span>
                    <strong style="color: #fbbf24; font-family: monospace; font-size: 0.85rem; margin-left: 6px;">~{geocoded['est_area_km2']:,} km²</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">2×2 AOI Bounds:</span>
                    <code style="color: #a78bfa; font-size: 0.78rem;">[{bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f}]</code>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------------------
    # 3. QUERY PARAMETERS
    # -------------------------------------------------------------------------
    col_prov, col_ep, col_cld, col_dec = st.columns([1.2, 1.2, 1.0, 0.8])
    with col_prov:
        prov_opt = ["Planetary Computer (Streaming COGs)", "Copernicus Data Space (ESA CDSE)"]
        cur_prov = st.session_state.get(AppStateManager.KEY_STAC_PROVIDER, prov_opt[0])
        idx_prov = prov_opt.index(cur_prov) if cur_prov in prov_opt else 0
        new_prov = st.selectbox("Satellite Provider:", options=prov_opt, index=idx_prov, key="sel_prov_explore")
        if new_prov != cur_prov:
            st.session_state[AppStateManager.KEY_STAC_PROVIDER] = new_prov
            st.session_state.pop(AppStateManager.KEY_DISCOVERED_SCENES, None)
            st.rerun()

    with col_ep:
        epoch_opts = list(HISTORICAL_EPOCHS.keys())
        cur_epoch = st.session_state.get(AppStateManager.KEY_EPOCH_LABEL, epoch_opts[0])
        idx_epoch = epoch_opts.index(cur_epoch) if cur_epoch in epoch_opts else 0
        new_epoch = st.selectbox("Acquisition Epoch / Date Range:", options=epoch_opts, index=idx_epoch, key="sel_epoch_explore")
        if new_epoch != cur_epoch:
            st.session_state[AppStateManager.KEY_EPOCH_LABEL] = new_epoch
            st.session_state.pop(AppStateManager.KEY_DISCOVERED_SCENES, None)
            st.rerun()

    with col_cld:
        cur_cloud = float(st.session_state.get(AppStateManager.KEY_MAX_CLOUD, 25.0))
        new_cloud = st.slider("Max Cloud Cover (%)", min_value=0.0, max_value=80.0, value=cur_cloud, step=5.0, key="sld_cloud_explore")
        if new_cloud != cur_cloud:
            st.session_state[AppStateManager.KEY_MAX_CLOUD] = new_cloud
            st.session_state.pop(AppStateManager.KEY_DISCOVERED_SCENES, None)
            st.rerun()

    with col_dec:
        cur_dec = int(st.session_state.get(AppStateManager.KEY_DECIMATION, 12))
        new_dec = st.slider("Decimation", min_value=4, max_value=24, value=cur_dec, step=2, key="sld_dec_explore", help="Sampling factor for responsive COG streaming.")
        if new_dec != cur_dec:
            st.session_state[AppStateManager.KEY_DECIMATION] = new_dec
            st.session_state.pop(AppStateManager.KEY_PRIMARY_MOSAIC, None)
            st.rerun()

    # -------------------------------------------------------------------------
    # 4. DISCOVER LIVE SCENES & GENERATE MOSAIC
    # -------------------------------------------------------------------------
    with st.spinner(f"Querying live Sentinel-2 catalogue around '{geocoded['name']}'..."):
        discovered_scenes = AppStateManager.ensure_discovered_scenes()

    if not discovered_scenes:
        st.warning(
            f"⚠️ No Sentinel-2 observations found with cloud cover < {new_cloud}% in '{new_epoch}'. "
            "Please broaden the date range or increase the max cloud cover slider."
        )
        return

    # Automatically identify 4 quadrants & stitch mosaic
    auto_4_scenes = AppStateManager.get_auto_4_scenes()

    with st.spinner(f"✨ Generating 4-quadrant fused square mosaic for {geocoded['name']}..."):
        active_mosaic = AppStateManager.ensure_primary_mosaic()

    current_stitched_img = active_mosaic.rgb if active_mosaic else st.session_state.get("latest_sentinel_mosaic")
    if current_stitched_img is None and auto_4_scenes and auto_4_scenes[0].preview_url:
        current_stitched_img = auto_4_scenes[0].preview_url

    # -------------------------------------------------------------------------
    # 5. 3D GLOBE VS 2D BOUNDARY PROJECTION
    # -------------------------------------------------------------------------
    c_mode1, c_mode2 = st.columns([2.2, 1.0])
    with c_mode1:
        st.markdown(
            """
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 6px;">
                <strong style="color: #00f0ff;">3D Spherical Surface Projection:</strong> The automatically stitched 4-tile square mosaic is curved and clamped directly onto the 3D Earth globe surface. Click <strong>[Zoom to Region]</strong> to fly down or <strong>[Full Orbit]</strong> to inspect the planet.
            </div>
            """,
            unsafe_allow_html=True
        )
    with c_mode2:
        globe_view_mode = st.radio(
            "Visualization Mode:",
            options=["🌍 3D Orbital Globe (Clamped)", "🗺️ 2D AOI Boundary"],
            horizontal=True,
            index=0,
            key="rad_globe_view_explore"
        )

    if globe_view_mode == "🌍 3D Orbital Globe (Clamped)":
        globe_html = build_3d_globe_html(
            target_name=geocoded["name"],
            lat=lat,
            lon=lon,
            bbox=bbox,
            stitched_image=current_stitched_img,
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
    # 6. SYNCHRONIZED CHRONOLOGICAL OBSERVATIONS TIMELINE
    # -------------------------------------------------------------------------
    st.markdown(
        f"""
        <div style="font-size: 0.8rem; color: #00f0ff; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; margin-top: 14px; margin-bottom: 8px;">
            🛰️ Chronological Satellite Observations Archive — {len(discovered_scenes)} Acquisitions for {geocoded['name']}
        </div>
        """,
        unsafe_allow_html=True
    )

    total_cards = len(discovered_scenes) + (1 if active_mosaic else 0)
    card_cols = st.columns(min(6, total_cards))
    col_idx = 0

    # 1. Mosaic Card (Active fused square map)
    cur_sel_id = st.session_state.get(AppStateManager.KEY_PRIMARY_OBS_ID, "mosaic")
    if active_mosaic is not None:
        with card_cols[col_idx % len(card_cols)]:
            st.image(active_mosaic.rgb, use_container_width=True)
            is_active_mosaic = (cur_sel_id == "mosaic")
            st.markdown(
                f"""
                <div style="font-size: 0.72rem; font-family: monospace; color: {'#34d399' if is_active_mosaic else '#94a3b8'}; text-align: center; margin-top: -4px;">
                    <span class='tech-badge {"badge-emerald" if is_active_mosaic else "badge-cyan"}' style='font-size: 0.65rem; padding: 1px 4px;'>
                        {"ACTIVE 2×2 MOSAIC" if is_active_mosaic else "FUSED MOSAIC"}
                    </span><br>
                    <strong>✨ FUSED SQUARE TILE</strong><br>
                    <span style="color: #38bdf8;">4 Quadrants 10m</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Select Mosaic", key="btn_sel_mosaic_primary", use_container_width=True, disabled=is_active_mosaic):
                AppStateManager.set_selected_observation_id("mosaic")
                st.rerun()

            col_idx += 1

    # 2. Individual STAC Observations
    auto_4_ids = set(s.id for s in auto_4_scenes)
    for sc in discovered_scenes:
        with card_cols[col_idx % len(card_cols)]:
            is_contributing = (sc.id in auto_4_ids)
            is_selected = (cur_sel_id == sc.id)
            thumb = sc.preview_url if sc.preview_url else "tile_left.jpg"
            st.image(thumb, use_container_width=True)

            badge = "<span class='tech-badge badge-cyan' style='font-size: 0.62rem; padding: 1px 4px;'>QUADRANT TILE</span><br>" if is_contributing else ""

            st.markdown(
                f"""
                <div style="font-size: 0.70rem; font-family: monospace; color: {'#00f0ff' if is_selected else '#94a3b8'}; text-align: center; margin-top: -4px;">
                    {badge}
                    <strong>{sc.date_str}</strong><br>
                    <span style="color: #64748b;">{sc.platform} (10m)</span><br>
                    <span style="color: #fbbf24;">☁️ {sc.cloud_cover:.1f}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            unique_btn_key = f"btn_exp_sc_{col_idx}_{sc.id}"
            if st.button("Inspect", key=unique_btn_key, use_container_width=True, disabled=is_selected):
                AppStateManager.set_selected_observation_id(sc.id)
                st.rerun()

            col_idx += 1

    # -------------------------------------------------------------------------
    # 7. AUTOMATICALLY DETECTED 4-TILE QUADRANTS
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🧩 Automatically Detected 4-Tile Quadrants")
    q_labels = ["North-West (Tile 1)", "North-East (Tile 2)", "South-West (Tile 3)", "South-East (Tile 4)"]
    q_cols = st.columns(4)
    for idx, sc in enumerate(auto_4_scenes[:4]):
        with q_cols[idx]:
            parts = sc.id.split('_')
            tc = [p for p in parts if p.startswith('T') and len(p) == 6]
            code = tc[0] if tc else sc.id[:12]
            st.markdown(
                f"""
                <div class="telemetry-card" style="padding: 10px 12px; margin-bottom: 8px;">
                    <div style="font-size: 0.70rem; color: #38bdf8; font-weight: 600; font-family: monospace;">{q_labels[idx]}</div>
                    <div style="font-size: 0.85rem; color: #f1f5f9; font-weight: 700; margin-top: 2px;">{code}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">
                        • Date: <strong>{sc.date_str}</strong><br>
                        • Cloud: <strong>{sc.cloud_cover:.1f}%</strong><br>
                        • Platform: <strong>{sc.platform}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
