# GeoAgent Tool Inventory

**Project:** GeoAgent  
**Version:** 1.9.1  
**Architecture:** Strands Agents framework with LiteLLM (`groq/openai/gpt-oss-120b`), AnyMap (MapLibre GL JS) and Solara web UI, plus PyQGIS desktop integration.  
**Audit Date:** 2026-10-31  

---

## 1. Executive Summary & Architecture Overview

GeoAgent 1.9.1 defines tools across 14 modules totaling **160 tool registrations** across environments (and **113 unique tool names**). 

In the active runtime specified in the audit context (**Solara UI with AnyMap / MapLibre**):
- When instantiated via `geoagent.ui.app.create_ui_map_binding()`, GeoAgent binds to `anymap.Map` (specifically `anymap.maplibre.MapLibreMap`) and registers **25 active tools** (24 AnyMap tools from `geoagent.tools.anymap` plus 1 image generation tool from `geoagent.tools.images`).
- For complete developer and QA reference, this inventory documents:
  1. The **Primary Runtime Surface (Solara UI + AnyMap)**: 25 tools immediately exposed to the user in chat.
  2. The **Alternative / Specialized Plugin Surfaces**: The remaining 88 tools covering PyQGIS, Browser MapLibre session, WhiteboxTools, NASA Earthdata, NASA OPERA, Google Earth Engine, HyperCoast, STAC, Vantor, Timelapse, and GeoAI.

---

## 2. Primary Runtime Surface: Solara UI + AnyMap (25 Tools)

These 25 tools are actively loaded when GeoAgent runs in the Solara web interface with AnyMap.

| # | Tool Name | Category | Confirmation Required | Required Parameters | Optional Parameters | Return Type | Primary Purpose |
|---|---|---|:---:|---|---|---|---|
| 1 | `list_layers` | `map` | No | None | None | `list[dict[str, Any]]` | List all layers currently tracked on the AnyMap instance. |
| 2 | `add_layer` | `map` | No | `url` (str), `name` (str) | `layer_type="auto"` (str) | `str` | Add a raster, vector, COG, PMTiles, or XYZ layer by URL with auto-detection. |
| 3 | `remove_layer` | `map` | **Yes** | `name` (str) | None | `str` | Remove a named layer from the map. |
| 4 | `clear_layers` | `map` | **Yes** | None | None | `str` | Remove all layers currently tracked by the map. |
| 5 | `set_layer_visibility` | `map` | No | `name` (str), `visible` (bool) | None | `str` | Toggle layer visibility (show or hide). |
| 6 | `set_layer_opacity` | `map` | No | `name` (str), `opacity` (float) | None | `str` | Adjust opacity of a named layer from 0.0 to 1.0. |
| 7 | `set_center` | `map` | No | `lat` (float), `lon` (float) | `zoom=None` (int) | `str` | Centre the map on latitude and longitude coordinates. |
| 8 | `fly_to` | `map` | No | `lat` (float), `lon` (float) | `zoom=None` (int) | `str` | Smoothly animate or pan the camera to coordinates and zoom. |
| 9 | `set_zoom` | `map` | No | `zoom` (int) | None | `str` | Set explicit zoom level. |
| 10 | `zoom_in` | `map` | No | None | `steps=1` (int) | `str` | Increase zoom level by integer step count. |
| 11 | `zoom_out` | `map` | No | None | `steps=1` (int) | `str` | Decrease zoom level by integer step count. |
| 12 | `zoom_to_bounds` | `map` | No | `west` (float), `south` (float), `east` (float), `north` (float) | None | `str` | Zoom the map to fit a bounding box `[west, south, east, north]`. |
| 13 | `zoom_to_layer` | `map` | No | `name` (str) | None | `str` | Zoom to a layer's recorded bounding box. |
| 14 | `change_basemap` | `map` | No | `basemap` (str) | None | `str` | Change the map style/basemap (e.g. `CartoDB.Positron`, `OpenStreetMap`). |
| 15 | `add_vector_data` | `map` | No | `path_or_url` (str), `name` (str) | `style=None` (dict) | `str` | Add vector data (GeoJSON, Shapefile URL/path). |
| 16 | `add_geojson_data` | `map` | No | `data` (dict), `name` (str) | `style=None` (dict) | `str` | Add an in-memory GeoJSON FeatureCollection or geometry dict. |
| 17 | `add_marker` | `map` | No | `lat` (float), `lon` (float) | `popup=None`, `tooltip=None`, `name=None` | `str` | Add an interactive point marker with tooltip/popup. |
| 18 | `add_raster_data` | `map` | No | `path_or_url` (str), `name` (str) | `colormap="viridis"` (str) | `str` | Add a raster dataset layer with optional colormap. |
| 19 | `add_stac_layer` | `map` | No | `collection` (str) | `item=None`, `assets=None`, `name=None`, `titiler_endpoint=None` | `str` | Add a STAC layer to the map via TiTiler tile service. |
| 20 | `add_cog_layer` | `map` | No | `url` (str), `name` (str) | `colormap="viridis"`, `titiler_endpoint=None` | `str` | Add a Cloud Optimized GeoTIFF tile layer. |
| 21 | `add_xyz_tile_layer` | `map` | No | `url` (str), `name` (str) | `attribution=""` (str) | `str` | Add custom XYZ slippy tile service URL template. |
| 22 | `add_pmtiles_layer` | `map` | No | `url` (str), `name` (str) | `style=None` (dict) | `str` | Add a PMTiles vector/raster tile archive. |
| 23 | `get_map_state` | `map` | No | None | None | `dict[str, Any]` | Return current camera state (center, zoom, bounds, pitch, bearing). |
| 24 | `save_map` | `map` | **Yes** | `path` (str) | None | `str` | Export current map view and layers to a standalone HTML file. |
| 25 | `generate_image` | `image_generation` | No | `prompt` (str) | `size="1024x1024"`, `quality="low"`, `model=""`, `output_dir=""`, etc. | `dict[str, Any]` | Generate an image or diagram asset via configured vision model. |

---

## 3. Tool Categorization Matrix

| Category ID | Functional Category | Tools in Solara AnyMap Runtime | Total Across Entire Repo |
|:---:|---|---|:---:|
| **CAT-01** | Map Navigation & View Control | `set_center`, `fly_to`, `set_zoom`, `zoom_in`, `zoom_out`, `zoom_to_bounds`, `zoom_to_layer`, `get_map_state` | 13 tools |
| **CAT-02** | Basemap Management | `change_basemap` | 2 tools |
| **CAT-03** | Map Layer Management & Inspection | `list_layers`, `remove_layer`, `clear_layers`, `set_layer_visibility`, `set_layer_opacity`, `save_map` | 14 tools |
| **CAT-04** | Vector & GeoJSON Data | `add_vector_data`, `add_geojson_data`, `add_marker` | 8 tools |
| **CAT-05** | Raster, Tile & Cloud Formats (COG, XYZ, PMTiles) | `add_layer`, `add_raster_data`, `add_cog_layer`, `add_xyz_tile_layer`, `add_pmtiles_layer` | 12 tools |
| **CAT-06** | STAC Catalogues & Collections | `add_stac_layer` | 6 tools |
| **CAT-07** | Multimodal & Asset Generation | `generate_image` | 1 tool |
| **CAT-08** | Desktop GIS & PyQGIS Automation | *Available in QGIS runtime* | 29 tools |
| **CAT-09** | Earth Observation & Remote Sensing APIs | *Available in QGIS plugin runtimes* (OPERA, Earthdata, GEE, HyperCoast, Vantor, Timelapse) | 50 tools |
| **CAT-10** | Geoprocessing & Spatial Analysis | *Available in Whitebox & GeoAI runtimes* | 10 tools |

---

## 4. Complete Tool Breakdown Across All Modules

### 4.1 `geoagent.tools.anymap` (24 tools)
- **Module File:** `geoagent/tools/anymap.py`
- **Dependencies:** `anymap` (MapLibre GL JS backend).
- **Decorators:** `@geo_tool(category="map")`.
- **Runtime Confirmation Required:** `remove_layer`, `clear_layers`, `save_map`.

### 4.2 `geoagent.tools.leafmap` (24 tools)
- **Module File:** `geoagent/tools/leafmap.py`
- **Dependencies:** `leafmap` (ipyleaflet / folium backend).
- **Tools:** Equivalent suite to AnyMap for Leaflet / ipyleaflet environments.

### 4.3 `geoagent.tools.browser_maplibre` (17 tools)
- **Module File:** `geoagent/tools/browser_maplibre.py`
- **Dependencies:** Browser headless or remote WebSocket session (`geoagent.browser.session`).
- **Tools:** `list_layers`, `get_map_state`, `set_center`, `fly_to`, `set_zoom`, `zoom_to_bounds`, `change_basemap`, `add_marker`, `add_geojson_data`, `add_vector_data`, `add_xyz_tile_layer`, `set_layer_visibility`, `set_layer_opacity`, `query_rendered_features`, `screenshot_map`, `remove_layer`, `clear_layers`, plus optional `run_maplibre_script`.

### 4.4 `geoagent.tools.images` (1 tool)
- **Module File:** `geoagent/tools/images.py`
- **Tool:** `generate_image`.
- **Dependencies:** LiteLLM / OpenAI image endpoints.

### 4.5 `geoagent.tools.qgis` (29 tools)
- **Module File:** `geoagent/tools/qgis.py`
- **Dependencies:** `qgis.core`, `qgis.gui`, PyQt5/6.
- **Tools:** `list_project_layers`, `get_active_layer`, `get_project_state`, `zoom_in`, `zoom_out`, `zoom_to_layer`, `zoom_to_extent`, `set_center`, `set_scale`, `add_vector_layer`, `add_raster_layer`, `add_xyz_tile_layer`, `remove_layer`, `set_layer_visibility`, `set_layer_opacity`, `set_layer_symbology`, `create_hillshade_layer`, `inspect_layer_fields`, `get_selected_features`, `select_features_by_expression`, `clear_selection`, `zoom_to_selected`, `get_layer_summary`, `run_processing_algorithm`, `buffer_active_layer`, `open_attribute_table`, `refresh_canvas`, `run_pyqgis_script`, `save_project`.

### 4.6 `geoagent.tools.stac` (5 tools)
- **Module File:** `geoagent/tools/stac.py`
- **Dependencies:** `pystac_client`, `requests`.
- **Tools:** `get_current_stac_search_extent`, `list_stac_collections`, `search_stac_items`, `get_stac_item_assets`, `add_stac_asset_to_qgis`.

### 4.7 `geoagent.tools.nasa_earthdata` (8 tools)
- **Module File:** `geoagent/tools/nasa_earthdata.py`
- **Dependencies:** NASA Earthdata CMR API, Earthdata Login credentials.
- **Tools:** `search_earthdata_catalog`, `get_earthdata_dataset_info`, `search_earthdata_data`, `display_earthdata_footprints`, `load_earthdata_raster`, `create_earthdata_rgb_composite`, `open_nasa_earthdata_search_panel`, `open_nasa_earthdata_settings`.

### 4.8 `geoagent.tools.nasa_opera` (8 tools)
- **Module File:** `geoagent/tools/nasa_opera.py`
- **Dependencies:** NASA OPERA SAR/optical endpoints, rasterio/GDAL.
- **Tools:** `get_available_datasets`, `get_dataset_info`, `search_opera_data`, `display_footprints`, `display_raster`, `create_mosaic`, `count_water_pixels`, `analyze_categorical_raster`.

### 4.9 `geoagent.tools.gee_data_catalogs` (12 tools)
- **Module File:** `geoagent/tools/gee_data_catalogs.py`
- **Dependencies:** `earthengine-api` (`ee`).
- **Tools:** `search_gee_datasets`, `get_gee_dataset_info`, `summarize_gee_catalog`, `initialize_earth_engine`, `load_gee_dataset`, `calculate_gee_normalized_difference`, `list_loaded_gee_layers`, `set_gee_layer_visualization`, `run_gee_python_snippet`, `calculate_gee_layer_statistics`, `open_gee_catalog_panel`, `configure_gee_dataset_load`.

### 4.10 `geoagent.tools.hypercoast` (9 tools)
- **Module File:** `geoagent/tools/hypercoast.py`
- **Dependencies:** `hypercoast` (EMIT, PACE hyperspectral processing).
- **Tools:** `list_hypercoast_data_types`, `search_hypercoast_data`, `display_hypercoast_footprints`, `get_selected_hypercoast_footprints`, `download_hypercoast_data`, `preview_hypercoast_dataset`, `load_hypercoast_rgb`, `load_hypercoast_variable`, `open_hypercoast_panel`.

### 4.11 `geoagent.tools.timelapse` (6 tools)
- **Module File:** `geoagent/tools/timelapse.py`
- **Dependencies:** Earth Engine, geemap timelapse utilities.
- **Tools:** `list_timelapse_imagery_types`, `get_current_timelapse_extent`, `initialize_timelapse_earth_engine`, `create_timelapse`, `open_timelapse_panel`, `open_timelapse_settings`.

### 4.12 `geoagent.tools.vantor` (7 tools)
- **Module File:** `geoagent/tools/vantor.py`
- **Dependencies:** Maxar Open Data / Vantor STAC endpoints.
- **Tools:** `list_vantor_events`, `get_vantor_event_info`, `get_current_vantor_search_extent`, `search_vantor_items`, `display_vantor_footprints`, `load_vantor_cog`, `open_vantor_panel`.

### 4.13 `geoagent.tools.whitebox` (7 tools)
- **Module File:** `geoagent/tools/whitebox.py`
- **Dependencies:** `whitebox` (WhiteboxTools Rust binary).
- **Tools:** `summarize_whitebox_tools`, `search_whitebox_tools`, `get_whitebox_tool_info`, `run_whitebox_tool`, `run_whitebox_flow_accumulation`, `run_whitebox_fill_sinks`, `run_whitebox_color_shaded_relief`.

### 4.14 `geoagent.tools.geoai` (3 tools)
- **Module File:** `geoagent/tools/geoai.py`
- **Dependencies:** `samgeo` (Segment Anything for Geospatial Data), PyTorch.
- **Tools:** `segment_image_with_text_prompt`, `regularize_segmentation_mask_to_vector`, `smooth_segmentation_mask_to_vector`.

---

## 5. Security & Permission Profiles Summary

The GeoAgent confirmation hook enforces granular safety controls:
1. **Auto-approve Safe Only (`auto_approve=False` in UI):**
   - Read-only tools (`list_layers`, `get_map_state`, navigation) execute automatically.
   - Any tool tagged `requires_confirmation=True` or `destructive=True` pauses execution and requests explicit user approval.
   - For AnyMap: `remove_layer`, `clear_layers`, and `save_map` prompt for confirmation.
2. **Auto-approve All (`auto_approve=True` in UI):**
   - All registered tools execute immediately without interrupting user prompts.
3. **QGIS Permission Profiles:**
   - Supports `"Trusted auto-approve"`, `"Execute Scripts"`, `"Run processing"`, `"Edit layers"`, and `"Read-only"` to isolate PyQGIS script execution and algorithm geoprocessing.

