# GeoAgent Code & Tool Bug Audit Report

**Audit Target:** GeoAgent 1.9.1  
**Runtime Audited:** Solara UI + AnyMap (MapLibre GL JS)  
**LLM Engine:** Groq / LiteLLM (`groq/openai/gpt-oss-120b`)  
**Audit Date:** 2026-10-31  

This report documents confirmed bugs discovered during live execution testing and code inspection, followed by potential architectural and integration risks.

---

## 1. Confirmed Issues & Bugs

### BUG-01: Positional Argument Overflow in `set_center`
- **Location:** `geoagent/tools/anymap.py`, lines 187–189
- **Severity:** **HIGH**
- **Symptom:** Calling `set_center(lat, lon, zoom)` or `set_center(lat, lon)` raises:
  ```text
  TypeError: MapLibreMap.set_center() takes 3 positional arguments but 4 were given
  ```
- **Root Cause:**
  `geoagent.tools.anymap.py` calls:
  ```python
  _safe_call(m, ["set_center"], lon, lat, zoom)
  ```
  In `anymap.maplibre.MapLibreMap`, the method signature is:
  ```python
  def set_center(self, lng: float, lat: float) -> None: ...
  ```
  It accepts exactly two positional arguments (`lng` and `lat`). When the adapter passes `(lon, lat, zoom)`, Python attempts to bind `zoom` as a 3rd positional argument (plus `self` = 4 total arguments), causing an immediate `TypeError`.
- **Impact:** Any user prompt asking to center the map on a location with a zoom level crashes the tool invocation.
- **Recommended Fix:**
  Inspect whether `zoom` is provided, and invoke `set_zoom` separately or conditionally:
  ```python
  _safe_call(m, ["set_center"], lon, lat)
  if zoom is not None:
      _safe_call(m, ["set_zoom"], zoom)
  ```

---

### BUG-02: Lat/Lon Coordinate Inversion in `fly_to`
- **Location:** `geoagent/tools/anymap.py`, lines 196–198
- **Severity:** **HIGH**
- **Symptom:** Map pans to the completely inverted coordinates (e.g. centering in the Indian Ocean or Antarctica instead of Bengaluru).
- **Root Cause:**
  In `anymap/maplibre/maplibre.py`, `fly_to` is declared as:
  ```python
  def fly_to(self, lat: float, lng: float, zoom: float | None = None, **kwargs) -> None:
  ```
  However, in `geoagent/tools/anymap.py`:
  ```python
  _safe_call(m, ["fly_to"], lon, lat, zoom)
  ```
  The adapter passes `lon` as the first argument and `lat` as the second argument, swapping the coordinates expected by `anymap.MapLibreMap.fly_to`.
- **Impact:** Any animated fly-to prompt sends the map camera to invalid, swapped coordinates.
- **Recommended Fix:**
  Check the underlying map type or call with keyword arguments:
  ```python
  if hasattr(m, "fly_to"):
      m.fly_to(lat=lat, lng=lon, zoom=zoom)
  ```

---

### BUG-03: Keyword Argument Mismatch in `add_marker`
- **Location:** `geoagent/tools/anymap.py`, lines 356–362
- **Severity:** **HIGH**
- **Symptom:** Calling `add_marker(lat, lon)` raises:
  ```text
  TypeError: MapLibreMap.add_marker() got an unexpected keyword argument 'location'
  ```
- **Root Cause:**
  In `geoagent/tools/anymap.py`:
  ```python
  if hasattr(m, "add_marker"):
      m.add_marker(
          location=(lat, lon),
          popup=popup,
          tooltip=tooltip,
          name=marker_name,
      )
  ```
  In `anymap.maplibre.MapLibreMap`, the signature is:
  ```python
  def add_marker(self, lng: float, lat: float, popup: str | None = None, tooltip: str | None = None, ...) -> None:
  ```
  It takes `(lng, lat)` positionally and does not have a `location` parameter or a `name` parameter.
- **Impact:** Adding point markers fails outright in AnyMap sessions.
- **Recommended Fix:**
  Adapt the call to `anymap.maplibre.MapLibreMap`:
  ```python
  if hasattr(m, "add_marker"):
      try:
          m.add_marker(lon, lat, popup=popup, tooltip=tooltip)
      except TypeError:
          m.add_marker(location=(lat, lon), popup=popup, tooltip=tooltip)
  ```

---

### BUG-04: Keyword Argument Mismatch in `add_pmtiles_layer`
- **Location:** `geoagent/tools/anymap.py`, lines 497–501
- **Severity:** **MEDIUM**
- **Symptom:** Calling `add_pmtiles_layer` raises:
  ```text
  TypeError: MapLibreMap.add_pmtiles() got an unexpected keyword argument 'name'
  ```
- **Root Cause:**
  `geoagent` calls `_safe_call(m, ["add_pmtiles", "add_pmtiles_layer"], url, name=name)`. In `anymap`, the parameter is `layer_id`, not `name`.
- **Recommended Fix:**
  Pass both or inspect signature: `m.add_pmtiles(url, layer_id=name)`.

---

### BUG-05: Parameter Name Mismatch in `add_xyz_tile_layer`
- **Location:** `geoagent/tools/anymap.py`, lines 480–485
- **Severity:** **MEDIUM**
- **Symptom:** Calling `add_xyz_tile_layer` raises:
  ```text
  TypeError: MapLibreMap.add_tile_layer() missing 1 required positional argument: 'source_url'
  ```
- **Root Cause:**
  In `anymap.maplibre.MapLibreMap`, `add_tile_layer` expects `(layer_id, source_url)`. The adapter passes `url` as first positional argument and `name` as keyword argument.
- **Recommended Fix:**
  Normalize call order: `m.add_tile_layer(layer_id=name, source_url=url)`.

---

## 2. Potential Issues & Integration Risks

### RISK-01: LiteLLM Remote Cost Map Fetch Latency
- **Severity:** **MEDIUM**
- **Details:** On initialization or cold start without internet connectivity, LiteLLM attempts to fetch `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json` 3 times with a network timeout, causing a 10–15 second startup delay before falling back to local cache.
- **Mitigation:** In `geoagent/core/model.py` or `.env`, set `os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"` by default.

---

### RISK-02: MapLibre Layer State Synchronization in Solara
- **Severity:** **MEDIUM**
- **Details:** In `anymap.MapLibreMap`, layers added via MapLibre GL JS direct client calls do not always populate Python's `m.layers` list unless explicitly tracked in `m.layer_dict` or `m._layers`. As a result, `list_layers()` and `clear_layers()` can report 0 layers even after layers are visually rendered on screen.
- **Mitigation:** Query both `m.layers` and `m.get_layers()` or `m.get_style_layers()`.

---

### RISK-03: Groq GPT-OSS 120B Tool Calling Formatting
- **Severity:** **LOW**
- **Details:** Groq's `gpt-oss-120b` occasionally emits reasoning XML blocks (`<thought>...</thought>`). Strands Agents strips or parses thinking tags, but complex nested JSON schemas (e.g. `add_geojson_data` with large coordinate arrays) can occasionally exceed context bounds if entire GeoJSON files are pasted in chat.
- **Mitigation:** Use `add_vector_data` with file paths or URLs for datasets with more than 10 features.

