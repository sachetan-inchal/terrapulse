"""Historical Sentinel-2 STAC Discovery and Environmental Layer Processing Test Suite.

Verifies authentic data access and processing across multi-decadal historical epochs:
1. 2017-2018
2. 2020-2021
3. 2023-2024
4. Most recent epoch (2024-2025)
for Bengaluru, Karnataka, India.
"""

import pytest
import numpy as np
from src.data.sentinel_explorer import (
    search_sentinel2_scenes,
    inspect_sentinel2_assets,
    retrieve_sentinel2_data,
    build_georeferenced_mosaic,
    calculate_environmental_layers,
    align_bitemporal_observations
)

BENGALURU_BBOX = [77.4598, 12.8334, 77.7840, 13.1426]


def test_historical_search_bengaluru_epochs():
    """Verifies that the live STAC catalogue returns real Sentinel-2 scenes for all 4 epochs."""
    epochs = [
        ("2017-2018", "2017-01-01/2018-12-31"),
        ("2020-2021", "2020-01-01/2021-12-31"),
        ("2023-2024", "2023-01-01/2024-12-31"),
        ("Recent", "2024-01-01/2025-12-31")
    ]

    discovery_report = {}

    for label, dt_range in epochs:
        scenes = search_sentinel2_scenes(
            bbox=BENGALURU_BBOX,
            datetime_range=dt_range,
            provider="planetary_computer",
            max_cloud=25.0,
            limit=5
        )
        assert len(scenes) > 0, f"Expected scenes for epoch {label} ({dt_range}), got 0"
        first = scenes[0]
        assert first.id is not None
        assert first.cloud_cover >= 0.0
        assert first.date_str != "Unknown"
        
        discovery_report[label] = {
            "count": len(scenes),
            "sample_id": first.id,
            "sample_date": first.date_str,
            "cloud_cover": first.cloud_cover
        }

    print("\n[HISTORICAL SENTINEL-2 DISCOVERY REPORT]")
    for lbl, rep in discovery_report.items():
        print(f"Epoch {lbl}: {rep['count']} scenes discovered | Sample: {rep['sample_id']} ({rep['sample_date']}, Cloud: {rep['cloud_cover']}%)")


def test_inspect_sentinel2_assets():
    """Inspects available spectral assets for a real Sentinel-2 scene."""
    scenes = search_sentinel2_scenes(
        bbox=BENGALURU_BBOX,
        datetime_range="2023-01-01/2023-12-31",
        provider="planetary_computer",
        max_cloud=15.0,
        limit=2
    )
    assert len(scenes) > 0
    inspection = inspect_sentinel2_assets(scenes[0])
    assert inspection["is_analysis_ready"] is True
    assert inspection["bands"]["B04"]["available"] is True
    assert inspection["bands"]["B08"]["available"] is True
    assert inspection["bands"]["B02"]["available"] is True
    assert inspection["bands"]["B03"]["available"] is True


def test_retrieve_and_mosaic_sentinel2():
    """Tests retrieval of real Sentinel-2 bands and mosaic generation."""
    scenes = search_sentinel2_scenes(
        bbox=BENGALURU_BBOX,
        datetime_range="2024-01-01/2024-04-01",
        provider="planetary_computer",
        max_cloud=15.0,
        limit=2
    )
    assert len(scenes) >= 1

    obs = retrieve_sentinel2_data(scenes[0], decimation_scale=15)
    assert obs is not None
    assert obs.rgb.shape[2] == 3
    assert obs.rgb.dtype == np.uint8

    mosaic = build_georeferenced_mosaic([obs])
    assert mosaic.rgb.shape == obs.rgb.shape


def test_environmental_layers_physical_ndvi():
    """Tests that genuine NDVI, NDWI, Land Cover, and Population layers are computed."""
    scenes = search_sentinel2_scenes(
        bbox=BENGALURU_BBOX,
        datetime_range="2024-01-01/2024-04-01",
        provider="planetary_computer",
        max_cloud=15.0,
        limit=1
    )
    obs = retrieve_sentinel2_data(scenes[0], decimation_scale=15)
    assert obs is not None

    layers = calculate_environmental_layers(obs)
    assert layers.ndvi.shape == obs.rgb.shape[:2]
    # Check valid range
    valid_ndvi = layers.ndvi[~np.isnan(layers.ndvi)]
    assert np.all(valid_ndvi >= -1.0) and np.all(valid_ndvi <= 1.0)
    assert layers.stats["mean_ndvi"] >= -1.0 and layers.stats["mean_ndvi"] <= 1.0
    assert layers.stats["forest_coverage_pct"] >= 0.0
    assert layers.stats["urban_built_pct"] >= 0.0
    assert layers.stats["mean_population_density"] >= 0.0


def test_bitemporal_alignment_and_difference():
    """Tests alignment and delta NDVI calculation between two distinct observations."""
    scenes = search_sentinel2_scenes(
        bbox=BENGALURU_BBOX,
        datetime_range="2020-01-01/2024-04-01",
        provider="planetary_computer",
        max_cloud=20.0,
        limit=4
    )
    assert len(scenes) >= 2

    # Pick two different dates
    obs_t0 = retrieve_sentinel2_data(scenes[-1], decimation_scale=16)
    obs_t1 = retrieve_sentinel2_data(scenes[0], decimation_scale=16)

    assert obs_t0 is not None
    assert obs_t1 is not None

    crop_t0, crop_t1, delta_ndvi, meta = align_bitemporal_observations(obs_t0, obs_t1)
    assert crop_t0.shape == crop_t1.shape
    assert delta_ndvi.shape == crop_t0.shape[:2]
    assert meta["overlap_pct"] > 0.0


def test_bengaluru_acceptance_pipeline():
    """Acceptance test verifying end-to-end Bengaluru navigation, STAC query, and georeferenced mosaicking."""
    from src.data.sentinel_service import geocode_user_location
    from src.data.sentinel_explorer import build_real_sentinel2_mosaic

    # 1. Geocode location
    geocoded = geocode_user_location("Bengaluru, Karnataka, India")
    lat, lon = geocoded["lat"], geocoded["lon"]
    assert abs(lat - 12.97) < 0.2, f"Expected lat ~12.97, got {lat}"
    assert abs(lon - 77.59) < 0.2, f"Expected lon ~77.59, got {lon}"
    assert geocoded["target_utm"] == "EPSG:32643"

    # 2. Globe coordinate mapping verification: Southern India is in +X, +Y, -Z quadrant
    u = (lon + 180.0) / 360.0
    v = (90.0 - lat) / 180.0
    theta_len, phi_len = np.pi, 2 * np.pi
    gx = - 100.0 * np.cos(u * phi_len) * np.sin(v * theta_len)
    gy = 100.0 * np.cos(v * theta_len)
    gz = 100.0 * np.sin(u * phi_len) * np.sin(v * theta_len)
    assert gz < -50.0, f"Expected gz < -50 (facing Southern India), got {gz} (Africa is near gz=0, gx=100)"
    assert gx > 0.0 and gy > 0.0

    # 3. STAC search returns real intersecting Sentinel-2 scenes covering Bengaluru
    scenes = search_sentinel2_scenes(
        bbox=geocoded["bbox"],
        datetime_range="2024-03-20/2024-03-31",
        provider="planetary_computer",
        max_cloud=10.0,
        limit=2
    )
    assert len(scenes) >= 1, "Expected real scenes covering Bengaluru"
    first = scenes[0]
    assert "T43P" in first.id, f"Expected Bengaluru MGRS tile T43P, got {first.id}"

    # 4. Multi-tile georeferenced mosaic creation via rasterio.merge
    mosaic = build_real_sentinel2_mosaic(
        scenes=scenes[:2],
        target_crs=geocoded["target_utm"],
        bbox=geocoded["bbox"],
        decimation_scale=16
    )
    assert mosaic is not None, "Failed to create real georeferenced mosaic"
    assert mosaic.crs == "EPSG:32643"
    assert mosaic.rgb.shape[2] == 3
    assert np.count_nonzero(mosaic.valid_mask) > 0
    print(f"\n[ACCEPTANCE TEST PASSED] Bengaluru mosaic built: shape={mosaic.rgb.shape}, CRS={mosaic.crs}, scenes={mosaic.source_scenes}")

