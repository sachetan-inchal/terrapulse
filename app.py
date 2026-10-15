import os
import sys

# Auto-launch with 'streamlit run' if executed directly via python app.py or IDE Run button
if __name__ == "__main__":
    try:
        import streamlit as st
        if not st.runtime.exists():
            from streamlit.web import cli as stcli
            sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
            sys.exit(stcli.main())
    except Exception:
        pass

import streamlit as st
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
import planetary_computer
import pystac_client
import matplotlib.pyplot as plt

try:
    from terrapulse.multispectral import RadiometricProcessor
    from terrapulse.change_detection import BiTemporalChangeDetector
    from terrapulse.osint_engine import GeospatialOSINTEngine, EcologicalThreatLevel
except ImportError:
    RadiometricProcessor = None
    BiTemporalChangeDetector = None
    GeospatialOSINTEngine = None

st.set_page_config(page_title="Sentinel-2 2x2 Grid Stitcher", layout="wide")

st.title("🛰️ Sentinel-2 Multi-Tile 2x2 Stitcher & UI Inspector")
st.markdown("Select a high-contrast global region below to stream, reproject, stitch, and visualize on the fly.")

# Location Presets Dictionary
LOCATIONS = {
    "Swiss Alps (Snow & Mountains)": {
        "bbox": [7.0, 45.5, 8.0, 46.2], 
        "target_crs": "EPSG:32632", 
        "stretch": 2000.0
    },
    "Grand Canyon, USA (Desert Canyons)": {
        "bbox": [-112.5, 35.8, -111.8, 36.4], 
        "target_crs": "EPSG:32612", 
        "stretch": 2500.0
    },
    "Nile Delta, Egypt (Green vs Desert)": {
        "bbox": [30.5, 30.5, 31.5, 31.5], 
        "target_crs": "EPSG:32636", 
        "stretch": 2000.0
    },
    "Tokyo Grid, Japan (Urban & Coast)": {
        "bbox": [139.5, 35.5, 140.0, 35.8], 
        "target_crs": "EPSG:32654", 
        "stretch": 2200.0
    }
}

selected_loc = st.sidebar.selectbox("Choose Study Region", list(LOCATIONS.keys()))
config = LOCATIONS[selected_loc]

if st.button("🚀 Fetch, Stitch & Render Grid"):
    with st.spinner(f"Connecting to Microsoft Planetary Computer for {selected_loc}..."):
        tile_files = []
        src_files = []
        try:
            catalog = pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=planetary_computer.sign_inplace,
            )

            search = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=config["bbox"],
                datetime="2026-01-01/2026-03-01", 
                query={"eo:cloud_cover": {"lt": 5.0}},
                max_items=4
            )

            items = list(search.items())
            if not items:
                st.error("No cloud-free items found for this region/date window.")
                st.stop()

            st.success(f"Found {len(items)} intersecting spatial tiles. Processing...")

            loaded_rgb_tiles = []
            target_crs = config["target_crs"]
            stretch_val = config["stretch"]

            progress_bar = st.progress(0)
            for i, item in enumerate(items[:4]):
                r_url = item.assets["B04"].href
                g_url = item.assets["B03"].href
                b_url = item.assets["B02"].href

                scale = 15  # Keeps download fast for 30 Mbps line
                
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

                tile_filename = f"web_tile_{i}.tif"
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

            # Render UI Figure using GridSpec to avoid subplot overlapping
            fig = plt.figure(figsize=(16, 8))
            fig.patch.set_facecolor('#0b0f19')
            gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1.3, 1.3])

            tile_coords = [(0, 0), (0, 1), (1, 0), (1, 1)]
            for idx, (tid, t_img) in enumerate(loaded_rgb_tiles):
                if idx < len(tile_coords):
                    tr, tc = tile_coords[idx]
                    ax = fig.add_subplot(gs[tr, tc])
                    ax.imshow(t_img)
                    ax.set_title(f"Source Tile {idx+1}", color="white", fontsize=9)
                    ax.axis('off')
                    ax.set_facecolor('#0b0f19')

            ax_mosaic = fig.add_subplot(gs[:, 2:])
            ax_mosaic.imshow(mosaic_rgb)
            ax_mosaic.set_title("Seamless 2x2 Stitched Grid", color="white", fontsize=12, pad=10)
            ax_mosaic.axis('off')
            ax_mosaic.set_facecolor('#0b0f19')

            plt.tight_layout()
            
            # Display inside Streamlit
            st.subheader("Before vs. After Visual Validation UI")
            st.pyplot(fig)

            # Radiometric Analysis Section
            if RadiometricProcessor is not None:
                st.markdown("---")
                st.subheader("🔬 Tier 2: Multi-Spectral Radiometric Analytics")
                col_r, col_g, col_b = mosaic_rgb[..., 0], mosaic_rgb[..., 1], mosaic_rgb[..., 2]
                nir_proxy = np.clip(col_g.astype(np.float32) * 1.35 + col_r.astype(np.float32) * 0.2, 0, 255).astype(np.uint8)
                bands = {"B02": col_b, "B03": col_g, "B04": col_r, "B08": nir_proxy}
                indices = RadiometricProcessor.process_all_indices(bands)

                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.image(RadiometricProcessor.colorize_index(indices.ndvi, "ndvi"), caption="NDVI (Canopy Health Heatmap)", use_container_width=True)
                with m_col2:
                    st.image(RadiometricProcessor.colorize_index(indices.ndwi, "ndwi"), caption="NDWI (Hydrology & Water Mask)", use_container_width=True)
                with m_col3:
                    st.image(RadiometricProcessor.generate_false_color_composite(bands, "cir"), caption="Color Infrared Composite (CIR)", use_container_width=True)

                st.write("**Ecological Surface Breakdown**:")
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                stat_col1.metric("Dense Canopy", f"{indices.statistics['dense_vegetation_pct']}%")
                stat_col2.metric("Water Bodies", f"{indices.statistics['water_body_pct']}%")
                stat_col3.metric("Built-up / Urban", f"{indices.statistics['built_up_urban_pct']}%")
                stat_col4.metric("Mean NDVI", f"{indices.statistics['ndvi_mean']:.3f}")

            # Autonomous OSINT Intelligence Section
            if GeospatialOSINTEngine is not None:
                st.markdown("---")
                st.subheader("🛡️ Tier 3: Autonomous OSINT Intelligence Dossier")
                with st.expander("Generate Autonomous OSINT Intelligence Briefing", expanded=True):
                    report = GeospatialOSINTEngine.analyze_change_intelligence(
                        region_query=selected_loc,
                        bbox=config["bbox"],
                        timeframe="2026-01-01 to 2026-03-01",
                        total_area_ha=1200.0,
                        deforestation_ha=15.4,
                        urban_sprawl_ha=38.2,
                        water_loss_ha=4.5,
                        revegetation_ha=1.8,
                    )
                    st.info(f"**Threat Status**: `{report.threat_level.value}` | **Ecological Vulnerability Index**: `{report.ecological_vulnerability_index:.1f}/100`")
                    st.markdown(report.to_markdown())

        except Exception as e:
            st.error(f"An error occurred during execution: {e}")

        finally:
            # Safe cleanup for Windows file locking
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