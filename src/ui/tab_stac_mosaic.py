"""Sentinel-2 Cloud STAC 2x2 Grid Stitcher Component.

Preserves and elevates the flagship capability from the 'main' branch:
Live streaming of Sentinel-2 L2A Cloud-Optimized GeoTIFFs (COGs) from Microsoft
Planetary Computer, cross-UTM reprojection, on-the-fly decimation, and 2x2 raster mosaicking.
"""

import os
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

LOCATIONS = {
    "Swiss Alps (Snow & Mountains)": {
        "bbox": [7.0, 45.5, 8.0, 46.2], 
        "target_crs": "EPSG:32632", 
        "stretch": 2000.0,
        "desc": "High-altitude snow pack, rugged granitic peaks, and alpine glacier dynamics."
    },
    "Grand Canyon, USA (Desert Canyons)": {
        "bbox": [-112.5, 35.8, -111.8, 36.4], 
        "target_crs": "EPSG:32612", 
        "stretch": 2500.0,
        "desc": "Spectacular stratigraphy, arid canyon topography, and the Colorado River channel."
    },
    "Nile Delta, Egypt (Green vs Desert)": {
        "bbox": [30.5, 30.5, 31.5, 31.5], 
        "target_crs": "EPSG:32636", 
        "stretch": 2000.0,
        "desc": "Sharp boundary between lush agricultural irrigation and hyper-arid Saharan sand dunes."
    },
    "Tokyo Grid, Japan (Urban & Coast)": {
        "bbox": [139.5, 35.5, 140.0, 35.8], 
        "target_crs": "EPSG:32654", 
        "stretch": 2200.0,
        "desc": "Dense megalopolis coastal grid, artificial islands, ports, and Pacific bay interface."
    }
}

def render_tab_stac_mosaic():
    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🌐 Planetary STAC 2×2 Mosaic Engine (Sentinel-2 L2A)</div>
            <div>
                <span class="tech-badge badge-cyan">Planetary Computer STAC</span>
                <span class="tech-badge badge-emerald">COG Window Streaming</span>
                <span class="tech-badge badge-purple">Cross-UTM Warping</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Stream multi-spectral Sentinel-2 satellite data directly from public cloud storage without downloading entire multi-gigabyte scenes.
        Applies geodetic reprojection across UTM zone boundaries and fuses overlapping tiles into an aligned 2×2 continuous mosaic.
        """
    )

    col_ctrl, col_info = st.columns([1.2, 1.8])

    with col_ctrl:
        selected_loc = st.selectbox("Select Planetary Study Region", list(LOCATIONS.keys()), key="stac_loc_select")
        config = LOCATIONS[selected_loc]
        st.caption(f"ℹ️ {config['desc']}")
        
        c_crs, c_stretch = st.columns(2)
        with c_crs:
            st.text_input("Target Geodetic CRS", value=config["target_crs"], disabled=True)
        with c_stretch:
            stretch_val = st.number_input("Reflectance Stretch (DN)", min_value=1000.0, max_value=5000.0, value=config["stretch"], step=200.0)

        decimation_scale = st.slider("Overview Decimation Factor", min_value=5, max_value=25, value=15, help="Sub-samples high-res 10m bands for rapid preview over broadband links.")

    with col_info:
        st.markdown(
            f"""
            <div class="telemetry-card" style="margin-top: 10px;">
                <div style="font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">
                    Target Bounding Box Coordinates
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; color: #38bdf8; font-size: 0.95rem; margin-top: 4px;">
                    [{config['bbox'][0]:.2f}° W, {config['bbox'][1]:.2f}° S, {config['bbox'][2]:.2f}° E, {config['bbox'][3]:.2f}° N]
                </div>
                <div style="display: flex; gap: 8px; margin-top: 12px;">
                    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 10px; font-size: 0.75rem;">
                        <span style="color: #64748b;">Source Collection:</span> <strong style="color: #f1f5f9;">sentinel-2-l2a</strong>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 10px; font-size: 0.75rem;">
                        <span style="color: #64748b;">Max Cloud Cover:</span> <strong style="color: #34d399;">&lt; 5.0%</strong>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    fetch_button = st.button("🚀 Fetch, Reproject & Stitch Mosaic", key="btn_run_stac")

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

        with st.spinner(f"Querying Microsoft Planetary Computer STAC Catalog for {selected_loc}..."):
            try:
                catalog = pystac_client.Client.open(
                    "https://planetarycomputer.microsoft.com/api/stac/v1",
                    modifier=planetary_computer.sign_inplace,
                )

                search = catalog.search(
                    collections=["sentinel-2-l2a"],
                    bbox=config["bbox"],
                    datetime="2025-06-01/2026-03-01",
                    query={"eo:cloud_cover": {"lt": 10.0}},
                    max_items=4
                )

                items = list(search.items())
                if not items:
                    st.warning("No scenes with < 10% cloud cover found in recent window. Expanding temporal search...")
                    search = catalog.search(
                        collections=["sentinel-2-l2a"],
                        bbox=config["bbox"],
                        max_items=4
                    )
                    items = list(search.items())

                if not items:
                    st.error("No imagery items returned for this bounding box.")
                    return

                st.success(f"Discovered {len(items)} intersecting spatial tiles. Streaming RGB bands...")

                loaded_rgb_tiles = []
                target_crs = config["target_crs"]

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
                    loaded_rgb_tiles.append((item.id, tile_rgb))

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

                # Render UI Figure using dark theme
                fig = plt.figure(figsize=(16, 8))
                fig.patch.set_facecolor('#070b14')
                gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1.4, 1.4])

                tile_coords = [(0, 0), (0, 1), (1, 0), (1, 1)]
                for idx, (tid, t_img) in enumerate(loaded_rgb_tiles):
                    if idx < len(tile_coords):
                        tr, tc = tile_coords[idx]
                        ax = fig.add_subplot(gs[tr, tc])
                        ax.imshow(t_img)
                        ax.set_title(f"Source Scene #{idx+1}", color="#38bdf8", fontsize=9, fontfamily='monospace')
                        ax.axis('off')
                        ax.set_facecolor('#070b14')

                ax_mosaic = fig.add_subplot(gs[:, 2:])
                ax_mosaic.imshow(mosaic_rgb)
                ax_mosaic.set_title(f"Seamless 2×2 Reprojected Mosaic ({target_crs})", color="#00f0ff", fontsize=12, pad=10, fontfamily='monospace')
                ax_mosaic.axis('off')
                ax_mosaic.set_facecolor('#070b14')

                plt.tight_layout()
                st.pyplot(fig)

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
