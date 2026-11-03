# GeoAgent Test Coverage Matrix

**Target:** GeoAgent 1.9.1 (Solara UI + AnyMap / MapLibre)  
**Total Registered Tools in Runtime:** 25  
**Coverage Standard:** Code inspection, signature audit, execution verification, and edge-case testing.

---

## 1. Primary Runtime Tool Coverage Matrix

| # | Tool Name | Category | Basic Test Coverage | Advanced Test Coverage | Dependencies | Safety / Confirmation | Audit Status | Notes |
|---|---|---|:---:|:---:|---|:---:|:---:|---|
| 1 | `list_layers` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Queries layer list from `m.layers` |
| 2 | `add_layer` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Automatically branches by file extension |
| 3 | `remove_layer` | `map` | Covered | Covered | AnyMap | **Requires Confirm** | **VERIFIED** | Prompts user before deletion |
| 4 | `clear_layers` | `map` | Covered | Covered | AnyMap | **Requires Confirm** | **VERIFIED** | Prompts user before clearing canvas |
| 5 | `set_layer_visibility` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Updates layer visibility trait |
| 6 | `set_layer_opacity` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Clamps opacity between 0.0 and 1.0 |
| 7 | `set_center` | `map` | Covered | Covered | AnyMap | Safe (None) | **BUG IDENTIFIED** | Positional argument error if `zoom` passed |
| 8 | `fly_to` | `map` | Covered | Covered | AnyMap | Safe (None) | **BUG IDENTIFIED** | Coordinate order flipped (`lon, lat` vs `lat, lng`) |
| 9 | `set_zoom` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Sets zoom trait directly |
| 10 | `zoom_in` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Increases zoom by step count |
| 11 | `zoom_out` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Decreases zoom by step count |
| 12 | `zoom_to_bounds` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Calls `fit_bounds` with bounding box |
| 13 | `zoom_to_layer` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Requires bounds record on layer |
| 14 | `change_basemap` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Calls `add_basemap` with style ID |
| 15 | `add_vector_data` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Loads remote/local vector files |
| 16 | `add_geojson_data` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Parses in-memory GeoJSON dict |
| 17 | `add_marker` | `map` | Covered | Covered | AnyMap | Safe (None) | **BUG IDENTIFIED** | Keyword argument error on `location` |
| 18 | `add_raster_data` | `map` | Covered | Covered | AnyMap, TiTiler | Safe (None) | **VERIFIED** | Rejects unsigned Planetary URLs |
| 19 | `add_stac_layer` | `map` | Covered | Covered | AnyMap, TiTiler | Safe (None) | **VERIFIED** | Connects to TiTiler STAC endpoint |
| 20 | `add_cog_layer` | `map` | Covered | Covered | AnyMap, TiTiler | Safe (None) | **VERIFIED** | Dynamic raster streaming via COG |
| 21 | `add_xyz_tile_layer` | `map` | Covered | Covered | AnyMap | Safe (None) | **BUG IDENTIFIED** | Parameter naming mismatch in `add_tile_layer` |
| 22 | `add_pmtiles_layer` | `map` | Covered | Covered | AnyMap | Safe (None) | **BUG IDENTIFIED** | Parameter naming mismatch (`name` vs `layer_id`) |
| 23 | `get_map_state` | `map` | Covered | Covered | AnyMap | Safe (None) | **VERIFIED** | Returns center, zoom, bounds dict |
| 24 | `save_map` | `map` | Covered | Covered | AnyMap | **Requires Confirm** | **VERIFIED** | Exports HTML file to disk |
| 25 | `generate_image` | `image_generation` | Covered | Covered | OpenAI / LiteLLM | Safe (None) | **REQUIRES API KEY** | Generates visual assets via prompt |

---

## 2. Overall Repository Modules Summary

| Module Name | File Path | Total Tools | Primary Integration Target | Audit Status |
|---|---|:---:|---|:---:|
| `geoagent.tools.anymap` | `geoagent/tools/anymap.py` | 24 | Solara UI + AnyMap (MapLibre) | **Audited & Tested** |
| `geoagent.tools.leafmap` | `geoagent/tools/leafmap.py` | 24 | Jupyter / Leaflet / Folium | Inspected |
| `geoagent.tools.browser_maplibre` | `geoagent/tools/browser_maplibre.py` | 17 | Headless / Remote Browser WebSocket | Inspected |
| `geoagent.tools.images` | `geoagent/tools/images.py` | 1 | Image Generation (DALL-E / Imagen) | Inspected |
| `geoagent.tools.qgis` | `geoagent/tools/qgis.py` | 29 | QGIS Desktop (PyQGIS) | Inspected |
| `geoagent.tools.stac` | `geoagent/tools/stac.py` | 5 | STAC API / Planetary Computer | Inspected |
| `geoagent.tools.nasa_earthdata` | `geoagent/tools/nasa_earthdata.py` | 8 | NASA CMR / Earthdata Search | Inspected |
| `geoagent.tools.nasa_opera` | `geoagent/tools/nasa_opera.py` | 8 | NASA OPERA Water & Disturbance | Inspected |
| `geoagent.tools.gee_data_catalogs` | `geoagent/tools/gee_data_catalogs.py` | 12 | Google Earth Engine API | Inspected |
| `geoagent.tools.hypercoast` | `geoagent/tools/hypercoast.py` | 9 | EMIT & PACE Hyperspectral | Inspected |
| `geoagent.tools.timelapse` | `geoagent/tools/timelapse.py` | 6 | Earth Engine / Wayback Timelapse | Inspected |
| `geoagent.tools.vantor` | `geoagent/tools/vantor.py` | 7 | Maxar / Vantor Disaster STAC | Inspected |
| `geoagent.tools.whitebox` | `geoagent/tools/whitebox.py` | 7 | WhiteboxTools Geoprocessing | Inspected |
| `geoagent.tools.geoai` | `geoagent/tools/geoai.py` | 3 | Segment Anything (SamGeo) | Inspected |
| **Total** | | **160** | | |

