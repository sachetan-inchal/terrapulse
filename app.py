"""🛰️ TerraPulse / EarthWatch: Unified Planetary-Scale Geospatial Vision Platform.

Single Unified Flagship Platform combining:
1. 🛰️ EarthWatch: Real Sentinel-2 L2A streaming, physical spectral patch land-cover classification, and bi-temporal disturbance masking
2. ↔️ Bi-Temporal Split Slider: Interactive before/after swipe comparison slider matching the reference layout
3. 🌐 Planetary STAC 2×2 Mosaicker: Dynamic geocoding for any typed location, cross-UTM reprojection, and 2×2 COG raster mosaicking
4. 🧠 AI Environmental Investigator: Multi-agent root-cause investigation, evidence synthesis, and causal relationship reasoning
5. 🔬 Multi-Model Studio: ResNet-18, Siamese U-Net, DeepLabV3+, and NASA Prithvi-EO ViT feature activation inspection
6. 📐 Analytical CV Stitcher: SIFT, FLANN KD-Tree, Lowe's Ratio pruning, and RANSAC Homography warping
7. 🔮 Future Earth World Model: Spatiotemporal multimodal world model forecasting and scenario simulation
"""

import os
import sys
from pathlib import Path

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

# Configure page layout and metadata
st.set_page_config(
    page_title="TerraPulse | Earth Observation AI",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modular UI components
from src.ui.theme import apply_futuristic_theme, render_hero_banner, render_telemetry_sidebar
from src.ui.tab_earthwatch import render_tab_earthwatch, get_torch_device
from src.ui.tab_split_slider import render_tab_split_slider
from src.ui.tab_stac_mosaic import render_tab_stac_mosaic
from src.ui.tab_ai_investigator import render_tab_ai_investigator
from src.ui.tab_model_studio import render_tab_model_studio
from src.ui.tab_cv_stitcher import render_tab_cv_stitcher
from src.ui.tab_future_simulator import render_tab_future_simulator

def main():
    # 1. Apply futuristic aerospace dark styling
    apply_futuristic_theme()

    # 2. Render Top Mission Banner
    render_hero_banner()

    # 3. Sidebar Telemetry
    device = get_torch_device()
    device_name = str(device)
    render_telemetry_sidebar(device_name=device_name)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="font-size: 0.72rem; color: #64748b; line-height: 1.4;">
            <strong>TerraPulse Unified Platform</strong><br>
            All-In-One Geospatial Intelligence<br>
            Real Sentinel-2 STAC Stream
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Single Unified Multi-Tab Navigation
    tabs = st.tabs([
        "🛰️ EarthWatch (Change & Land Cover)",
        "↔️ Bi-Temporal Split Slider",
        "🌐 Planetary STAC 2×2 Mosaicker",
        "🧠 AI Environmental Investigator",
        "🔬 Model Architecture Studio",
        "📐 SIFT & RANSAC Homography",
        "🔮 Future Earth World Model"
    ])

    with tabs[0]:
        render_tab_earthwatch()

    with tabs[1]:
        render_tab_split_slider()

    with tabs[2]:
        render_tab_stac_mosaic()

    with tabs[3]:
        render_tab_ai_investigator()

    with tabs[4]:
        render_tab_model_studio()

    with tabs[5]:
        render_tab_cv_stitcher()

    with tabs[6]:
        render_tab_future_simulator()

if __name__ == "__main__":
    main()
