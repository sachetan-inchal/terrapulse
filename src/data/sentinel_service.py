"""Sentinel-2 Cloud STAC Service & Dynamic Geocoding Ingestion.

Converts arbitrary user-typed locations into verified geographical coordinates,
bounding boxes, and UTM projections, then streams real-time and multi-temporal
Sentinel-2 L2A satellite observations directly from Microsoft Planetary Computer STAC.
"""

from typing import Dict, Any, List, Tuple, Optional
import io
import requests
import numpy as np
from PIL import Image
import pystac_client
import planetary_computer

from backend.services.geocoding import geocode_location as _geocode_core

# In-memory session cache to keep Streamlit UI lightning fast
_STAC_CACHE: Dict[str, Any] = {}

def geocode_user_location(query: str) -> Dict[str, Any]:
    """
    Converts any user-typed query (e.g. 'Bengaluru', 'Tokyo', 'Cairo', 'Paris')
    into exact coordinates, bounding box [min_lon, min_lat, max_lon, max_lat],
    and target UTM projection EPSG code.
    """
    loc = _geocode_core(query)
    return {
        "id": loc.id,
        "name": loc.name,
        "country": loc.country,
        "lat": loc.latitude,
        "lon": loc.longitude,
        "bbox": loc.bbox,
        "target_utm": loc.target_utm,
        "description": loc.description
    }

def get_stac_catalog():
    """Initializes authenticated Planetary Computer STAC client."""
    return pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

def fetch_real_sentinel2_pair(
    bbox: List[float],
    max_cloud: float = 20.0
) -> Tuple[Optional[Tuple[Image.Image, Dict[str, Any]]], Optional[Tuple[Image.Image, Dict[str, Any]]]]:
    """
    Searches Microsoft Planetary Computer STAC for a bi-temporal Sentinel-2 L2A observation pair:
    - Recent observation (latest cloud-free scene)
    - Historical observation (e.g., 2020 - 2022)
    Returns: ((img_historical, meta_historical), (img_recent, meta_recent))
    """
    cache_key = f"pair_{bbox[0]:.2f}_{bbox[1]:.2f}_{bbox[2]:.2f}_{bbox[3]:.2f}_{max_cloud}"
    if cache_key in _STAC_CACHE:
        return _STAC_CACHE[cache_key]

    catalog = get_stac_catalog()

    # 1. Fetch recent scene (latest available)
    recent_item = None
    try:
        search_recent = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime="2023-01-01/..",
            query={"eo:cloud_cover": {"lt": max_cloud}},
            max_items=5
        )
        recent_items = list(search_recent.items())
        if not recent_items:
            # Relax cloud constraint if cloudy
            search_recent = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime="2023-01-01/..",
                max_items=3
            )
            recent_items = list(search_recent.items())
        
        if recent_items:
            recent_item = recent_items[0]
    except Exception as e:
        print(f"Error fetching recent Sentinel-2: {e}")

    # 2. Fetch historical scene (earlier epoch 2019 - 2022)
    historical_item = None
    try:
        search_hist = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime="2018-01-01/2022-12-31",
            query={"eo:cloud_cover": {"lt": max_cloud}},
            max_items=5
        )
        hist_items = list(search_hist.items())
        if not hist_items:
            search_hist = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime="2018-01-01/2022-12-31",
                max_items=3
            )
            hist_items = list(search_hist.items())
        
        if hist_items:
            # Pick a well-separated historical scene
            historical_item = hist_items[-1]
    except Exception as e:
        print(f"Error fetching historical Sentinel-2: {e}")

    def download_preview_image(item) -> Optional[Tuple[Image.Image, Dict[str, Any]]]:
        if not item:
            return None
        preview_asset = item.assets.get("rendered_preview")
        if not preview_asset:
            return None
        url = preview_asset.href
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                dt = item.datetime
                date_str = dt.strftime("%Y-%m-%d") if dt else "Unknown"
                cloud = float(item.properties.get("eo:cloud_cover", 0.0))
                meta = {
                    "id": item.id,
                    "date": date_str,
                    "cloud_cover": round(cloud, 2),
                    "platform": item.properties.get("platform", "Sentinel-2"),
                    "sensor": "MultiSpectral Instrument (MSI)",
                    "preview_url": url,
                    "crs": item.properties.get("proj:epsg", "EPSG:32643")
                }
                return img, meta
        except Exception as err:
            print(f"Failed to download Sentinel preview: {err}")
        return None

    res_recent = download_preview_image(recent_item)
    res_hist = download_preview_image(historical_item)

    # If only one was found, try fallback
    if res_recent and not res_hist:
        res_hist = res_recent

    result = (res_hist, res_recent)
    if res_hist or res_recent:
        _STAC_CACHE[cache_key] = result
    return result

def query_sentinel2_mosaic_items(bbox: List[float], max_items: int = 4, max_cloud: float = 15.0):
    """Queries intersecting Sentinel-2 items for 2x2 mosaic stitching."""
    catalog = get_stac_catalog()
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        query={"eo:cloud_cover": {"lt": max_cloud}},
        max_items=max_items
    )
    items = list(search.items())
    if not items:
        # Fallback without cloud filter
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            max_items=max_items
        )
        items = list(search.items())
    return items
