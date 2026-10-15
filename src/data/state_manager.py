"""TerraPulse v2.0 Centralized State & Provenance Manager.

Establishes a single source of truth for:
- Location, coordinates, and bounding box (AOI)
- STAC Provider & acquisition query parameters
- Discovered satellite observations & source scenes
- Active 4-tile fused georeferenced mosaic
- Selected primary observation & cached assets
- Real computed environmental layers (NDVI, CIR, NDWI, NDBI, Land Cover, Population)
- Conditional bi-temporal alignment & change detection (t0 vs t1)
- Evidence-based AI environmental investigation synthesis
- Expandable diagnostics (SIFT/RANSAC, Model Studio, World Model)

Ensures consistent cache invalidation:
- Location change -> invalidates all location-dependent scenes, mosaics, and analyses
- Observation selection change -> refreshes imagery and all dependent layers
- Preserves cache across repeat visits to identical observation IDs
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import streamlit as st

from src.data.sentinel_service import geocode_user_location
from src.data.sentinel_explorer import (
    search_sentinel2_scenes,
    auto_detect_2x2_tiles,
    build_real_sentinel2_mosaic,
    retrieve_sentinel2_data,
    build_georeferenced_mosaic,
    calculate_environmental_layers,
    align_bitemporal_observations,
    SentinelSceneMetadata,
    ObservationData,
    EnvironmentalLayers,
    StitchingLaboratoryData,
)

POPULAR_LOCATIONS = {
    "Bengaluru, India": "Bengaluru, Karnataka, India",
    "Tokyo Bay, Japan": "Tokyo Bay Megalopolis, Japan",
    "Cairo & Nile, Egypt": "Nile Delta & Cairo, Egypt",
    "Swiss Alps": "Swiss Alps (Rhone Glacier), Switzerland",
    "Grand Canyon, USA": "Grand Canyon, Arizona, USA",
    "Paris, France": "Paris, France",
    "Dubai, UAE": "Dubai, United Arab Emirates"
}

HISTORICAL_EPOCHS = {
    "Recent (2024–2025)": "2024-01-01/..",
    "Epoch 2023–2024": "2023-01-01/2024-12-31",
    "Epoch 2020–2021": "2020-01-01/2021-12-31",
    "Historical (2017–2018)": "2017-01-01/2018-12-31",
    "Full Archive (2016–Present)": "2016-01-01/.."
}


class AppStateManager:
    """Central state controller binding all TerraPulse v2.0 workspaces to a single source of truth."""

    # Key namespace constants in st.session_state
    KEY_LOCATION_QUERY = "tp2_location_query"
    KEY_GEOCODED = "tp2_geocoded"
    KEY_STAC_PROVIDER = "tp2_stac_provider"
    KEY_EPOCH_LABEL = "tp2_epoch_label"
    KEY_MAX_CLOUD = "tp2_max_cloud"
    KEY_DECIMATION = "tp2_decimation"
    KEY_DISCOVERED_SCENES = "tp2_discovered_scenes"
    KEY_AUTO_4_SCENES = "tp2_auto_4_scenes"
    KEY_PRIMARY_OBS_ID = "tp2_primary_obs_id"
    KEY_PRIMARY_MOSAIC = "tp2_primary_mosaic"
    KEY_CACHED_OBS = "tp2_cached_observations"
    KEY_ENV_LAYERS = "tp2_env_layers"
    KEY_SECONDARY_SCENE_ID = "tp2_secondary_scene_id"
    KEY_COMPARISON_RESULT = "tp2_comparison_result"
    KEY_STATUS_MESSAGES = "tp2_status_messages"

    @classmethod
    def init_state(cls):
        """Initializes default application state on first run."""
        if cls.KEY_LOCATION_QUERY not in st.session_state:
            st.session_state[cls.KEY_LOCATION_QUERY] = "Bengaluru, Karnataka, India"
            cls._update_geocoded("Bengaluru, Karnataka, India")

        if cls.KEY_STAC_PROVIDER not in st.session_state:
            st.session_state[cls.KEY_STAC_PROVIDER] = "Planetary Computer (Streaming COGs)"

        if cls.KEY_EPOCH_LABEL not in st.session_state:
            st.session_state[cls.KEY_EPOCH_LABEL] = "Recent (2024–2025)"

        if cls.KEY_MAX_CLOUD not in st.session_state:
            st.session_state[cls.KEY_MAX_CLOUD] = 25.0

        if cls.KEY_DECIMATION not in st.session_state:
            st.session_state[cls.KEY_DECIMATION] = 12

        if cls.KEY_CACHED_OBS not in st.session_state:
            st.session_state[cls.KEY_CACHED_OBS] = {}

        if cls.KEY_STATUS_MESSAGES not in st.session_state:
            st.session_state[cls.KEY_STATUS_MESSAGES] = []

    @classmethod
    def _update_geocoded(cls, query: str):
        """Geocodes a query and computes target UTM and a 40km bounding box."""
        geo = geocode_user_location(query)
        lat, lon = geo["lat"], geo["lon"]
        # ~40km footprint for 2x2 multi-swath boundary
        bbox = [round(lon - 0.40, 4), round(lat - 0.40, 4), round(lon + 0.40, 4), round(lat + 0.40, 4)]
        d_lon_km = (bbox[2] - bbox[0]) * 111.32 * np.cos(np.radians(lat))
        d_lat_km = (bbox[3] - bbox[1]) * 110.57
        geo["bbox"] = bbox
        geo["est_area_km2"] = round(abs(d_lon_km * d_lat_km), 1)
        st.session_state[cls.KEY_GEOCODED] = geo

    @classmethod
    def set_location(cls, new_query: str):
        """Changes the active location and systematically invalidates all location-dependent results."""
        if not new_query or new_query.strip() == "":
            return

        current_query = st.session_state.get(cls.KEY_LOCATION_QUERY, "")
        if new_query.strip() != current_query.strip():
            st.session_state[cls.KEY_LOCATION_QUERY] = new_query.strip()
            cls._update_geocoded(new_query.strip())

            # Systematic Invalidation of stale location artifacts
            st.session_state.pop(cls.KEY_DISCOVERED_SCENES, None)
            st.session_state.pop(cls.KEY_AUTO_4_SCENES, None)
            st.session_state.pop(cls.KEY_PRIMARY_OBS_ID, None)
            st.session_state.pop(cls.KEY_PRIMARY_MOSAIC, None)
            st.session_state.pop(cls.KEY_ENV_LAYERS, None)
            st.session_state.pop(cls.KEY_SECONDARY_SCENE_ID, None)
            st.session_state.pop(cls.KEY_COMPARISON_RESULT, None)
            st.session_state[cls.KEY_CACHED_OBS] = {}
            st.session_state["latest_sentinel_mosaic"] = None

    @classmethod
    def get_geocoded(cls) -> Dict[str, Any]:
        """Returns the geocoded metadata for the current location."""
        return st.session_state.get(cls.KEY_GEOCODED, {
            "name": "Bengaluru, Karnataka, India",
            "lat": 12.9716,
            "lon": 77.5946,
            "target_utm": "EPSG:32643",
            "bbox": [77.1946, 12.5716, 77.9946, 13.3716],
            "est_area_km2": 7780.0
        })

    @classmethod
    def get_query_params(cls) -> Tuple[str, str, float, int]:
        """Returns (provider_key, datetime_range, max_cloud, decimation)."""
        prov_label = st.session_state.get(cls.KEY_STAC_PROVIDER, "Planetary Computer (Streaming COGs)")
        prov_key = "planetary_computer" if "Planetary" in prov_label else "copernicus"

        epoch_label = st.session_state.get(cls.KEY_EPOCH_LABEL, "Recent (2024–2025)")
        dt_range = HISTORICAL_EPOCHS.get(epoch_label, "2024-01-01/..")

        max_cld = float(st.session_state.get(cls.KEY_MAX_CLOUD, 25.0))
        decim = int(st.session_state.get(cls.KEY_DECIMATION, 12))

        return prov_key, dt_range, max_cld, decim

    @classmethod
    def ensure_discovered_scenes(cls) -> List[SentinelSceneMetadata]:
        """Discovers real Sentinel-2 scenes for the current location & query params."""
        if cls.KEY_DISCOVERED_SCENES in st.session_state:
            return st.session_state[cls.KEY_DISCOVERED_SCENES]

        geo = cls.get_geocoded()
        prov_key, dt_range, max_cld, _ = cls.get_query_params()

        scenes = search_sentinel2_scenes(
            bbox=geo["bbox"],
            datetime_range=dt_range,
            provider=prov_key,
            max_cloud=max_cld,
            limit=20
        )

        st.session_state[cls.KEY_DISCOVERED_SCENES] = scenes

        if scenes:
            auto_4 = auto_detect_2x2_tiles(scenes, target_lat=geo["lat"], target_lon=geo["lon"])
            st.session_state[cls.KEY_AUTO_4_SCENES] = auto_4
            if cls.KEY_PRIMARY_OBS_ID not in st.session_state:
                st.session_state[cls.KEY_PRIMARY_OBS_ID] = "mosaic"

        return scenes

    @classmethod
    def get_auto_4_scenes(cls) -> List[SentinelSceneMetadata]:
        """Returns the 4 automatically detected quadrant scenes (NW, NE, SW, SE)."""
        if cls.KEY_AUTO_4_SCENES in st.session_state:
            return st.session_state[cls.KEY_AUTO_4_SCENES]
        scenes = cls.ensure_discovered_scenes()
        geo = cls.get_geocoded()
        auto_4 = auto_detect_2x2_tiles(scenes, target_lat=geo["lat"], target_lon=geo["lon"])
        st.session_state[cls.KEY_AUTO_4_SCENES] = auto_4
        return auto_4

    @classmethod
    def ensure_primary_mosaic(cls) -> Optional[ObservationData]:
        """Retrieves and stitches the 4-tile fused square mosaic for the current location."""
        if cls.KEY_PRIMARY_MOSAIC in st.session_state and st.session_state[cls.KEY_PRIMARY_MOSAIC] is not None:
            return st.session_state[cls.KEY_PRIMARY_MOSAIC]

        auto_4 = cls.get_auto_4_scenes()
        if not auto_4:
            return None

        geo = cls.get_geocoded()
        _, _, _, decim = cls.get_query_params()

        # Try high-fidelity multi-band streaming
        mosaic_data = build_real_sentinel2_mosaic(
            scenes=auto_4,
            target_crs=geo["target_utm"],
            bbox=geo["bbox"],
            decimation_scale=decim,
            stretch_val=2400.0
        )

        # Resilient fallback to individual scene download & georeferenced stitching
        if not mosaic_data:
            obs_list = []
            for s in auto_4:
                obs_tile = retrieve_sentinel2_data(s, bands=["B04", "B03", "B02", "B08"], decimation_scale=decim)
                if obs_tile:
                    obs_list.append(obs_tile)
            if obs_list:
                mosaic_data = build_georeferenced_mosaic(obs_list, target_crs=geo["target_utm"])

        if mosaic_data:
            st.session_state[cls.KEY_PRIMARY_MOSAIC] = mosaic_data
            st.session_state["latest_sentinel_mosaic"] = mosaic_data.rgb
            # Cache under "mosaic" ID
            st.session_state[cls.KEY_CACHED_OBS]["mosaic"] = mosaic_data

        return mosaic_data

    @classmethod
    def get_active_observation(cls) -> Optional[ObservationData]:
        """Returns the currently active ObservationData (mosaic or individual scene)."""
        selected_id = st.session_state.get(cls.KEY_PRIMARY_OBS_ID, "mosaic")

        if selected_id == "mosaic":
            return cls.ensure_primary_mosaic()

        # Check cache
        cached = st.session_state.get(cls.KEY_CACHED_OBS, {})
        if selected_id in cached:
            return cached[selected_id]

        # Retrieve specific scene
        scenes = cls.ensure_discovered_scenes()
        target_scene = next((s for s in scenes if s.id == selected_id), None)
        if target_scene:
            _, _, _, decim = cls.get_query_params()
            obs = retrieve_sentinel2_data(target_scene, bands=["B04", "B03", "B02", "B08"], decimation_scale=decim)
            if obs:
                st.session_state[cls.KEY_CACHED_OBS][selected_id] = obs
                return obs

        # Fallback to mosaic
        return cls.ensure_primary_mosaic()

    @classmethod
    def set_selected_observation_id(cls, obs_id: str):
        """Sets the selected observation ID and invalidates dependent environmental analysis."""
        current_id = st.session_state.get(cls.KEY_PRIMARY_OBS_ID)
        if current_id != obs_id:
            st.session_state[cls.KEY_PRIMARY_OBS_ID] = obs_id
            st.session_state.pop(cls.KEY_ENV_LAYERS, None)
            st.session_state.pop(cls.KEY_COMPARISON_RESULT, None)

    @classmethod
    def ensure_environmental_layers(cls) -> Optional[EnvironmentalLayers]:
        """Calculates or retrieves verified environmental CV layers from the active observation."""
        if cls.KEY_ENV_LAYERS in st.session_state and st.session_state[cls.KEY_ENV_LAYERS] is not None:
            return st.session_state[cls.KEY_ENV_LAYERS]

        active_obs = cls.get_active_observation()
        if active_obs is None:
            return None

        layers = calculate_environmental_layers(active_obs)
        st.session_state[cls.KEY_ENV_LAYERS] = layers
        return layers

    @classmethod
    def run_temporal_comparison(cls, secondary_scene_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Aligns secondary observation with active observation and computes change detection."""
        primary_obs = cls.get_active_observation()
        if primary_obs is None:
            return False, "Primary observation is not loaded yet.", None

        scenes = cls.ensure_discovered_scenes()
        sec_scene = next((s for s in scenes if s.id == secondary_scene_id), None)
        if not sec_scene:
            return False, f"Secondary scene '{secondary_scene_id}' not found in catalogue.", None

        # Retrieve or use cached secondary observation
        cached = st.session_state.get(cls.KEY_CACHED_OBS, {})
        _, _, _, decim = cls.get_query_params()

        if secondary_scene_id in cached:
            sec_obs = cached[secondary_scene_id]
        else:
            sec_obs = retrieve_sentinel2_data(sec_scene, bands=["B04", "B03", "B02", "B08"], decimation_scale=decim)
            if sec_obs:
                st.session_state[cls.KEY_CACHED_OBS][secondary_scene_id] = sec_obs
            else:
                return False, f"Failed to download spectral bands for {sec_scene.date_str}.", None

        # Align grids and calculate delta
        crop0, crop1, delta_ndvi, comp_meta = align_bitemporal_observations(sec_obs, primary_obs)

        result = {
            "scene_t0": sec_scene,
            "obs_t0": sec_obs,
            "obs_t1": primary_obs,
            "crop_t0": crop0,
            "crop_t1": crop1,
            "delta_ndvi": delta_ndvi,
            "meta": comp_meta
        }
        st.session_state[cls.KEY_SECONDARY_SCENE_ID] = secondary_scene_id
        st.session_state[cls.KEY_COMPARISON_RESULT] = result
        return True, "Successfully harmonized spatial grids and computed bi-temporal change.", result

    @classmethod
    def get_comparison_result(cls) -> Optional[Dict[str, Any]]:
        """Returns the current bi-temporal comparison result if computed."""
        return st.session_state.get(cls.KEY_COMPARISON_RESULT)
