"""Futuristic UI Theme, Custom CSS, and Layout Components for TerraPulse / EarthWatch.

Provides sleek dark-mode aesthetics inspired by aerospace HUDs and planetary intelligence platforms.
"""

import streamlit as st

def apply_futuristic_theme():
    """Injects high-end, cyberpunk / aerospace geospatial CSS styling into Streamlit."""
    st.markdown(
        """
        <style>
        /* Base Dark Background and Clean Typography */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

        :root {
            --bg-primary: #070b14;
            --bg-card: rgba(15, 23, 42, 0.75);
            --bg-card-hover: rgba(30, 41, 59, 0.85);
            --border-glow: rgba(0, 240, 255, 0.25);
            --accent-cyan: #00f0ff;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-emerald: #10b981;
            --accent-rose: #f43f5e;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        /* Streamlit Main View Port */
        html, body, .stApp, div[data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 50% 0%, #0d1527 0%, #060911 100%) !important;
            color: var(--text-main);
            font-family: 'Space Grotesk', -apple-system, sans-serif;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: rgba(10, 15, 29, 0.95);
            border-right: 1px solid rgba(0, 240, 255, 0.15);
        }

        /* Custom Telemetry Card */
        .telemetry-card {
            background: var(--bg-card);
            border: 1px solid var(--border-glow);
            border-radius: 12px;
            padding: 16px 20px;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 20px -2px rgba(0, 240, 255, 0.08);
            margin-bottom: 16px;
            transition: all 0.25s ease;
        }
        .telemetry-card:hover {
            border-color: rgba(0, 240, 255, 0.5);
            box-shadow: 0 6px 25px -2px rgba(0, 240, 255, 0.18);
            transform: translateY(-2px);
        }

        /* Hero Header Banner */
        .hero-banner {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.15) 50%, rgba(168, 85, 247, 0.08) 100%);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 24px;
            backdrop-filter: blur(16px);
            position: relative;
            overflow: hidden;
        }
        .hero-banner::after {
            content: '';
            position: absolute;
            top: 0; right: 0;
            width: 180px; height: 180px;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.18) 0%, transparent 70%);
            pointer-events: none;
        }

        .hero-title {
            font-size: 2.1rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            background: linear-gradient(90deg, #ffffff 0%, #38bdf8 50%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }

        .hero-subtitle {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-top: 6px;
            line-height: 1.5;
        }

        /* High-Tech Badges */
        .tech-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-family: 'JetBrains Mono', monospace;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-right: 6px;
            margin-bottom: 6px;
        }
        .badge-cyan {
            background: rgba(0, 240, 255, 0.12);
            color: #00f0ff;
            border: 1px solid rgba(0, 240, 255, 0.4);
        }
        .badge-emerald {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .badge-purple {
            background: rgba(168, 85, 247, 0.12);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.4);
        }
        .badge-rose {
            background: rgba(244, 63, 94, 0.12);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.4);
        }

        /* KPI / Metric Pill */
        .kpi-container {
            display: flex;
            gap: 12px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .kpi-item {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 8px 14px;
            min-width: 120px;
        }
        .kpi-label {
            font-size: 0.7rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: 'JetBrains Mono', monospace;
        }
        .kpi-value {
            font-size: 1.15rem;
            font-weight: 700;
            color: #00f0ff;
            margin-top: 2px;
        }

        /* Tab Navigation Enhancements */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(15, 23, 42, 0.6);
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 0.9rem;
            color: #94a3b8;
            transition: all 0.2s ease;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.15) 0%, rgba(59, 130, 246, 0.2) 100%) !important;
            color: #00f0ff !important;
            border: 1px solid rgba(0, 240, 255, 0.4) !important;
        }

        /* Futuristic Section Header */
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 8px;
            margin-top: 20px;
            margin-bottom: 16px;
        }
        .section-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #f1f5f9;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Button Styling */
        div.stButton > button {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            color: white;
            border: 1px solid rgba(56, 189, 248, 0.5);
            border-radius: 8px;
            font-weight: 600;
            letter-spacing: 0.02em;
            padding: 10px 24px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 15px -2px rgba(2, 132, 199, 0.3);
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #0369a1 0%, #1d4ed8 100%);
            border-color: #00f0ff;
            box-shadow: 0 6px 20px -2px rgba(0, 240, 255, 0.4);
            transform: translateY(-1px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_hero_banner():
    """Renders the top futuristic mission banner."""
    banner_html = """<div class="hero-banner">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
            <div>
                <h1 class="hero-title">🛰️ TerraPulse / EarthWatch AI</h1>
                <p class="hero-subtitle">
                    Planetary-Scale Geospatial Vision, Bi-Temporal Change Detection & Spatiotemporal World Modeling
                </p>
            </div>
            <div style="margin-top: 8px;">
                <span class="tech-badge badge-cyan">● Online STAC Streamer</span>
                <span class="tech-badge badge-emerald">● ResNet-18 (96.4% Acc)</span>
                <span class="tech-badge badge-purple">● Siamese U-Net (0.80 F1)</span>
            </div>
        </div>
    </div>"""
    if hasattr(st, "html"):
        st.html(banner_html)
    else:
        st.markdown(banner_html, unsafe_allow_html=True)

def render_telemetry_sidebar(device_name="CPU"):
    """Renders the sidebar system status telemetry."""
    card_html = f"""<div class="telemetry-card">
        <div style="font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;">
            Core Telemetry
        </div>
        <div style="font-size: 1.1rem; font-weight: 700; color: #00f0ff; margin-top: 4px;">
            TerraPulse v2.0
        </div>
        <div class="kpi-container" style="margin-top: 10px;">
            <div class="kpi-item" style="min-width: 90px; padding: 6px 10px;">
                <div class="kpi-label">Compute</div>
                <div class="kpi-value" style="font-size: 0.95rem;">{device_name.upper()}</div>
            </div>
            <div class="kpi-item" style="min-width: 90px; padding: 6px 10px;">
                <div class="kpi-label">Status</div>
                <div class="kpi-value" style="font-size: 0.95rem; color: #34d399;">Active</div>
            </div>
        </div>
    </div>"""
    if hasattr(st.sidebar, "html"):
        st.sidebar.html(card_html)
    else:
        st.sidebar.markdown(card_html, unsafe_allow_html=True)


def render_workflow_step_indicator(
    step_statuses=None,
    step_subtitles=None,
    active_step: int = 1
):
    """Renders the guided 6-step progress indicator for TerraPulse v2.0 using native Streamlit containers."""
    steps = [
        (1, "1. Choose Location", "📍"),
        (2, "2. Select Imagery", "🛰️"),
        (3, "3. Generate Map", "🗺️"),
        (4, "4. Environmental Layers", "🌿"),
        (5, "5. Compare Dates", "↔️"),
        (6, "6. Investigate Findings", "🧠")
    ]

    cols = st.columns(6)
    for idx, (step_num, step_title, step_icon) in enumerate(steps):
        if step_statuses and step_num in step_statuses:
            status = step_statuses[step_num]
        else:
            if step_num < active_step:
                status = "completed"
            elif step_num == active_step:
                status = "active"
            else:
                status = "pending"

        sub = (step_subtitles.get(step_num, "") if step_subtitles else "")

        with cols[idx]:
            with st.container(border=True):
                if status == "completed":
                    st.markdown(f"**{step_icon} {step_title}**")
                    st.markdown(":green[**✓ READY**]")
                elif status == "active":
                    st.markdown(f"**{step_icon} {step_title}**")
                    st.markdown(":blue[**● ACTIVE**]")
                elif status == "ready":
                    st.markdown(f"**{step_icon} {step_title}**")
                    st.markdown(":orange[**⏳ READY**]")
                else:
                    st.markdown(f"{step_icon} {step_title}")
                    st.markdown(":gray[○ PENDING]")

                if sub:
                    st.caption(sub)





