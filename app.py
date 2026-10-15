"""🛰️ TerraPulse v2.0: Unified, User-Friendly and Data-Driven Geospatial Intelligence Platform.

Organized into four primary workspaces connected by a shared application state:
1. 🌍 Explore: Global location search, 3D orbital globe, STAC observations archive, 4-quadrant mosaic generation
2. 🌿 Analyze: True-color satellite imagery, calibrated environmental CV layers (NDVI, CIR, NDWI, NDBI, Land Cover, Population) with 0-100% opacity overlay
3. ↔️ Compare: Conditional bi-temporal split-view slider and ΔNDVI change detection over common spatial coverage
4. 🧠 Investigate: Evidence-based AI investigator grounded in empirical optical sensor data, peer-reviewed citations, and causal graphs

Advanced Tools & Diagnostics (Expandable Area):
- 🔬 SIFT & RANSAC Image Alignment & Stitching Laboratory
- 📐 Deep Learning Model Architecture Studio (U-Net, DeepLabV3+, NASA Prithvi-EO ViT)
- 🔮 Future Earth Spatiotemporal World Model Roadmap
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
    page_title="TerraPulse v2.0 | Planetary Geospatial Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import shared state manager
from src.data.state_manager import AppStateManager

# Import thematic styles and layout elements
from src.ui.theme import (
    apply_futuristic_theme,
    render_hero_banner,
    render_telemetry_sidebar,
    render_workflow_step_indicator
)

# Import unified workspaces
from src.ui.workspace_explore import render_workspace_explore
from src.ui.workspace_analyze import render_workspace_analyze
from src.ui.workspace_compare import render_workspace_compare
from src.ui.workspace_investigate import render_workspace_investigate
from src.ui.workspace_advanced import render_workspace_advanced
from src.ui.tab_earthwatch import get_torch_device


def compute_workflow_progress() -> int:
    """Calculates current workflow progress step (1 to 6) based on shared state."""
    if st.session_state.get(AppStateManager.KEY_COMPARISON_RESULT) is not None:
        return 5
    if st.session_state.get(AppStateManager.KEY_ENV_LAYERS) is not None:
        return 4
    if st.session_state.get(AppStateManager.KEY_PRIMARY_MOSAIC) is not None:
        return 3
    if st.session_state.get(AppStateManager.KEY_DISCOVERED_SCENES):
        return 2
    return 1


def main():
    # 1. Initialize centralized application state
    AppStateManager.init_state()

    # 2. Apply aerospace dark theme
    apply_futuristic_theme()

    # 3. Top Mission Banner
    render_hero_banner()

    # 4. Guided Workflow Step Indicator (1 to 6)
    current_step = compute_workflow_progress()
    render_workflow_step_indicator(active_step=current_step)

    # 5. Sidebar Telemetry & Single Source of Truth Provenance
    device = get_torch_device()
    device_name = str(device)
    render_telemetry_sidebar(device_name=device_name)

    geocoded = AppStateManager.get_geocoded()
    active_obs = AppStateManager.get_active_observation()
    obs_date = active_obs.date_str if active_obs else "Awaiting query"
    obs_cloud = f"{active_obs.cloud_cover:.1f}%" if active_obs else "N/A"

    st.sidebar.markdown(
        f"""
        <div class="telemetry-card" style="margin-top: 10px; font-size: 0.72rem; line-height: 1.4;">
            <div style="color: #00f0ff; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">
                🛰️ Active Data Provenance
            </div>
            • Target: <strong>{geocoded['name']}</strong><br>
            • Coordinates: <code>{geocoded['lat']:.3f}°N, {geocoded['lon']:.3f}°E</code><br>
            • Target Grid: <strong>{geocoded['target_utm']}</strong><br>
            • Active Date: <strong>{obs_date}</strong><br>
            • Cloud Cover: <strong>{obs_cloud}</strong><br>
            • Resolution: <strong>10m MultiSpectral</strong><br>
            <hr style="border-color: rgba(255,255,255,0.08); margin: 6px 0;">
            <span style="color: #34d399;">● Shared State Synchronized</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown(
        """
        <div style="font-size: 0.70rem; color: #64748b; line-height: 1.4; padding: 4px;">
            <strong>TerraPulse v2.0 Architecture:</strong><br>
            Every workspace reads from the same verified Sentinel-2 data stream. Changing location or observation immediately updates all dependent maps, statistics, and AI analyses.
        </div>
        """,
        unsafe_allow_html=True
    )

    # 6. Four Clean Workspaces Navigation
    workspaces = st.tabs([
        "🌍 Explore (Locate & Discover)",
        "🌿 Analyze (Environmental Layers)",
        "↔️ Compare (Bi-Temporal Change)",
        "🧠 Investigate (AI Evidence Synthesis)"
    ])

    with workspaces[0]:
        render_workspace_explore()

    with workspaces[1]:
        render_workspace_analyze()

    with workspaces[2]:
        render_workspace_compare()

    with workspaces[3]:
        render_workspace_investigate()

    # 7. Collapsible Advanced Tools & Diagnostics Area
    st.markdown("---")
    with st.expander("🛠️ Advanced Tools & Diagnostics (SIFT/RANSAC Alignment, Model Studio & World Model)", expanded=False):
        render_workspace_advanced()


if __name__ == "__main__":
    main()
