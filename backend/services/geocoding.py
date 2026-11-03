"""Geocoding & Region of Interest (AOI) Service.

Dynamically converts ANY worldwide user-typed location query (cities, towns,
villages, lakes, rivers, oceans, mountains, forests, national parks, neighborhoods,
streets, or direct coordinates) into accurate geographical coordinates, bounding
boxes, and target UTM EPSG codes via OpenStreetMap Nominatim and Komoot Photon
with resilient fallback and local in-memory caching.
"""
from typing import List, Optional, Dict
import re
import requests
from backend.models.schemas import LocationInfo

# Optional preset research corridors (suggestions only - never restricts global search)
PRESET_LOCATIONS: List[LocationInfo] = [
    LocationInfo(
        id="bengaluru",
        name="Bengaluru, Karnataka, India",
        country="India",
        latitude=12.9716,
        longitude=77.5946,
        bbox=[77.4598, 12.8334, 77.7840, 13.1426],
        default_crs="EPSG:4326",
        target_utm="EPSG:32643",
        description="High-growth global IT hub undergoing intensive multi-decade urban expansion and green canopy reduction.",
        feature_type="City"
    ),
    LocationInfo(
        id="chennai",
        name="Chennai, Tamil Nadu, India",
        country="India",
        latitude=13.0827,
        longitude=80.2707,
        bbox=[80.1500, 12.9500, 80.3500, 13.2000],
        default_crs="EPSG:4326",
        target_utm="EPSG:32644",
        description="Major coastal metropolitan industrial corridor along the Coromandel Coast with Adyar and Cooum river basins.",
        feature_type="City"
    ),
    LocationInfo(
        id="mumbai",
        name="Mumbai, Maharashtra, India",
        country="India",
        latitude=19.0760,
        longitude=72.8777,
        bbox=[72.7500, 18.9000, 73.0000, 19.2500],
        default_crs="EPSG:4326",
        target_utm="EPSG:32643",
        description="High-density maritime megacity on Salsette Island displaying coastal reclamation, industrial emissions, and port logistics.",
        feature_type="City"
    ),
    LocationInfo(
        id="delhi",
        name="Delhi National Capital Region, India",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
        bbox=[77.0500, 28.4500, 77.3500, 28.7500],
        default_crs="EPSG:4326",
        target_utm="EPSG:32643",
        description="Major metropolitan capital region with intense seasonal atmospheric particulate loading, Yamuna river basin, and thermal inversions.",
        feature_type="Administrative Region"
    ),
    LocationInfo(
        id="hyderabad",
        name="Hyderabad, Telangana, India",
        country="India",
        latitude=17.3850,
        longitude=78.4867,
        bbox=[78.3500, 17.2500, 78.6000, 17.5500],
        default_crs="EPSG:4326",
        target_utm="EPSG:32644",
        description="Deccan plateau IT and pharmaceutical industrial center with Musi river basin and urban lake catchment networks.",
        feature_type="City"
    ),
    LocationInfo(
        id="bellandur",
        name="Bellandur Lake Catchment, Bengaluru, India",
        country="India",
        latitude=12.9385,
        longitude=77.6680,
        bbox=[77.6300, 12.9100, 77.7100, 12.9600],
        default_crs="EPSG:4326",
        target_utm="EPSG:32643",
        description="Urban wetland lake catchment in southeast Bengaluru experiencing severe eutrophication, sewage influx, and surfactant foam events.",
        feature_type="Water Body (Lake)"
    ),
    LocationInfo(
        id="varthur",
        name="Varthur Lake Wetland, Bengaluru, India",
        country="India",
        latitude=12.9421,
        longitude=77.7420,
        bbox=[77.7100, 12.9200, 77.7700, 12.9700],
        default_crs="EPSG:4326",
        target_utm="EPSG:32643",
        description="Downstream receiving wetland lake in the Bellandur-Varthur catchment displaying hypoxic dissolved oxygen and phosphate accumulation.",
        feature_type="Water Body (Lake)"
    ),
    LocationInfo(
        id="swiss_alps",
        name="Swiss Alps (Rhone Glacier), Switzerland",
        country="Switzerland",
        latitude=46.5600,
        longitude=8.3800,
        bbox=[7.0000, 45.5000, 8.0000, 46.2000],
        default_crs="EPSG:4326",
        target_utm="EPSG:32632",
        description="Alpine cryogenic ecosystem showing accelerating glacial retreat, snowpack depletion, and moraine transformation.",
        feature_type="Mountain / Glacier"
    ),
    LocationInfo(
        id="grand_canyon",
        name="Grand Canyon, Arizona, USA",
        country="United States",
        latitude=36.1000,
        longitude=-112.1100,
        bbox=[-112.5000, 35.8000, -111.8000, 36.4000],
        default_crs="EPSG:4326",
        target_utm="EPSG:32612",
        description="Hyper-arid sedimentary canyon system displaying Colorado river seasonal discharge shifts and riparian ecosystem changes.",
        feature_type="Canyon / River Basin"
    ),
    LocationInfo(
        id="tokyo_bay",
        name="Tokyo Bay Megalopolis, Japan",
        country="Japan",
        latitude=35.6800,
        longitude=139.7600,
        bbox=[139.5000, 35.5000, 140.0000, 35.8000],
        default_crs="EPSG:4326",
        target_utm="EPSG:32654",
        description="Densely packed maritime metropolis showing artificial land reclamation in Tokyo Bay, coastal infrastructure, and heat island indices.",
        feature_type="Coastal Metropolis"
    )
]

# In-memory geocoding cache to minimize external network requests and rate limits
_GEO_CACHE: Dict[str, LocationInfo] = {loc.id: loc for loc in PRESET_LOCATIONS}


def calculate_utm_epsg(lat: float, lon: float) -> str:
    """Calculates appropriate UTM zone EPSG code for any lat/lon coordinate."""
    zone = int((lon + 180) / 6) + 1
    base = 32600 if lat >= 0 else 32700
    return f"EPSG:{base + zone}"


def _format_feature_type(osm_class: str, osm_type: str) -> str:
    """Maps raw OpenStreetMap tags to human-readable geographic feature categories."""
    cls = (osm_class or "").lower()
    typ = (osm_type or "").lower()

    if cls in ("water", "waterway") or typ in ("lake", "river", "reservoir", "stream", "canal", "pond", "bay"):
        return f"Water Body ({typ.capitalize() or 'Hydrology'})"
    if cls in ("natural", "landuse") and typ in ("wood", "forest", "tree_row"):
        return "Forest / Woodland"
    if typ in ("national_park", "nature_reserve", "protected_area"):
        return "Protected Nature Reserve"
    if typ in ("mountain", "peak", "volcano", "ridge", "valley"):
        return f"Topography ({typ.capitalize()})"
    if cls == "place" and typ in ("city", "town", "village", "hamlet", "suburb", "neighbourhood"):
        return f"Settlement ({typ.capitalize()})"
    if cls == "boundary" and typ == "administrative":
        return "Administrative Region"
    if cls in ("coastal", "coastline") or typ in ("coastline", "beach", "reef"):
        return "Coastal / Marine Feature"
    if typ:
        return typ.replace("_", " ").capitalize()
    return "Geographical Place"


def _try_parse_coordinates(query: str) -> Optional[LocationInfo]:
    """
    Checks if query is in any recognized direct coordinate format:
    - Decimal: '12.9716, 77.5946' or '-3.4653, -62.2159'
    - Directional: '12.9716N, 77.5946E' or '38.8951 N, 77.0364 W'
    - Space separated: '40.7128 -74.0060'
    """
    q = query.strip()
    
    # 1. Decimal coordinates
    pattern1 = r"^\s*([-+]?\d{1,2}(?:\.\d+)?)\s*[, ]\s*([-+]?\d{1,3}(?:\.\d+)?)\s*$"
    m1 = re.match(pattern1, q)
    if m1:
        try:
            lat = float(m1.group(1))
            lon = float(m1.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return _build_coordinate_location(lat, lon)
        except Exception:
            pass

    # 2. Directional coordinates (e.g. 12.9716 N, 77.5946 E)
    pattern2 = r"^\s*(\d{1,2}(?:\.\d+)?)\s*°?\s*([NSns])\s*[, ]\s*(\d{1,3}(?:\.\d+)?)\s*°?\s*([EWew])\s*$"
    m2 = re.match(pattern2, q)
    if m2:
        try:
            lat = float(m2.group(1)) * (-1 if m2.group(2).upper() == 'S' else 1)
            lon = float(m2.group(3)) * (-1 if m2.group(4).upper() == 'W' else 1)
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return _build_coordinate_location(lat, lon)
        except Exception:
            pass

    return None


def _build_coordinate_location(lat: float, lon: float) -> LocationInfo:
    """Creates a LocationInfo object for a direct coordinate point."""
    min_lon, min_lat = round(lon - 0.10, 4), round(lat - 0.10, 4)
    max_lon, max_lat = round(lon + 0.10, 4), round(lat + 0.10, 4)
    utm_crs = calculate_utm_epsg(lat, lon)
    lat_str = f"{abs(lat):.4f}°{'N' if lat >= 0 else 'S'}"
    lon_str = f"{abs(lon):.4f}°{'E' if lon >= 0 else 'W'}"
    loc_id = f"coord_{abs(hash((round(lat, 4), round(lon, 4)))) % 1000000}"

    return LocationInfo(
        id=loc_id,
        name=f"Point ({lat_str}, {lon_str})",
        country="Geographic Coordinate",
        latitude=round(lat, 5),
        longitude=round(lon, 5),
        bbox=[min_lon, min_lat, max_lon, max_lat],
        default_crs="EPSG:4326",
        target_utm=utm_crs,
        description=f"Direct geographic coordinates {lat_str}, {lon_str}.",
        feature_type="Geographic Coordinate"
    )


def search_locations(query: str, limit: int = 8) -> List[LocationInfo]:
    """
    Performs dynamic, worldwide geographical search across the actual global OpenStreetMap database.
    
    Supports:
    - Any city, town, village, or settlement worldwide
    - Any lake, river, sea, or ocean
    - Any mountain, forest, or national park
    - Any country, state, province, or district
    - Direct latitude/longitude coordinates
    - Ambiguous place names (returns multiple candidate locations)
    """
    q_clean = query.strip()
    if not q_clean:
        return PRESET_LOCATIONS[:limit]

    # 1. Direct coordinate check
    coord_loc = _try_parse_coordinates(q_clean)
    if coord_loc:
        return [coord_loc]

    results: List[LocationInfo] = []
    seen_keys = set()

    def _is_duplicate(lat: float, lon: float) -> bool:
        key = (round(lat, 2), round(lon, 2))
        if key in seen_keys:
            return True
        seen_keys.add(key)
        return False

    headers = {
        "User-Agent": "TerraPulseGeospatialIntelligence/2.0 (research@terrapulse.internal; contact: ops@terrapulse.io)"
    }

    # 2. Query OpenStreetMap Nominatim API (Primary worldwide geospatial database)
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": q_clean,
                "format": "json",
                "limit": limit,
                "addressdetails": 1,
                "extratags": 1
            },
            headers=headers,
            timeout=4.0
        )
        if resp.status_code == 200:
            items = resp.json()
            for item in items:
                try:
                    lat = float(item["lat"])
                    lon = float(item["lon"])
                    if _is_duplicate(lat, lon):
                        continue

                    raw_bbox = item.get("boundingbox")
                    if raw_bbox and len(raw_bbox) == 4:
                        min_lat, max_lat = float(raw_bbox[0]), float(raw_bbox[1])
                        min_lon, max_lon = float(raw_bbox[2]), float(raw_bbox[3])
                        # Ensure reasonable bounding box span for small or point features
                        if abs(max_lon - min_lon) < 0.05:
                            center_lon = (max_lon + min_lon) / 2
                            min_lon, max_lon = center_lon - 0.08, center_lon + 0.08
                        if abs(max_lat - min_lat) < 0.05:
                            center_lat = (max_lat + min_lat) / 2
                            min_lat, max_lat = center_lat - 0.08, center_lat + 0.08
                    else:
                        min_lon, min_lat = lon - 0.10, lat - 0.10
                        max_lon, max_lat = lon + 0.10, lat + 0.10

                    addr = item.get("address", {})
                    country = addr.get("country", "Global")
                    utm_crs = calculate_utm_epsg(lat, lon)
                    feat_type = _format_feature_type(item.get("class", ""), item.get("type", ""))
                    loc_id = f"osm_{item.get('osm_id', abs(hash(item['display_name'])) % 1000000)}"

                    loc = LocationInfo(
                        id=loc_id,
                        name=item["display_name"],
                        country=country,
                        latitude=round(lat, 5),
                        longitude=round(lon, 5),
                        bbox=[round(min_lon, 4), round(min_lat, 4), round(max_lon, 4), round(max_lat, 4)],
                        default_crs="EPSG:4326",
                        target_utm=utm_crs,
                        description=f"Resolved via OpenStreetMap Nominatim • Category: {feat_type}.",
                        feature_type=feat_type
                    )
                    results.append(loc)
                    _GEO_CACHE[loc.name.lower()] = loc
                    _GEO_CACHE[loc_id] = loc
                except Exception:
                    continue
    except Exception as e:
        print(f"Nominatim lookup notice (switching to Photon fallback): {e}")

    # 3. High-Speed Worldwide Photon Fallback (Built on OpenStreetMap worldwide data)
    if len(results) < 2:
        try:
            resp_photon = requests.get(
                "https://photon.komoot.io/api/",
                params={"q": q_clean, "limit": limit},
                headers=headers,
                timeout=3.5
            )
            if resp_photon.status_code == 200:
                features = resp_photon.json().get("features", [])
                for feat in features:
                    try:
                        coords = feat.get("geometry", {}).get("coordinates", [])
                        if len(coords) < 2:
                            continue
                        lon, lat = float(coords[0]), float(coords[1])
                        if _is_duplicate(lat, lon):
                            continue

                        props = feat.get("properties", {})
                        name_val = props.get("name", q_clean)
                        state_val = props.get("state") or props.get("county") or ""
                        country_val = props.get("country", "Global")
                        
                        full_name_parts = [p for p in [name_val, state_val, country_val] if p]
                        display_name = ", ".join(full_name_parts)

                        utm_crs = calculate_utm_epsg(lat, lon)
                        feat_type = _format_feature_type(props.get("osm_key", ""), props.get("osm_value", ""))
                        loc_id = f"photon_{props.get('osm_id', abs(hash(display_name)) % 1000000)}"

                        # Generate suitable extent based on feature type
                        span = 0.25 if feat_type.startswith("Administrative") else 0.08
                        min_lon, min_lat = round(lon - span, 4), round(lat - span, 4)
                        max_lon, max_lat = round(lon + span, 4), round(lat + span, 4)

                        loc = LocationInfo(
                            id=loc_id,
                            name=display_name,
                            country=country_val,
                            latitude=round(lat, 5),
                            longitude=round(lon, 5),
                            bbox=[min_lon, min_lat, max_lon, max_lat],
                            default_crs="EPSG:4326",
                            target_utm=utm_crs,
                            description=f"Resolved via OpenStreetMap Photon • Category: {feat_type}.",
                            feature_type=feat_type
                        )
                        results.append(loc)
                        _GEO_CACHE[loc.name.lower()] = loc
                        _GEO_CACHE[loc_id] = loc
                    except Exception:
                        continue
        except Exception as e:
            print(f"Photon fallback notice: {e}")

    # 4. Optional: Match presets as suggestions if they match query and aren't already included
    cache_key = q_clean.lower()
    for p in PRESET_LOCATIONS:
        if cache_key in p.name.lower() or cache_key in p.id.lower():
            if not _is_duplicate(p.latitude, p.longitude):
                results.append(p)

    return results[:limit]


def geocode_location(query: str, allow_fallback: bool = False) -> LocationInfo:
    """
    Resolves any worldwide place name or coordinate into an authenticated LocationInfo object.
    
    If allow_fallback is False and resolution fails, raises ValueError instead of
    silently substituting an unrelated location (e.g. never substitutes Bengaluru).
    """
    q_clean = query.strip()
    cache_key = q_clean.lower()

    # Check cache first
    if cache_key in _GEO_CACHE:
        return _GEO_CACHE[cache_key]

    # Coordinate check
    coord_loc = _try_parse_coordinates(q_clean)
    if coord_loc:
        _GEO_CACHE[cache_key] = coord_loc
        return coord_loc

    # Check presets
    for p in PRESET_LOCATIONS:
        if cache_key == p.name.lower() or cache_key == p.id.lower():
            _GEO_CACHE[cache_key] = p
            return p

    # Dynamic global search
    res = search_locations(q_clean, limit=1)
    if res:
        best = res[0]
        _GEO_CACHE[cache_key] = best
        return best

    if not allow_fallback:
        raise ValueError(
            f"Geographic location '{query}' could not be resolved in the worldwide geospatial database. "
            f"Please verify spelling or enter latitude/longitude coordinates (e.g. '40.7128, -74.0060')."
        )

    # Controlled explicit fallback
    print(f"Warning: Geocoding failed for '{query}', falling back to default preset.")
    return PRESET_LOCATIONS[0]


def list_preset_locations() -> List[LocationInfo]:
    """Returns optional preset research corridor suggestions."""
    return PRESET_LOCATIONS


def get_location_by_id(loc_id: str) -> Optional[LocationInfo]:
    """Retrieves a LocationInfo by ID or query, dynamically geocoding if needed."""
    if not loc_id:
        return PRESET_LOCATIONS[0]
    loc_clean = loc_id.lower().strip()
    if loc_clean in _GEO_CACHE:
        return _GEO_CACHE[loc_clean]
    for loc in PRESET_LOCATIONS:
        if loc.id.lower() == loc_clean or loc_clean in loc.name.lower():
            return loc
    # Dynamically geocode if not already cached
    try:
        geocoded = geocode_location(loc_id, allow_fallback=False)
        if geocoded:
            _GEO_CACHE[loc_clean] = geocoded
            _GEO_CACHE[geocoded.id] = geocoded
            return geocoded
    except Exception:
        pass
    return None
