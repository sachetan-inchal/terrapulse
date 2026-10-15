"""Tests for Stitching Laboratory and Environmental Computer Vision Workspace."""

import numpy as np
import cv2
from src.data.sentinel_explorer import (
    StitchingTileInfo,
    compute_stitching_laboratory,
    draw_sift_correspondence_canvas,
    ObservationData,
    calculate_environmental_layers
)


def test_stitching_laboratory_diagnostics():
    """Verify SIFT feature detection, inlier classification, and overlap diagnostics."""
    # Synthetic textured pair
    np.random.seed(42)
    img1 = np.random.randint(40, 220, (180, 180, 3), dtype=np.uint8)
    M_shift = np.float32([[1, 0, 4], [0, 1, 2]])
    img2 = cv2.warpAffine(img1.copy(), M_shift, (180, 180))

    t1 = StitchingTileInfo(
        id="S2A_TEST_TILE1",
        date_str="2024-03-28",
        platform="Sentinel-2A MSI",
        cloud_cover=4.5,
        raw_shape=(180, 180),
        raw_crs="EPSG:32643",
        raw_rgb=img1,
        valid_mask=np.ones((180, 180), dtype=np.uint8) * 255,
        reprojected_rgb=img1,
        reprojected_crs="EPSG:32643",
        reprojected_shape=(180, 180),
        bbox=[77.5, 12.9, 77.6, 13.0]
    )

    t2 = StitchingTileInfo(
        id="S2B_TEST_TILE2",
        date_str="2024-03-28",
        platform="Sentinel-2B MSI",
        cloud_cover=3.8,
        raw_shape=(180, 180),
        raw_crs="EPSG:32643",
        raw_rgb=img2,
        valid_mask=np.ones((180, 180), dtype=np.uint8) * 255,
        reprojected_rgb=img2,
        reprojected_crs="EPSG:32643",
        reprojected_shape=(180, 180),
        bbox=[77.5, 12.8, 77.6, 12.9]
    )

    merged = np.hstack((img1, img2))
    lab = compute_stitching_laboratory([t1, t2], merged, "EPSG:32643")

    assert lab is not None
    assert len(lab.tiles) == 2
    assert lab.correspondence is not None
    assert lab.correspondence.num_kp1 > 0
    assert lab.correspondence.num_kp2 > 0
    assert lab.correspondence.num_inliers > 0
    assert lab.correspondence.inlier_ratio > 0.0
    assert lab.correspondence.match_image_all.shape == (180, 360, 3)
    assert lab.correspondence.alpha_overlap_blend.shape == (180, 180, 3)
    assert lab.correspondence.checkerboard_comparison.shape == (180, 180, 3)
    assert lab.seamline_preview.shape == merged.shape


def test_environmental_cv_statistics_calibration():
    """Verify calibrated physical metrics, median NDVI, and area calculations in km²."""
    H, W = 100, 100
    nir = np.full((H, W), 2400.0, dtype=np.float32)
    red = np.full((H, W), 400.0, dtype=np.float32)
    green = np.full((H, W), 900.0, dtype=np.float32)
    blue = np.full((H, W), 350.0, dtype=np.float32)
    rgb = np.dstack((red, green, blue)).astype(np.uint8)

    obs = ObservationData(
        id="OBS_CALIBRATION_TEST",
        date_str="2024-03-28",
        cloud_cover=2.0,
        crs="EPSG:32643",
        bbox=[77.5, 12.9, 77.6, 13.0],
        rgb=rgb,
        red=red,
        nir=nir,
        green=green,
        blue=blue,
        valid_mask=np.ones((H, W), dtype=np.uint8) * 255
    )

    env = calculate_environmental_layers(obs)
    stats = env.stats

    # Expected NDVI = (2400 - 400) / (2400 + 400) = 2000 / 2800 = 0.714
    assert np.isclose(stats["mean_ndvi"], 0.714, atol=0.01)
    assert np.isclose(stats["median_ndvi"], 0.714, atol=0.01)
    assert stats["forest_coverage_pct"] > 90.0
    assert stats["forest_area_km2"] > 0.0
    assert "total_area_km2" in stats


def test_auto_detect_2x2_tiles_and_multi_seam_canvas():
    """Verify auto-detection of 4 quadrant tiles and 2x2 multi-seam reference lines canvas."""
    from src.data.sentinel_explorer import (
        SentinelSceneMetadata,
        auto_detect_2x2_tiles,
        create_2x2_multi_seam_landmark_canvas
    )

    scenes = [
        SentinelSceneMetadata("S2A_T43PHQ_2024", None, "2024-03-28", 2024, 0.1, "Sentinel-2A", "EPSG:32643", [77.6, 12.9, 78.6, 13.9], {}, "planetary_computer"),
        SentinelSceneMetadata("S2A_T43PHP_2024", None, "2024-03-28", 2024, 1.2, "Sentinel-2A", "EPSG:32643", [77.6, 11.9, 78.6, 12.9], {}, "planetary_computer"),
        SentinelSceneMetadata("S2A_T43PGQ_2024", None, "2024-03-28", 2024, 0.3, "Sentinel-2A", "EPSG:32643", [76.6, 12.9, 77.6, 13.9], {}, "planetary_computer"),
        SentinelSceneMetadata("S2A_T43PGP_2024", None, "2024-03-28", 2024, 2.1, "Sentinel-2A", "EPSG:32643", [76.6, 11.9, 77.6, 12.9], {}, "planetary_computer"),
    ]

    detected = auto_detect_2x2_tiles(scenes, target_lat=12.97, target_lon=77.59)
    assert len(detected) == 4

    tiles_img = [np.full((120, 120, 3), 50 + i * 20, dtype=np.uint8) for i in range(4)]
    canvas = create_2x2_multi_seam_landmark_canvas(tiles_img)
    assert canvas is not None
    assert canvas.shape[0] > 240
    assert canvas.shape[1] > 240

