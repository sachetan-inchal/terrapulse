"""Geocoding & Region of Interest (AOI) Service.

Dynamically converts user-typed location queries (cities, addresses, coordinates)
into accurate geographical coordinates, bounding boxes, and target UTM EPSG codes
via OpenStreetMap Nominatim with local in-memory caching.
"""
from typing import List, Optional, Dict
import re
import requests
from backend.models.schemas import LocationInfo

# Verified global presets for instant navigation
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
        description="High-growth global IT hub undergoing intensive multi-decade urban expansion and green canopy reduction."
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
        description="Major coastal metropolitan industrial corridor along the Coromandel Coast with Adyar and Cooum river basins."
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
        description="High-density maritime megacity on Salsette Island displaying coastal reclamation, industrial emissions, and port logistics."
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
        description="Major metropolitan capital region with intense seasonal atmospheric particulate loading, Yamuna river basin, and thermal inversions."
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
        description="Deccan plateau IT and pharmaceutical industrial center with Musi river basin and urban lake catchment networks."
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
        description="Urban wetland lake catchment in southeast Bengaluru experiencing severe eutrophication, sewage influx, and surfactant foam events."
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
        description="Downstream receiving wetland lake in the Bellandur-Varthur catchment displaying hypoxic dissolved oxygen and phosphate accumulation."
    ),
    LocationInfo(
        id="swiss_alps",
        name="Swiss Alps (Rhone Glacier), Switzerland",
        country="Switzerland",
        latitude=46.56,
        longitude=8.38,
        bbox=[7.0, 45.5, 8.0, 46.2],
        default_crs="EPSG:4326",
        target_utm="EPSG:32632",
        description="Alpine cryogenic ecosystem showing accelerating glacial retreat, snowpack depletion, and moraine transformation."
    ),
    LocationInfo(
        id="grand_canyon",
        name="Grand Canyon, Arizona, USA",
        country="United States",
        latitude=36.10,
        longitude=-112.11,
        bbox=[-112.5, 35.8, -111.8, 36.4],
        default_crs="EPSG:4326",
        target_utm="EPSG:32612",
        description="Hyper-arid sedimentary canyon system displaying Colorado river seasonal discharge shifts and riparian ecosystem changes."
    ),
    LocationInfo(
        id="nile_delta",
        name="Nile Delta & Cairo, Egypt",
        country="Egypt",
        latitude=30.80,
        longitude=31.25,
        bbox=[30.5, 30.5, 31.5, 31.5],
        default_crs="EPSG:4326",
        target_utm="EPSG:32636",
        description="Vulnerable Mediterranean delta basin displaying intense agricultural encroachment, coastal subsidence, and desert boundary dynamics."
    ),
    LocationInfo(
        id="tokyo_bay",
        name="Tokyo Bay Megalopolis, Japan",
        country="Japan",
        latitude=35.68,
        longitude=139.76,
        bbox=[139.5, 35.5, 140.0, 35.8],
        default_crs="EPSG:4326",
        target_utm="EPSG:32654",
        description="Densely packed maritime metropolis showing artificial land reclamation in Tokyo Bay, coastal infrastructure, and heat island indices."
    ),
    LocationInfo(
        id="new_delhi",
        name="New Delhi, National Capital Territory of Delhi, India",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
        bbox=[77.0500, 28.4500, 77.3500, 28.7500],
        default_crs="EPSG:4326",
        target_utm="EPSG:32643",
        description="Major metropolitan national capital region displaying intensive urban sprawl, industrial corridors, and seasonal atmospheric dynamics."
    ),
    LocationInfo(
        id="paris",
        name="Paris, Île-de-France, France",
        country="France",
        latitude=48.8566,
        longitude=2.3522,
        bbox=[2.2000, 48.7500, 2.5000, 48.9500],
        default_crs="EPSG:4326",
        target_utm="EPSG:32631",
        description="Historic European cultural and urban hub along the Seine river basin with dense urban fabric and peripheral agricultural tracts."
    )
]

# In-memory geocoding cache to minimize rate limits
_GEO_CACHE: Dict[str, LocationInfo] = {loc.id: loc for loc in PRESET_LOCATIONS}


def calculate_utm_epsg(lat: float, lon: float) -> str:
    """Calculates appropriate UTM zone EPSG code for any lat/lon coordinate."""
    zone = int((lon + 180) / 6) + 1
    base = 32600 if lat >= 0 else 32700
    return f"EPSG:{base + zone}"


def _try_parse_coordinates(query: str) -> Optional[LocationInfo]:
    """Checks if query is in decimal coordinates format: 'lat, lon' or 'lat lon'."""
    pattern = r"^\s*([-+]?\d{1,2}(?:\.\d+)?)\s*[, ]\s*([-+]?\d{1,3}(?:\.\d+)?)\s*$"
    match = re.match(pattern, query.strip())
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                min_lon, min_lat = lon - 0.20, lat - 0.20
                max_lon, max_lat = lon + 0.20, lat + 0.20
                utm_crs = calculate_utm_epsg(lat, lon)
                loc_id = f"coord_{round(lat, 4)}_{round(lon, 4)}"
                return LocationInfo(
                    id=loc_id,
                    name=f"Point ({lat:.4f}° N, {lon:.4f}° E)",
                    country="Geographic Point",
                    latitude=round(lat, 5),
                    longitude=round(lon, 5),
                    bbox=[round(min_lon, 4), round(min_lat, 4), round(max_lon, 4), round(max_lat, 4)],
                    default_crs="EPSG:4326",
                    target_utm=utm_crs,
                    description=f"Direct geographic coordinates {lat:.4f}° N, {lon:.4f}° E."
                )
        except Exception:
            pass
    return None


def search_locations(query: str, limit: int = 5) -> List[LocationInfo]:
    """
    Searches for matching geographic places, returning a ranked list of suggestions
    with place name, administrative region, country, and coordinates.
    """
    q_clean = query.strip()
    if not q_clean:
        return PRESET_LOCATIONS[:limit]

    # Check coordinate pattern first
    coord_loc = _try_parse_coordinates(q_clean)
    if coord_loc:
        return [coord_loc]

    results: List[LocationInfo] = []
    seen_ids = set()

    # Check preset matches first
    cache_key = q_clean.lower()
    for p in PRESET_LOCATIONS:
        if cache_key in p.name.lower() or cache_key in p.id.lower() or any(term in p.name.lower() for term in cache_key.split()):
            if p.id not in seen_ids:
                results.append(p)
                seen_ids.add(p.id)

    # Query Nominatim API for live search results
    headers = {
        "User-Agent": "TerraPulseGeospatialIntelligence/2.0 (research@terrapulse.internal)"
    }
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q_clean, "format": "json", "limit": limit, "addressdetails": 1},
            headers=headers,
            timeout=5.0
        )
        if resp.status_code == 200:
            items = resp.json()
            for item in items:
                try:
                    lat = float(item["lat"])
                    lon = float(item["lon"])
                    raw_bbox = item.get("boundingbox")
                    if raw_bbox and len(raw_bbox) == 4:
                        min_lat, max_lat = float(raw_bbox[0]), float(raw_bbox[1])
                        min_lon, max_lon = float(raw_bbox[2]), float(raw_bbox[3])
                        if abs(max_lon - min_lon) < 0.05:
                            min_lon -= 0.10
                            max_lon += 0.10
                        if abs(max_lat - min_lat) < 0.05:
                            min_lat -= 0.10
                            max_lat += 0.10
                    else:
                        min_lon, min_lat = lon - 0.20, lat - 0.20
                        max_lon, max_lat = lon + 0.20, lat + 0.20

                    loc_id = f"osm_{item.get('osm_id', abs(hash(item['display_name'])) % 1000000)}"
                    if loc_id in seen_ids:
                        continue
                    seen_ids.add(loc_id)

                    addr = item.get("address", {})
                    country = addr.get("country", "Global")
                    utm_crs = calculate_utm_epsg(lat, lon)

                    loc = LocationInfo(
                        id=loc_id,
                        name=item["display_name"],
                        country=country,
                        latitude=round(lat, 5),
                        longitude=round(lon, 5),
                        bbox=[round(min_lon, 4), round(min_lat, 4), round(max_lon, 4), round(max_lat, 4)],
                        default_crs="EPSG:4326",
                        target_utm=utm_crs,
                        description=f"Resolved via OpenStreetMap Nominatim at {lat:.4f}° N, {lon:.4f}° E."
                    )
                    results.append(loc)
                    _GEO_CACHE[loc.name.lower()] = loc
                    _GEO_CACHE[loc_id] = loc
                except Exception:
                    continue
    except Exception as e:
        print(f"Nominatim search request failed: {e}")

    return results[:limit]


def geocode_location(query: str, allow_fallback: bool = True) -> LocationInfo:
    """
    Converts any typed location string into verified geographic coordinates,
    bounding box [min_lon, min_lat, max_lon, max_lat], and UTM CRS.

    If allow_fallback is False and resolution fails, raises ValueError instead of
    silently substituting an unrelated location.
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

    # Check if query matches a preset directly
    for p in PRESET_LOCATIONS:
        if cache_key == p.name.lower() or cache_key == p.id.lower():
            _GEO_CACHE[cache_key] = p
            return p

    # Query Nominatim
    res = search_locations(q_clean, limit=1)
    if res:
        best = res[0]
        _GEO_CACHE[cache_key] = best
        return best

    if not allow_fallback:
        raise ValueError(f"Could not resolve geographic location '{query}'. Please verify spelling or provide coordinates.")

    # Controlled fallback with explicit logging
    print(f"Warning: Geocoding failed for '{query}', falling back to default preset.")
    return PRESET_LOCATIONS[0]


def list_preset_locations() -> List[LocationInfo]:
    return PRESET_LOCATIONS


def get_location_by_id(loc_id: str) -> Optional[LocationInfo]:
    if not loc_id:
        return PRESET_LOCATIONS[0]
    loc_clean = loc_id.lower().strip()
    if loc_clean in _GEO_CACHE:
        return _GEO_CACHE[loc_clean]
    for loc in PRESET_LOCATIONS:
        if loc.id.lower() == loc_clean or loc_clean in loc.name.lower():
            return loc
    # Dynamically geocode if not already cached
    geocoded = geocode_location(loc_id)
    if geocoded:
        _GEO_CACHE[loc_clean] = geocoded
        _GEO_CACHE[geocoded.id] = geocoded
        return geocoded
    return PRESET_LOCATIONS[0]
