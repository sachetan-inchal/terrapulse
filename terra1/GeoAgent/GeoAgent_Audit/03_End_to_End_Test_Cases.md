# End-to-End Practical Test Cases

This document provides complete, multi-step testing workflows for validating GeoAgent in the Solara UI environment using AnyMap / MapLibre. All scenarios use **Bengaluru, India** (`12.9716° N, 77.5946° E`) as the primary geographic area.

---

## Test Suite 1: Urban Exploration & Map Navigation

### Test Case 1.1: Precise City Centering & Zoom Adjustment
- **Objective:** Verify navigation tools center the map on Bengaluru and adjust zoom levels accurately.
- **Prompt:**
  ```text
  Center the map on Bengaluru at latitude 12.9716 and longitude 77.5946, then set the zoom level to 13.
  ```
- **Expected Sequence of Tool Calls:**
  1. `set_center(lat=12.9716, lon=77.5946)`
  2. `set_zoom(zoom=13)`
- **Expected Map / Data Result:** The canvas updates to show central Bengaluru (Cubbon Park, MG Road area) at zoom 13.
- **Verification Steps:**
  1. Inspect the map UI canvas.
  2. Run `What is the current map state?` to confirm `center` is `[77.5946, 12.9716]` and `zoom` is `13`.
- **Possible Failure Points:** If the LLM passes `zoom` directly into `set_center`, AnyMap raises `TypeError: takes 3 positional arguments but 4 were given`. Splitting into `set_center` and `set_zoom` avoids this bug.

---

### Test Case 1.2: Camera Step Zooming and State Inspection
- **Objective:** Verify relative zoom adjustments (`zoom_in`, `zoom_out`) and state querying.
- **Prompt:**
  ```text
  First, zoom in 2 steps. Then report the current map state.
  ```
- **Expected Sequence of Tool Calls:**
  1. `zoom_in(steps=2)`
  2. `get_map_state()`
- **Expected Map / Data Result:** Map zooms in closer; the agent outputs a JSON-formatted summary of center coordinates, zoom, and bounding box.
- **Verification Steps:** Check that returned zoom equals the initial zoom plus 2.

---

### Test Case 1.3: Animated Pan to Major Infrastructure
- **Objective:** Test camera movement to Kempegowda International Airport.
- **Prompt:**
  ```text
  Fly the camera to Kempegowda International Airport at latitude 13.1986, longitude 77.7066 with zoom 14.
  ```
- **Expected Sequence of Tool Calls:**
  1. `fly_to(lat=13.1986, lon=77.7066, zoom=14)`
- **Expected Map / Data Result:** Smooth animated transition to the airport north of Bengaluru.
- **Possible Failure Points:** Note that `_safe_call(m, ["fly_to"], lon, lat, zoom)` flips latitude and longitude in `anymap.py`.

---

## Test Suite 2: Basemap & Visual Styling

### Test Case 2.1: Basemap Switching to High-Contrast Theme
- **Objective:** Test switching the underlying map styling.
- **Prompt:**
  ```text
  Change the basemap to "CartoDB.Positron".
  ```
- **Expected Sequence of Tool Calls:**
  1. `change_basemap(basemap="CartoDB.Positron")`
- **Expected Map / Data Result:** Background tiles switch to a light, minimalist grayscale CartoDB style.
- **Verification Steps:** Visual confirmation in the browser viewport.

---

### Test Case 2.2: Nighttime Basemap Switch
- **Prompt:**
  ```text
  Switch the basemap to "CartoDB.DarkMatter".
  ```
- **Expected Sequence of Tool Calls:**
  1. `change_basemap(basemap="CartoDB.DarkMatter")`
- **Expected Map / Data Result:** Dark themed vector/raster tile basemap displays.

---

## Test Suite 3: Vector & GeoJSON Layers

### Test Case 3.1: In-Memory GeoJSON Landmark Rendering
- **Objective:** Render an in-memory GeoJSON point representing the Karnataka Legislative building (Vidhana Soudha).
- **Prompt:**
  ```text
  Add a GeoJSON layer named "vidhana_soudha" with this data:
  {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [77.5906, 12.9797]}, "properties": {"name": "Vidhana Soudha", "category": "Government"}}]}
  ```
- **Expected Sequence of Tool Calls:**
  1. `add_geojson_data(data=..., name="vidhana_soudha")`
- **Expected Map / Data Result:** A point feature is rendered at Vidhana Soudha.
- **Verification Steps:** Check that `list_layers()` includes `"vidhana_soudha"`.

---

### Test Case 3.2: Remote Vector Dataset Loading (Lakes of Bengaluru)
- **Objective:** Load waterbody polygons from a remote GeoJSON repository.
- **Prompt:**
  ```text
  Add vector data from "https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/countries.geojson" named "world_countries".
  ```
- **Expected Sequence of Tool Calls:**
  1. `add_vector_data(path_or_url="https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/countries.geojson", name="world_countries")`
- **Expected Map / Data Result:** Country boundary polygons appear over the globe.
- **Verification Steps:** Call `list_layers()` to verify the layer exists and is visible.

---

## Test Suite 4: Layer Management, Visibility & Opacity

### Test Case 4.1: Adjust Layer Transparency and Toggle Visibility
- **Objective:** Test dynamic styling adjustments on a loaded layer.
- **Prompt:**
  ```text
  Set the opacity of layer "world_countries" to 0.4, then hide the layer.
  ```
- **Expected Sequence of Tool Calls:**
  1. `set_layer_opacity(name="world_countries", opacity=0.4)`
  2. `set_layer_visibility(name="world_countries", visible=False)`
- **Expected Map / Data Result:** The layer fades to 40% opacity, then disappears from the view.
- **Verification Steps:** Call `list_layers()` and inspect `opacity: 0.4` and `visible: false`.

---

### Test Case 4.2: Layer Removal with Safety Confirmation
- **Objective:** Test removing a specific layer under confirmation controls.
- **Prompt:**
  ```text
  Remove the layer "world_countries" from the map.
  ```
- **Expected Sequence of Tool Calls:**
  1. Agent prompts for confirmation (if `auto_approve=False` in UI).
  2. Executes `remove_layer(name="world_countries")`.
- **Expected Map / Data Result:** The layer is deleted from the canvas.
- **Verification Steps:** `list_layers()` no longer shows `"world_countries"`.

---

### Test Case 4.3: Resetting Canvas (Clear Layers)
- **Objective:** Reset all custom overlays to pristine basemap state.
- **Prompt:**
  ```text
  Clear all layers from the map.
  ```
- **Expected Sequence of Tool Calls:**
  1. Requests confirmation.
  2. Calls `clear_layers()`.
- **Expected Map / Data Result:** All custom layers removed; returns `"Cleared N layer(s)."`.

---

## Test Suite 5: Cloud Formats & Remote Sensing (COG / STAC / Tiles)

### Test Case 5.1: Cloud Optimized GeoTIFF (COG) Streaming
- **Objective:** Stream and display a remote Cloud Optimized GeoTIFF tile layer.
- **Prompt:**
  ```text
  Add the Cloud Optimized GeoTIFF from "https://storage.googleapis.com/pdd-stac/disasters/cyclone-idai/sample.tif" as layer "cyclone_cog" using the "viridis" colormap.
  ```
- **Expected Sequence of Tool Calls:**
  1. `add_cog_layer(url="https://storage.googleapis.com/pdd-stac/disasters/cyclone-idai/sample.tif", name="cyclone_cog", colormap="viridis")`
- **Expected Map / Data Result:** High-resolution raster tiles render over the region.
- **Verification Steps:** MapLibre displays raster layer tiles from the TiTiler service.

---

### Test Case 5.2: Planetary STAC Catalog Integration
- **Objective:** Overlay an open STAC collection.
- **Prompt:**
  ```text
  Add a STAC layer from collection "cop-dem-glo-30" with titiler_endpoint "pc" named "global_elevation".
  ```
- **Expected Sequence of Tool Calls:**
  1. `add_stac_layer(collection="cop-dem-glo-30", titiler_endpoint="pc", name="global_elevation")`
- **Expected Map / Data Result:** Dynamic DEM tiles stream onto the map.

---

## Test Suite 6: Full Multi-Step Geospatial Visualization Workflow

### Test Case 6.1: Comprehensive End-to-End Bengaluru GIS Dashboard Setup
- **Objective:** Execute an end-to-end multi-tool workflow setting up a complete urban analysis session.
- **Prompt:**
  ```text
  Please perform the following complete geospatial workflow for Bengaluru:
  1. Switch the basemap to "CartoDB.Positron".
  2. Center the map on Bengaluru (latitude 12.9716, longitude 77.5946).
  3. Set the zoom level to 12.
  4. Add a point GeoJSON layer named "vidhana_soudha" at latitude 12.9797, longitude 77.5906.
  5. Save the interactive map to "bengaluru_urban_session.html".
  6. Summarize the final map state.
  ```
- **Expected Sequence of Tool Calls:**
  1. `change_basemap(basemap="CartoDB.Positron")`
  2. `set_center(lat=12.9716, lon=77.5946)`
  3. `set_zoom(zoom=12)`
  4. `add_geojson_data(data=..., name="vidhana_soudha")`
  5. `save_map(path="bengaluru_urban_session.html")` (requires confirmation)
  6. `get_map_state()`
- **Expected Map / Data Result:**
  - Canvas updates to clean light basemap.
  - Centered over Bengaluru at street/city scale.
  - Landmark point rendered.
  - HTML file saved to workspace.
  - Agent returns state dictionary with coordinates and layer metadata.
- **Verification Steps:**
  1. Confirm file `bengaluru_urban_session.html` exists in the project workspace.
  2. Open the file in a web browser to verify identical map view and layer presence.

