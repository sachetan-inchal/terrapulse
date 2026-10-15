"""Geocoding & Region of Interest (AOI) Service."""
from typing import List, Optional
from backend.models.schemas import LocationInfo

PRESET_LOCATIONS: List[LocationInfo] = [
    LocationInfo(
        id="bengaluru",
        name="Bengaluru, Karnataka",
        country="India",
        latitude=12.9716,
        longitude=77.5946,
        bbox=[77.45, 12.85, 77.75, 13.10],
        target_utm="EPSG:32643",
        description="High-growth global IT hub undergoing intensive multi-decade urban expansion, lake encroachment, and green canopy reduction."
    ),
    LocationInfo(
        id="swiss_alps",
        name="Swiss Alps (Rhone Glacier)",
        country="Switzerland",
        latitude=46.56,
        longitude=8.38,
        bbox=[7.0, 45.5, 8.0, 46.2],
        target_utm="EPSG:32632",
        description="Alpine cryogenic ecosystem showing accelerating glacial retreat, snowpack depletion, and moraine transformation."
    ),
    LocationInfo(
        id="grand_canyon",
        name="Grand Canyon, Arizona",
        country="United States",
        latitude=36.10,
        longitude=-112.11,
        bbox=[-112.5, 35.8, -111.8, 36.4],
        target_utm="EPSG:32612",
        description="Hyper-arid sedimentary canyon system displaying Colorado river seasonal discharge shifts and riparian ecosystem changes."
    ),
    LocationInfo(
        id="nile_delta",
        name="Nile Delta & Cairo",
        country="Egypt",
        latitude=30.80,
        longitude=31.25,
        bbox=[30.5, 30.5, 31.5, 31.5],
        target_utm="EPSG:32636",
        description="Vulnerable Mediterranean delta basin displaying intense agricultural encroachment, coastal subsidence, and desert boundary dynamics."
    ),
    LocationInfo(
        id="tokyo_bay",
        name="Tokyo Megalopolis Grid",
        country="Japan",
        latitude=35.68,
        longitude=139.76,
        bbox=[139.5, 35.5, 140.0, 35.8],
        target_utm="EPSG:32654",
        description="Densely packed maritime metropolis showing artificial land reclamation in Tokyo Bay, coastal infrastructure, and heat island indices."
    )
]

def list_preset_locations() -> List[LocationInfo]:
    return PRESET_LOCATIONS

def get_location_by_id(loc_id: str) -> Optional[LocationInfo]:
    for loc in PRESET_LOCATIONS:
        if loc.id == loc_id:
            return loc
    return None

def search_locations(query: str) -> List[LocationInfo]:
    q = query.lower().strip()
    matches = [loc for loc in PRESET_LOCATIONS if q in loc.name.lower() or q in loc.country.lower()]
    if matches:
        return matches
    # Return default Bengaluru if search is unknown
    return [PRESET_LOCATIONS[0]]
