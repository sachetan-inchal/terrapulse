"""Unit and mathematical verification tests for Environmental Spatial Analysis Engine (Phase 2)."""

from __future__ import annotations

import unittest
import numpy as np

from environmental.spatial_analysis import (
    MonitoringStation,
    SpatialBoundingBox,
    IDWConfig,
    haversine_distance_km,
    compute_idw_surface,
    compute_getis_ord_gi_star,
    detect_spatial_anomalies,
    compute_temporal_trend,
    compute_regional_statistics,
    generate_investigation_geojson,
    get_preset_bengaluru_monitoring_stations,
)


class TestSpatialAnalysis(unittest.TestCase):

    def setUp(self):
        self.stations = [
            MonitoringStation(
                id="ST-01",
                name="Central Station",
                latitude=12.95,
                longitude=77.60,
                pollutant="PM2.5",
                measured_value=50.0,
                unit="µg/m³",
                timestamp="2024-05-01T12:00:00Z",
            ),
            MonitoringStation(
                id="ST-02",
                name="North Station",
                latitude=13.05,
                longitude=77.60,
                pollutant="PM2.5",
                measured_value=120.0,
                unit="µg/m³",
                timestamp="2024-05-01T12:00:00Z",
            ),
            MonitoringStation(
                id="ST-03",
                name="East Station",
                latitude=12.95,
                longitude=77.70,
                pollutant="PM2.5",
                measured_value=80.0,
                unit="µg/m³",
                timestamp="2024-05-01T12:00:00Z",
            ),
            MonitoringStation(
                id="ST-04",
                name="South Station",
                latitude=12.85,
                longitude=77.60,
                pollutant="PM2.5",
                measured_value=30.0,
                unit="µg/m³",
                timestamp="2024-05-01T12:00:00Z",
            ),
        ]
        self.bbox = SpatialBoundingBox(
            min_lon=77.50, min_lat=12.80, max_lon=77.75, max_lat=13.10
        )

    def test_haversine_distance(self):
        # Distance to self is 0
        d0 = haversine_distance_km(12.95, 77.60, 12.95, 77.60)
        self.assertAlmostEqual(d0, 0.0, places=4)

        # 1 degree latitude is approx 111 km
        d1 = haversine_distance_km(12.0, 77.0, 13.0, 77.0)
        self.assertGreater(d1, 110.0)
        self.assertLess(d1, 112.0)

    def test_monitoring_station_geojson(self):
        st = self.stations[0]
        feat = st.to_geojson_feature()
        self.assertEqual(feat["type"], "Feature")
        self.assertEqual(feat["geometry"]["type"], "Point")
        self.assertEqual(feat["geometry"]["coordinates"], [77.60, 12.95])
        self.assertEqual(feat["properties"]["data_type"], "MEASURED_POINT")
        self.assertFalse(feat["properties"]["is_interpolated"])
        self.assertEqual(feat["properties"]["measured_value"], 50.0)

    def test_bounding_box(self):
        self.assertTrue(self.bbox.contains(12.95, 77.60))
        self.assertFalse(self.bbox.contains(14.0, 77.60))
        area = self.bbox.area_sq_km()
        self.assertGreater(area, 500.0)

    def test_idw_surface_math_and_bounds(self):
        cfg = IDWConfig(power=2.0, grid_resolution_x=10, grid_resolution_y=10)
        cells, meta = compute_idw_surface(self.stations, self.bbox, config=cfg)

        self.assertEqual(len(cells), 100)
        self.assertEqual(meta["data_type"], "INTERPOLATED_MODEL")
        self.assertIn("data_coverage_pct", meta)

        # Check values are bounded between min and max observed values (30.0 and 120.0)
        vals = [c.estimated_value for c in cells]
        self.assertGreaterEqual(min(vals), 29.99)
        self.assertLessEqual(max(vals), 120.01)

        # Check uncertainty is normalized in [0, 1]
        for c in cells:
            self.assertGreaterEqual(c.uncertainty_score, 0.0)
            self.assertLessEqual(c.uncertainty_score, 1.0)
            self.assertEqual(len(c.cell_bounds), 5)  # Closed polygon

    def test_getis_ord_gi_star_hotspots(self):
        hotspots = compute_getis_ord_gi_star(self.stations, distance_threshold_km=25.0)
        self.assertGreater(len(hotspots), 0)

        # Station 2 has value 120 (highest), it should have the highest positive z-score
        top_hs = hotspots[0]
        self.assertEqual(top_hs.hotspot_id, "HS-ST-02")
        self.assertGreater(top_hs.gi_z_score, 0.0)

        feat = top_hs.to_geojson_feature()
        self.assertEqual(feat["properties"]["data_type"], "HOTSPOT")
        self.assertFalse(feat["properties"]["is_interpolated"])

    def test_detect_spatial_anomalies(self):
        # With values [50, 120, 80, 30], mean is 70, std is ~33.9
        # Let's add an extreme spike
        spike_st = MonitoringStation(
            id="SPIKE-01",
            name="Chemical Factory Stack",
            latitude=13.00,
            longitude=77.65,
            pollutant="PM2.5",
            measured_value=350.0,
            unit="µg/m³",
            timestamp="2024-05-01T12:00:00Z",
        )
        anomalies = detect_spatial_anomalies(self.stations + [spike_st], z_threshold=1.8)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["station_id"], "SPIKE-01")
        self.assertEqual(anomalies[0]["anomaly_type"], "HIGH_SPIKE")

    def test_compute_temporal_trend(self):
        # Increasing trend: 10, 20, 30 over 30 days
        history_increasing = [
            {"timestamp": "2024-01-01T00:00:00Z", "value": 20.0},
            {"timestamp": "2024-01-15T00:00:00Z", "value": 40.0},
            {"timestamp": "2024-01-30T00:00:00Z", "value": 60.0},
        ]
        trend = compute_temporal_trend(history_increasing)
        self.assertIsNotNone(trend)
        self.assertEqual(trend["direction"], "INCREASING")
        self.assertGreater(trend["slope_per_day"], 1.0)
        self.assertAlmostEqual(trend["r_squared"], 1.0, places=2)

        # Stable trend: 50, 50.1, 49.9
        history_stable = [
            {"timestamp": "2024-01-01T00:00:00Z", "value": 50.0},
            {"timestamp": "2024-01-15T00:00:00Z", "value": 50.1},
            {"timestamp": "2024-01-30T00:00:00Z", "value": 49.9},
        ]
        trend_stable = compute_temporal_trend(history_stable)
        self.assertEqual(trend_stable["direction"], "STABLE")

    def test_compute_regional_statistics(self):
        stats = compute_regional_statistics(self.stations, self.bbox)
        self.assertEqual(stats["station_count"], 4)
        self.assertEqual(stats["pollutant"], "PM2.5")
        self.assertEqual(stats["min"], 30.0)
        self.assertEqual(stats["max"], 120.0)
        self.assertEqual(stats["mean"], 70.0)
        self.assertEqual(stats["range"], 90.0)
        self.assertIn("coverage", stats)
        self.assertGreater(stats["coverage"]["station_density_per_1000km2"], 0.0)

    def test_generate_investigation_geojson_contract(self):
        cells, _ = compute_idw_surface(
            self.stations, self.bbox, config=IDWConfig(grid_resolution_x=5, grid_resolution_y=5)
        )
        hotspots = compute_getis_ord_gi_star(self.stations)

        geojson = generate_investigation_geojson(
            self.stations, interpolated_cells=cells, hotspots=hotspots
        )

        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertGreater(len(geojson["features"]), 0)

        # Verify strict categorization of all features
        types_found = {f["properties"]["data_type"] for f in geojson["features"]}
        self.assertIn("MEASURED_POINT", types_found)
        self.assertIn("INTERPOLATED_MODEL", types_found)

        # Check disclaimer on interpolated model
        for f in geojson["features"]:
            if f["properties"]["data_type"] == "INTERPOLATED_MODEL":
                self.assertTrue(f["properties"]["is_interpolated"])
                self.assertIn("disclaimer", f["properties"])
            elif f["properties"]["data_type"] == "MEASURED_POINT":
                self.assertFalse(f["properties"]["is_interpolated"])

    def test_preset_bengaluru_stations(self):
        blr_stations = get_preset_bengaluru_monitoring_stations()
        self.assertEqual(len(blr_stations), 8)
        names = [s.name for s in blr_stations]
        self.assertTrue(any("Bellandur" in n for n in names))
        self.assertTrue(any("Varthur" in n for n in names))
        self.assertTrue(any("Peenya" in n for n in names))


if __name__ == "__main__":
    unittest.main()

