"""Test Suite for Temporal Image Registration, Footprint Determination & Change Detection.

Validates:
1. Identical images (Identity matrix, ~0px residual, 100% overlap)
2. Translated image pair (Sub-pixel translation recovery, boundary padding exclusion)
3. Rotated and scaled image pair (Rotation and scale parameter recovery)
4. Partial overlap with differing image boundaries (Different dimensions, exact rectangle cropping)
5. Images with large non-overlapping regions (Benchmark tile_left vs tile_right)
6. Low-texture and untextured scenes (Graceful rejection, quality gate safety warnings)
7. Scenes with genuine landscape changes (Stable landmark isolation, change detection on common crop)
8. Validity mask exclusion (Black padding excluded from change metrics)
9. Immutability of original image arrays
"""

import pytest
import numpy as np
import cv2
from PIL import Image

from src.models.registration import (
    run_temporal_registration,
    run_aligned_common_change_detection,
    find_largest_inscribed_rectangle,
    generate_checkerboard
)

def create_synthetic_textured_scene(w: int = 512, h: int = 512, seed: int = 42) -> np.ndarray:
    """Generates a rich synthetic geospatial landscape with roads, fields, and structures."""
    np.random.seed(seed)
    scene = np.zeros((h, w, 3), dtype=np.uint8)

    # Base land textures
    scene[:, :] = [45, 85, 45]  # Green pasture baseline

    # Add agricultural parcel grid
    for r in range(40, h - 40, 70):
        for c in range(40, w - 40, 70):
            color = [int(x) for x in np.random.randint(60, 160, size=3)]
            cv2.rectangle(scene, (c, r), (c + 55, r + 55), color, -1)

    # Add highway corridors
    cv2.line(scene, (0, h // 3), (w, h // 3), (180, 180, 180), 8)
    cv2.line(scene, (w // 2, 0), (w // 2, h), (180, 180, 180), 8)
    cv2.line(scene, (0, 0), (w, h), (140, 140, 140), 5)

    # Add building clusters
    for b in range(25):
        bx = int(np.random.randint(30, w - 30))
        by = int(np.random.randint(30, h - 30))
        bw = int(np.random.randint(12, 28))
        bh = int(np.random.randint(12, 28))
        cv2.rectangle(scene, (bx, by), (bx + bw, by + bh), (220, 220, 230), -1)
        cv2.rectangle(scene, (bx, by), (bx + bw, by + bh), (40, 40, 40), 1)

    return scene

def test_identical_images():
    scene = create_synthetic_textured_scene(400, 400)
    img = Image.fromarray(scene)

    res = run_temporal_registration(img, img)

    assert res.success is True
    assert res.diagnostics.quality_passed is True
    assert res.diagnostics.num_inliers >= 30
    assert res.diagnostics.inlier_ratio > 0.80
    assert res.diagnostics.reprojection_error_median < 0.5
    assert res.diagnostics.valid_overlap_pct_ref > 99.0
    assert res.ref_cropped.shape == res.mov_cropped.shape
    assert res.ref_cropped.shape[:2] == (400, 400)

def test_translated_image_pair():
    scene = create_synthetic_textured_scene(500, 500)
    tx, ty = 45, -30

    # Apply known translation
    M_gt = np.float32([[1, 0, tx], [0, 1, ty]])
    warped_scene = cv2.warpAffine(scene, M_gt, (500, 500), borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    img_ref = Image.fromarray(scene)
    img_mov = Image.fromarray(warped_scene)

    res = run_temporal_registration(img_ref, img_mov, transform_model="Partial Affine (Translation + Rotation + Scale)")

    assert res.success is True
    assert res.diagnostics.transformation_matrix is not None
    M_est = res.diagnostics.transformation_matrix

    # Check that estimated translation aligns moving back to reference
    # moving has +tx, so moving->ref should have -tx approx
    est_tx = M_est[0, 2]
    est_ty = M_est[1, 2]
    assert abs(est_tx - (-tx)) < 1.5, f"Translation X error too high: {est_tx} vs {-tx}"
    assert abs(est_ty - (-ty)) < 1.5, f"Translation Y error too high: {est_ty} vs {-ty}"

    # Verify both final crops have IDENTICAL shapes
    assert res.ref_cropped.shape == res.mov_cropped.shape
    assert res.ref_cropped.shape[0] > 0 and res.ref_cropped.shape[1] > 0
    # Common mask should exclude the shifted margin
    assert np.all(res.mask_cropped == 255)

def test_rotated_and_scaled_image_pair():
    scene = create_synthetic_textured_scene(512, 512)
    center = (256, 256)
    angle = 12.0
    scale = 1.08

    M_gt = cv2.getRotationMatrix2D(center, angle, scale)
    warped_scene = cv2.warpAffine(scene, M_gt, (512, 512), borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    img_ref = Image.fromarray(scene)
    img_mov = Image.fromarray(warped_scene)

    res = run_temporal_registration(img_ref, img_mov, transform_model="Partial Affine (Translation + Rotation + Scale)")

    assert res.success is True
    assert res.diagnostics.num_inliers >= 20
    assert res.diagnostics.reprojection_error_median < 2.0
    assert res.ref_cropped.shape == res.mov_cropped.shape

def test_partial_overlap_differing_dimensions():
    # Image A: 500 x 400
    scene_a = create_synthetic_textured_scene(500, 400, seed=1)
    # Image B: 450 x 500, shifted
    M_shift = np.float32([[1, 0, 50], [0, 1, 40]])
    scene_b = cv2.warpAffine(scene_a, M_shift, (450, 500), borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    img_a = Image.fromarray(scene_a)
    img_b = Image.fromarray(scene_b)

    res = run_temporal_registration(img_a, img_b)

    assert res.success is True
    # Dimensions of final crops must be identically matched
    assert res.ref_cropped.shape == res.mov_cropped.shape
    assert res.ref_cropped.shape[0] == res.diagnostics.crop_dimensions[1]
    assert res.ref_cropped.shape[1] == res.diagnostics.crop_dimensions[0]
    # Overlap must be detected properly
    assert 20.0 < res.diagnostics.valid_overlap_pct_ref < 95.0

def test_benchmark_tiles_large_offset():
    # Test on repo benchmark spatial tiles if present
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    p_left = root / "tile_left.jpg"
    p_right = root / "tile_right.jpg"

    if p_left.exists() and p_right.exists():
        img1 = Image.open(p_left)
        img2 = Image.open(p_right)

        res = run_temporal_registration(img1, img2, transform_model="Partial Affine (Translation + Rotation + Scale)")
        assert res.success is True
        assert res.diagnostics.num_inliers > 100
        # Check that 360 px horizontal shift is accurately recovered
        M = res.diagnostics.transformation_matrix
        assert abs(M[0, 2] - 360.0) < 2.0
        assert abs(M[1, 2] - 0.0) < 2.0
        assert res.ref_cropped.shape == res.mov_cropped.shape

def test_low_texture_rejection_and_warnings():
    # Uniform low-texture canvas with no keypoints
    blank1 = np.ones((300, 300, 3), dtype=np.uint8) * 128
    blank2 = np.ones((300, 300, 3), dtype=np.uint8) * 135

    img1 = Image.fromarray(blank1)
    img2 = Image.fromarray(blank2)

    res = run_temporal_registration(img1, img2)

    # Must NOT claim verified registration when features are absent
    assert res.diagnostics.quality_passed is False
    assert len(res.diagnostics.quality_warnings) > 0
    assert any("match" in w.lower() or "insufficient" in w.lower() for w in res.diagnostics.quality_warnings)

def test_genuine_changes_isolated_on_common_crop():
    scene_t0 = create_synthetic_textured_scene(400, 400, seed=10)
    scene_t1 = scene_t0.copy()

    # Introduce genuine land-cover changes (new built-up area and road)
    cv2.rectangle(scene_t1, (100, 100), (220, 220), (240, 240, 250), -1)
    cv2.line(scene_t1, (50, 280), (350, 280), (200, 200, 200), 12)

    # Shift t1 slightly
    M = np.float32([[1, 0, 15], [0, 1, -10]])
    scene_t1_shifted = cv2.warpAffine(scene_t1, M, (400, 400))

    res = run_temporal_registration(
        Image.fromarray(scene_t0),
        Image.fromarray(scene_t1_shifted),
        transform_model="Partial Affine (Translation + Rotation + Scale)"
    )

    assert res.success is True
    assert res.diagnostics.quality_passed is True

    # Run change detection on aligned common crop
    c_mask, diff, changed_pct, changed_px, total_valid = run_aligned_common_change_detection(
        res.ref_cropped, res.mov_cropped, res.mask_cropped, threshold=60.0
    )

    # Genuine change must be detected, and only within valid common area
    assert 5.0 < changed_pct < 35.0
    assert changed_px > 0
    assert total_valid > 0
    assert (c_mask[res.mask_cropped == 0] > 0).sum() == 0  # Invalid pixels must be zero change

def test_immutability_of_input_images():
    scene1 = create_synthetic_textured_scene(300, 300, seed=5)
    scene2 = create_synthetic_textured_scene(300, 300, seed=6)
    copy1 = scene1.copy()
    copy2 = scene2.copy()

    img1 = Image.fromarray(scene1)
    img2 = Image.fromarray(scene2)

    run_temporal_registration(img1, img2)

    # Check original numpy inputs were not modified in place
    np.testing.assert_array_equal(scene1, copy1)
    np.testing.assert_array_equal(scene2, copy2)
