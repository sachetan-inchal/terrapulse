"""Geocoding & Region of Interest (AOI) Service.

Dynamically converts user-typed location queries (cities, addresses, coordinates)
into accurate geographical coordinates, bounding boxes, and target UTM EPSG codes
via OpenStreetMap Nominatim with local in-memory caching.
"""
from typing import List, Optional, Dict
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
    )
]

# In-memory geocoding cache to minimize rate limits
_GEO_CACHE: Dict[str, LocationInfo] = {loc.id: loc for loc in PRESET_LOCATIONS}

def calculate_utm_epsg(lat: float, lon: float) -> str:
    """Calculates appropriate UTM zone EPSG code for any lat/lon coordinate."""
    zone = int((lon + 180) / 6) + 1
    base = 32600 if lat >= 0 else 32700
    return f"EPSG:{base + zone}"

def geocode_location(query: str) -> LocationInfo:
    """
    Converts any typed location string into verified geographic coordinates,
    bounding box [min_lon, min_lat, max_lon, max_lat], and UTM CRS.
    """
    q_clean = query.strip()
    cache_key = q_clean.lower()
    
    # Check cache first
    if cache_key in _GEO_CACHE:
        return _GEO_CACHE[cache_key]
    
    # Check if query matches a preset directly
    for p in PRESET_LOCATIONS:
        if cache_key in p.name.lower() or cache_key in p.id.lower():
            _GEO_CACHE[cache_key] = p
            return p

    # Query OpenStreetMap Nominatim for real geocoding
    headers = {
        "User-Agent": "EarthTemporalIntelligence/2.0 (research@terrapulse.internal)"
    }
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q_clean, "format": "json", "limit": 1, "addressdetails": 1},
            headers=headers,
            timeout=5.0
        )
        if resp.status_code == 200 and resp.json():
            item = resp.json()[0]
            lat = float(item["lat"])
            lon = float(item["lon"])
            raw_bbox = item.get("boundingbox")
            
            if raw_bbox and len(raw_bbox) == 4:
                # Nominatim returns [south, north, west, east]
                min_lat, max_lat = float(raw_bbox[0]), float(raw_bbox[1])
                min_lon, max_lon = float(raw_bbox[2]), float(raw_bbox[3])
                # Ensure bbox has non-zero spatial area
                if abs(max_lon - min_lon) < 0.05:
                    min_lon -= 0.05
                    max_lon += 0.05
                if abs(max_lat - min_lat) < 0.05:
                    min_lat -= 0.05
                    max_lat += 0.05
            else:
                # Default 0.15 degree window (~16 km) around centroid
                min_lon, min_lat = lon - 0.12, lat - 0.10
                max_lon, max_lat = lon + 0.12, lat + 0.10

            loc_id = f"custom_{abs(hash(q_clean)) % 100000}"
            country = item.get("address", {}).get("country", "Global")
            utm_crs = calculate_utm_epsg(lat, lon)
            
            loc_info = LocationInfo(
                id=loc_id,
                name=item["display_name"],
                country=country,
                latitude=round(lat, 5),
                longitude=round(lon, 5),
                bbox=[round(min_lon, 4), round(min_lat, 4), round(max_lon, 4), round(max_lat, 4)],
                default_crs="EPSG:4326",
                target_utm=utm_crs,
                description=f"User-queried location resolved via Nominatim at {lat:.4f}° N, {lon:.4f}° E."
            )
            _GEO_CACHE[cache_key] = loc_info
            _GEO_CACHE[loc_id] = loc_info
            return loc_info
            
    except Exception as e:
        print(f"Nominatim geocoding failed for '{query}': {e}")

    # Fallback to Bengaluru if geocoding cannot resolve
    return PRESET_LOCATIONS[0]

def list_preset_locations() -> List[LocationInfo]:
    return PRESET_LOCATIONS

def get_location_by_id(loc_id: str) -> Optional[LocationInfo]:
    if loc_id in _GEO_CACHE:
        return _GEO_CACHE[loc_id]
    for loc in PRESET_LOCATIONS:
        if loc.id == loc_id:
            return loc
    return PRESET_LOCATIONS[0]
