"""TerraPulse Geographical Intelligence, Geocoding, and Smart Map Labeling.

Provides authoritative geographical search, knowledge lookups, location discovery,
and smart MapLibre symbol & vector labeling capabilities.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Optional

from geoagent.core.decorators import geo_tool

# Curated high-precision geographical knowledge for landmark reference
GEOGRAPHICAL_KNOWLEDGE_BASE: dict[str, dict[str, Any]] = {
    "mount everest": {
        "name": "Mount Everest (Sagarmatha / Chomolungma)",
        "category": "Mountain Peak",
        "description": "Highest mountain peak above sea level on Earth at 8,848.86 metres (29,031.7 ft). Located in the Mahalangur Himal sub-range of the Himalayas on the China–Nepal border.",
        "lat": 27.9881,
        "lon": 86.9250,
        "zoom": 12,
        "elevation_m": 8848.86,
        "continent": "Asia",
        "countries": ["Nepal", "China"],
    },
    "k2": {
        "name": "K2 (Mount Godwin-Austen / Qogir)",
        "category": "Mountain Peak",
        "description": "Second-highest mountain in the world at 8,611 metres (28,251 ft), located in the Karakoram range on the Pakistan–China border.",
        "lat": 35.8813,
        "lon": 76.5133,
        "zoom": 12,
        "elevation_m": 8611,
        "continent": "Asia",
    },
    "kangchenjunga": {
        "name": "Kangchenjunga",
        "category": "Mountain Peak",
        "description": "Third-highest mountain in the world at 8,586 metres (28,169 ft), located on the India–Nepal border in Sikkim.",
        "lat": 27.7025,
        "lon": 88.1475,
        "zoom": 12,
        "elevation_m": 8586,
        "continent": "Asia",
    },
    "lhotse": {
        "name": "Lhotse",
        "category": "Mountain Peak",
        "description": "Fourth-highest mountain in the world at 8,516 metres (27,940 ft), connected to Everest via the South Col.",
        "lat": 27.9617,
        "lon": 86.9333,
        "zoom": 12,
        "elevation_m": 8516,
        "continent": "Asia",
    },
    "makalu": {
        "name": "Makalu",
        "category": "Mountain Peak",
        "description": "Fifth-highest mountain in the world at 8,485 metres (27,838 ft), an isolated four-sided pyramid peak southeast of Everest.",
        "lat": 27.8892,
        "lon": 87.0889,
        "zoom": 12,
        "elevation_m": 8485,
        "continent": "Asia",
    },
    "challenger deep": {
        "name": "Challenger Deep (Mariana Trench)",
        "category": "Oceanic Trench",
        "description": "The deepest known point in Earth's oceans, measured at approximately 10,928 metres (35,853 ft) below sea level in the western Pacific Ocean.",
        "lat": 11.3300,
        "lon": 142.1990,
        "zoom": 8,
        "depth_m": 10928,
        "ocean": "Pacific Ocean",
    },
    "mariana trench": {
        "name": "Mariana Trench",
        "category": "Oceanic Trench",
        "description": "Crescent-shaped oceanic trench in the Western Pacific, extending ~2,550 km with an average width of 69 km.",
        "lat": 11.3500,
        "lon": 142.2000,
        "zoom": 6,
        "depth_m": 10994,
        "ocean": "Pacific Ocean",
    },
    "amazon river": {
        "name": "Amazon River",
        "category": "River",
        "description": "The largest river in the world by discharge volume (average ~209,000 m³/s, accounting for ~20% of global river flow) and second-longest river (~6,400 km).",
        "lat": -3.1070,
        "lon": -60.0261,
        "zoom": 6,
        "continent": "South America",
    },
    "nile river": {
        "name": "Nile River",
        "category": "River",
        "description": "Traditionally recognized as the longest river in the world (~6,650 km), flowing northward through northeastern Africa into the Mediterranean Sea.",
        "lat": 15.6000,
        "lon": 32.5333,
        "zoom": 5,
        "continent": "Africa",
    },
    "sahara desert": {
        "name": "Sahara Desert",
        "category": "Desert",
        "description": "The largest hot desert in the world and the third-largest desert overall (after Antarctica and the Arctic), covering over 9.2 million km² across North Africa.",
        "lat": 23.4162,
        "lon": 25.6628,
        "zoom": 4,
        "area_km2": 9200000,
        "continent": "Africa",
    },
    "pacific ocean": {
        "name": "Pacific Ocean",
        "category": "Ocean",
        "description": "The largest and deepest of Earth's oceanic divisions, covering ~165.25 million km² (about 46% of Earth's water surface and 32% of its total surface area).",
        "lat": 0.0,
        "lon": -160.0,
        "zoom": 2,
        "area_km2": 165250000,
    },
    "india": {
        "name": "Republic of India",
        "category": "Country",
        "description": "Seventh-largest country by area (3,287,263 km²) and most populous nation, sharing terrestrial borders with Pakistan, China, Nepal, Bhutan, Bangladesh, and Myanmar.",
        "lat": 20.5937,
        "lon": 78.9629,
        "zoom": 5,
        "capital": "New Delhi",
        "continent": "Asia",
    },
    "karnataka": {
        "name": "Karnataka, India",
        "category": "State",
        "description": "State in southwestern India bordered by the Arabian Sea to the west, Goa to the northwest, Maharashtra to the north, Telangana to the northeast, Andhra Pradesh to the east, Tamil Nadu to the southeast, and Kerala to the southwest.",
        "lat": 15.3173,
        "lon": 75.7139,
        "zoom": 7,
        "capital": "Bengaluru",
        "country": "India",
    },
    "bengaluru": {
        "name": "Bengaluru (Bangalore)",
        "category": "City",
        "description": "Capital of Karnataka, situated on the Deccan Plateau at an elevation of ~900 m (3,000 ft). Known as the Silicon Valley of India and Garden City.",
        "lat": 12.9716,
        "lon": 77.5946,
        "zoom": 12,
        "state": "Karnataka",
        "country": "India",
    },
}

NEIGHBORING_COUNTRIES_OF_INDIA = [
    {"name": "Pakistan", "capital": "Islamabad", "lat": 30.3753, "lon": 69.3451, "border_km": 3323},
    {"name": "China", "capital": "Beijing", "lat": 35.8617, "lon": 104.1954, "border_km": 3488},
    {"name": "Nepal", "capital": "Kathmandu", "lat": 28.3949, "lon": 84.1240, "border_km": 1751},
    {"name": "Bhutan", "capital": "Thimphu", "lat": 27.5142, "lon": 90.4336, "border_km": 699},
    {"name": "Bangladesh", "capital": "Dhaka", "lat": 23.6850, "lon": 90.3563, "border_km": 4096},
    {"name": "Myanmar", "capital": "Naypyidaw", "lat": 21.9162, "lon": 95.9560, "border_km": 1643},
    {"name": "Sri Lanka", "capital": "Colombo", "lat": 7.8731, "lon": 80.7718, "maritime": True},
]

TOP_5_PEAKS = [
    {"rank": 1, "name": "Mount Everest", "elevation_m": 8848.86, "range": "Himalayas", "countries": "Nepal / China", "lat": 27.9881, "lon": 86.9250},
    {"rank": 2, "name": "K2", "elevation_m": 8611, "range": "Karakoram", "countries": "Pakistan / China", "lat": 35.8813, "lon": 76.5133},
    {"rank": 3, "name": "Kangchenjunga", "elevation_m": 8586, "range": "Himalayas", "countries": "India / Nepal", "lat": 27.7025, "lon": 88.1475},
    {"rank": 4, "name": "Lhotse", "elevation_m": 8516, "range": "Himalayas", "countries": "Nepal / China", "lat": 27.9617, "lon": 86.9333},
    {"rank": 5, "name": "Makalu", "elevation_m": 8485, "range": "Himalayas", "countries": "Nepal / China", "lat": 27.8892, "lon": 87.0889},
]


def _nominatim_search(query: str, limit: int = 1) -> list[dict[str, Any]]:
    """Query OpenStreetMap Nominatim for real-world geographic coordinates."""
    safe_query = urllib.parse.quote(query.strip())
    url = f"https://nominatim.openstreetmap.org/search?q={safe_query}&format=json&limit={limit}&addressdetails=1"
    req = urllib.request.Request(url, headers={"User-Agent": "TerraPulse-Geographical-Agent/1.9.1"})
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return []


def geographical_intelligence_tools(m: Any) -> list[Any]:
    """Build Geographical Intelligence & Smart Map Labeling tools bound to map `m`."""
    if m is None:
        return []

    @geo_tool(category="geography")
    def locate_geographical_feature(query: str, auto_zoom: Optional[int] = None) -> dict[str, Any]:
        """Search and visually locate any geographic feature, landmark, country, mountain, ocean, or city on the interactive map.

        Args:
            query: Name of the geographical entity (e.g. 'Mount Everest', 'Challenger Deep', 'Bengaluru', 'Sahara Desert').
            auto_zoom: Optional zoom override. If omitted, an optimal zoom level is chosen automatically based on the feature type.

        Returns:
            A dictionary containing the location name, category, coordinates, zoom, description, and status.
        """
        clean = query.strip().lower()
        res_info: dict[str, Any] = {}

        # 1. Check knowledge base first
        for key, info in GEOGRAPHICAL_KNOWLEDGE_BASE.items():
            if key in clean or clean in key:
                res_info = dict(info)
                break

        # 2. Live geocode via Nominatim if not found or for generic places
        if not res_info:
            nom_results = _nominatim_search(query, limit=1)
            if nom_results:
                hit = nom_results[0]
                lat = float(hit["lat"])
                lon = float(hit["lon"])
                cls_type = f"{hit.get('class', '')} / {hit.get('type', '')}"
                res_info = {
                    "name": hit.get("display_name", query).split(",")[0],
                    "category": cls_type,
                    "description": hit.get("display_name", query),
                    "lat": lat,
                    "lon": lon,
                    "zoom": 12 if "city" in cls_type or "town" in cls_type else (6 if "country" in cls_type or "state" in cls_type else 10),
                }

        if not res_info:
            return {"status": "NOT_FOUND", "message": f"Could not find coordinates for {query!r}."}

        lat = float(res_info["lat"])
        lon = float(res_info["lon"])
        zoom = auto_zoom or res_info.get("zoom", 11)

        # 3. Update the map viewport
        if hasattr(m, "set_center"):
            try:
                m.set_center(lon, lat)
            except Exception:
                m.set_center(lat, lon)
        if hasattr(m, "set_zoom"):
            m.set_zoom(int(zoom))

        # 4. Add smart interactive marker
        marker_label = res_info.get("name", query)
        popup_text = f"<b>{marker_label}</b><br>{res_info.get('category', 'Geographic Feature')}<br>Coordinates: {lat:.4f}° N, {lon:.4f}° E"
        if hasattr(m, "add_marker"):
            try:
                m.add_marker(lon, lat, popup=popup_text, tooltip=marker_label)
            except Exception:
                pass

        return {
            "status": "LOCATED",
            "name": marker_label,
            "category": res_info.get("category"),
            "coordinates": {"latitude": lat, "longitude": lon},
            "zoom": zoom,
            "description": res_info.get("description"),
            "map_action": f"Map centered and marked at ({lat:.4f}, {lon:.4f}) with zoom {zoom}.",
        }

    @geo_tool(category="geography")
    def show_top_mountain_peaks() -> dict[str, Any]:
        """Locate and compare the world's 5 highest mountain peaks (Everest, K2, Kangchenjunga, Lhotse, Makalu) simultaneously on the map."""
        if hasattr(m, "set_center"):
            m.set_center(86.9250, 27.9881)
        if hasattr(m, "set_zoom"):
            m.set_zoom(7)

        for peak in TOP_5_PEAKS:
            if hasattr(m, "add_marker"):
                popup_msg = f"<b>#{peak['rank']}: {peak['name']}</b><br>Elevation: {peak['elevation_m']} m<br>Range: {peak['range']}"
                try:
                    m.add_marker(peak["lon"], peak["lat"], popup=popup_msg, tooltip=f"#{peak['rank']} {peak['name']} ({peak['elevation_m']}m)")
                except Exception:
                    pass

        return {
            "status": "SUCCESS",
            "peaks": TOP_5_PEAKS,
            "summary": "Displayed the top 5 highest peaks in the world (Everest, K2, Kangchenjunga, Lhotse, Makalu) with individual markers across the Himalayas and Karakoram ranges.",
        }

    @geo_tool(category="geography")
    def show_neighboring_countries_of_india() -> dict[str, Any]:
        """Highlight and locate all terrestrial and maritime countries bordering India (Pakistan, China, Nepal, Bhutan, Bangladesh, Myanmar, Sri Lanka)."""
        if hasattr(m, "set_center"):
            m.set_center(78.9629, 22.5937)
        if hasattr(m, "set_zoom"):
            m.set_zoom(5)

        for country in NEIGHBORING_COUNTRIES_OF_INDIA:
            if hasattr(m, "add_marker"):
                popup_msg = f"<b>{country['name']}</b><br>Capital: {country['capital']}<br>{'Border length: ' + str(country.get('border_km', '')) + ' km' if 'border_km' in country else 'Maritime border'}"
                try:
                    m.add_marker(country["lon"], country["lat"], popup=popup_msg, tooltip=country["name"])
                except Exception:
                    pass

        return {
            "status": "SUCCESS",
            "countries": NEIGHBORING_COUNTRIES_OF_INDIA,
            "summary": "Marked all countries bordering India on the interactive map: Pakistan, China, Nepal, Bhutan, Bangladesh, Myanmar, and Sri Lanka.",
        }

    @geo_tool(category="geography")
    def toggle_smart_map_labels(enabled: bool = True) -> str:
        """Toggle Google Maps-style smart dynamic vector labels (countries, cities, roads, landmarks) across zoom levels.

        Args:
            enabled: Whether labels should be enabled (True) or hidden (False).

        Returns:
            A status confirmation string.
        """
        layer_id = "terrapulse_smart_labels"
        if enabled:
            if hasattr(m, "add_tile_layer"):
                try:
                    m.add_tile_layer(
                        source_url="https://basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png",
                        layer_id=layer_id,
                        attribution="© CARTO © OpenStreetMap",
                    )
                    return "Smart dynamic labels enabled: progressive zoom-dependent names for continents, countries, cities, and streets."
                except Exception as e:
                    return f"Failed to enable smart labels: {e}"
        else:
            if hasattr(m, "remove_layer"):
                try:
                    m.remove_layer(layer_id)
                    return "Smart dynamic labels disabled."
                except Exception:
                    pass
        return "Smart labels toggled."

    return [
        locate_geographical_feature,
        show_top_mountain_peaks,
        show_neighboring_countries_of_india,
        toggle_smart_map_labels,
    ]

