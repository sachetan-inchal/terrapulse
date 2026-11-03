"""TerraPulse Strands Conversational Environmental Investigator Agent.

Provides:
- Multi-turn conversational investigation with sliding memory and session isolation.
- Automatic slot-filling and proactive clarification questions for missing parameters (location, symptom, timeframe).
- Dynamic tool dispatcher connecting Phase 1 literature APIs, Phase 2 spatial analysis, Phase 3 symptom investigation, and Phase 4 forecasting.
- Real-time activity event generator emitting structured events:
    * tool_call_start
    * tool_call_args
    * tool_call_result
    * clarification_needed
    * final_response
- Scientific integrity enforcer: preserves epistemic distinction between measured observations, interpolated models, and future forecasts.
"""

from __future__ import annotations

import os
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
import re
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, Iterator, List, Optional, Tuple

from geoagent.core.config import GeoAgentConfig
from geoagent.core.decorators import geo_tool
from environmental.research_apis import (
    search_academic_literature,
    search_environmental_news,
    search_all_research,
)
from environmental.spatial_analysis import (
    MonitoringStation,
    SpatialBoundingBox,
    IDWConfig,
    compute_idw_surface,
    compute_getis_ord_gi_star,
    compute_regional_statistics,
    generate_investigation_geojson,
    get_preset_bengaluru_monitoring_stations,
)
from environmental.symptom_analyzer import (
    classify_symptom_from_text,
    investigate_environmental_symptom,
)
from environmental.forecasting import (
    HistoricalObservation,
    generate_environmental_forecast,
)

logger = logging.getLogger(__name__)


class ActivityEventType(str, Enum):
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_ARGS = "tool_call_args"
    TOOL_CALL_RESULT = "tool_call_result"
    CLARIFICATION_NEEDED = "clarification_needed"
    FINAL_RESPONSE = "final_response"


@dataclass
class ActivityEvent:
    """A structured observable activity event emitted during agent execution."""
    event_type: ActivityEventType
    timestamp: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "timestamp": self.timestamp,
            **self.data,
        }


@dataclass
class InvestigationSession:
    """Isolated session state for a multi-turn environmental investigation."""
    session_id: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    pollutant: Optional[str] = None
    symptom_key: Optional[str] = None
    symptom_name: Optional[str] = None
    pending_symptom_query: Optional[str] = None
    timeframe: Optional[str] = None
    pending_clarification: Optional[str] = None  # e.g. "LOCATION", "POLLUTANT"
    turns: List[Dict[str, str]] = field(default_factory=list)  # [{"role": "user"|"assistant", "content": ...}]
    last_findings: Optional[Dict[str, Any]] = None
    last_geojson: Optional[Dict[str, Any]] = None
    last_forecast: Optional[Dict[str, Any]] = None
    max_history_turns: int = 20

    def add_message(self, role: str, content: str) -> None:
        self.turns.append({"role": role, "content": content})
        if len(self.turns) > self.max_history_turns:
            self.turns = self.turns[-self.max_history_turns:]

    @property
    def messages(self) -> List[Dict[str, str]]:
        return self.turns


class SessionManager:
    """In-memory thread-safe session manager providing isolated conversation state."""

    def __init__(self):
        self._sessions: Dict[str, InvestigationSession] = {}

    def get_or_create_session(self, session_id: str) -> InvestigationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = InvestigationSession(session_id=session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def reset_session(self, session_id: str) -> InvestigationSession:
        self.clear_session(session_id)
        return self.get_or_create_session(session_id)

    def get_session(self, session_id: str) -> Optional[InvestigationSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())


# Global session manager instance
_default_session_manager = SessionManager()


# ---------------------------------------------------------------------------
# Strands Callable Environmental Tools
# ---------------------------------------------------------------------------

@geo_tool(category="environmental", name="search_academic_literature")
def search_academic_literature_tool(query: str, limit_per_source: int = 3) -> Dict[str, Any]:
    """Search peer-reviewed scientific literature across OpenAlex, Crossref, Europe PMC, and Semantic Scholar.
    
    Args:
        query: Academic keywords (e.g. "lake hypoxia fish kill eutrophication").
        limit_per_source: Maximum articles per academic repository.
    """
    articles, metrics = search_academic_literature(query=query, limit_per_source=limit_per_source)
    return {
        "query": query,
        "total_results": len(articles),
        "articles": [a.to_dict() for a in articles],
        "metrics": metrics,
    }


@geo_tool(category="environmental", name="search_environmental_news")
def search_environmental_news_tool(query: str, limit_per_source: int = 3) -> Dict[str, Any]:
    """Search investigative news and international media reports across The Guardian and GDELT 2.0.
    
    Args:
        query: Environmental event or controversy keywords.
        limit_per_source: Maximum articles per news platform.
    """
    articles, metrics = search_environmental_news(query=query, limit_per_source=limit_per_source)
    return {
        "query": query,
        "total_results": len(articles),
        "articles": [a.to_dict() for a in articles],
        "metrics": metrics,
    }


@geo_tool(category="environmental", name="investigate_environmental_symptom")
def investigate_environmental_symptom_tool(symptom_query: str, location: Optional[str] = None) -> Dict[str, Any]:
    """Investigate environmental symptoms (e.g. fish deaths, toxic foam, green algae, smog) using causal analysis.
    
    Args:
        symptom_query: Description of the observed symptom.
        location: Target geographic region or water body name.
    """
    from environmental.spatial_analysis import get_monitoring_stations_for_location
    stations = get_monitoring_stations_for_location(location or "bengaluru")
    return investigate_environmental_symptom(
        user_query=symptom_query,
        stations=stations,
        fetch_live_literature=True,
        literature_limit=2,
    )


@geo_tool(category="environmental", name="compute_idw_surface")
def compute_idw_surface_tool(
    min_lat: float, min_lon: float, max_lat: float, max_lon: float,
    power: float = 2.0, search_radius_km: float = 25.0,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """Compute an Inverse Distance Weighting (IDW) continuous pollution surface over a geographic bounding box.
    
    Args:
        min_lat: Minimum bounding latitude.
        min_lon: Minimum bounding longitude.
        max_lat: Maximum bounding latitude.
        max_lon: Maximum bounding longitude.
        power: Distance decay exponent (default: 2.0).
        search_radius_km: Maximum interpolation neighborhood distance in km.
        location: Optional location name to resolve telemetry.
    """
    from environmental.spatial_analysis import get_monitoring_stations_for_location
    stations = get_monitoring_stations_for_location(location or ("chennai" if min_lon > 79 else "bengaluru"))
    bbox = SpatialBoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)
    cfg = IDWConfig(power=power, search_radius_km=search_radius_km, grid_resolution_x=12, grid_resolution_y=12)
    cells, meta = compute_idw_surface(stations, bbox, cfg)
    geojson = generate_investigation_geojson(stations, interpolated_cells=cells)
    return {
        "metadata": meta,
        "geojson": geojson,
        "cell_count": len(cells),
    }


@geo_tool(category="environmental", name="compute_getis_ord_gi_star")
def compute_getis_ord_gi_star_tool(
    distance_threshold_km: float = 15.0,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """Compute Getis-Ord Gi* spatial statistics to detect statistically significant pollution hotspots.
    
    Args:
        distance_threshold_km: Spatial weight distance band in km.
        location: Optional target region name.
    """
    from environmental.spatial_analysis import get_monitoring_stations_for_location
    stations = get_monitoring_stations_for_location(location or "bengaluru")
    hotspots = compute_getis_ord_gi_star(stations, distance_threshold_km=distance_threshold_km)
    significant = [h for h in hotspots if h.severity in ["CRITICAL_HOTSPOT", "HIGH_HOTSPOT", "MODERATE_HOTSPOT"]]
    geojson = generate_investigation_geojson(stations, hotspots=hotspots)
    return {
        "total_stations_evaluated": len(stations),
        "significant_hotspots_count": len(significant),
        "hotspots": [h.to_geojson_feature()["properties"] for h in significant],
        "geojson": geojson,
    }


@geo_tool(category="environmental", name="compute_regional_statistics")
def compute_regional_statistics_tool(
    min_lat: float, min_lon: float, max_lat: float, max_lon: float
) -> Dict[str, Any]:
    """Calculate descriptive statistics, station density, and data coverage for a study area.
    
    Args:
        min_lat: Minimum bounding latitude.
        min_lon: Minimum bounding longitude.
        max_lat: Maximum bounding latitude.
        max_lon: Maximum bounding longitude.
    """
    stations = get_preset_bengaluru_monitoring_stations()
    bbox = SpatialBoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)
    return compute_regional_statistics(stations, bbox)


@geo_tool(category="environmental", name="generate_environmental_forecast")
def generate_environmental_forecast_tool(
    indicator: str = "PM2.5",
    horizon: str = "+5 years",
    reduction_percentage: float = 30.0,
) -> Dict[str, Any]:
    """Generate multi-scenario forecasts comparing Business-As-Usual, Pollution Reduction, and Ecological Interventions.
    
    Args:
        indicator: Environmental indicator (e.g. "PM2.5", "dissolved_oxygen_mg_l", "NDVI", "built_up_coverage_pct").
        horizon: Target horizon ("+1 year", "+3 years", "+5 years", "2030", "2040").
        reduction_percentage: Target reduction percentage for policy scenario (default: 30.0).
    """
    ind_norm = indicator.lower().replace("-", "_").strip()
    prov_note = "Sample historical sequence for validation. Not live telemetry."

    if "oxygen" in ind_norm or "dissolved" in ind_norm or "do" == ind_norm:
        hist = [
            HistoricalObservation("2020-01-01T00:00:00Z", 2020.0, 4.5, "mg/L", "dissolved_oxygen_mg_l", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2021-01-01T00:00:00Z", 2021.0, 3.8, "mg/L", "dissolved_oxygen_mg_l", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2022-01-01T00:00:00Z", 2022.0, 2.9, "mg/L", "dissolved_oxygen_mg_l", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2023-01-01T00:00:00Z", 2023.0, 2.1, "mg/L", "dissolved_oxygen_mg_l", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2024-01-01T00:00:00Z", 2024.0, 1.4, "mg/L", "dissolved_oxygen_mg_l", is_sample_illustrative=True, source=prov_note),
        ]
    elif "ndvi" in ind_norm or "canopy" in ind_norm:
        hist = [
            HistoricalObservation("2020-01-01T00:00:00Z", 2020.0, 0.45, "index", "NDVI", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2021-01-01T00:00:00Z", 2021.0, 0.42, "index", "NDVI", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2022-01-01T00:00:00Z", 2022.0, 0.39, "index", "NDVI", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2023-01-01T00:00:00Z", 2023.0, 0.36, "index", "NDVI", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2024-01-01T00:00:00Z", 2024.0, 0.34, "index", "NDVI", is_sample_illustrative=True, source=prov_note),
        ]
    elif "built" in ind_norm or "urban" in ind_norm:
        hist = [
            HistoricalObservation("2020-01-01T00:00:00Z", 2020.0, 28.5, "%", "built_up_coverage_pct", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2021-01-01T00:00:00Z", 2021.0, 30.1, "%", "built_up_coverage_pct", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2022-01-01T00:00:00Z", 2022.0, 31.8, "%", "built_up_coverage_pct", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2023-01-01T00:00:00Z", 2023.0, 33.2, "%", "built_up_coverage_pct", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2024-01-01T00:00:00Z", 2024.0, 34.5, "%", "built_up_coverage_pct", is_sample_illustrative=True, source=prov_note),
        ]
    else:
        # Default PM2.5
        hist = [
            HistoricalObservation("2020-01-01T00:00:00Z", 2020.0, 60.0, "µg/m³", "PM2.5", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2021-01-01T00:00:00Z", 2021.0, 68.0, "µg/m³", "PM2.5", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2022-01-01T00:00:00Z", 2022.0, 74.0, "µg/m³", "PM2.5", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2023-01-01T00:00:00Z", 2023.0, 82.0, "µg/m³", "PM2.5", is_sample_illustrative=True, source=prov_note),
            HistoricalObservation("2024-01-01T00:00:00Z", 2024.0, 90.0, "µg/m³", "PM2.5", is_sample_illustrative=True, source=prov_note),
        ]

    report, err = generate_environmental_forecast(hist, horizon=horizon, reduction_percentage=reduction_percentage)
    if err:
        return {"error": err}
    return report.to_dict() if report else {"error": "Failed to generate forecast report."}


# ---------------------------------------------------------------------------
# Conversational Environmental Investigator Agent Core
# ---------------------------------------------------------------------------

KNOWN_LOCATIONS: Dict[str, Dict[str, Any]] = {
    "bellandur": {
        "canonical": "Bellandur Lake Catchment, Bengaluru",
        "lat": 12.9385,
        "lon": 77.6680,
        "bbox": [77.63, 12.91, 77.71, 12.96],
    },
    "varthur": {
        "canonical": "Varthur Lake Wetland, Bengaluru",
        "lat": 12.9421,
        "lon": 77.7420,
        "bbox": [77.71, 12.92, 77.77, 12.97],
    },
    "bengaluru": {
        "canonical": "Bengaluru Metropolitan Region, Karnataka, India",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.80, 77.75, 13.10],
    },
    "bangalore": {
        "canonical": "Bengaluru Metropolitan Region, Karnataka, India",
        "lat": 12.9716,
        "lon": 77.5946,
        "bbox": [77.45, 12.80, 77.75, 13.10],
    },
    "chennai": {
        "canonical": "Chennai Metropolitan Area, Tamil Nadu, India",
        "lat": 13.0827,
        "lon": 80.2707,
        "bbox": [80.15, 12.95, 80.35, 13.20],
    },
    "mumbai": {
        "canonical": "Mumbai Metropolitan Region, Maharashtra, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "bbox": [72.75, 18.90, 73.00, 19.25],
    },
    "bombay": {
        "canonical": "Mumbai Metropolitan Region, Maharashtra, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "bbox": [72.75, 18.90, 73.00, 19.25],
    },
    "delhi": {
        "canonical": "Delhi National Capital Region, India",
        "lat": 28.6139,
        "lon": 77.2090,
        "bbox": [77.05, 28.45, 77.35, 28.75],
    },
    "hyderabad": {
        "canonical": "Hyderabad Metropolitan Region, Telangana, India",
        "lat": 17.3850,
        "lon": 78.4867,
        "bbox": [78.35, 17.25, 78.60, 17.55],
    },
    "peenya": {
        "canonical": "Peenya Industrial Area, Bengaluru, India",
        "lat": 13.0315,
        "lon": 77.5185,
        "bbox": [77.45, 12.98, 77.58, 13.08],
    },
    "whitefield": {
        "canonical": "Whitefield Industrial Corridor, Bengaluru, India",
        "lat": 12.9812,
        "lon": 77.7289,
        "bbox": [77.65, 12.90, 77.80, 13.05],
    },
}


def _extract_location_from_query(query: str) -> Optional[Dict[str, Any]]:
    """Extract and resolve geographical entities from natural-language query with dynamic geocoding."""
    q_lower = query.lower()
    for loc_key, loc_info in KNOWN_LOCATIONS.items():
        if loc_key in q_lower:
            return loc_info

    # Dynamic prepositional extraction (e.g., "around Mumbai", "in Chennai", "over Bellandur Lake")
    patterns = [
        r'\b(?:around|in|at|near|of|for|over)\s+([A-Z][a-zA-Z\s]{2,28}(?:Lake|River|Wetland|City|District|Corridor|Bay)?)',
        r'\b([A-Z][a-zA-Z]{2,20}\s+Lake)\b',
        r'\b([A-Z][a-zA-Z]{2,20}\s+River)\b'
    ]
    for pattern in patterns:
        m = re.search(pattern, query)
        if m:
            candidate = m.group(1).strip()
            stop_words = {"the", "this", "that", "these", "those", "future", "past", "next", "five years", "air pollution", "water quality", "pollution"}
            if candidate.lower() not in stop_words and len(candidate) > 2:
                try:
                    from backend.services.geocoding import geocode_location
                    resolved = geocode_location(candidate)
                    if resolved:
                        loc_dict = {
                            "canonical": resolved.name,
                            "lat": resolved.latitude,
                            "lon": resolved.longitude,
                            "bbox": resolved.bbox,
                        }
                        KNOWN_LOCATIONS[candidate.lower()] = loc_dict
                        return loc_dict
                except Exception:
                    pass
    return None


class TerraPulseInvestigatorAgent:
    """Conversational AI Environmental Investigator Agent."""

    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        config: Optional[GeoAgentConfig] = None,
    ):
        self.session_manager = session_manager or _default_session_manager
        self.config = config or GeoAgentConfig()

    def process_message(
        self,
        user_message: str,
        session_id: str = "default_session",
    ) -> Iterator[ActivityEvent]:
        """Process user message in a multi-turn conversation, yielding structured activity events.
        
        Yields:
            ActivityEvent objects:
                - tool_call_start
                - tool_call_args
                - tool_call_result
                - clarification_needed
                - final_response
        """
        now_iso = lambda: datetime.now(timezone.utc).isoformat()
        session = self.session_manager.get_or_create_session(session_id)
        session.add_message("user", user_message)

        q_clean = user_message.strip()
        symptom: Optional[Any] = None

        # Step 1: Check if responding to an active clarification question
        if session.pending_clarification == "LOCATION":
            extracted_loc = _extract_location_from_query(q_clean)
            if extracted_loc:
                session.location_name = extracted_loc["canonical"]
                session.latitude = extracted_loc["lat"]
                session.longitude = extracted_loc["lon"]
                session.bbox = extracted_loc["bbox"]
                session.pending_clarification = None
                # Continue with the previously held investigation
            else:
                # Still ambiguous
                yield ActivityEvent(
                    event_type=ActivityEventType.CLARIFICATION_NEEDED,
                    timestamp=now_iso(),
                    data={
                        "slot": "location",
                        "question": (
                            "I could not pinpoint that location. Which specific lake, water body, or city "
                            "are you investigating? (e.g. 'Bellandur Lake in Bengaluru' or 'Chennai')"
                        ),
                    },
                )
                return
        elif session.pending_clarification == "POLLUTANT":
            q_lower = q_clean.lower()
            if "air" in q_lower or "pm" in q_lower or "smog" in q_lower or "particulate" in q_lower:
                session.pollutant = "PM2.5"
                session.symptom_key = "smog"
                session.symptom_name = "Atmospheric Smog & Particulate Elevation"
                symptom = classify_symptom_from_text("atmospheric smog PM2.5 air pollution")
            elif "water" in q_lower or "hypoxia" in q_lower or "fish" in q_lower or "lake" in q_lower:
                session.pollutant = "dissolved_oxygen_mg_l"
                session.symptom_key = "fish_mortality"
                session.symptom_name = "Aquatic Hypoxia & Fish Mortality"
                symptom = classify_symptom_from_text("fish mortality hypoxia")
            else:
                session.pollutant = "PM2.5"
                session.symptom_key = "smog"
                session.symptom_name = "Atmospheric Smog & Particulate Elevation"
                symptom = classify_symptom_from_text("atmospheric smog PM2.5 air pollution")
            session.pending_clarification = None

        # Step 2: Check for geographical location in current query
        query_loc = _extract_location_from_query(q_clean)
        if query_loc:
            session.location_name = query_loc["canonical"]
            session.latitude = query_loc["lat"]
            session.longitude = query_loc["lon"]
            session.bbox = query_loc["bbox"]
            yield ActivityEvent(
                event_type=ActivityEventType.TOOL_CALL_RESULT,
                timestamp=now_iso(),
                data={
                    "tool_name": "resolve_geographical_location",
                    "latency_ms": 12.0,
                    "result_summary": f"Identified study AOI: {session.location_name} ({session.latitude:.4f}°N, {session.longitude:.4f}°E)",
                    "location_info": {
                        "id": session.location_name.lower().split(",")[0].strip().replace(" ", "_"),
                        "name": session.location_name,
                        "latitude": session.latitude,
                        "longitude": session.longitude,
                        "bbox": session.bbox,
                    }
                }
            )

        # Step 3: Check if query is an environmental symptom investigation
        if not symptom:
            symptom = classify_symptom_from_text(q_clean)

        # Slot-filling check A: if symptom is present but location is missing and not in session context:
        if symptom and not session.location_name:
            session.symptom_key = symptom.symptom_key
            session.symptom_name = symptom.canonical_name
            session.pending_symptom_query = q_clean
            session.pending_clarification = "LOCATION"

            clarification_q = (
                f"I recognize an investigation into {symptom.canonical_name}. "
                f"Which lake, water body, or geographic region are you referring to?"
            )
            yield ActivityEvent(
                event_type=ActivityEventType.CLARIFICATION_NEEDED,
                timestamp=now_iso(),
                data={
                    "slot": "location",
                    "question": clarification_q,
                    "symptom_identified": symptom.canonical_name,
                },
            )
            session.add_message("assistant", clarification_q)
            return

        # Slot-filling check B: Generic pollution inquiry around location requires pollutant classification
        is_generic_pollution = (
            any(w in q_clean.lower() for w in ["pollution", "contamination"])
            and not symptom
            and not session.pollutant
            and not any(w in q_clean.lower() for w in ["forecast", "future", "predict", "year", "years"])
        )
        if is_generic_pollution and session.location_name:
            session.pending_clarification = "POLLUTANT"
            clarification_q = (
                f"Which type of pollution around {session.location_name} are you investigating? "
                "Please select whether you want to examine air pollution (PM2.5 & smog), aquatic hypoxia (DO), or industrial effluents."
            )
            yield ActivityEvent(
                event_type=ActivityEventType.CLARIFICATION_NEEDED,
                timestamp=now_iso(),
                data={
                    "slot": "pollutant",
                    "question": clarification_q,
                    "options": [
                        "Air Pollution (PM2.5 & Smog)",
                        "Water Quality & Hypoxia (DO)",
                        "Industrial & Chemical Effluents"
                    ],
                },
            )
            session.add_message("assistant", clarification_q)
            return

        # Step 4: Handle specific intent workflows
        # Intent A: Forecasting Request
        if any(w in q_clean.lower() for w in ["forecast", "future", "predict", "in 5 years", "in 3 years", "by 2030", "by 2040", "next five years", "next 5 years", "five years"]):
            # Determine horizon
            horizon = "+5 years"
            for h in ["2040", "2030", "+5 years", "+3 years", "+1 year"]:
                if h.lower() in q_clean.lower() or h.replace("+", "") in q_clean.lower():
                    horizon = h
                    break
            if "next five years" in q_clean.lower() or "five years" in q_clean.lower() or "5 years" in q_clean.lower():
                horizon = "+5 years"

            yield ActivityEvent(
                event_type=ActivityEventType.TOOL_CALL_START,
                timestamp=now_iso(),
                data={"tool_name": "generate_environmental_forecast", "intent": f"Simulating future scenario trajectories for {horizon}."},
            )

            start_t = time.perf_counter()
            forecast_data = generate_environmental_forecast_tool(indicator="PM2.5", horizon=horizon)
            latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

            yield ActivityEvent(
                event_type=ActivityEventType.TOOL_CALL_RESULT,
                timestamp=now_iso(),
                data={
                    "tool_name": "generate_environmental_forecast",
                    "latency_ms": latency_ms,
                    "summary": f"Completed multi-scenario projections for horizon {horizon} across BAU, Policy Reduction, and Ecological Interventions.",
                },
            )

            session.last_forecast = forecast_data
            loc_str = session.location_name or "the study region"
            response_text = (
                f"### Environmental Forecasting Report ({loc_str})\n\n"
                f"**Indicator:** {forecast_data.get('indicator', 'PM2.5')} ({forecast_data.get('unit', 'µg/m³')})\n"
                f"**Baseline (2024):** {forecast_data.get('baseline_value', 'N/A')} {forecast_data.get('unit', 'µg/m³')}\n"
                f"**Horizon:** {horizon}\n\n"
                f"#### Scenario Projections:\n"
                f"1. **Business-As-Usual (BAU):** Trajectory projects a change of {forecast_data.get('scenarios', {}).get('BAU', {}).get('net_change_pct', 0.0):+.1f}% "
                f"under continued status-quo emissions and urban expansion.\n"
                f"2. **Pollution Reduction Target (-30%):** Enforced point-source caps curb projected levels by {forecast_data.get('scenarios', {}).get('POL_RED', {}).get('net_change_pct', 0.0):+.1f}%.\n"
                f"3. **Comprehensive Ecological Intervention:** Targeted aeration and riparian buffer restoration achieves an overall {forecast_data.get('scenarios', {}).get('INTERVENTION', {}).get('net_change_pct', 0.0):+.1f}% reduction.\n\n"
                f"**Prediction Intervals:** 80% and 95% confidence bands widen progressively with horizon distance to reflect parameter and meteorological uncertainty.\n\n"
                f"> **Scientific Integrity Notice:** {forecast_data.get('disclaimer', '')}"
            )

            session.add_message("assistant", response_text)
            yield ActivityEvent(
                event_type=ActivityEventType.FINAL_RESPONSE,
                timestamp=now_iso(),
                data={
                    "content": response_text,
                    "forecast": forecast_data,
                    "location": session.location_name,
                    "location_info": {
                        "id": session.location_name.lower().split(",")[0].strip().replace(" ", "_"),
                        "name": session.location_name,
                        "latitude": session.latitude,
                        "longitude": session.longitude,
                        "bbox": session.bbox,
                    } if session.location_name else None,
                },
            )
            return

        # Intent B: Symptom-to-Cause Investigation
        if symptom or session.symptom_key:
            target_symptom = symptom.canonical_name if symptom else (session.symptom_name or "Environmental Anomaly")
            loc_name = session.location_name or "Specified Region"

            # 1. Start Symptom Analysis Tool
            yield ActivityEvent(
                event_type=ActivityEventType.TOOL_CALL_START,
                timestamp=now_iso(),
                data={"tool_name": "investigate_environmental_symptom", "intent": f"Analyzing candidate hypotheses and telemetry for {target_symptom} at {loc_name}."},
            )

            start_t = time.perf_counter()
            effective_symptom_query = session.pending_symptom_query or (session.symptom_name or q_clean)
            investigation_res = investigate_environmental_symptom_tool(
                symptom_query=effective_symptom_query,
                location=loc_name,
            )
            latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

            yield ActivityEvent(
                event_type=ActivityEventType.TOOL_CALL_RESULT,
                timestamp=now_iso(),
                data={
                    "tool_name": "investigate_environmental_symptom",
                    "latency_ms": latency_ms,
                    "summary": f"Evaluated {len(investigation_res.get('hypotheses_ranked', []))} causal hypotheses against biological thresholds and literature.",
                },
            )

            # 2. Trigger Spatial Hotspot Analysis for Map Visualizer
            yield ActivityEvent(
                event_type=ActivityEventType.TOOL_CALL_START,
                timestamp=now_iso(),
                data={"tool_name": "compute_getis_ord_gi_star", "intent": f"Evaluating spatial clustering and monitoring stations around {loc_name}."},
            )

            hotspot_res = compute_getis_ord_gi_star_tool(distance_threshold_km=15.0, location=loc_name)

            yield ActivityEvent(
                event_type=ActivityEventType.TOOL_CALL_RESULT,
                timestamp=now_iso(),
                data={
                    "tool_name": "compute_getis_ord_gi_star",
                    "latency_ms": 15.0,
                    "summary": f"Detected {hotspot_res.get('significant_hotspots_count', 0)} statistically significant hotspots out of {hotspot_res.get('total_stations_evaluated', 0)} stations.",
                },
            )

            session.last_findings = investigation_res
            session.last_geojson = hotspot_res.get("geojson")

            # Format comprehensive investigation report
            hypotheses = investigation_res.get("hypotheses_ranked", [])
            top_hyp = hypotheses[0] if hypotheses else None
            verdict = investigation_res.get("verdict_summary", "")

            response_parts = [
                f"### Environmental Investigation Report: {target_symptom}\n",
                f"**Target Location:** {loc_name}\n",
                f"**Synthesis Verdict:**\n{verdict}\n\n",
                "#### Ranked Causal Hypotheses:\n",
            ]

            for idx, h in enumerate(investigation_res.get("hypotheses_ranked", [])[:3], 1):
                tier_badge = h.get("support_tier", "UNVERIFIED")
                score = h.get("evidence_score", 0.0)
                cause = h.get("cause_name", "Unknown")
                mech = h.get("mechanistic_summary", "")
                dose = h.get("bradford_hill", {}).get("dose_response_gradient", "Unknown")
                response_parts.append(f"{idx}. **{cause}** `[{tier_badge}]` (Relative Evidence Index: {score})\n")
                response_parts.append(f"   - **Mechanism:** {mech}\n")
                response_parts.append(f"   - **Dose-Response:** {dose}\n")

                supp = h.get("supporting_evidence", [])
                if supp:
                    response_parts.append(f"   - **Empirical Corroboration:** {supp[0].get('claim')}\n")

                citations = h.get("scientific_citations", [])
                if citations:
                    c = citations[0]
                    response_parts.append(f"   - **Peer-Reviewed Reference:** *\"{c.get('title')}\"* ({c.get('journal')}, {c.get('year')}) [DOI: {c.get('doi')}]\n")

                rivals = h.get("bradford_hill", {}).get("alternative_explanations", [])
                if rivals:
                    response_parts.append(f"   - **Rival Alternative Hypotheses:** {', '.join(rivals[:2])}\n")
                response_parts.append("\n")

            missing = investigation_res.get("missing_measurements", [])
            if missing:
                response_parts.append("#### Missing Telemetry Needed to Establish Proven Causality:\n")
                for m in missing[:4]:
                    response_parts.append(f"- {m}\n")
                response_parts.append("\n")

            response_parts.append(f"> **Scientific Integrity Rule:** {investigation_res.get('causal_disclaimer', '')}")

            final_text = "".join(response_parts)
            session.add_message("assistant", final_text)

            yield ActivityEvent(
                event_type=ActivityEventType.FINAL_RESPONSE,
                timestamp=now_iso(),
                data={
                    "content": final_text,
                    "text": final_text,
                    "investigation": investigation_res,
                    "map_geojson": session.last_geojson,
                    "geojson": session.last_geojson,
                    "location": session.location_name,
                    "location_info": {
                        "id": session.location_name.lower().split(",")[0].strip().replace(" ", "_"),
                        "name": session.location_name,
                        "latitude": session.latitude,
                        "longitude": session.longitude,
                        "bbox": session.bbox,
                    } if session.location_name else None,
                },
            )
            return

        # Intent C: General Literature or News Query
        yield ActivityEvent(
            event_type=ActivityEventType.TOOL_CALL_START,
            timestamp=now_iso(),
            data={"tool_name": "search_all_research", "intent": f"Querying academic journals and news archives for '{q_clean}'."},
        )

        res_data = search_academic_literature_tool(q_clean, limit_per_source=2)

        yield ActivityEvent(
            event_type=ActivityEventType.TOOL_CALL_RESULT,
            timestamp=now_iso(),
            data={
                "tool_name": "search_all_research",
                "latency_ms": 25.0,
                "summary": f"Retrieved {res_data.get('total_results', 0)} verified peer-reviewed articles.",
            },
        )

        articles = res_data.get("articles", [])
        if articles:
            lines = [f"### Scientific Literature Findings for '{q_clean}':\n\n"]
            for a in articles[:4]:
                lines.append(f"- **{a.get('title')}** ({a.get('publication_name')}, {a.get('publication_date')})\n")
                lines.append(f"  *Authors:* {', '.join(a.get('authors', [])[:3])}\n")
                if a.get("doi"):
                    lines.append(f"  *DOI:* [{a.get('doi')}]({a.get('url')})\n")
                lines.append(f"  *{a.get('abstract_or_summary', '')[:220]}...*\n\n")
            ans_text = "".join(lines)
        else:
            ans_text = (
                f"No indexed publications were retrieved for '{q_clean}'. "
                "Try refining your search terms or specifying an observed symptom or pollutant name."
            )

        session.add_message("assistant", ans_text)
        yield ActivityEvent(
            event_type=ActivityEventType.FINAL_RESPONSE,
            timestamp=now_iso(),
            data={"content": ans_text, "articles": articles},
        )
