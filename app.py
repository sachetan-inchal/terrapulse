"""🛰️ TerraPulse / EarthWatch: Unified Planetary-Scale Geospatial Vision Platform.

Combines:
1. EarthWatch: ResNet-18 Land-Cover Classification & Siamese U-Net Change Detection (LEVIR-CD / EuroSAT)
2. Planetary STAC 2x2 Mosaicker: Microsoft Planetary Computer Sentinel-2 COG streamer with cross-UTM reprojection
3. Multi-Model Studio: U-Net, DeepLabV3+, and NASA Prithvi-EO ViT feature activation inspection
4. Analytical CV Stitcher: SIFT, FLANN KD-Tree, Lowe's Ratio pruning, and RANSAC Homography warping
5. Future Earth Simulator: Multimodal Spatiotemporal World Model roadmap, timeline scrubber, and animated visualization workspace
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
from src.ui.tab_stac_mosaic import render_tab_stac_mosaic
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
            <strong>TerraPulse Core</strong><br>
            Merged build: <code>main</code> + <code>earthwatch</code><br>
            Multi-spectral & AI Pipeline
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Modular Tabbed Navigation
    tabs = st.tabs([
        "🛰️ EarthWatch (Change & Land Cover)",
        "🌐 Planetary STAC 2×2 Mosaicker",
        "🔬 Model Architecture Studio",
        "📐 SIFT & RANSAC Homography",
        "🔮 Future Earth World Model (Preview)"
    ])

    with tabs[0]:
        render_tab_earthwatch()

    with tabs[1]:
        render_tab_stac_mosaic()

    with tabs[2]:
        render_tab_model_studio()

    with tabs[3]:
        render_tab_cv_stitcher()

    with tabs[4]:
        render_tab_future_simulator()

if __name__ == "__main__":
    main()
