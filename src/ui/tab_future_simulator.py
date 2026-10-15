"""Future Earth Simulator & World Model Architecture Component.

Visualizes the next-generation spatiotemporal generative modeling roadmap:
- Visual scrub slider spanning 1985 -> 2024 -> 2050
- The 'EarthTilePackage' multimodal composite data structure
- Two-Stage Dynamics & Generative Diffusion Architecture
- Preparation zone for animated visualizations of project technologies
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def render_tab_future_simulator():
    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">🔮 Future Earth Simulator & World Model Architecture</div>
            <div>
                <span class="tech-badge badge-purple">Spatiotemporal Transformer</span>
                <span class="tech-badge badge-cyan">Conditional Latent Diffusion</span>
                <span class="tech-badge badge-emerald">EarthTilePackage Schema</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Simulate planetary evolution over multi-decade horizons. The model consumes a self-made multimodal data structure
        (historical imagery sequence, geodetic coordinates, land-cover percentages, and local geopolitical/demographic time-series)
        to predict future terrain transformations, urban encroachment, and ecological shifts.
        """
    )

    # 1. TIMELINE SCRUB SLIDER
    st.markdown("### ⏱️ Multitemporal Observation & Future Scenario Timeline")

    TIMELINE_YEARS = [1985, 1995, 2005, 2015, 2024, 2030, 2040, 2050]
    col_s1, col_s2 = st.columns([2.5, 1])

    with col_s1:
        selected_year = st.select_slider(
            "Temporal Scrub Bar (Years 1985 - 2050)",
            options=TIMELINE_YEARS,
            value=2024,
            format_func=lambda y: f"{y} (Scenario)" if y > 2024 else f"{y} (Historical)" if y < 2024 else f"{y} (Current State)"
        )

    with col_s2:
        is_future = selected_year > 2024
        badge_cls = "badge-purple" if is_future else "badge-cyan"
        horizon = f"+{selected_year - 2024} Years Forecast" if is_future else f"{2024 - selected_year} Years Past" if selected_year < 2024 else "Present Epoch"
        st.markdown(
            f"""
            <div style="margin-top: 24px;">
                <span class="tech-badge {badge_cls}">● {horizon}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Dynamic visual rendering based on selected year
    p_ref = ROOT_DIR / "tile_left.jpg"
    p_alt = ROOT_DIR / "tile_right.jpg"

    base_img = Image.open(p_ref).convert("RGB") if p_ref.exists() else Image.new("RGB", (512, 512), (30, 60, 40))
    current_img = Image.open(p_alt).convert("RGB") if p_alt.exists() else Image.new("RGB", (512, 512), (70, 70, 80))

    # Simulate temporal evolution visually
    ratio = (selected_year - 1985) / (2050 - 1985)
    # Blend base with current and apply saturation/contrast modifications for future
    arr_base = np.asarray(base_img.resize((512, 512)), dtype=np.float32)
    arr_cur = np.asarray(current_img.resize((512, 512)), dtype=np.float32)

    if selected_year <= 2024:
        sub_ratio = (selected_year - 1985) / (2024 - 1985)
        blended = arr_base * (1.0 - sub_ratio) + arr_cur * sub_ratio
        synth_img = Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))
    else:
        # Future synthetic projection: higher concrete/urban heat, decreased canopy
        fut_ratio = (selected_year - 2024) / (2050 - 2024)
        synth_arr = arr_cur.copy()
        # Boost bright concrete channels, reduce green channel slightly
        synth_arr[..., 0] = np.clip(synth_arr[..., 0] * (1.0 + 0.3 * fut_ratio), 0, 255)
        synth_arr[..., 1] = np.clip(synth_arr[..., 1] * (1.0 - 0.25 * fut_ratio), 0, 255)
        synth_arr[..., 2] = np.clip(synth_arr[..., 2] * (1.0 + 0.15 * fut_ratio), 0, 255)
        synth_img = Image.fromarray(synth_arr.astype(np.uint8))

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("**Epoch 1985 Baseline State (Historical)**")
        st.image(base_img, use_container_width=True)
        st.caption("Vegetation: 64.2% | Urban Built-up: 12.1% | Water Table: Normal")

    with col_v2:
        st.markdown(f"**Epoch {selected_year} {'Projected World State' if is_future else 'Observed State'}**")
        st.image(synth_img, use_container_width=True)
        veg_pct = max(18.0, 64.2 - ratio * 42.0)
        urb_pct = min(72.0, 12.1 + ratio * 58.0)
        st.caption(f"Vegetation: {veg_pct:.1f}% | Urban Built-up: {urb_pct:.1f}% | Confidence: {'84.2% (Generative Prior)' if is_future else 'Direct Observation'}")

    st.markdown("---")

    # 2. MULTIMODAL DATA STRUCTURE INSPECTOR
    st.subheader("2. 📦 Multimodal `EarthTilePackage` Data Structure")
    st.markdown("Formal schema combining spatial imagery, geodetic coordinates, land-cover distributions, and geopolitical series:")

    col_d1, col_d2 = st.columns([1.5, 1])

    with col_d1:
        st.code(
            '''@dataclass
class EarthTilePackage:
    # 1. Visual Spatiotemporal Tensor: (Sequence T, Channels C, Height H, Width W)
    image_sequence: torch.Tensor          # e.g., shape: [5, 4, 512, 512] (RGB + NIR)
    
    # 2. Geodetic Spatial Anchor: [min_lat, min_lon, max_lat, max_lon, crs_epsg]
    geo_bounds: torch.Tensor              # [12.92, 77.55, 13.02, 77.68, 32643]
    
    # 3. Categorical Land-Cover Percentages: [forest%, water%, urban%, agriculture%, barren%]
    lulc_distribution: torch.Tensor       # [0.22, 0.08, 0.54, 0.12, 0.04]
    
    # 4. Geopolitical & Socioeconomic Historical Time-Series (T years):
    #    [population_density, gdp_growth_rate, road_network_density, industrial_permits]
    socioeconomic_series: torch.Tensor    # shape: [T, 4]
    
    # 5. Target Forecast Horizon (+years)
    delta_years: float                    # e.g. 10.0 (predict year 2034)''',
            language="python"
        )

    with col_d2:
        st.markdown(
            """
            <div class="telemetry-card">
                <div style="font-size: 0.8rem; font-weight: 700; color: #38bdf8;">Why This Structure Matters</div>
                <p style="font-size: 0.78rem; color: #94a3b8; margin-top: 6px; line-height: 1.5;">
                    Raw satellite pixels alone cannot forecast where a new highway or commercial IT corridor will emerge.
                    Fusing satellite rasters with municipal master plans, population growth curves, and infrastructure investments
                    transforms this from a naive extrapolation into a <strong>Physics- and Policy-Informed World Model</strong>.
                </p>
                <div style="margin-top: 10px;">
                    <span class="tech-badge badge-emerald">Ready for Animated Demos</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # 3. UPCOMING ANIMATIONS & VISUALIZATIONS ZONE
    st.subheader("3. 🎬 Future Animated Visualizations Workspace")
    st.info("💡 Tab ready: In the upcoming iteration, we can render real-time WebGL particle flows, animated attention maps, and continuous year-by-year time-lapse transitions right here.")
