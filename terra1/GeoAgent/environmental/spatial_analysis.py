"""Environmental Spatial Analysis Engine.

Provides:
- Monitoring station data models with provenance, units, and timestamps.
- Inverse Distance Weighting (IDW) interpolation with configurable power and search radius.
- Spatial anomaly detection & Getis-Ord Gi* hotspot analysis.
- Statistical summarization (mean, median, range, std dev, station density, data coverage).
- Temporal trend computation (OLS rate of change, direction, and fit).
- Standard RFC 7946 GeoJSON generation strictly separating:
    * MEASURED_POINT
    * INTERPOLATED_MODEL
    * HOTSPOT
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Literal
import numpy as np


DataTypeTag = Literal["MEASURED_POINT", "INTERPOLATED_MODEL", "HOTSPOT"]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in kilometers between two points on Earth."""
    r = 6371.0  # Earth's mean radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


@dataclass
class MonitoringStation:
    """Direct ground measurement station observation."""
    id: str
    name: str
    latitude: float
    longitude: float
    pollutant: str
    measured_value: float
    unit: str
    timestamp: str
    sensor_type: str = "Continuous Monitoring Sensor"
    source_agency: str = "Environmental Protection Agency"
    quality_flag: str = "VALID"
    extra_attributes: Dict[str, Any] = field(default_factory=dict)

    def to_geojson_feature(self) -> Dict[str, Any]:
        """Convert measured station observation to a GeoJSON Feature."""
        return {
            "type": "Feature",
            "id": self.id,
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude],
            },
            "properties": {
                "data_type": "MEASURED_POINT",
                "station_id": self.id,
                "station_name": self.name,
                "pollutant": self.pollutant,
                "measured_value": round(self.measured_value, 2),
                "unit": self.unit,
                "timestamp": self.timestamp,
                "sensor_type": self.sensor_type,
                "source_agency": self.source_agency,
                "quality_flag": self.quality_flag,
                "is_interpolated": False,
                **self.extra_attributes,
            },
        }


@dataclass
class SpatialBoundingBox:
    """Geographic bounding box [min_lon, min_lat, max_lon, max_lat]."""
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def contains(self, lat: float, lon: float) -> bool:
        return (
            self.min_lat <= lat <= self.max_lat
            and self.min_lon <= lon <= self.max_lon
        )

    def area_sq_km(self) -> float:
        """Approximate bounding box surface area in km²."""
        width_km = haversine_distance_km(
            (self.min_lat + self.max_lat) / 2.0, self.min_lon,
            (self.min_lat + self.max_lat) / 2.0, self.max_lon
        )
        height_km = haversine_distance_km(
            self.min_lat, (self.min_lon + self.max_lon) / 2.0,
            self.max_lat, (self.min_lon + self.max_lon) / 2.0
        )
        return max(0.001, width_km * height_km)


@dataclass
class IDWConfig:
    """Configuration for Inverse Distance Weighting interpolation."""
    power: float = 2.0
    search_radius_km: Optional[float] = 25.0
    min_neighbors: int = 1
    max_neighbors: int = 15
    grid_resolution_x: int = 20
    grid_resolution_y: int = 20


@dataclass
class InterpolatedGridCell:
    """A single spatial cell of the interpolated model."""
    lat: float
    lon: float
    estimated_value: float
    uncertainty_score: float  # Normalized 0.0 (near station) to 1.0 (far/isolated)
    nearest_station_km: float
    contributing_neighbors: int
    cell_bounds: List[List[float]]  # Polygon coords [[lon, lat], ...]


@dataclass
class SpatialHotspot:
    """Identified spatial hotspot or cluster with statistical confidence."""
    hotspot_id: str
    latitude: float
    longitude: float
    pollutant: str
    mean_value: float
    gi_z_score: float
    p_value: float
    confidence_tier: str  # "99%", "95%", "90%", or "Not Significant"
    severity: str        # "CRITICAL_HOTSPOT", "HIGH_HOTSPOT", "MODERATE", "COLDSPOT", "NORMAL"
    contributing_stations: List[str]

    def to_geojson_feature(self) -> Dict[str, Any]:
        return {
            "type": "Feature",
            "id": self.hotspot_id,
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude],
            },
            "properties": {
                "data_type": "HOTSPOT",
                "hotspot_id": self.hotspot_id,
                "pollutant": self.pollutant,
                "mean_value": round(self.mean_value, 2),
                "gi_z_score": round(self.gi_z_score, 3),
                "p_value": round(self.p_value, 4),
                "confidence_tier": self.confidence_tier,
                "severity": self.severity,
                "contributing_stations": self.contributing_stations,
                "is_interpolated": False,
            },
        }


def compute_idw_surface(
    stations: List[MonitoringStation],
    bbox: SpatialBoundingBox,
    config: Optional[IDWConfig] = None,
) -> Tuple[List[InterpolatedGridCell], Dict[str, Any]]:
    """Compute an Inverse Distance Weighting (IDW) 2D interpolated surface.
    
    Returns:
        Tuple of (grid cells, metadata summary).
    """
    if not stations:
        return [], {"error": "No monitoring stations provided for interpolation."}

    cfg = config or IDWConfig()
    power = max(0.5, float(cfg.power))
    search_r = cfg.search_radius_km

    lats = np.linspace(bbox.min_lat, bbox.max_lat, cfg.grid_resolution_y)
    lons = np.linspace(bbox.min_lat, bbox.max_lon, cfg.grid_resolution_x)

    # Cell half-step for polygon bounding boxes
    d_lat = (bbox.max_lat - bbox.min_lat) / (cfg.grid_resolution_y * 2)
    d_lon = (bbox.max_lon - bbox.min_lon) / (cfg.grid_resolution_x * 2)

    cells: List[InterpolatedGridCell] = []
    covered_cells = 0
    total_cells = len(lats) * len(lons)

    # Pre-extract station coordinate arrays and values
    st_lats = np.array([s.latitude for s in stations])
    st_lons = np.array([s.longitude for s in stations])
    st_vals = np.array([s.measured_value for s in stations])

    max_uncertainty_dist = search_r if search_r else 50.0

    for lat in lats:
        for lon in lons:
            # Calculate distance to all stations
            distances = np.array([
                haversine_distance_km(lat, lon, st_lat, st_lon)
                for st_lat, st_lon in zip(st_lats, st_lons)
            ])

            # Check if point coincides with a station (d < 50 meters)
            coincident_idx = np.where(distances < 0.05)[0]
            if len(coincident_idx) > 0:
                idx = coincident_idx[0]
                val = float(st_vals[idx])
                uncertainty = 0.0
                min_dist = float(distances[idx])
                contributing = 1
                covered_cells += 1
            else:
                # Filter by search radius if configured
                if search_r is not None:
                    valid_mask = distances <= search_r
                else:
                    valid_mask = np.ones_like(distances, dtype=bool)

                valid_distances = distances[valid_mask]
                valid_values = st_vals[valid_mask]

                if len(valid_distances) < cfg.min_neighbors:
                    # Beyond coverage radius: fallback to nearest station with maximum uncertainty
                    nearest_idx = np.argmin(distances)
                    val = float(st_vals[nearest_idx])
                    min_dist = float(distances[nearest_idx])
                    uncertainty = 1.0
                    contributing = 0
                else:
                    # Take up to max_neighbors nearest stations
                    if len(valid_distances) > cfg.max_neighbors:
                        sort_idx = np.argsort(valid_distances)[: cfg.max_neighbors]
                        valid_distances = valid_distances[sort_idx]
                        valid_values = valid_values[sort_idx]

                    weights = 1.0 / (valid_distances ** power)
                    weight_sum = np.sum(weights)
                    val = float(np.sum(weights * valid_values) / weight_sum)
                    min_dist = float(np.min(valid_distances))
                    # Uncertainty scales with distance from nearest ground observation
                    uncertainty = min(1.0, min_dist / max_uncertainty_dist)
                    contributing = len(valid_distances)
                    covered_cells += 1

            # Build cell boundary polygon [lon, lat]
            bounds = [
                [lon - d_lon, lat - d_lat],
                [lon + d_lon, lat - d_lat],
                [lon + d_lon, lat + d_lat],
                [lon - d_lon, lat + d_lat],
                [lon - d_lon, lat - d_lat],
            ]

            cells.append(
                InterpolatedGridCell(
                    lat=float(lat),
                    lon=float(lon),
                    estimated_value=float(val),
                    uncertainty_score=round(float(uncertainty), 3),
                    nearest_station_km=round(float(min_dist), 2),
                    contributing_neighbors=contributing,
                    cell_bounds=bounds,
                )
            )

    coverage_pct = round((covered_cells / total_cells) * 100.0, 1)

    coverage_note = "Adequate spatial coverage." if coverage_pct >= 60.0 else (
        f"Low spatial coverage ({coverage_pct}%). Portions of the study area exceed the "
        f"{search_r} km search radius of monitoring stations and carry high interpolation uncertainty."
    )

    metadata = {
        "methodology": f"Inverse Distance Weighting (IDW p={power})",
        "power": power,
        "search_radius_km": search_r,
        "grid_size": f"{cfg.grid_resolution_x}x{cfg.grid_resolution_y}",
        "total_cells": total_cells,
        "data_coverage_pct": coverage_pct,
        "coverage_note": coverage_note,
        "data_type": "INTERPOLATED_MODEL",
        "provenance": "Interpolated mathematical model derived from discrete ground measurements. Not measured truth.",
    }

    return cells, metadata


def compute_getis_ord_gi_star(
    stations: List[MonitoringStation],
    distance_threshold_km: float = 15.0,
) -> List[SpatialHotspot]:
    """Compute Getis-Ord Gi* spatial statistics to identify statistically significant hotspots.
    
    Formula:
        Gi* = (sum(w_ij * x_j) - X_bar * sum(w_ij)) / (S * sqrt((n*sum(w_ij^2) - (sum(w_ij))^2) / (n - 1)))
    """
    n = len(stations)
    if n < 3:
        # Statistical clustering requires at least 3 spatial points
        return []

    values = np.array([s.measured_value for s in stations], dtype=float)
    x_bar = np.mean(values)
    s = np.std(values, ddof=0)

    if s == 0.0:
        # No spatial variance
        return []

    # Calculate spatial weight matrix W based on distance band with continuous decay fallback
    distances_matrix = np.zeros((n, n), dtype=float)
    weights = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            dist = haversine_distance_km(
                stations[i].latitude, stations[i].longitude,
                stations[j].latitude, stations[j].longitude
            )
            distances_matrix[i, j] = dist
            if dist <= distance_threshold_km:
                weights[i, j] = 1.0  # Binary spatial adjacency band including self (Gi*)

    # If any station has all weights == 1 (all stations within threshold), use continuous distance decay
    # to preserve spatial variance and ensure mathematically non-zero denominator
    for i in range(n):
        w_i = weights[i, :]
        sum_w = np.sum(w_i)
        sum_w2 = np.sum(w_i ** 2)
        if (n * sum_w2 - (sum_w ** 2)) <= 1e-6:
            # Fall back to continuous inverse-distance weighting for this row
            weights[i, :] = 1.0 / (1.0 + (distances_matrix[i, :] / max(1.0, distance_threshold_km * 0.5)))

    hotspots: List[SpatialHotspot] = []

    for i in range(n):
        w_i = weights[i, :]
        sum_w = np.sum(w_i)
        sum_w2 = np.sum(w_i ** 2)

        numerator = np.sum(w_i * values) - (x_bar * sum_w)
        denominator_term = (n * sum_w2 - (sum_w ** 2)) / (n - 1)
        if denominator_term <= 0.0:
            continue
        denominator = s * math.sqrt(denominator_term)

        if denominator == 0.0:
            continue

        z_score = float(numerator / denominator)

        # Standard normal p-value approximation
        p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z_score) / math.sqrt(2.0))))

        # Classify confidence and severity
        if z_score >= 2.58:
            conf = "99% Confidence"
            sev = "CRITICAL_HOTSPOT"
        elif z_score >= 1.96:
            conf = "95% Confidence"
            sev = "HIGH_HOTSPOT"
        elif z_score >= 1.65:
            conf = "90% Confidence"
            sev = "MODERATE_HOTSPOT"
        elif z_score <= -1.96:
            conf = "95% Confidence"
            sev = "COLDSPOT"
        else:
            conf = "Not Significant"
            sev = "NORMAL"

        contributing = [
            stations[j].id
            for j in range(n)
            if weights[i, j] > 0
        ]

        hotspots.append(
            SpatialHotspot(
                hotspot_id=f"HS-{stations[i].id}",
                latitude=stations[i].latitude,
                longitude=stations[i].longitude,
                pollutant=stations[i].pollutant,
                mean_value=float(values[i]),
                gi_z_score=z_score,
                p_value=p_val,
                confidence_tier=conf,
                severity=sev,
                contributing_stations=contributing,
            )
        )

    # Sort descending by Gi* z-score
    hotspots.sort(key=lambda h: h.gi_z_score, reverse=True)
    return hotspots


def detect_spatial_anomalies(
    stations: List[MonitoringStation],
    z_threshold: float = 2.0,
) -> List[Dict[str, Any]]:
    """Detect local monitoring stations with statistically anomalous values relative to regional baseline."""
    if len(stations) < 3:
        return []

    vals = np.array([s.measured_value for s in stations])
    mean = np.mean(vals)
    std = np.std(vals)

    if std == 0.0:
        return []

    anomalies: List[Dict[str, Any]] = []
    for s in stations:
        z = (s.measured_value - mean) / std
        if abs(z) >= z_threshold:
            anomalies.append({
                "station_id": s.id,
                "station_name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "pollutant": s.pollutant,
                "measured_value": s.measured_value,
                "unit": s.unit,
                "regional_mean": round(float(mean), 2),
                "z_score": round(float(z), 2),
                "anomaly_type": "HIGH_SPIKE" if z > 0 else "LOW_OUTLIER",
                "timestamp": s.timestamp,
            })
    return anomalies


def compute_temporal_trend(
    measurements: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Compute temporal rate of change for a set of time-series observations.
    
    Each item in measurements should have:
        - "timestamp": ISO string or epoch
        - "value": float
    """
    if len(measurements) < 3:
        return None

    # Parse timestamps to relative days from earliest observation
    parsed_points: List[Tuple[float, float]] = []
    for m in measurements:
        ts_raw = m.get("timestamp")
        val = m.get("value")
        if ts_raw is None or val is None:
            continue
        try:
            if isinstance(ts_raw, (int, float)):
                dt = datetime.fromtimestamp(ts_raw)
            else:
                # ISO parsing fallback
                dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
            epoch_days = dt.timestamp() / 86400.0
            parsed_points.append((epoch_days, float(val)))
        except Exception:
            continue

    if len(parsed_points) < 3:
        return None

    parsed_points.sort(key=lambda p: p[0])
    t0 = parsed_points[0][0]
    x_days = np.array([p[0] - t0 for p in parsed_points])
    y_vals = np.array([p[1] for p in parsed_points])

    span_days = float(x_days[-1])
    if span_days < 1.0:
        return {
            "slope_per_day": 0.0,
            "slope_per_year": 0.0,
            "direction": "INSUFFICIENT_TIME_SPAN",
            "observation_days": round(span_days, 1),
            "r_squared": 0.0,
        }

    # Linear OLS regression
    n = len(x_days)
    mean_x = np.mean(x_days)
    mean_y = np.mean(y_vals)

    ss_xx = np.sum((x_days - mean_x) ** 2)
    ss_yy = np.sum((y_vals - mean_y) ** 2)
    ss_xy = np.sum((x_days - mean_x) * (y_vals - mean_y))

    if ss_xx == 0.0:
        return None

    slope_day = float(ss_xy / ss_xx)
    slope_year = float(slope_day * 365.25)
    r2 = float((ss_xy ** 2) / (ss_xx * ss_yy)) if ss_yy > 0.0 else 0.0

    if slope_year > 0.05 * mean_y:
        direction = "INCREASING"
    elif slope_year < -0.05 * mean_y:
        direction = "DECREASING"
    else:
        direction = "STABLE"

    return {
        "slope_per_day": round(slope_day, 4),
        "slope_per_year": round(slope_year, 2),
        "direction": direction,
        "observation_days": round(span_days, 1),
        "r_squared": round(r2, 3),
        "sample_count": n,
    }


def compute_regional_statistics(
    stations: List[MonitoringStation],
    bbox: SpatialBoundingBox,
    temporal_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compute rigorous statistical summaries and coverage indicators for a study region."""
    if not stations:
        return {
            "station_count": 0,
            "error": "No monitoring stations available in the specified bounding box.",
        }

    vals = np.array([s.measured_value for s in stations], dtype=float)
    pollutant = stations[0].pollutant
    unit = stations[0].unit

    area_km2 = bbox.area_sq_km()
    station_density = round((len(stations) / area_km2) * 1000.0, 2)  # Stations per 1,000 km²

    mean_val = float(np.mean(vals))
    median_val = float(np.median(vals))
    min_val = float(np.min(vals))
    max_val = float(np.max(vals))
    val_range = max_val - min_val
    std_dev = float(np.std(vals))
    variance = float(np.var(vals))

    # Calculate 95% confidence interval for the mean: mean +/- 1.96 * (std / sqrt(n))
    se = std_dev / math.sqrt(len(stations)) if len(stations) > 1 else 0.0
    ci_95 = (round(mean_val - 1.96 * se, 2), round(mean_val + 1.96 * se, 2))

    trend_report = compute_temporal_trend(temporal_history) if temporal_history else None

    # Missing data / coverage breakdown
    missing_count = sum(1 for s in stations if s.quality_flag != "VALID")
    coverage_report = {
        "total_stations": len(stations),
        "valid_stations": len(stations) - missing_count,
        "suspect_or_uncalibrated": missing_count,
        "study_area_sq_km": round(area_km2, 1),
        "station_density_per_1000km2": station_density,
    }

    return {
        "pollutant": pollutant,
        "unit": unit,
        "station_count": len(stations),
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "range": round(val_range, 2),
        "std_dev": round(std_dev, 2),
        "spatial_variance": round(variance, 2),
        "confidence_interval_95": ci_95,
        "coverage": coverage_report,
        "temporal_trend": trend_report,
        "data_provenance": "Aggregated from verified regional ground monitoring telemetry.",
    }


def generate_investigation_geojson(
    stations: List[MonitoringStation],
    interpolated_cells: Optional[List[InterpolatedGridCell]] = None,
    hotspots: Optional[List[SpatialHotspot]] = None,
) -> Dict[str, Any]:
    """Generate RFC 7946 GeoJSON FeatureCollection compatible with Earth Observation Explorer and globe.
    
    Strictly categorizes every feature with `data_type`:
        - MEASURED_POINT
        - INTERPOLATED_MODEL
        - HOTSPOT
    """
    features: List[Dict[str, Any]] = []

    # 1. Measured Ground Points (Highest epistemic weight)
    for st in stations:
        features.append(st.to_geojson_feature())

    # 2. Interpolated Surface Polygons (Modeled estimates)
    if interpolated_cells:
        for idx, cell in enumerate(interpolated_cells):
            features.append({
                "type": "Feature",
                "id": f"INTERP-{idx}",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [cell.cell_bounds],
                },
                "properties": {
                    "data_type": "INTERPOLATED_MODEL",
                    "estimated_value": round(cell.estimated_value, 2),
                    "uncertainty_score": cell.uncertainty_score,
                    "nearest_station_km": cell.nearest_station_km,
                    "contributing_neighbors": cell.contributing_neighbors,
                    "is_interpolated": True,
                    "disclaimer": "Interpolated model estimation. Not a ground measurement.",
                },
            })

    # 3. Hotspot Clusters (Statistical z-score clusters)
    if hotspots:
        for hs in hotspots:
            if hs.severity in ["CRITICAL_HOTSPOT", "HIGH_HOTSPOT", "MODERATE_HOTSPOT"]:
                features.append(hs.to_geojson_feature())

    significant_hotspots_count = sum(
        1 for hs in (hotspots or [])
        if hs.severity in ["CRITICAL_HOTSPOT", "HIGH_HOTSPOT", "MODERATE_HOTSPOT"]
    )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_features": len(features),
            "measured_points": len(stations),
            "interpolated_cells": len(interpolated_cells or []),
            "stations_evaluated_for_clustering": len(hotspots or []),
            "significant_hotspots_detected": significant_hotspots_count,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def get_preset_bengaluru_monitoring_stations() -> List[MonitoringStation]:
    """Illustrative sample monitoring dataset for the Bengaluru urban/wetland catchment.
    
    Coordinates correspond to real monitoring sites (Bellandur, Varthur, Peenya, etc.),
    with illustrative sample telemetry values for testing, validation, and demo investigations.
    Not live calibrated agency telemetry.
    """
    now_ts = "2024-05-15T10:00:00Z"
    prov_note = "Sample illustrative dataset based on CPCB/KSPCB station coordinates. Not live telemetry."
    return [
        MonitoringStation(
            id="BLR-BEL-01",
            name="Bellandur Lake North Catchment (Inlet)",
            latitude=12.9385,
            longitude=77.6680,
            pollutant="PM2.5",
            measured_value=78.4,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="Optical Particle Counter (Sample)",
            source_agency="Sample Dataset (CPCB/KSPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={
                "dissolved_oxygen_mg_l": 1.2,
                "surfactants_mg_l": 4.8,
                "data_provenance": prov_note,
            },
        ),
        MonitoringStation(
            id="BLR-VAR-02",
            name="Varthur Lake Wetland Outlet",
            latitude=12.9421,
            longitude=77.7410,
            pollutant="PM2.5",
            measured_value=84.2,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="Optical Particle Counter (Sample)",
            source_agency="Sample Dataset (KSPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={
                "dissolved_oxygen_mg_l": 0.8,
                "surfactants_mg_l": 6.2,
                "data_provenance": prov_note,
            },
        ),
        MonitoringStation(
            id="BLR-PEE-03",
            name="Peenya Industrial Cluster Sector 2",
            latitude=13.0315,
            longitude=77.5185,
            pollutant="PM2.5",
            measured_value=122.6,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="Beta Attenuation Monitor (Sample)",
            source_agency="Sample Dataset (CPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={
                "so2_ug_m3": 44.5,
                "no2_ug_m3": 68.2,
                "data_provenance": prov_note,
            },
        ),
        MonitoringStation(
            id="BLR-WHI-04",
            name="Whitefield Export Promotion Zone",
            latitude=12.9812,
            longitude=77.7289,
            pollutant="PM2.5",
            measured_value=62.5,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS Micro-Sensor (Sample)",
            source_agency="Sample Dataset (KSPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="BLR-HEB-05",
            name="Hebbal Lake Buffer Zone",
            latitude=13.0450,
            longitude=77.5920,
            pollutant="PM2.5",
            measured_value=48.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (CPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="BLR-SLK-06",
            name="Silk Board Junction Traffic Hub",
            latitude=12.9175,
            longitude=77.6238,
            pollutant="PM2.5",
            measured_value=114.8,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="Beta Attenuation Monitor (Sample)",
            source_agency="Sample Dataset (KSPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={
                "no2_ug_m3": 72.1,
                "data_provenance": prov_note,
            },
        ),
        MonitoringStation(
            id="BLR-JAY-07",
            name="Jayanagar Residential Reserve",
            latitude=12.9250,
            longitude=77.5838,
            pollutant="PM2.5",
            measured_value=38.5,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (CPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="BLR-ELE-08",
            name="Electronic City Industrial Corridor",
            latitude=12.8450,
            longitude=77.6630,
            pollutant="PM2.5",
            measured_value=58.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (KSPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
    ]


def get_preset_chennai_monitoring_stations() -> List[MonitoringStation]:
    """Illustrative sample monitoring dataset for the Chennai metropolitan / coastal basin."""
    now_ts = "2024-05-15T10:00:00Z"
    prov_note = "Sample illustrative dataset based on TNPCB/CPCB station coordinates. Not live telemetry."
    return [
        MonitoringStation(
            id="CHN-ALA-01",
            name="Alandur Urban Air Quality Station",
            latitude=13.0033,
            longitude=80.2012,
            pollutant="PM2.5",
            measured_value=64.2,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (TNPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="CHN-VEL-02",
            name="Velachery Lake Wetland Monitoring Site",
            latitude=12.9815,
            longitude=80.2180,
            pollutant="DO",
            measured_value=3.4,
            unit="mg/L",
            timestamp=now_ts,
            sensor_type="Electrochemical Probe (Sample)",
            source_agency="Sample Dataset (TNPCB Wetland Unit)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="CHN-MAN-03",
            name="Manali Petrochemical Industrial Cluster",
            latitude=13.1667,
            longitude=80.2600,
            pollutant="PM2.5",
            measured_value=84.5,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (TNPCB Industrial Zone)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="CHN-KOD-04",
            name="Kodungaiyur Solid Waste Buffer Zone",
            latitude=13.1410,
            longitude=80.2450,
            pollutant="PM2.5",
            measured_value=72.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (TNPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="CHN-ADY-05",
            name="Adyar River Estuary Monitoring Site",
            latitude=13.0067,
            longitude=80.2572,
            pollutant="DO",
            measured_value=4.1,
            unit="mg/L",
            timestamp=now_ts,
            sensor_type="Sonde Multi-sensor (Sample)",
            source_agency="Sample Dataset (TNPCB River Basin Network)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="CHN-COO-06",
            name="Cooum River Urban Basin Site",
            latitude=13.0732,
            longitude=80.2610,
            pollutant="DO",
            measured_value=1.8,
            unit="mg/L",
            timestamp=now_ts,
            sensor_type="Optical DO Sensor (Sample)",
            source_agency="Sample Dataset (TNPCB Surface Water Unit)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="CHN-ROY-07",
            name="Royapuram Port & Logistics Corridor",
            latitude=13.1120,
            longitude=80.2950,
            pollutant="PM2.5",
            measured_value=59.5,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="Beta Attenuation Monitor (Sample)",
            source_agency="Sample Dataset (TNPCB Port Division)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="CHN-TNR-08",
            name="T. Nagar Commercial & Transit Hub",
            latitude=13.0418,
            longitude=80.2341,
            pollutant="PM2.5",
            measured_value=68.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (TNPCB Urban Monitoring)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
    ]


def get_preset_mumbai_monitoring_stations() -> List[MonitoringStation]:
    """Illustrative sample monitoring dataset for the Mumbai metropolitan / coastal island corridor."""
    now_ts = "2024-05-15T10:00:00Z"
    prov_note = "Sample illustrative dataset based on MPCB/CPCB station coordinates. Not live telemetry."
    return [
        MonitoringStation(
            id="MUM-BAN-01",
            name="Bandra Urban Air Quality Station",
            latitude=19.0596,
            longitude=72.8295,
            pollutant="PM2.5",
            measured_value=74.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (MPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="MUM-KUR-02",
            name="Kurla Commercial & Traffic Corridor",
            latitude=19.0726,
            longitude=72.8845,
            pollutant="PM2.5",
            measured_value=82.5,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (MPCB Urban Unit)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="MUM-MAH-03",
            name="Mithi River Basin Wetland Station",
            latitude=19.0430,
            longitude=72.8610,
            pollutant="DO",
            measured_value=1.5,
            unit="mg/L",
            timestamp=now_ts,
            sensor_type="Electrochemical Probe (Sample)",
            source_agency="Sample Dataset (MPCB River Monitoring)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="MUM-CHM-04",
            name="Chembur Industrial Refining Cluster",
            latitude=19.0522,
            longitude=72.8990,
            pollutant="PM2.5",
            measured_value=89.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="Beta Attenuation Monitor (Sample)",
            source_agency="Sample Dataset (MPCB Industrial Zone)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="MUM-COL-05",
            name="Colaba Coastal Baseline Observatory",
            latitude=18.9067,
            longitude=72.8147,
            pollutant="PM2.5",
            measured_value=48.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (MPCB Coastal Unit)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
    ]


def get_preset_delhi_monitoring_stations() -> List[MonitoringStation]:
    """Illustrative sample monitoring dataset for the Delhi National Capital Region."""
    now_ts = "2024-05-15T10:00:00Z"
    prov_note = "Sample illustrative dataset based on DPCC/CPCB station coordinates. Not live telemetry."
    return [
        MonitoringStation(
            id="DEL-ANA-01",
            name="Anand Vihar Transport & Interstate Hub",
            latitude=28.6476,
            longitude=77.3160,
            pollutant="PM2.5",
            measured_value=142.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (DPCC Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="DEL-ITO-02",
            name="ITO Central Administrative Junction",
            latitude=28.6315,
            longitude=77.2492,
            pollutant="PM2.5",
            measured_value=118.5,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="CAAQMS (Sample)",
            source_agency="Sample Dataset (CPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="DEL-YAM-03",
            name="Yamuna River Okhla Barrage Station",
            latitude=28.5447,
            longitude=77.3114,
            pollutant="DO",
            measured_value=0.8,
            unit="mg/L",
            timestamp=now_ts,
            sensor_type="Optical DO Sensor (Sample)",
            source_agency="Sample Dataset (DPCC River Basin Unit)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
        MonitoringStation(
            id="DEL-RKM-04",
            name="R.K. Puram Residential Monitoring Station",
            latitude=28.5630,
            longitude=77.1860,
            pollutant="PM2.5",
            measured_value=98.0,
            unit="µg/m³",
            timestamp=now_ts,
            sensor_type="Beta Attenuation Monitor (Sample)",
            source_agency="Sample Dataset (CPCB Site Ref)",
            quality_flag="SAMPLE_ILLUSTRATIVE",
            extra_attributes={"data_provenance": prov_note},
        ),
    ]


def get_monitoring_stations_for_location(location: Optional[str] = None) -> List[MonitoringStation]:
    """Resolves monitoring stations for the requested region without cross-city substitution.
    Returns empty list when no location is selected or stations are unavailable.
    """
    if not location or location.lower() in ("null", "none", "", "undefined"):
        return []
    loc_clean = location.lower()
    if "chennai" in loc_clean:
        return get_preset_chennai_monitoring_stations()
    if "mumbai" in loc_clean or "bombay" in loc_clean:
        return get_preset_mumbai_monitoring_stations()
    if "delhi" in loc_clean:
        return get_preset_delhi_monitoring_stations()
    if "bengaluru" in loc_clean or "bangalore" in loc_clean or "bellandur" in loc_clean or "varthur" in loc_clean:
        return get_preset_bengaluru_monitoring_stations()
    return []


