"""Tests for TerraPulse v2.0 State Manager and Unified Workspaces."""

import numpy as np
import pytest
import streamlit as st

from src.data.state_manager import AppStateManager
from src.data.sentinel_explorer import (
    SentinelSceneMetadata,
    ObservationData,
    EnvironmentalLayers,
    calculate_environmental_layers
)


def test_state_manager_initialization():
    """Verify default state variables and location resolution."""
    AppStateManager.init_state()
    geo = AppStateManager.get_geocoded()

    assert "lat" in geo
    assert "lon" in geo
    assert "target_utm" in geo
    assert "bbox" in geo
    assert len(geo["bbox"]) == 4
    assert geo["bbox"][0] < geo["bbox"][2]
    assert geo["bbox"][1] < geo["bbox"][3]


def test_state_manager_location_invalidation():
    """Verify that changing location invalidates previous scenes, mosaics, and comparisons."""
    AppStateManager.init_state()
    initial_geo = AppStateManager.get_geocoded()
    assert "Bengaluru" in initial_geo["name"]

    # Mock setting some cached artifacts
    st.session_state[AppStateManager.KEY_PRIMARY_OBS_ID] = "test_scene_1"
    st.session_state[AppStateManager.KEY_DISCOVERED_SCENES] = ["scene1", "scene2"]
    st.session_state[AppStateManager.KEY_PRIMARY_MOSAIC] = "dummy_mosaic"
    st.session_state[AppStateManager.KEY_ENV_LAYERS] = "dummy_layers"

    # Now change location to Tokyo
    AppStateManager.set_location("Tokyo Bay Megalopolis, Japan")
    new_geo = AppStateManager.get_geocoded()

    assert "Tokyo" in new_geo["name"]
    # Verify stale items are invalidated
    assert AppStateManager.KEY_PRIMARY_OBS_ID not in st.session_state
    assert AppStateManager.KEY_DISCOVERED_SCENES not in st.session_state
    assert AppStateManager.KEY_PRIMARY_MOSAIC not in st.session_state
    assert AppStateManager.KEY_ENV_LAYERS not in st.session_state


def test_state_manager_observation_switching():
    """Verify that switching observation invalidates dependent environmental layers."""
    AppStateManager.init_state()
    st.session_state[AppStateManager.KEY_PRIMARY_OBS_ID] = "mosaic"
    st.session_state[AppStateManager.KEY_ENV_LAYERS] = "mosaic_layers"

    AppStateManager.set_selected_observation_id("scene_2024_03")
    assert st.session_state[AppStateManager.KEY_PRIMARY_OBS_ID] == "scene_2024_03"
    assert AppStateManager.KEY_ENV_LAYERS not in st.session_state


def test_environmental_layers_derivation():
    """Verify that environmental layers are accurately calculated from active observation bands."""
    h, w = 60, 60
    # Synthetic bands
    r = np.ones((h, w), dtype=np.float32) * 0.10
    g = np.ones((h, w), dtype=np.float32) * 0.15
    b = np.ones((h, w), dtype=np.float32) * 0.08
    nir = np.ones((h, w), dtype=np.float32) * 0.40  # Healthy vegetation: NIR > Red

    rgb = np.stack([(r * 255).astype(np.uint8), (g * 255).astype(np.uint8), (b * 255).astype(np.uint8)], axis=-1)
    bands = {"B02": b, "B03": g, "B04": r, "B08": nir}

    obs = ObservationData(
        id="SYNTHETIC_OBS",
        date_str="2024-05-15",
        platform="Sentinel-2A",
        cloud_cover=2.0,
        crs="EPSG:32643",
        bbox=[77.5, 12.9, 77.6, 13.0],
        rgb=rgb,
        red=r,
        green=g,
        blue=b,
        nir=nir
    )

    layers = calculate_environmental_layers(obs)
    assert layers is not None
    assert layers.ndvi is not None
    assert layers.ndwi is not None
    assert layers.ndbi is not None
    assert layers.landcover is not None
    assert layers.stats["mean_ndvi"] > 0.4  # Expected for high NIR and low Red
