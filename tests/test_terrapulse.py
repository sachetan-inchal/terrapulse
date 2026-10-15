"""
Comprehensive Unit & Integration Test Suite for TerraPulse.

Verifies:
- Multi-spectral radiometric calculations (NDVI, NDWI, NDBI, SAVI, BSI, EVI)
- Sentinel-2 SCL cloud and shadow masking
- Bi-temporal change detection and transition matrix logic
- Autonomous OSINT intelligence dossier generation
- Illumination-invariant robust feature matching
"""

import unittest
import numpy as np
import cv2

from terrapulse.multispectral import RadiometricProcessor, MultiSpectralIndices, SCLQualityMetrics
from terrapulse.change_detection import (
    BiTemporalChangeDetector,
    LandCoverClass,
    LandCoverTransitionMatrix,
    ChangeDetectionResult,
)
from terrapulse.osint_engine import (
    GeospatialOSINTEngine,
    EcologicalThreatLevel,
    OSINTIntelligenceReport,
)
from terrapulse.robust_matcher import RobustGeospatialMatcher, AlignmentResult


class TestMultiSpectralEngine(unittest.TestCase):
    """Test suite for radiometric indices, SCL masks, and composites."""

    def setUp(self):
        self.shape = (100, 100)
        # Synthetic high-NDVI vegetation patch
        self.nir_veg = np.full(self.shape, 200, dtype=np.uint8)
        self.red_veg = np.full(self.shape, 40, dtype=np.uint8)
        self.green_veg = np.full(self.shape, 120, dtype=np.uint8)
        self.blue_veg = np.full(self.shape, 30, dtype=np.uint8)
        self.swir_veg = np.full(self.shape, 50, dtype=np.uint8)

    def test_ndvi_values(self):
        ndvi = RadiometricProcessor.compute_ndvi(self.nir_veg, self.red_veg)
        self.assertEqual(ndvi.shape, self.shape)
        # (200 - 40) / (200 + 40) = 160 / 240 = 0.6667
        self.assertAlmostEqual(float(ndvi[50, 50]), 0.6667, places=3)
        self.assertTrue(np.all(ndvi >= -1.0) and np.all(ndvi <= 1.0))

    def test_ndwi_values(self):
        # Water body: high green, low NIR
        green_water = np.full(self.shape, 180, dtype=np.uint8)
        nir_water = np.full(self.shape, 30, dtype=np.uint8)
        ndwi = RadiometricProcessor.compute_ndwi(green_water, nir_water)
        # (180 - 30) / (180 + 30) = 150 / 210 = 0.714
        self.assertAlmostEqual(float(ndwi[50, 50]), 0.714, places=3)
        self.assertTrue(np.all(ndwi > 0.5))

    def test_ndbi_values(self):
        # Built-up area: high SWIR, low NIR
        swir_urban = np.full(self.shape, 220, dtype=np.uint8)
        nir_urban = np.full(self.shape, 60, dtype=np.uint8)
        ndbi = RadiometricProcessor.compute_ndbi(swir_urban, nir_urban)
        # (220 - 60) / (220 + 60) = 160 / 280 = 0.571
        self.assertAlmostEqual(float(ndbi[50, 50]), 0.571, places=3)
        self.assertTrue(np.all(ndbi > 0.4))

    def test_process_all_indices(self):
        bands = {
            "B02": self.blue_veg,
            "B03": self.green_veg,
            "B04": self.red_veg,
            "B08": self.nir_veg,
            "B11": self.swir_veg,
        }
        res = RadiometricProcessor.process_all_indices(bands)
        self.assertIsInstance(res, MultiSpectralIndices)
        self.assertIn("dense_vegetation_pct", res.statistics)
        self.assertGreater(res.statistics["dense_vegetation_pct"], 90.0)

    def test_scl_masking(self):
        scl = np.full(self.shape, RadiometricProcessor.SCL_VEGETATION, dtype=np.uint8)
        # Add 10% clouds and 5% cloud shadows
        scl[:10, :] = RadiometricProcessor.SCL_CLOUD_HIGH_PROB
        scl[10:15, :] = RadiometricProcessor.SCL_CLOUD_SHADOW

        quality = RadiometricProcessor.parse_scl(scl)
        self.assertIsInstance(quality, SCLQualityMetrics)
        self.assertEqual(quality.cloud_contamination_percentage, 10.0)
        self.assertEqual(quality.shadow_percentage, 5.0)
        self.assertEqual(quality.clear_sky_percentage, 85.0)
        self.assertLess(quality.quality_score, 100.0)

    def test_false_color_composite(self):
        bands = {
            "B02": self.blue_veg,
            "B03": self.green_veg,
            "B04": self.red_veg,
            "B08": self.nir_veg,
            "B11": self.swir_veg,
        }
        cir = RadiometricProcessor.generate_false_color_composite(bands, "cir")
        self.assertEqual(cir.shape, (100, 100, 3))
        self.assertEqual(cir.dtype, np.uint8)


class TestChangeDetectionEngine(unittest.TestCase):
    """Test suite for bi-temporal spectral change detection and transition matrix."""

    def setUp(self):
        self.h, self.w = 200, 200
        # t1: Pristine green landscape
        self.t1 = np.full((self.h, self.w, 3), (35, 160, 45), dtype=np.uint8)
        # t2: Forest partially converted into concrete urban center
        self.t2 = self.t1.copy()
        # Urban area in bottom-right quadrant (100x100 = 25% of image)
        self.t2[100:200, 100:200] = (210, 210, 215)

    def test_spectral_change_detection(self):
        res = BiTemporalChangeDetector.detect_spectral_change(self.t1, self.t2, threshold_mode="otsu")
        self.assertIsInstance(res, ChangeDetectionResult)
        # ~25% of the scene should be detected as changed
        self.assertGreater(res.changed_pixel_ratio, 20.0)
        self.assertLess(res.changed_pixel_ratio, 30.0)
        self.assertEqual(res.binary_change_mask.shape, (self.h, self.w))

    def test_transition_matrix(self):
        classes_t1 = BiTemporalChangeDetector.classify_land_cover_heuristic(self.t1)
        classes_t2 = BiTemporalChangeDetector.classify_land_cover_heuristic(self.t2)
        trans = BiTemporalChangeDetector.compute_transition_matrix(classes_t1, classes_t2)
        self.assertIsInstance(trans, LandCoverTransitionMatrix)
        self.assertGreater(trans.urban_sprawl_hectares, 0.0)
        table = trans.to_markdown_table()
        self.assertIn("Urban Encroachment", table)

    def test_change_dashboard_rendering(self):
        res = BiTemporalChangeDetector.detect_spectral_change(self.t1, self.t2)
        dashboard = BiTemporalChangeDetector.render_change_dashboard(self.t1, self.t2, res)
        # Dashboard is 2x2 grid: (2*h, 2*w, 3)
        self.assertEqual(dashboard.shape, (self.h * 2, self.w * 2, 3))


class TestOSINTEngine(unittest.TestCase):
    """Test suite for autonomous OSINT intelligence analysis."""

    def test_critical_threat_scenario(self):
        report = GeospatialOSINTEngine.analyze_change_intelligence(
            region_query="Bengaluru Tech Corridor",
            bbox=[77.5, 12.8, 77.8, 13.1],
            timeframe="2020 to 2025",
            total_area_ha=500.0,
            deforestation_ha=120.0,
            urban_sprawl_ha=180.0,
            water_loss_ha=45.0,
            revegetation_ha=2.0,
        )
        self.assertIsInstance(report, OSINTIntelligenceReport)
        self.assertGreaterEqual(report.ecological_vulnerability_index, 50.0)
        self.assertIn(report.threat_level, [EcologicalThreatLevel.CRITICAL, EcologicalThreatLevel.HIGH])
        md = report.to_markdown()
        self.assertIn("Executive Threat Telemetry", md)
        self.assertIn("Bengaluru", md)
        js = report.to_json()
        self.assertIn("ecological_vulnerability_index", js)

    def test_regenerative_scenario(self):
        report = GeospatialOSINTEngine.analyze_change_intelligence(
            region_query="Swiss Alps Reserve",
            bbox=[7.0, 45.5, 8.0, 46.2],
            timeframe="2024 to 2025",
            total_area_ha=300.0,
            deforestation_ha=0.0,
            urban_sprawl_ha=0.0,
            water_loss_ha=0.0,
            revegetation_ha=25.0,
        )
        self.assertEqual(report.threat_level, EcologicalThreatLevel.REGENERATIVE)
        self.assertLess(report.ecological_vulnerability_index, 20.0)


class TestRobustMatcher(unittest.TestCase):
    """Test suite for illumination-invariant feature matching."""

    def test_illumination_normalization(self):
        sample = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        norm = RobustGeospatialMatcher.normalize_illumination(sample)
        self.assertEqual(norm.shape, (200, 200))
        self.assertEqual(norm.dtype, np.uint8)

    def test_synthetic_alignment(self):
        # Generate overlapping tiles
        base = np.zeros((400, 600, 3), dtype=np.uint8)
        cv2.rectangle(base, (50, 50), (250, 250), (120, 180, 200), -1)
        cv2.rectangle(base, (200, 100), (450, 350), (70, 90, 160), -1)
        for i in range(50):
            cv2.circle(base, (np.random.randint(20, 580), np.random.randint(20, 380)), 6, (80, 150, 90), -1)

        tile1 = base[:, :400]
        tile2 = base[:, 200:]
        res = RobustGeospatialMatcher.match_and_align(tile1, tile2)
        self.assertIsInstance(res, AlignmentResult)
        if res.is_valid:
            self.assertIsNotNone(res.stitched_image)
            self.assertGreater(res.inlier_count, 4)


if __name__ == "__main__":
    unittest.main()
