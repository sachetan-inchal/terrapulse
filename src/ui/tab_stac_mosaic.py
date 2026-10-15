"""Sentinel-2 Cloud STAC 2x2 Grid Stitcher Component.

Live streaming of Sentinel-2 L2A Cloud-Optimized GeoTIFFs (COGs) from Microsoft
Planetary Computer STAC, dynamic geocoding of any typed location, cross-UTM reprojection,
on-the-fly decimation, and 2x2 raster mosaicking.
"""

import os
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from src.data.sentinel_service import geocode_user_location

DEFAULT_PRESETS = {
    "Swiss Alps": "Swiss Alps (Snow & Mountains)",
    "Bengaluru": "Bengaluru, Karnataka, India",
    "Grand Canyon": "Grand Canyon, Arizona, USA",
    "Nile Delta": "Nile Delta & Cairo, Egypt",
    "Tokyo Bay": "Tokyo Bay Megalopolis, Japan",
    "Paris": "Paris, Île-de-France, France",
    "Dubai": "Dubai, United Arab Emirates"
}

def render_tab_stac_mosaic():
    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🌐 Planetary STAC 2×2 Mosaic Engine (Sentinel-2 L2A)</div>
            <div>
                <span class="tech-badge badge-cyan">Planetary Computer STAC</span>
                <span class="tech-badge badge-emerald">Real Sentinel-2 L2A COGs</span>
                <span class="tech-badge badge-purple">Cross-UTM Warping</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Convert any typed location into verified coordinates and stream multi-spectral Sentinel-2 satellite data 
        directly from Microsoft Planetary Computer cloud storage. Applies geodetic reprojection across UTM zone boundaries 
        and fuses overlapping tiles into an aligned 2×2 continuous mosaic.
        """
    )

    # 1. Location Search Strip
    st.markdown("### 📍 Location Geocoding & Region of Interest (AOI)")
    
    col_search, col_presets = st.columns([2, 1.2])
    
    with col_search:
        with st.form(key="stac_loc_form"):
            c_inp, c_sub = st.columns([3, 1.2])
            with c_inp:
                current_query = st.session_state.get("stac_mosaic_query", "Bengaluru, Karnataka, India")
                typed_query = st.text_input(
                    "Type ANY City, Region, or Coordinates:",
                    value=current_query,
                    placeholder="e.g. Cairo, Tokyo, Paris, Bengaluru, Dubai..."
                )
            with c_sub:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                loc_submitted = st.form_submit_button("🔍 Geocode", use_container_width=True)
            if loc_submitted:
                st.session_state["stac_mosaic_query"] = typed_query

    with col_presets:
        st.write("Popular Study Regions:")
        preset_cols = st.columns(4)
        for idx, (lbl, full_val) in enumerate(list(DEFAULT_PRESETS.items())[:4]):
            with preset_cols[idx]:
                if st.button(lbl, key=f"btn_stac_preset_{lbl}"):
                    st.session_state["stac_mosaic_query"] = full_val
                    st.rerun()

    # 2. Geocode the query dynamically
    active_query = st.session_state.get("stac_mosaic_query", "Bengaluru, Karnataka, India")
    geocoded = geocode_user_location(active_query)

    # 3. Settings & Telemetry Strip
    col_ctrl, col_info = st.columns([1.2, 1.8])

    with col_ctrl:
        st.markdown(f"**Target Location:** `{geocoded['name']}`")
        
        c_crs, c_stretch = st.columns(2)
        with c_crs:
            st.text_input("Calculated UTM CRS", value=geocoded["target_utm"], disabled=True)
        with c_stretch:
            stretch_val = st.number_input("Reflectance Stretch (DN)", min_value=1000.0, max_value=5000.0, value=2200.0, step=200.0)

        c_dec, c_cloud = st.columns(2)
        with c_dec:
            decimation_scale = st.slider("Decimation Factor", min_value=5, max_value=25, value=12, help="Sub-samples high-res 10m bands for rapid preview over broadband links.")
        with c_cloud:
            max_cloud_cover = st.slider("Max Cloud Cover (%)", min_value=5.0, max_value=50.0, value=15.0, step=5.0)

    with col_info:
        b = geocoded["bbox"]
        st.markdown(
            f"""
            <div class="telemetry-card" style="margin-top: 10px;">
                <div style="font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">
                    Target Bounding Box Coordinates (OpenStreetMap WGS-84)
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; color: #38bdf8; font-size: 0.95rem; margin-top: 4px;">
                    [{b[0]:.4f}° E, {b[1]:.4f}° N, {b[2]:.4f}° E, {b[3]:.4f}° N]
                </div>
                <div style="display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap;">
                    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 10px; font-size: 0.75rem;">
                        <span style="color: #64748b;">Source Collection:</span> <strong style="color: #f1f5f9;">sentinel-2-l2a</strong>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 10px; font-size: 0.75rem;">
                        <span style="color: #64748b;">Sensor:</span> <strong style="color: #38bdf8;">MSI (Multi-Spectral 10m)</strong>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 10px; font-size: 0.75rem;">
                        <span style="color: #64748b;">Target Projection:</span> <strong style="color: #34d399;">{geocoded['target_utm']}</strong>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    fetch_button = st.button("🚀 Fetch, Reproject & Stitch Real Sentinel-2 Mosaic", key="btn_run_stac")

    if fetch_button:
        try:
            import rasterio
            from rasterio.merge import merge
            from rasterio.warp import calculate_default_transform, reproject, Resampling
            import planetary_computer
            import pystac_client
        except ImportError as e:
            st.error(
                f"Missing GIS dependencies for STAC streaming: {e}. "
                "Ensure `rasterio`, `pystac-client`, and `planetary-computer` are installed."
            )
            return

        tile_files = []
        src_files = []

        with st.spinner(f"Querying Microsoft Planetary Computer STAC for '{geocoded['name']}'..."):
            try:
                catalog = pystac_client.Client.open(
                    "https://planetarycomputer.microsoft.com/api/stac/v1",
                    modifier=planetary_computer.sign_inplace,
                )

                search = catalog.search(
                    collections=["sentinel-2-l2a"],
                    bbox=geocoded["bbox"],
                    datetime="2023-01-01/..",
                    query={"eo:cloud_cover": {"lt": max_cloud_cover}},
                    max_items=4
                )

                items = list(search.items())
                if not items:
                    st.warning(f"No scenes with < {max_cloud_cover}% cloud cover found in recent window. Expanding temporal search...")
                    search = catalog.search(
                        collections=["sentinel-2-l2a"],
                        bbox=geocoded["bbox"],
                        max_items=4
                    )
                    items = list(search.items())

                if not items:
                    st.error("No imagery items returned for this bounding box.")
                    return

                st.success(f"Discovered {len(items)} intersecting Sentinel-2 spatial tiles for {geocoded['name']}. Streaming RGB bands...")

                loaded_rgb_tiles = []
                target_crs = geocoded["target_utm"]

                progress_bar = st.progress(0.0)

                for i, item in enumerate(items[:4]):
                    r_url = item.assets["B04"].href
                    g_url = item.assets["B03"].href
                    b_url = item.assets["B02"].href

                    scale = decimation_scale

                    with rasterio.open(r_url) as src:
                        h, w = int(src.height / scale), int(src.width / scale)
                        r = src.read(1, out_shape=(h, w), resampling=Resampling.bilinear)
                        src_transform = src.transform * rasterio.Affine.scale(scale, scale)
                        src_crs = src.crs

                    with rasterio.open(g_url) as src:
                        g = src.read(1, out_shape=(h, w), resampling=Resampling.bilinear)
                    with rasterio.open(b_url) as src:
                        b = src.read(1, out_shape=(h, w), resampling=Resampling.bilinear)

                    # Build RGB preview
                    tile_rgb = np.dstack((r.astype(np.float32), g.astype(np.float32), b.astype(np.float32)))
                    tile_rgb = np.clip(tile_rgb / stretch_val * 255.0, 0, 255).astype(np.uint8)
                    date_str = item.datetime.strftime("%Y-%m-%d") if item.datetime else "Unknown"
                    cloud_val = item.properties.get("eo:cloud_cover", 0.0)
                    loaded_rgb_tiles.append((item.id, tile_rgb, date_str, cloud_val))

                    # Reproject to shared UTM zone
                    dst_transform, dst_width, dst_height = calculate_default_transform(
                        src_crs, target_crs, w, h, *rasterio.transform.array_bounds(h, w, src_transform)
                    )

                    reprojected_r = np.zeros((dst_height, dst_width), dtype=r.dtype)
                    reprojected_g = np.zeros((dst_height, dst_width), dtype=g.dtype)
                    reprojected_b = np.zeros((dst_height, dst_width), dtype=b.dtype)

                    for band_src, band_dst in zip([r, g, b], [reprojected_r, reprojected_g, reprojected_b]):
                        reproject(
                            source=band_src, destination=band_dst,
                            src_transform=src_transform, src_crs=src_crs,
                            dst_transform=dst_transform, dst_crs=target_crs,
                            resampling=Resampling.bilinear
                        )

                    tile_filename = f"temp_tile_{i}.tif"
                    profile = {
                        "driver": "GTiff", "dtype": str(r.dtype), "count": 3,
                        "width": dst_width, "height": dst_height,
                        "transform": dst_transform, "crs": target_crs
                    }

                    with rasterio.open(tile_filename, "w", **profile) as dst:
                        dst.write(reprojected_r, 1)
                        dst.write(reprojected_g, 2)
                        dst.write(reprojected_b, 3)

                    tile_files.append(tile_filename)
                    progress_bar.progress((i + 1) / len(items[:4]))

                # Merge step
                src_files = [rasterio.open(f) for f in tile_files]
                mosaic, out_trans = merge(src_files)

                rm, gm, bm = mosaic[0].astype(np.float32), mosaic[1].astype(np.float32), mosaic[2].astype(np.float32)
                mosaic_rgb = np.dstack((rm, gm, bm))
                mosaic_rgb = np.clip(mosaic_rgb / stretch_val * 255.0, 0, 255).astype(np.uint8)

                # Cache in session state
                st.session_state["latest_sentinel_mosaic"] = mosaic_rgb
                st.session_state["latest_sentinel_tiles"] = loaded_rgb_tiles

                # Render UI Figure using dark theme
                fig = plt.figure(figsize=(16, 8))
                fig.patch.set_facecolor('#070b14')
                gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1.4, 1.4])

                tile_coords = [(0, 0), (0, 1), (1, 0), (1, 1)]
                for idx, (tid, t_img, dt_str, c_val) in enumerate(loaded_rgb_tiles):
                    if idx < len(tile_coords):
                        tr, tc = tile_coords[idx]
                        ax = fig.add_subplot(gs[tr, tc])
                        ax.imshow(t_img)
                        ax.set_title(f"Scene #{idx+1} ({dt_str}) Cloud: {c_val:.1f}%", color="#38bdf8", fontsize=8, fontfamily='monospace')
                        ax.axis('off')
                        ax.set_facecolor('#070b14')

                ax_mosaic = fig.add_subplot(gs[:, 2:])
                ax_mosaic.imshow(mosaic_rgb)
                ax_mosaic.set_title(f"Seamless 2×2 Reprojected Mosaic ({target_crs})\n{geocoded['name']}", color="#00f0ff", fontsize=11, pad=10, fontfamily='monospace')
                ax_mosaic.axis('off')
                ax_mosaic.set_facecolor('#070b14')

                plt.tight_layout()
                st.pyplot(fig)

                st.success("✅ Real Sentinel-2 observation successfully streamed, reprojected, and fused into mosaic!")

            except Exception as e:
                st.error(f"Error during STAC streaming or geodetic warping: {e}")

            finally:
                for src in src_files:
                    try:
                        src.close()
                    except Exception:
                        pass
                for f in tile_files:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception:
                            pass
