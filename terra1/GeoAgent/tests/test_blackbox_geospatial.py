"""Independent Black-Box Verification Suite: Geospatial Analysis & Interpolation.

Verifies mathematical accuracy of Haversine distance, UTM projections,
IDW 2D surface interpolation, and checks monitoring station coverage bounds.
"""

import math
import numpy as np
import pytest
from environmental.spatial_analysis import (
    haversine_distance_km,
    compute_idw_surface,
    SpatialBoundingBox,
    IDWConfig,
    MonitoringStation,
    get_monitoring_stations_for_location,
)
from backend.services.geocoding import calculate_utm_epsg


class TestGeospatialBlackBox:

    def test_haversine_distance_ground_truth(self):
        """J. Output correctness against known geographic distances."""
        # Known geodetic distance between San Francisco (37.7749, -122.4194) and Los Angeles (34.0522, -118.2437) ~ 559 km
        calc_dist = haversine_distance_km(37.7749, -122.4194, 34.0522, -118.2437)
        expected = 559.0
        error = abs(calc_dist - expected) / expected * 100.0
        assert error < 1.0, f"Haversine calculation error: {error:.2f}% ({calc_dist} vs {expected} km)"

    def test_utm_projection_calculation(self):
        """J. Geodetic UTM calculation across hemispheres."""
        # Western hemisphere: NYC (-74.00) -> UTM Zone 18N (EPSG:32618)
        assert calculate_utm_epsg(40.71, -74.00) == "EPSG:32618"
        # Eastern hemisphere: Tokyo (139.69) -> UTM Zone 54N (EPSG:32654)
        assert calculate_utm_epsg(35.68, 139.69) == "EPSG:32654"

    def test_idw_interpolation_surface_properties(self):
        """A. IDW interpolation mathematical bounds."""
        stations = [
            MonitoringStation(id="s1", name="S1", latitude=12.90, longitude=77.50, pollutant="PM2.5", measured_value=50.0, unit="ug/m3", timestamp="2024-01-01"),
            MonitoringStation(id="s2", name="S2", latitude=13.00, longitude=77.60, pollutant="PM2.5", measured_value=150.0, unit="ug/m3", timestamp="2024-01-01"),
            MonitoringStation(id="s3", name="S3", latitude=12.95, longitude=77.55, pollutant="PM2.5", measured_value=100.0, unit="ug/m3", timestamp="2024-01-01"),
        ]
        bbox = SpatialBoundingBox(min_lon=77.45, min_lat=12.85, max_lon=77.65, max_lat=13.05)
        cells, meta = compute_idw_surface(stations, bbox, IDWConfig(grid_resolution_x=10, grid_resolution_y=10))

        assert len(cells) == 100
        assert "data_coverage_pct" in meta
        # Max in cells cannot exceed max observed (150.0)
        max_val = max(c.estimated_value for c in cells)
        min_val = min(c.estimated_value for c in cells)
        assert max_val <= 150.0 + 1e-4
        # Min in cells cannot fall below min observed (50.0)
        assert min_val >= 50.0 - 1e-4

    def test_monitoring_stations_city_coverage_limitation(self):
        """I. Authenticity Check: Expose that only 4 Indian cities have sample stations."""
        # 4 supported preset cities
        assert len(get_monitoring_stations_for_location("bengaluru")) > 0
        assert len(get_monitoring_stations_for_location("chennai")) > 0
        assert len(get_monitoring_stations_for_location("mumbai")) > 0
        assert len(get_monitoring_stations_for_location("delhi")) > 0

        # All other world locations return empty list []
        assert get_monitoring_stations_for_location("tokyo") == []
        assert get_monitoring_stations_for_location("london") == []
        assert get_monitoring_stations_for_location("new york") == []
