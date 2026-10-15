"""TerraPulse v2.0 Workspace 2: Analyze.

Capabilities:
- View selected authentic satellite observation (Combined Satellite Map or single scene)
- Explore environmental computer vision layers:
  * 🌿 Vegetation Index (NDVI)
  * 🔴 False-Color Canopy (CIR NIR-R-G)
  * 💧 Surface Water Extent (NDWI McFeeters)
  * 🏙️ Built-Up Impervious Footprint (NDBI Urban Proxy)
  * 🗺️ Physical Land Cover Classification (Rule-Based 5-Class)
  * 👥 Gridded Population Density (Demographic Proxy)
- Interactive 0–100% Opacity Slider directly overlaid on true-color satellite imagery
- Real calibrated metrics (km² area, percentages, mean/median values)
- Pixel distribution histograms
- Scientific legends, data sources, observation dates, and known limitations
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from src.data.state_manager import AppStateManager
from src.data.sentinel_explorer import ObservationData, EnvironmentalLayers


def render_workspace_analyze():
    """Renders the unified Analyze workspace."""
    AppStateManager.init_state()

    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🌿 Workspace 2: Environmental Computer Vision Analysis</div>
            <div>
                <span class="tech-badge badge-emerald">Vegetation Index (NDVI)</span>
                <span class="tech-badge badge-cyan">Water Extent (NDWI)</span>
                <span class="tech-badge badge-rose">Built-Up Footprint</span>
                <span class="tech-badge badge-purple">Calibrated Spectral Masks</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        Extract verified biophysical indicators from optical reflectance bands (Red B04, Green B03, Blue B02, Near-Infrared B08).
        Every metric represents real physical sensor measurements calibrated to square kilometers.
        """
    )

    # 1. Fetch Active Observation from Shared State
    active_obs: ObservationData = AppStateManager.get_active_observation()
    geocoded = AppStateManager.get_geocoded()

    if active_obs is None:
        st.warning("⚠️ No satellite observation is currently loaded. Please visit the **🌍 Explore** workspace first to discover scenes.")
        return

    # 2. Compute or Fetch Environmental Layers from Shared State
    env_layers: EnvironmentalLayers = AppStateManager.ensure_environmental_layers()
    if env_layers is None:
        st.error("Failed to compute environmental layers for the active observation.")
        return

    stats = env_layers.stats

    # Telemetry bar showing observation provenance
    obs_type_label = "Combined Satellite Map (4-Tile Mosaic)" if "mosaic" in active_obs.id.lower() else "Individual STAC Scene"
    st.markdown(
        f"""
        <div class="telemetry-card" style="border-left: 3px solid #10b981; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Active Target:</span>
                    <strong style="color: #f1f5f9; font-size: 0.95rem; margin-left: 6px;">{geocoded['name']}</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Acquisition Date:</span>
                    <strong style="color: #00f0ff; font-family: monospace; font-size: 0.9rem; margin-left: 6px;">{active_obs.date_str}</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Observation Mode:</span>
                    <span class="tech-badge badge-emerald" style="margin-left: 4px;">{obs_type_label}</span>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Cloud Cover:</span>
                    <strong style="color: #fbbf24; font-family: monospace; font-size: 0.85rem; margin-left: 6px;">{active_obs.cloud_cover:.1f}%</strong>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-family: monospace;">Resolution:</span>
                    <strong style="color: #a78bfa; font-family: monospace; font-size: 0.85rem; margin-left: 6px;">10m Ground Sample Distance</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Primary Metrics Strip (Empirical km² and percentages)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Mean Vegetation Index",
        f"{stats['mean_ndvi']:.3f}",
        help="Mean Normalized Difference Vegetation Index: values > 0.4 indicate dense canopy."
    )
    c2.metric(
        "Forest Canopy",
        f"{stats['forest_coverage_pct']}%",
        f"{stats['forest_area_km2']} km²",
        help="Dense tree canopy (> 0.45 NDVI)."
    )
    c3.metric(
        "Vegetation / Crops",
        f"{stats['vegetation_coverage_pct']}%",
        f"{stats['vegetation_area_km2']} km²",
        help="Moderate agricultural and grassland canopy [0.20 – 0.45 NDVI]."
    )
    c4.metric(
        "Built-Up Footprint",
        f"{stats['urban_built_pct']}%",
        f"{stats['urban_area_km2']} km²",
        help="Impervious surfaces, high albedo concrete and asphalt fabric."
    )
    c5.metric(
        "Surface Water",
        f"{stats['water_extent_pct']}%",
        f"{stats['water_area_km2']} km²",
        help="Open surface water extent (McFeeters NDWI > 0)."
    )

    st.markdown("---")

    # 4. Layer Selector & Dynamic Opacity Slider Controls
    col_sel, col_op = st.columns([1.6, 1.4])

    with col_sel:
        cv_layer_choice = st.selectbox(
            "Select Environmental Layer to Explore:",
            options=[
                "🌿 Vegetation Index (NDVI) — Canopy Density & Greenness",
                "🔴 False-Color Infrared (CIR NIR-R-G) — Plant Chlorophyll Vigor",
                "💧 Surface Water Extent (NDWI) — Lakes, Reservoirs & Waterways",
                "🏙️ Built-Up Impervious Area (NDBI) — Urban Infrastructure",
                "🗺️ Land Cover Classification — ESA WorldCover Aligned Classes",
                "👥 Population Density — Demographic Proxy Model"
            ],
            index=0,
            key="sel_cv_layer_analyze"
        )

    with col_op:
        overlay_opacity = st.slider(
            "Overlay Opacity (%) over Satellite Imagery:",
            min_value=0, max_value=100, value=75, step=5,
            key="sld_opacity_analyze",
            help="0% = Pure True-Color Satellite Imagery | 100% = Pure Analytical Mask | 50% = Semi-transparent overlay"
        )

    alpha = overlay_opacity / 100.0
    bg_rgb = active_obs.rgb

    # -------------------------------------------------------------------------
    # LAYER 1: VEGETATION INDEX (NDVI)
    # -------------------------------------------------------------------------
    if "Vegetation Index" in cv_layer_choice:
        col_v1, col_v2 = st.columns([2.0, 1.1])
        with col_v1:
            ndvi_valid = np.nan_to_num(env_layers.ndvi, nan=0.0)
            norm_ndvi = np.clip((ndvi_valid + 0.2) / 1.0, 0, 1)
            ndvi_cmap = plt.cm.RdYlGn(norm_ndvi)[:, :, :3]
            ndvi_colored = (ndvi_cmap * 255.0).astype(np.uint8)

            blended = (bg_rgb * (1.0 - alpha) + ndvi_colored * alpha).astype(np.uint8)

            fig, ax = plt.subplots(figsize=(10, 5.8))
            fig.patch.set_facecolor('#070b14')
            ax.set_facecolor('#070b14')
            im = ax.imshow(blended)
            ax.set_title(f"Vegetation Index (NDVI) — Sentinel-2 ({active_obs.date_str}) [Opacity: {overlay_opacity}%]", color="#00f0ff", fontsize=11, fontfamily='monospace')
            ax.axis("off")

            sm = plt.cm.ScalarMappable(cmap="RdYlGn", norm=plt.Normalize(vmin=-0.2, vmax=0.8))
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
            cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
            cbar.set_label("Vegetation Index: Water (<0) | Barren (0-0.2) | Shrub/Crop (0.2-0.45) | Dense Canopy (>0.45)", color="#94a3b8", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        with col_v2:
            fig_h, ax_h = plt.subplots(figsize=(5, 3.4))
            fig_h.patch.set_facecolor('#070b14')
            ax_h.set_facecolor('#070b14')
            vals = env_layers.ndvi[~np.isnan(env_layers.ndvi)].flatten()
            ax_h.hist(vals, bins=40, range=(-0.2, 0.9), color="#34d399", alpha=0.85, edgecolor="#070b14")
            ax_h.set_title("NDVI Pixel Frequency Distribution", color="#00f0ff", fontsize=9, fontfamily='monospace')
            ax_h.tick_params(colors="#94a3b8", labelsize=7)
            for spine in ax_h.spines.values():
                spine.set_color("#334155")
            plt.tight_layout()
            st.pyplot(fig_h)
            plt.close(fig_h)

            st.markdown(
                f"""
                <div class="telemetry-card" style="font-size: 0.72rem; color: #94a3b8;">
                    <strong style="color: #34d399;">What it does:</strong> Measures chlorophyll absorption of red light versus near-infrared reflection.<br>
                    <strong style="color: #38bdf8;">Why it matters:</strong> Directly tracks plant health, forest preservation, and crop growth.<br>
                    <strong style="color: #fbbf24;">Data used:</strong> Sentinel-2 Band 08 (NIR) & Band 04 (Red). Formula: <code>(NIR - Red) / (NIR + Red)</code><br>
                    <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                    • Mean NDVI: <strong>{stats['mean_ndvi']}</strong><br>
                    • Median NDVI: <strong>{stats['median_ndvi']}</strong><br>
                    • Dense Forest Area: <strong>{stats['forest_area_km2']} km²</strong> ({stats['forest_coverage_pct']}%)<br>
                    • Total Mapped Extent: <strong>{stats['total_area_km2']} km²</strong><br>
                    <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                    <em>Limitations: NDVI saturates in ultra-dense rainforests and can be affected by surface soil moisture.</em>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -------------------------------------------------------------------------
    # LAYER 2: FALSE-COLOR INFRARED (CIR)
    # -------------------------------------------------------------------------
    elif "False-Color" in cv_layer_choice:
        col_c1, col_c2 = st.columns([2.0, 1.1])
        with col_c1:
            if active_obs.cir is not None:
                st.image(
                    active_obs.cir,
                    caption=f"Color-Infrared False Color Composite (NIR B08 → Red, Red B04 → Green, Green B03 → Blue) — Sentinel-2 ({active_obs.date_str})",
                    use_container_width=True
                )
            else:
                st.warning("Color-Infrared composite requires NIR Band 08.")

        with col_c2:
            st.markdown(
                """
                <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8;">
                    <strong style="color: #fb7185;">What it does:</strong> Maps invisible Near-Infrared energy into the human visible red channel.<br><br>
                    <strong style="color: #38bdf8;">Why it matters:</strong> Chlorophyll strongly scatters NIR radiation. Healthy forests appear vibrant crimson, clear water appears black/dark blue, and concrete roads appear steel-grey.<br><br>
                    <strong style="color: #fbbf24;">Data used:</strong> Sentinel-2 Level-2A bands: B08 (NIR 842nm), B04 (Red 665nm), and B03 (Green 560nm).
                </div>
                """,
                unsafe_allow_html=True
            )

    # -------------------------------------------------------------------------
    # LAYER 3: SURFACE WATER EXTENT (NDWI)
    # -------------------------------------------------------------------------
    elif "Surface Water" in cv_layer_choice:
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
            ax.set_title(f"Surface Water Extent (NDWI) — Sentinel-2 ({active_obs.date_str}) [Opacity: {overlay_opacity}%]", color="#38bdf8", fontsize=11, fontfamily='monospace')
            ax.axis("off")
            sm = plt.cm.ScalarMappable(cmap="Blues", norm=plt.Normalize(vmin=-0.4, vmax=0.4))
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
            cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
            cbar.set_label("Water Index: Non-Water (<0) | Open Surface Water Bodies (>0)", color="#94a3b8", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        with col_w2:
            st.markdown(
                f"""
                <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8;">
                    <strong style="color: #38bdf8;">What it does:</strong> Enhances open water bodies while suppressing terrestrial vegetation and bare soil features.<br>
                    <strong style="color: #34d399;">Why it matters:</strong> Monitors reservoir water storage, lake surface shrinking, and river basin extent.<br>
                    <strong style="color: #fbbf24;">Data used:</strong> Sentinel-2 Band 03 (Green) & Band 08 (NIR). Formula: <code>(Green - NIR) / (Green + NIR)</code><br>
                    <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                    • Open Water Extent: <strong>{stats['water_extent_pct']}%</strong><br>
                    • Mapped Water Area: <strong>{stats['water_area_km2']} km²</strong><br>
                    • McFeeters Threshold: <code>NDWI > 0.0</code><br>
                    <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                    <em>Limitations: Shallow murky waters or heavy algae blooms can lower the NDWI response.</em>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -------------------------------------------------------------------------
    # LAYER 4: BUILT-UP IMPERVIOUS FOOTPRINT (NDBI)
    # -------------------------------------------------------------------------
    elif "Built-Up" in cv_layer_choice:
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
            ax.set_title(f"Built-Up / Urban Impervious Footprint — {stats['urban_built_pct']}% Urban [Opacity: {overlay_opacity}%]", color="#f43f5e", fontsize=11, fontfamily='monospace')
            ax.axis("off")
            sm = plt.cm.ScalarMappable(cmap="magma", norm=plt.Normalize(vmin=-0.3, vmax=0.3))
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046)
            cbar.ax.tick_params(labelsize=8, colors="#94a3b8")
            cbar.set_label("NDBI Urban Index: Natural Land (<0) | Built-Up / Paved Fabric (>0)", color="#94a3b8", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        with col_b2:
            st.markdown(
                f"""
                <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8;">
                    <strong style="color: #f43f5e;">What it does:</strong> Identifies urban infrastructure, road networks, commercial complexes, and residential developments.<br>
                    <strong style="color: #38bdf8;">Why it matters:</strong> Quantifies urbanization rate, impervious surface runoff, and loss of permeable catchment soil.<br>
                    <strong style="color: #fbbf24;">Data used:</strong> High visible-spectrum albedo with low photosynthetic absorption proxy (10m).<br>
                    <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                    • Urban Impervious Coverage: <strong>{stats['urban_built_pct']}%</strong><br>
                    • Mapped Built-Up Area: <strong>{stats['urban_area_km2']} km²</strong><br>
                    <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                    <em>Limitations: Dry barren soil or rock quarries can display similar high albedo signatures to concrete.</em>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -------------------------------------------------------------------------
    # LAYER 5: PHYSICAL LAND COVER CLASSIFICATION
    # -------------------------------------------------------------------------
    elif "Land Cover" in cv_layer_choice:
        cmap_lc = mcolors.ListedColormap(['#1e40af', '#15803d', '#84cc16', '#dc2626', '#d97706'])
        fig, ax = plt.subplots(figsize=(10, 5.8))
        fig.patch.set_facecolor('#070b14')
        ax.set_facecolor('#070b14')
        im = ax.imshow(env_layers.landcover, cmap=cmap_lc, vmin=0, vmax=4)
        ax.set_title(f"Physical Land Cover Classification (Sentinel-2 10m L2A)", color="#a855f7", fontsize=11, fontfamily='monospace')
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

        st.markdown(
            f"""
            <div class="telemetry-card" style="font-size: 0.75rem; color: #94a3b8; margin-top: 10px;">
                <strong style="color: #c084fc;">Classification Methodology:</strong> Deterministic multi-spectral decision boundaries calibrated against the European Space Agency (ESA) WorldCover 10m taxonomy.<br>
                Classifies every 10m pixel into 5 discrete physical biophysical classes based on validated reflectance thresholds.
            </div>
            """,
            unsafe_allow_html=True
        )

    # -------------------------------------------------------------------------
    # LAYER 6: POPULATION DENSITY MODEL
    # -------------------------------------------------------------------------
    elif "Population" in cv_layer_choice:
        col_p1, col_p2 = st.columns([2.0, 1.1])
        with col_p1:
            fig, ax = plt.subplots(figsize=(10, 5.8))
            fig.patch.set_facecolor('#070b14')
            ax.set_facecolor('#070b14')
            im = ax.imshow(env_layers.population_density, cmap="YlOrRd", vmin=0, vmax=15000)
            ax.set_title(f"Gridded Demographic Density Model (persons / km²)", color="#f59e0b", fontsize=11, fontfamily='monospace')
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
                    <strong style="color: #f59e0b;">Population Layer Provenance:</strong><br>
                    • Mean Regional Density: <strong>{stats['mean_population_density']:,.0f} / km²</strong><br>
                    • Estimated AOI Population: <strong>~{stats['estimated_total_population']:,} residents</strong><br>
                    • Data Source: <strong>GPWv4 / WorldPop Reference Baseline Model</strong><br>
                    • Disaggregation: <strong>Dasymetric built-up weighting</strong><br>
                    <hr style="border-color: rgba(255,255,255,0.06); margin: 6px 0;">
                    <strong>Critical Scientific Transparency:</strong> Optical satellite sensors do not count people directly. 
                    This layer integrates external census records disaggregated proportionally onto the detected impervious urban fabric.
                </div>
                """,
                unsafe_allow_html=True
            )
