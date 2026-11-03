# GeoAgent Prompt Catalogue

**Environment:** Solara UI + AnyMap / MapLibre  
**Model:** Groq / `openai/gpt-oss-120b` via LiteLLM  
**Target City:** Bengaluru, Karnataka, India (Center: `12.9716° N, 77.5946° E`)  

This catalogue contains copy-pasteable prompts to trigger and test every registered tool in the active runtime. Each tool includes basic, practical, and advanced prompts with required/optional arguments, expected outputs, verification methods, and runtime limitations.

---

## 1. Map Navigation & View Control

### Tool: `set_center`
- **Category:** `map`
- **Purpose:** Center the map canvas on a specific latitude and longitude, with an optional zoom level.
- **Required parameters:** `lat` (float), `lon` (float)
- **Optional parameters:** `zoom` (int or None)
- **Basic prompt:**
  ```text
  Center the map on latitude 12.9716 and longitude 77.5946.
  ```
- **Practical prompt:**
  ```text
  Pan the view to Bengaluru city center at latitude 12.9716, longitude 77.5946.
  ```
- **Advanced prompt:**
  ```text
  Center the map directly over Kempegowda International Airport at latitude 13.1986, longitude 77.7066.
  ```
- **Expected result:** Agent invokes `set_center(lat=12.9716, lon=77.5946)`.
- **Verification:** Map viewpoint centers on Bengaluru. Inspecting `get_map_state()` shows updated coordinates.
- **Limitations:** Passing `zoom` triggers a known argument bug in `anymap.Map.set_center` (it accepts 2 arguments, but the adapter passes 3). Use `set_zoom` separately if zoom adjustment is needed.

---

### Tool: `fly_to`
- **Category:** `map`
- **Purpose:** Smoothly animate or move the map camera to a coordinate and zoom level.
- **Required parameters:** `lat` (float), `lon` (float)
- **Optional parameters:** `zoom` (int or None)
- **Basic prompt:**
  ```text
  Fly to latitude 12.9716 and longitude 77.5946 with zoom level 12.
  ```
- **Practical prompt:**
  ```text
  Smoothly fly the camera to Bengaluru at latitude 12.9716, longitude 77.5946, and set the zoom to 13.
  ```
- **Advanced prompt:**
  ```text
  Take me on an animated transition to Electronic City, Bengaluru at latitude 12.8452 and longitude 77.6602 at zoom 14.
  ```
- **Expected result:** Agent invokes `fly_to(lat=12.9716, lon=77.5946, zoom=12)`.
- **Verification:** Map animates to the location.
- **Limitations:** The underlying adapter in `anymap.py` forwards `_safe_call(m, ["fly_to"], lon, lat, zoom)`, whereas `anymap.maplibre.MapLibreMap.fly_to` expects `(lat, lng, zoom)`. This inverts latitude and longitude during animation unless fixed.

---

### Tool: `set_zoom`
- **Category:** `map`
- **Purpose:** Set the map zoom level directly.
- **Required parameters:** `zoom` (int)
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  Set the map zoom level to 12.
  ```
- **Practical prompt:**
  ```text
  Zoom the map directly to level 14 to see city streets clearly.
  ```
- **Advanced prompt:**
  ```text
  Adjust the current camera zoom level to 16 for high-resolution building visibility.
  ```
- **Expected result:** Agent invokes `set_zoom(zoom=12)` and returns `"Zoom set to 12."`.
- **Verification:** Canvas zooms in or out to level 12.

---

### Tool: `zoom_in`
- **Category:** `map`
- **Purpose:** Increment current zoom level by one or more steps.
- **Required parameters:** None
- **Optional parameters:** `steps` (int, default: 1)
- **Basic prompt:**
  ```text
  Zoom in on the map.
  ```
- **Practical prompt:**
  ```text
  Zoom in by 2 levels to get a closer view of the area.
  ```
- **Advanced prompt:**
  ```text
  Please zoom in 3 steps into the current center.
  ```
- **Expected result:** Agent invokes `zoom_in(steps=2)` and returns `"Zoomed in to <level>."`.
- **Verification:** Map scale doubles for each step.

---

### Tool: `zoom_out`
- **Category:** `map`
- **Purpose:** Decrement current zoom level by one or more steps.
- **Required parameters:** None
- **Optional parameters:** `steps` (int, default: 1)
- **Basic prompt:**
  ```text
  Zoom out on the map.
  ```
- **Practical prompt:**
  ```text
  Zoom out by 2 steps to see the regional surroundings.
  ```
- **Advanced prompt:**
  ```text
  Zoom out 3 steps to inspect the broader metropolitan district.
  ```
- **Expected result:** Agent invokes `zoom_out(steps=2)` and returns `"Zoomed out to <level>."`.
- **Verification:** Canvas expands to show broader area.

---

### Tool: `zoom_to_bounds`
- **Category:** `map`
- **Purpose:** Fit the map viewpoint to a bounding box `[west, south, east, north]`.
- **Required parameters:** `west` (float), `south` (float), `east` (float), `north` (float)
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  Zoom to the bounding box with west 77.45, south 12.85, east 77.75, north 13.15.
  ```
- **Practical prompt:**
  ```text
  Fit the map view to the Bengaluru Urban boundary: west=77.46, south=12.83, east=77.75, north=13.14.
  ```
- **Advanced prompt:**
  ```text
  Set the map camera extent to encompass greater Bengaluru using bounds: west 77.35, south 12.75, east 77.85, north 13.25.
  ```
- **Expected result:** Agent invokes `zoom_to_bounds(west=77.46, south=12.83, east=77.75, north=13.14)`.
- **Verification:** Map viewport adjusts to fit the bounding coordinates.

---

### Tool: `zoom_to_layer`
- **Category:** `map`
- **Purpose:** Zoom the camera to the recorded bounding box of a named layer.
- **Required parameters:** `name` (str)
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  Zoom to the layer named "bengaluru_lakes".
  ```
- **Practical prompt:**
  ```text
  Adjust the map camera to fit the full extent of the "metro_lines" layer.
  ```
- **Advanced prompt:**
  ```text
  Find the layer "admin_boundary" and zoom directly to its bounding box.
  ```
- **Expected result:** Agent calls `zoom_to_layer(name="bengaluru_lakes")`.
- **Verification:** Map frames the layer features.
- **Limitations:** Only works if the layer object tracks a `.bounds` attribute or record.

---

### Tool: `get_map_state`
- **Category:** `map`
- **Purpose:** Retrieve the current camera center coordinates, zoom level, bounds, pitch, and bearing.
- **Required parameters:** None
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  What is the current map state?
  ```
- **Practical prompt:**
  ```text
  Get the current map camera position, including center coordinates and zoom level.
  ```
- **Advanced prompt:**
  ```text
  Inspect and summarize the current map view state, pitch, bearing, and bounding box.
  ```
- **Expected result:** Returns a dictionary containing `center`, `zoom`, `bounds`, and layer details.
- **Verification:** Coordinates match the current visible map in the UI.

---

## 2. Basemap Management

### Tool: `change_basemap`
- **Category:** `map`
- **Purpose:** Change the background basemap style.
- **Required parameters:** `basemap` (str)
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  Change the basemap to "CartoDB.Positron".
  ```
- **Practical prompt:**
  ```text
  Switch the map basemap style to "OpenStreetMap".
  ```
- **Advanced prompt:**
  ```text
  Change the basemap to "CartoDB.DarkMatter" for high-contrast nighttime visualization.
  ```
- **Expected result:** Agent invokes `change_basemap(basemap="CartoDB.Positron")`.
- **Verification:** The map background tiles reload in the new style.

---

## 3. Map Layer Management & Inspection

### Tool: `list_layers`
- **Category:** `map`
- **Purpose:** List all active layers currently displayed on the map.
- **Required parameters:** None
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  List all layers on the map.
  ```
- **Practical prompt:**
  ```text
  Show me the inventory of all currently loaded layers, their types, and visibility status.
  ```
- **Advanced prompt:**
  ```text
  Inspect the active layers on the canvas and report their names, sources, and opacity values.
  ```
- **Expected result:** Agent calls `list_layers()` and returns a list of dictionaries with layer properties.
- **Verification:** Matches the layers visible in the AnyMap layer control panel.

---

### Tool: `set_layer_visibility`
- **Category:** `map`
- **Purpose:** Show or hide a specific map layer.
- **Required parameters:** `name` (str), `visible` (bool)
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  Hide the layer "bengaluru_lakes".
  ```
- **Practical prompt:**
  ```text
  Set visibility of layer "city_boundary" to false.
  ```
- **Advanced prompt:**
  ```text
  Make the layer "metro_stations" visible again by setting visible to true.
  ```
- **Expected result:** Agent executes `set_layer_visibility(name="bengaluru_lakes", visible=False)`.
- **Verification:** Layer disappears or reappears on the map canvas.

---

### Tool: `set_layer_opacity`
- **Category:** `map`
- **Purpose:** Adjust the opacity of a layer between 0.0 (transparent) and 1.0 (opaque).
- **Required parameters:** `name` (str), `opacity` (float)
- **Optional parameters:** None
- **Basic prompt:**
  ```text
  Set the opacity of layer "bengaluru_lakes" to 0.5.
  ```
- **Practical prompt:**
  ```text
  Adjust the "satellite_overlay" layer opacity to 0.75 so the underlying roads remain visible.
  ```
- **Advanced prompt:**
  ```text
  Make the layer "heat_island_index" semi-transparent by setting its opacity to 0.4.
  ```
- **Expected result:** Returns `"Layer 'bengaluru_lakes' opacity set to 0.5."`.
- **Verification:** Visual transparency of the layer changes.

---

### Tool: `remove_layer`
- **Category:** `map`
- **Purpose:** Delete a specific layer from the map.
- **Required parameters:** `name` (str)
- **Optional parameters:** None
- **Confirmation Required:** Yes
- **Basic prompt:**
  ```text
  Remove the layer "temp_points".
  ```
- **Practical prompt:**
  ```text
  Delete the layer named "bengaluru_lakes" from the map.
  ```
- **Advanced prompt:**
  ```text
  Remove the obsolete layer "test_overlay" after confirming.
  ```
- **Expected result:** GeoAgent requests user confirmation (if `auto_approve` is off), then executes `remove_layer(name="temp_points")`.
- **Verification:** Layer is removed from `list_layers()` and canvas.

---

### Tool: `clear_layers`
- **Category:** `map`
- **Purpose:** Remove all user-added layers from the map canvas.
- **Required parameters:** None
- **Optional parameters:** None
- **Confirmation Required:** Yes
- **Basic prompt:**
  ```text
  Clear all layers from the map.
  ```
- **Practical prompt:**
  ```text
  Remove every loaded data layer to reset the map canvas to just the basemap.
  ```
- **Advanced prompt:**
  ```text
  Wipe the map clean by removing all active layers and overlays.
  ```
- **Expected result:** Agent asks for confirmation, then executes `clear_layers()`, returning `"Cleared X layer(s)."`.
- **Verification:** Map contains zero overlay layers.

---

### Tool: `save_map`
- **Category:** `map`
- **Purpose:** Export the map and all active layers to an interactive HTML file on disk.
- **Required parameters:** `path` (str)
- **Optional parameters:** None
- **Confirmation Required:** Yes
- **Basic prompt:**
  ```text
  Save the map to "bengaluru_map.html".
  ```
- **Practical prompt:**
  ```text
  Export the current interactive map to a standalone HTML file at "exports/bengaluru_overview.html".
  ```
- **Advanced prompt:**
  ```text
  Save the complete configured map including all layers to "C:/Users/rishi/Desktop/CCVR/terrapulse/terra1/GeoAgent/bengaluru_export.html".
  ```
- **Expected result:** Agent executes `save_map(path=...)` and returns the resolved absolute file path.
- **Verification:** Opening the HTML file in any browser displays the map.

---

## 4. Vector & GeoJSON Data Operations

### Tool: `add_vector_data`
- **Category:** `map`
- **Purpose:** Load a vector dataset from a remote URL or local file path.
- **Required parameters:** `path_or_url` (str), `name` (str)
- **Optional parameters:** `style` (dict or None)
- **Basic prompt:**
  ```text
  Add vector data from "https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/countries.geojson" with name "world_countries".
  ```
- **Practical prompt:**
  ```text
  Load the Bengaluru lakes GeoJSON from "https://raw.githubusercontent.com/datameet/bengaluru/master/waterbodies/lakes.geojson" as layer "bengaluru_lakes".
  ```
- **Advanced prompt:**
  ```text
  Add the vector layer from "https://raw.githubusercontent.com/datameet/bengaluru/master/waterbodies/lakes.geojson" as "bengaluru_lakes" with style {"fillColor": "#0077be", "fillOpacity": 0.6, "color": "#002244", "weight": 2}.
  ```
- **Expected result:** Invokes `add_vector_data(...)` and returns `"Added vector layer 'bengaluru_lakes'."`.
- **Verification:** Vector polygons render on the map.

---

### Tool: `add_geojson_data`
- **Category:** `map`
- **Purpose:** Render an in-memory GeoJSON dictionary (FeatureCollection, Feature, or Geometry).
- **Required parameters:** `data` (dict), `name` (str)
- **Optional parameters:** `style` (dict or None)
- **Basic prompt:**
  ```text
  Add a GeoJSON layer named "vidhana_soudha" with data: {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [77.5906, 12.9797]}, "properties": {"title": "Vidhana Soudha"}}]}
  ```
- **Practical prompt:**
  ```text
  Add an in-memory GeoJSON polygon representing Cubbon Park in Bengaluru named "cubbon_park" with coordinates [[77.590, 12.973], [77.595, 12.973], [77.595, 12.978], [77.590, 12.978], [77.590, 12.973]].
  ```
- **Advanced prompt:**
  ```text
  Plot a GeoJSON point for Bengaluru City Railway Station at [77.5696, 12.9784] as layer "railway_station" with style {"color": "#ff3300", "radius": 8}.
  ```
- **Expected result:** Invokes `add_geojson_data(data=..., name=...)`.
- **Verification:** Point or polygon renders at the specified coordinates.

---

### Tool: `add_marker`
- **Category:** `map`
- **Purpose:** Add an interactive point marker to the map canvas.
- **Required parameters:** `lat` (float), `lon` (float)
- **Optional parameters:** `popup` (str or None), `tooltip` (str or None), `name` (str or None)
- **Basic prompt:**
  ```text
  Add a marker at latitude 12.9716 and longitude 77.5946.
  ```
- **Practical prompt:**
  ```text
  Place a marker at latitude 12.9797, longitude 77.5906 with tooltip "Vidhana Soudha" and popup "Government headquarters of Karnataka".
  ```
- **Advanced prompt:**
  ```text
  Add a point marker named "Lalbagh Botanical Garden" at latitude 12.9507, longitude 77.5848 with popup "Lalbagh Glass House".
  ```
- **Expected result:** Agent calls `add_marker(...)`.
- **Verification:** Marker icon appears on the map.
- **Limitations:** Note that `anymap.maplibre.MapLibreMap.add_marker` expects `(lng, lat)` positional arguments, whereas the adapter calls `m.add_marker(location=(lat, lon), ...)`, raising a `TypeError: unexpected keyword argument 'location'` unless caught.

---

## 5. Raster, COG, Tile & Cloud Formats

### Tool: `add_layer`
- **Category:** `map`
- **Purpose:** Universal layer adder with automatic format detection based on file extension.
- **Required parameters:** `url` (str), `name` (str)
- **Optional parameters:** `layer_type` (str, default: `"auto"`)
- **Basic prompt:**
  ```text
  Add the layer at URL "https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/countries.geojson" named "countries".
  ```
- **Practical prompt:**
  ```text
  Load the raster data from "https://storage.googleapis.com/pdd-stac/disasters/cyclone-idai/sample.tif" as "idai_cyclone" with layer_type "cog".
  ```
- **Advanced prompt:**
  ```text
  Add a vector layer from "https://raw.githubusercontent.com/datameet/bengaluru/master/waterbodies/lakes.geojson" with name "bengaluru_water" using layer_type auto.
  ```
- **Expected result:** Tool inspects the URL, routes to the appropriate handler, and adds the layer.
- **Verification:** Layer is added and appears in `list_layers()`.

---

### Tool: `add_raster_data`
- **Category:** `map`
- **Purpose:** Add a local or remote raster dataset with a specified color map.
- **Required parameters:** `path_or_url` (str), `name` (str)
- **Optional parameters:** `colormap` (str, default: `"viridis"`)
- **Basic prompt:**
  ```text
  Add raster data from "https://storage.googleapis.com/pdd-stac/disasters/cyclone-idai/sample.tif" named "cyclone_raster".
  ```
- **Practical prompt:**
  ```text
  Load the elevation raster from "https://elevation.example.com/bengaluru_dem.tif" named "bengaluru_elevation" using the "terrain" colormap.
  ```
- **Advanced prompt:**
  ```text
  Add the surface temperature raster from "https://data.example.com/surface_temp.tif" as layer "surface_temp" with colormap "plasma".
  ```
- **Expected result:** Invokes `add_raster_data(...)`.
- **Verification:** Raster overlay renders across its geographic bounds.
- **Limitations:** Rejects Planetary Computer asset URLs without TiTiler signing.

---

### Tool: `add_cog_layer`
- **Category:** `map`
- **Purpose:** Stream and display a Cloud Optimized GeoTIFF (COG) via a dynamic tile server.
- **Required parameters:** `url` (str), `name` (str)
- **Optional parameters:** `colormap` (str, default: `"viridis"`), `titiler_endpoint` (str or None)
- **Basic prompt:**
  ```text
  Add the COG layer from "https://storage.googleapis.com/pdd-stac/disasters/cyclone-idai/sample.tif" named "cyclone_cog".
  ```
- **Practical prompt:**
  ```text
  Add a Cloud Optimized GeoTIFF from "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/43/P/FS/2023/1/S2A_43PFS_20230101_0_L2A/B04.tif" as "bengaluru_red_band" with colormap "magma".
  ```
- **Advanced prompt:**
  ```text
  Display the COG at "https://data.example.com/bengaluru_ndvi.tif" named "bengaluru_ndvi" using the "greens" colormap and custom titiler_endpoint "https://titiler.xyz".
  ```
- **Expected result:** Invokes `add_cog_layer(...)`.
- **Verification:** MapLibre requests raster tiles dynamically from TiTiler.

---

### Tool: `add_xyz_tile_layer`
- **Category:** `map`
- **Purpose:** Add an XYZ slippy tile raster layer (e.g. OpenStreetMap, Stamen, USGS, ESRI).
- **Required parameters:** `url` (str), `name` (str)
- **Optional parameters:** `attribution` (str, default: `""`)
- **Basic prompt:**
  ```text
  Add an XYZ tile layer with URL "https://tile.openstreetmap.org/{z}/{x}/{y}.png" and name "osm_layer".
  ```
- **Practical prompt:**
  ```text
  Add CartoDB Voyager tiles using URL "https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" named "carto_voyager" with attribution "© OpenStreetMap © CARTO".
  ```
- **Advanced prompt:**
  ```text
  Add the USGS Topographic tile layer from "https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}" as "usgs_topo" with attribution "USGS National Map".
  ```
- **Expected result:** Adds the tile source and layer to the map.
- **Verification:** Tiles render on the canvas.
- **Limitations:** In `anymap.maplibre.MapLibreMap`, the method is `add_tile_layer(layer_id, source_url)`, whereas the adapter passes `(url, name=name, attribution=attribution)`, leading to a keyword argument error in some versions.

---

### Tool: `add_pmtiles_layer`
- **Category:** `map`
- **Purpose:** Add a PMTiles single-file archive layer.
- **Required parameters:** `url` (str), `name` (str)
- **Optional parameters:** `style` (dict or None)
- **Basic prompt:**
  ```text
  Add PMTiles from "https://r2-public.protomaps.com/protomaps-sample-datasets/bengaluru.pmtiles" named "bengaluru_pmtiles".
  ```
- **Practical prompt:**
  ```text
  Load the PMTiles archive at "https://pmtiles.example.com/bengaluru_buildings.pmtiles" as layer "bengaluru_buildings" with style {"fill-color": "#4488aa"}.
  ```
- **Advanced prompt:**
  ```text
  Add the vector PMTiles archive from "https://r2-public.protomaps.com/protomaps-sample-datasets/nz-buildings.pmtiles" as "sample_pmtiles" with vector polygon styling.
  ```
- **Expected result:** Connects the PMTiles protocol to MapLibre.
- **Verification:** Vector features render smoothly from the archive.
- **Limitations:** In `MapLibreMap`, the argument is `pmtiles_url, layer_id`, whereas the adapter passes `name=name`.

---

## 6. STAC Catalogues & Collections

### Tool: `add_stac_layer`
- **Category:** `map`
- **Purpose:** Query and overlay a STAC collection or item as a dynamic tile layer.
- **Required parameters:** `collection` (str)
- **Optional parameters:** `item` (str or None), `assets` (list[str] or None), `name` (str or None), `titiler_endpoint` (str or None)
- **Basic prompt:**
  ```text
  Add a STAC layer from collection "sentinel-2-l2a".
  ```
- **Practical prompt:**
  ```text
  Add STAC collection "cop-dem-glo-30" with titiler_endpoint "pc" as layer "global_dem".
  ```
- **Advanced prompt:**
  ```text
  Display STAC layer from collection "sentinel-2-l2a", item "S2A_43PFS_20230101_0_L2A", assets ["visual"], named "bengaluru_sentinel_visual", using titiler_endpoint "pc".
  ```
- **Expected result:** Invokes `add_stac_layer(collection="sentinel-2-l2a", item="...", assets=["visual"], ...)`.
- **Verification:** STAC raster composite loads over the target area.

---

## 7. Multimodal & Visual Asset Generation

### Tool: `generate_image`
- **Category:** `image_generation`
- **Purpose:** Generate a diagram, illustration, or visual map rendering from natural language using image models.
- **Required parameters:** `prompt` (str)
- **Optional parameters:** `size` (str, default: `"1024x1024"`), `quality` (str, default: `"low"`), `model` (str), `output_dir` (str), `aspect_ratio` (str), `response_format` (str), `seed` (int), `n` (int)
- **Basic prompt:**
  ```text
  Generate an image of a futuristic green smart city in Bengaluru with solar-powered transit.
  ```
- **Practical prompt:**
  ```text
  Generate an illustration diagram showing urban heat island mitigation in Bengaluru with green corridors and lake rejuvenation.
  ```
- **Advanced prompt:**
  ```text
  Generate an architectural elevation diagram of a sustainable lakefront promenade in Bengaluru, size 1024x1024, quality high.
  ```
- **Expected result:** Invokes `generate_image(prompt=...)` and saves the generated PNG/JPG to disk.
- **Verification:** Image file is written to output path and returned in the chat.
- **Limitations:** Requires an active OpenAI or compatible image generation API key in environment variables (`OPENAI_API_KEY`).

