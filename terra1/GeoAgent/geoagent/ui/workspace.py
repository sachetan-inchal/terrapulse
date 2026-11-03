"""TerraPulse Geospatial Intelligence Workspace for Solara.

Transforms the UI into a modern 3-panel professional GIS application:
- Left Panel: Data Explorer & Layer Manager
- Center Panel: Interactive MapLibre / AnyMap Map with Toolbar, Coordinates, & Mode Switches
- Right Panel: Agent Configuration, Jobs & Execution Monitor, Sample Prompts, & Chat
"""

from __future__ import annotations

import time
from typing import Any

import solara

from geoagent import __version__
from geoagent.ui.app import (
    PROVIDER_NAMES,
    compact_tool_call,
    create_ui_map_binding,
    default_model_for_provider,
    default_provider,
    dispatch_prompt,
)

SAMPLE_PROMPT_CATEGORIES = {
    "Geographical Discovery": [
        "Where is Mount Everest? Locate it on the map.",
        "What is the deepest point in the ocean? Locate it.",
        "Show the five highest mountain peaks in the world.",
        "Show the countries bordering India.",
        "Where is the Amazon River? Locate it.",
        "Where is the Sahara Desert? Show it on the map.",
    ],
    "Smart Map Labeling": [
        "Enable smart dynamic map labels.",
        "Toggle off smart map labels.",
    ],
    "Navigation": [
        "Zoom into Bengaluru at latitude 12.9716 and longitude 77.5946 with zoom level 12.",
        "Center the map on San Francisco at latitude 37.7749 and longitude -122.4194.",
        "Fly to Tokyo, Japan at latitude 35.6762, longitude 139.6503 with zoom 13.",
    ],
    "Basemaps": [
        "Switch the map to satellite imagery.",
        "Change the basemap to topographic terrain.",
        "Switch the basemap to OpenStreetMap streets.",
        "Use CartoDB DarkMatter for high-contrast nighttime view.",
    ],
    "Terrain & Elevation": [
        "Enable 3D terrain elevation with exaggeration 1.5.",
        "Add an available elevation shaded relief layer to the map.",
        "Center on the Himalayas (latitude 27.9881, longitude 86.9250) and enable 3D terrain.",
    ],
    "Vector & Markers": [
        "Add a point marker at Vidhana Soudha, Bengaluru (latitude 12.9797, longitude 77.5906).",
        "Add vector data from 'https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/countries.geojson' named 'world_countries'.",
    ],
    "Multi-Step Workflows": [
        "Locate Mount Everest, switch to satellite imagery, and enable 3D terrain elevation.",
        "Show Bengaluru on satellite imagery, zoom to level 13, and add a marker at city center.",
        "Center on Mount Fuji (latitude 35.3606, longitude 138.7274), switch to satellite, and enable 3D terrain.",
    ],
}

CATALOG_DATASETS = [
    {"name": "World Countries GeoJSON", "type": "Vector", "url": "https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/countries.geojson"},
    {"name": "Cyclone Idai COG", "type": "Raster COG", "url": "https://storage.googleapis.com/pdd-stac/disasters/cyclone-idai/sample.tif"},
    {"name": "CartoDB Positron Tiles", "type": "XYZ Tiles", "url": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png"},
    {"name": "USGS Shaded Relief", "type": "Elevation", "url": "Esri.WorldShadedRelief"},
]


def _safe_create_binding() -> tuple[Any | None, str]:
    """Create map binding without throwing render-time exceptions."""
    try:
        return create_ui_map_binding(), ""
    except Exception as exc:
        return None, str(exc)


@solara.component
def WorkspacePage() -> None:
    """Render the full TerraPulse Agentic GIS Workspace."""
    provider = solara.use_reactive(default_provider())
    model_id = solara.use_reactive(default_model_for_provider(provider.value))
    prompt = solara.use_reactive("")
    fast = solara.use_reactive(False)
    auto_approve = solara.use_reactive(True)  # Auto-approve enabled for responsive agent workflows
    busy = solara.use_reactive(False)
    history = solara.use_reactive([])
    jobs = solara.use_reactive([])
    active_job = solara.use_reactive(None)
    show_left_panel = solara.use_reactive(True)
    show_sample_prompts = solara.use_reactive(False)
    selected_basemap = solara.use_reactive("Esri.WorldImagery")

    binding_state = solara.use_memo(_safe_create_binding, dependencies=[])
    binding, binding_error = binding_state
    map_obj = binding.map_obj if binding is not None else None

    def _provider_changed(val: str) -> None:
        provider.set(val)
        model_id.set(default_model_for_provider(val))

    def _execute_prompt(query_text: str) -> None:
        text = query_text.strip()
        if not text or busy.value:
            return
        prompt.set("")
        busy.set(True)
        job_id = f"JOB-{len(jobs.value) + 1:03d}"
        start_time = time.time()
        job_record = {
            "id": job_id,
            "prompt": text,
            "status": "RUNNING",
            "start_time": time.strftime("%H:%M:%S"),
            "duration": "...",
            "tool_calls": [],
            "error": None,
        }
        active_job.set(job_record)
        jobs.set([job_record, *jobs.value])

        try:
            binding_obj, err = binding_state if isinstance(binding_state, tuple) else (None, "")
            new_history, tool_calls = dispatch_prompt(
                text,
                history=history.value,
                binding=binding_obj,
                binding_error=err,
                provider=provider.value,
                model_id=model_id.value,
                fast=fast.value,
                auto_approve=auto_approve.value,
            )
            duration = f"{time.time() - start_time:.2f}s"
            status = "SUCCESS" if (new_history and new_history[-1].get("status") == "ok") else "FAILED"
            job_record["status"] = status
            job_record["duration"] = duration
            job_record["tool_calls"] = tool_calls
            active_job.set(job_record)
            history.set(new_history)
        except Exception as exc:
            duration = f"{time.time() - start_time:.2f}s"
            job_record["status"] = "FAILED"
            job_record["duration"] = duration
            job_record["error"] = str(exc)
            active_job.set(job_record)
        finally:
            busy.set(False)

    def _send() -> None:
        _execute_prompt(prompt.value)

    def _quick_basemap(basemap_name: str) -> None:
        selected_basemap.set(basemap_name)
        if map_obj is not None:
            try:
                if hasattr(map_obj, "add_basemap"):
                    map_obj.add_basemap(basemap_name)
            except Exception:
                pass

    def _quick_3d_terrain() -> None:
        if map_obj is not None and hasattr(map_obj, "set_terrain"):
            try:
                map_obj.set_terrain(exaggeration=1.5)
            except Exception:
                pass

    def _clear_chat() -> None:
        history.set([])
        jobs.set([])
        active_job.set(None)

    # TerraPulse Dark GIS Style Rules & Solara Theme Overrides
    custom_css = """
    <style>
    /* Global overrides to eliminate Solara purple header */
    .v-application--wrap > header, 
    .v-toolbar, 
    .v-app-bar,
    .theme--light.v-app-bar.v-toolbar.v-sheet,
    header.v-sheet {
        background-color: #0f172a !important;
        border-bottom: 1px solid #1e293b !important;
        color: #f8fafc !important;
    }
    .v-application, .theme--light.v-application {
        background-color: #0b0f19 !important;
        color: #f1f5f9 !important;
    }
    .tp-workspace {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #0b0f19;
        color: #f1f5f9;
        min-height: 100vh;
    }
    .tp-header {
        background-color: #0f172a;
        border-bottom: 1px solid #1e293b;
        padding: 10px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .tp-panel {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .tp-btn {
        background-color: #1f2937;
        color: #f8fafc;
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 5px 12px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.15s ease-in-out;
    }
    .tp-btn:hover {
        background-color: #374151;
        border-color: #4b5563;
    }
    .tp-btn-primary {
        background-color: #0284c7;
        color: white;
        border: none;
        font-weight: 600;
    }
    .tp-btn-primary:hover {
        background-color: #0369a1;
    }
    .tp-tag {
        background-color: #0369a1;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    .tp-job-success {
        color: #34d399;
        font-weight: 600;
    }
    .tp-job-running {
        color: #38bdf8;
        font-weight: 600;
    }
    .tp-job-failed {
        color: #f87171;
        font-weight: 600;
    }
    /* Input & Select Dark Overrides */
    .v-input input, .v-select, .v-textarea textarea {
        color: #f8fafc !important;
    }
    .theme--light.v-card {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }
    </style>
    """

    solara.HTML(tag="div", unsafe_innerHTML=custom_css)

    with solara.Column(classes=["tp-workspace"], style={"width": "100%", "padding": "0"}):
        # 1. Top Application Bar
        with solara.Row(classes=["tp-header"], style={"alignItems": "center"}):
            with solara.Row(gap="10px", style={"alignItems": "center"}):
                solara.HTML(
                    tag="span",
                    unsafe_innerHTML='<b style="font-size: 18px; color: #38bdf8;">🌐 TerraPulse</b> <span style="font-size: 12px; color: #94a3b8;">Agentic GIS Platform v' + __version__ + '</span>',
                )
                solara.Button(
                    "📁 Explorer" if not show_left_panel.value else "✖ Close Explorer",
                    on_click=lambda: show_left_panel.set(not show_left_panel.value),
                    classes=["tp-btn"],
                )
                solara.Button(
                    "💡 Sample Prompts",
                    on_click=lambda: show_sample_prompts.set(not show_sample_prompts.value),
                    classes=["tp-btn"],
                )

            with solara.Row(gap="8px", style={"alignItems": "center"}):
                solara.HTML(tag="span", unsafe_innerHTML='<span style="font-size: 12px; color: #94a3b8;">Quick Basemap:</span>')
                solara.Button("Satellite", on_click=lambda: _quick_basemap("Esri.WorldImagery"), classes=["tp-btn"])
                solara.Button("Terrain", on_click=lambda: _quick_basemap("Esri.WorldTopoMap"), classes=["tp-btn"])
                solara.Button("Relief", on_click=lambda: _quick_basemap("Esri.WorldShadedRelief"), classes=["tp-btn"])
                solara.Button("3D Terrain", on_click=_quick_3d_terrain, classes=["tp-btn"])
                solara.HTML(tag="a", unsafe_innerHTML='<a href="http://localhost:8000" target="_blank" class="tp-btn tp-btn-primary" style="text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">🚀 TerraPulse Explorer & Investigator</a>')

        # 2. Main 3-Column Layout
        with solara.Row(gap="12px", style={"padding": "12px", "alignItems": "flex-start"}):
            # LEFT PANEL: Data Explorer & Layer Manager
            if show_left_panel.value:
                with solara.Column(classes=["tp-panel"], style={"width": "280px", "gap": "10px"}):
                    solara.HTML(tag="div", unsafe_innerHTML='<b style="color: #38bdf8;">📊 Data Explorer</b>')
                    solara.Markdown("Quickly add curated geospatial datasets to the active canvas:")
                    for ds in CATALOG_DATASETS:
                        with solara.Row(style={"justifyContent": "space-between", "alignItems": "center", "borderBottom": "1px solid #334155", "padding": "4px 0"}):
                            with solara.Column(gap="2px"):
                                solara.HTML(tag="span", unsafe_innerHTML=f'<span style="font-size: 13px; font-weight: 500;">{ds["name"]}</span>')
                                solara.HTML(tag="span", unsafe_innerHTML=f'<span class="tp-tag">{ds["type"]}</span>')
                            solara.Button(
                                "Add",
                                on_click=lambda url=ds["url"], n=ds["name"]: _execute_prompt(f"Add the layer from '{url}' named '{n}'"),
                                classes=["tp-btn"],
                            )

                    solara.HTML(tag="div", unsafe_innerHTML='<b style="color: #38bdf8; margin-top: 10px;">🗺️ Layer Manager</b>')
                    if map_obj is not None:
                        layers = getattr(map_obj, "layers", []) or []
                        if not layers:
                            solara.HTML(tag="span", unsafe_innerHTML='<span style="font-size: 12px; color: #94a3b8;">No custom layers loaded.</span>')
                        else:
                            for idx, lay in enumerate(layers):
                                l_name = str(lay.get("name") if isinstance(lay, dict) else getattr(lay, "name", f"Layer {idx+1}"))
                                with solara.Row(style={"justifyContent": "space-between", "alignItems": "center"}):
                                    solara.HTML(tag="span", unsafe_innerHTML=f'<span style="font-size: 12px;">• {l_name}</span>')
                                    solara.Button(
                                        "Hide",
                                        on_click=lambda name=l_name: _execute_prompt(f"Hide the layer '{name}'"),
                                        classes=["tp-btn"],
                                    )
                    solara.Button(
                        "Clear All Layers",
                        on_click=lambda: _execute_prompt("Clear all layers from the map."),
                        classes=["tp-btn"],
                    )

            # CENTER PANEL: Main Interactive Map Canvas
            with solara.Column(classes=["tp-panel"], style={"flex": "1", "minWidth": "480px", "gap": "8px"}):
                with solara.Row(style={"justifyContent": "space-between", "alignItems": "center"}):
                    solara.HTML(tag="div", unsafe_innerHTML='<b style="color: #38bdf8;">🌍 Central Interactive Map (MapLibre / AnyMap)</b>')
                    if busy.value:
                        solara.HTML(tag="span", unsafe_innerHTML='<span style="color: #38bdf8; font-size: 12px;">⚡ Agent executing tool...</span>')
                    else:
                        solara.HTML(tag="span", unsafe_innerHTML='<span style="color: #4ade80; font-size: 12px;">● Live & Ready</span>')

                if binding_error:
                    solara.Markdown(f"**Map unavailable**: {binding_error}")
                elif map_obj is not None:
                    solara.display(map_obj)
                else:
                    solara.Markdown("Map instance loading...")

                # Map Status Bar
                with solara.Row(style={"justifyContent": "space-between", "color": "#94a3b8", "fontSize": "11px", "marginTop": "4px"}):
                    solara.HTML(tag="span", unsafe_innerHTML="Default Basemap: High-Resolution Satellite (Esri WorldImagery)")
                    solara.HTML(tag="span", unsafe_innerHTML="MapLibre GL JS | 3D Terrain Supported")

            # RIGHT PANEL: AI Agent, Settings, Jobs, & Chat
            with solara.Column(classes=["tp-panel"], style={"width": "380px", "gap": "10px"}):
                solara.HTML(tag="div", unsafe_innerHTML='<b style="color: #38bdf8;">🤖 TerraPulse AI Agent</b>')

                # Provider & Configuration
                with solara.Column(gap="4px"):
                    solara.Select(label="Provider", values=list(PROVIDER_NAMES), value=provider.value, on_value=_provider_changed)
                    solara.InputText(label="Model ID", value=model_id.value, on_value=model_id.set)
                    with solara.Row():
                        solara.Checkbox(label="Fast mode", value=fast.value, on_value=fast.set)
                        solara.Checkbox(label="Auto-approve tools", value=auto_approve.value, on_value=auto_approve.set)

                # Jobs & Execution Tracker
                solara.HTML(tag="div", unsafe_innerHTML='<b style="color: #38bdf8; margin-top: 4px;">⚡ Jobs & Tool Execution</b>')
                if not jobs.value:
                    solara.HTML(tag="span", unsafe_innerHTML='<span style="font-size: 12px; color: #94a3b8;">No jobs executed yet. Submit a prompt below.</span>')
                else:
                    curr = jobs.value[0]
                    status_class = "tp-job-running" if curr["status"] == "RUNNING" else ("tp-job-success" if curr["status"] == "SUCCESS" else "tp-job-failed")
                    with solara.Column(style={"background": "#0f172a", "padding": "8px", "borderRadius": "4px", "fontSize": "12px"}):
                        solara.HTML(tag="div", unsafe_innerHTML=f'<b>{curr["id"]}</b> | <span class="{status_class}">{curr["status"]}</span> ({curr["duration"]})')
                        solara.HTML(tag="div", unsafe_innerHTML=f'<i>Query:</i> {curr["prompt"]}')
                        if curr["tool_calls"]:
                            solara.HTML(tag="div", unsafe_innerHTML='<b>Executed Tools:</b>')
                            for call in curr["tool_calls"]:
                                solara.HTML(tag="div", unsafe_innerHTML=f'<code style="font-size: 11px; color: #38bdf8;">• {compact_tool_call(call)}</code>')
                        elif curr["error"]:
                            solara.HTML(tag="div", unsafe_innerHTML=f'<span style="color: #f87171;">Error: {curr["error"]}</span>')

                # Chat Transcript
                solara.HTML(tag="div", unsafe_innerHTML='<b style="color: #38bdf8; margin-top: 4px;">💬 Chat Transcript</b>')
                with solara.Column(style={"maxHeight": "240px", "overflowY": "auto", "gap": "6px"}):
                    if not history.value:
                        solara.HTML(tag="span", unsafe_innerHTML='<span style="font-size: 12px; color: #94a3b8;">Ask TerraPulse to zoom, change basemaps, add COGs, or render terrain.</span>')
                    for msg in history.value:
                        role = str(msg.get("role") or "").title()
                        txt = str(msg.get("text") or "")
                        is_user = msg.get("role") == "user"
                        bg = "#334155" if is_user else "#0f172a"
                        with solara.Column(style={"background": bg, "padding": "6px 8px", "borderRadius": "4px", "fontSize": "12px"}):
                            solara.HTML(tag="b", unsafe_innerHTML=f'<span style="color: {"#38bdf8" if is_user else "#4ade80"};">{role}:</span>')
                            solara.Markdown(txt)

                # Prompt Input Box
                solara.InputTextArea(
                    label="Command TerraPulse",
                    value=prompt.value,
                    on_value=prompt.set,
                    rows=3,
                )
                with solara.Row(style={"justifyContent": "space-between"}):
                    solara.Button(
                        "Execute Command",
                        on_click=_send,
                        disabled=busy.value or not prompt.value.strip(),
                        classes=["tp-btn", "tp-btn-primary"],
                    )
                    solara.Button("Clear History", on_click=_clear_chat, classes=["tp-btn"])

                if busy.value:
                    solara.ProgressLinear()

        # 3. Collapsible Sample Prompts Drawer
        if show_sample_prompts.value:
            with solara.Column(classes=["tp-panel"], style={"margin": "0 12px 12px 12px", "background": "#1e293b"}):
                solara.HTML(tag="div", unsafe_innerHTML='<b style="font-size: 15px; color: #38bdf8;">💡 Curated Sample Prompts (Click to Execute)</b>')
                with solara.Row(gap="16px", style={"flexWrap": "wrap", "marginTop": "8px"}):
                    for category, prompts_list in SAMPLE_PROMPT_CATEGORIES.items():
                        with solara.Column(style={"minWidth": "220px", "maxWidth": "320px", "flex": "1", "gap": "4px"}):
                            solara.HTML(tag="span", unsafe_innerHTML=f'<b style="color: #94a3b8; font-size: 13px;">{category}</b>')
                            for sp in prompts_list:
                                solara.Button(
                                    sp,
                                    on_click=lambda p=sp: _execute_prompt(p),
                                    classes=["tp-btn"],
                                    style={"textAlign": "left", "fontSize": "11px", "marginBottom": "4px"},
                                )


__all__ = ["WorkspacePage"]
