"""Temporal Image Registration, Footprint Determination & Common-Area Cropping Engine.

Implements rigorous computer vision temporal registration for satellite image pairs:
- Stable landmark detection (SIFT / ORB fallback)
- Descriptor matching with Lowe's ratio distance test (FLANN / BFMatcher)
- RANSAC geometric verification (Partial Affine, Full Affine, Homography)
- Rejection of degenerate or poorly distributed correspondences
- Separate nearest-neighbor warping of validity masks to prevent black padding leakage
- Exact common valid footprint calculation (ref_mask AND warped_mov_mask)
- Maximal axis-aligned rectangular common crop derivation
- Masked change detection restricted exclusively to valid common footprints
"""

import time
from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import cv2
from PIL import Image

@dataclass
class RegistrationDiagnostics:
    reference_name: str
    moving_name: str
    ref_shape: Tuple[int, int, int]
    mov_shape: Tuple[int, int, int]
    detector: str
    transform_model: str
    num_keypoints_ref: int
    num_keypoints_mov: int
    num_raw_matches: int
    num_ratio_matches: int
    num_inliers: int
    inlier_ratio: float
    reprojection_error_median: float
    reprojection_error_p90: float
    spatial_spread_score: float  # Convex hull area / image area
    transformation_matrix: Optional[np.ndarray]
    valid_overlap_pct_ref: float
    valid_overlap_pct_mov: float
    crop_rect: Tuple[int, int, int, int]  # (xmin, ymin, xmax, ymax)
    crop_dimensions: Tuple[int, int]      # (width, height)
    retained_footprint_pct: float
    quality_passed: bool
    quality_warnings: List[str]
    processing_time_s: float

@dataclass
class RegistrationResult:
    success: bool
    diagnostics: RegistrationDiagnostics
    ref_orig: np.ndarray           # Original Reference RGB
    mov_orig: np.ndarray           # Original Moving RGB
    warped_mov: np.ndarray         # Warped Moving in Reference Coordinate System
    ref_valid_mask: np.ndarray     # Reference Validity Mask (uint8: 0 or 255)
    warped_mov_valid_mask: np.ndarray  # Warped Moving Validity Mask (uint8: 0 or 255)
    common_valid_mask: np.ndarray      # Intersection of Valid Data (uint8: 0 or 255)
    ref_cropped: np.ndarray        # Identically Cropped Reference RGB
    mov_cropped: np.ndarray        # Identically Cropped Warped Moving RGB
    mask_cropped: np.ndarray       # Identically Cropped Common Valid Mask
    inlier_matches_vis: Optional[np.ndarray] = None
    all_matches_vis: Optional[np.ndarray] = None
    footprint_vis: Optional[np.ndarray] = None

def get_feature_detector(detector_type: str = "SIFT", n_features: int = 2500):
    """Instantiates requested feature detector with documented fallback."""
    det_clean = detector_type.upper().strip()
    if det_clean == "SIFT":
        try:
            return cv2.SIFT_create(nfeatures=n_features, contrastThreshold=0.03, edgeThreshold=10), "SIFT"
        except Exception:
            pass
    # Documented robust fallback
    return cv2.ORB_create(nfeatures=n_features), "ORB"

def extract_and_match(
    img_ref: np.ndarray,
    img_mov: np.ndarray,
    detector_type: str = "SIFT",
    lowe_ratio: float = 0.75,
    n_features: int = 2500
):
    """
    Detects stable keypoints and finds candidate correspondences using Lowe's ratio test.
    """
    detector, active_detector = get_feature_detector(detector_type, n_features)

    # Convert to grayscale for landmark detection
    gray_ref = cv2.cvtColor(img_ref, cv2.COLOR_RGB2GRAY) if img_ref.ndim == 3 else img_ref
    gray_mov = cv2.cvtColor(img_mov, cv2.COLOR_RGB2GRAY) if img_mov.ndim == 3 else img_mov

    kp_ref, des_ref = detector.detectAndCompute(gray_ref, None)
    kp_mov, des_mov = detector.detectAndCompute(gray_mov, None)

    if des_ref is None or des_mov is None or len(kp_ref) < 4 or len(kp_mov) < 4:
        return active_detector, kp_ref, kp_mov, [], []

    # Choose appropriate matcher based on descriptor type
    if active_detector == "SIFT":
        index_params = dict(algorithm=1, trees=5)  # FLANN KD-Tree
        search_params = dict(checks=50)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    else:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    try:
        raw_matches = matcher.knnMatch(des_mov, des_ref, k=2)
    except Exception:
        # Fallback to brute-force L2 if FLANN encounters dtype mismatch
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        raw_matches = bf.knnMatch(des_mov.astype(np.float32), des_ref.astype(np.float32), k=2)

    # Lowe's ratio test pruning
    ratio_matches = []
    for match_pair in raw_matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < lowe_ratio * n.distance:
                ratio_matches.append(m)

    return active_detector, kp_ref, kp_mov, raw_matches, ratio_matches

def estimate_geometric_transform(
    pts_mov: np.ndarray,
    pts_ref: np.ndarray,
    transform_model: str = "Partial Affine (Translation + Rotation + Scale)",
    ransac_thresh: float = 4.0,
    max_iters: int = 2000,
    confidence: float = 0.99
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Estimates geometric transformation using RANSAC.
    Returns (transform_matrix, inliers_mask).
    """
    if len(pts_mov) < 4 or len(pts_ref) < 4:
        return None, None

    model_clean = transform_model.lower()

    if "partial" in model_clean:
        # 4-DoF similarity: translation, rotation, uniform scale
        M, inliers = cv2.estimateAffinePartial2D(
            pts_mov, pts_ref,
            method=cv2.RANSAC,
            ransacReprojThreshold=ransac_thresh,
            maxIters=max_iters,
            confidence=confidence
        )
        return M, inliers

    elif "affine" in model_clean and "partial" not in model_clean:
        # 6-DoF full affine: translation, rotation, scale, shear
        M, inliers = cv2.estimateAffine2D(
            pts_mov, pts_ref,
            method=cv2.RANSAC,
            ransacReprojThreshold=ransac_thresh,
            maxIters=max_iters,
            confidence=confidence
        )
        return M, inliers

    else:
        # 8-DoF homography: projective perspective
        H, inliers = cv2.findHomography(
            pts_mov, pts_ref,
            method=cv2.RANSAC,
            ransacReprojThreshold=ransac_thresh,
            maxIters=max_iters,
            confidence=confidence
        )
        return H, inliers

def compute_spatial_spread_score(pts: np.ndarray, img_shape: Tuple[int, int]) -> float:
    """
    Calculates spatial distribution score of inlier coordinates using convex hull area
    relative to total image area. Prevents degenerate alignment constrained along a single line.
    """
    if len(pts) < 3:
        return 0.0
    try:
        hull = cv2.convexHull(pts.astype(np.float32))
        hull_area = cv2.contourArea(hull)
        total_area = float(img_shape[0] * img_shape[1])
        return float(min(1.0, hull_area / (total_area + 1e-6)))
    except Exception:
        return 0.0

def compute_reprojection_residuals(
    pts_mov: np.ndarray,
    pts_ref: np.ndarray,
    M: np.ndarray,
    is_homography: bool = False
) -> Tuple[float, float]:
    """Computes median and 90th percentile Euclidean reprojection residuals."""
    if len(pts_mov) == 0:
        return 999.0, 999.0

    if not is_homography:
        # M is 2x3
        pts_mov_h = np.hstack([pts_mov, np.ones((len(pts_mov), 1), dtype=np.float32)])
        pts_proj = (M @ pts_mov_h.T).T
    else:
        # M is 3x3 homography
        pts_mov_h = np.hstack([pts_mov, np.ones((len(pts_mov), 1), dtype=np.float32)])
        pts_proj_h = (M @ pts_mov_h.T).T
        pts_proj = pts_proj_h[:, :2] / (pts_proj_h[:, 2:] + 1e-12)

    diffs = pts_proj - pts_ref
    residuals = np.sqrt(np.sum(diffs ** 2, axis=1))
    med_res = float(np.median(residuals))
    p90_res = float(np.percentile(residuals, 90))
    return med_res, p90_res

def check_transformation_plausibility(M: np.ndarray, is_homography: bool = False) -> List[str]:
    """Inspects transformation matrix eigenvalues/determinant to detect degenerate or inverted warps."""
    warnings = []
    if M is None:
        return ["Transformation matrix could not be solved."]

    if not is_homography:
        A = M[:2, :2]
        det = np.linalg.det(A)
        if det <= 0:
            warnings.append("Degenerate transformation: negative determinant indicates reflection or inversion.")
        scale = np.sqrt(np.abs(det))
        if scale < 0.35 or scale > 2.8:
            warnings.append(f"Implausible scale change ({scale:.2f}x). Check image resolution matching.")
    else:
        H_norm = M / (M[2, 2] + 1e-12)
        det = np.linalg.det(H_norm[:2, :2])
        if det <= 0:
            warnings.append("Degenerate projective transform: inverted orientation detected.")
        if abs(H_norm[2, 0]) > 0.01 or abs(H_norm[2, 1]) > 0.01:
            warnings.append("Extreme projective foreshortening detected; planar assumption may be violated.")

    return warnings

def find_largest_inscribed_rectangle(mask: np.ndarray) -> Tuple[Tuple[int, int, int, int], int]:
    """
    Finds the maximum axis-aligned rectangle fully contained within the binary common mask.
    Linear-time dynamic programming algorithm O(H x W).
    Returns ((xmin, ymin, xmax, ymax), max_area).
    """
    H, W = mask.shape
    heights = np.zeros(W, dtype=np.int32)
    max_area = 0
    best_rect = (0, 0, W, H)

    bin_mask = (mask > 0).astype(np.int32)

    for r in range(H):
        heights = np.where(bin_mask[r] == 1, heights + 1, 0)
        stack = []
        for c in range(W + 1):
            h = heights[c] if c < W else 0
            start = c
            while stack and stack[-1][1] > h:
                idx, prev_h = stack.pop()
                area = prev_h * (c - idx)
                if area > max_area:
                    max_area = area
                    best_rect = (idx, r - prev_h + 1, c, r + 1)
                start = idx
            stack.append((start, h))

    return best_rect, max_area

def draw_matches_visualization(
    img_ref: np.ndarray,
    img_mov: np.ndarray,
    kp_ref: List,
    kp_mov: List,
    matches: List,
    inliers_mask: Optional[np.ndarray] = None,
    max_draw: int = 120,
    inliers_only: bool = False
) -> np.ndarray:
    """Renders pixel-sharp side-by-side match visualization."""
    h1, w1 = img_mov.shape[:2]
    h2, w2 = img_ref.shape[:2]

    out_h = max(h1, h2)
    out_w = w1 + w2

    vis = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    vis[:h1, :w1] = img_mov
    vis[:h2, w1:w1+w2] = img_ref

    if inliers_mask is not None:
        mask_flat = inliers_mask.ravel().tolist()
    else:
        mask_flat = [1] * len(matches)

    step = max(1, len(matches) // max_draw)
    for idx in range(0, len(matches), step):
        m = matches[idx]
        is_inlier = bool(mask_flat[idx]) if idx < len(mask_flat) else False

        if inliers_only and not is_inlier:
            continue

        pt_mov = tuple(map(int, kp_mov[m.queryIdx].pt))
        pt_ref = (int(kp_ref[m.trainIdx].pt[0]) + w1, int(kp_ref[m.trainIdx].pt[1]))

        color = (16, 185, 129) if is_inlier else (239, 68, 68)  # Green inlier, Red outlier
        thickness = 2 if is_inlier else 1

        cv2.circle(vis, pt_mov, 3, color, -1)
        cv2.circle(vis, pt_ref, 3, color, -1)
        cv2.line(vis, pt_mov, pt_ref, color, thickness, cv2.LINE_AA)

    return vis

def generate_footprint_visualization(
    ref_mask: np.ndarray,
    warped_mov_mask: np.ndarray
) -> np.ndarray:
    """
    Generates high-contrast color footprint map:
    - Green: Valid Common Footprint
    - Amber / Orange: Reference-Only Extent
    - Magenta / Pink: Moving-Image-Only Extent
    - Dark Navy: Invalid Outside Area
    """
    H, W = ref_mask.shape
    vis = np.zeros((H, W, 3), dtype=np.uint8)
    vis[:] = [15, 23, 42]  # Dark navy background

    ref_bool = ref_mask > 0
    mov_bool = warped_mov_mask > 0

    common_bool = ref_bool & mov_bool
    ref_only_bool = ref_bool & (~mov_bool)
    mov_only_bool = mov_bool & (~ref_bool)

    vis[common_bool] = [16, 185, 129]    # Emerald Green (Common)
    vis[ref_only_bool] = [245, 158, 11]  # Amber (Ref Only)
    vis[mov_only_bool] = [217, 70, 239]  # Magenta (Mov Only)

    return vis

def generate_checkerboard(
    img_a: np.ndarray,
    img_b: np.ndarray,
    block_size: int = 40
) -> np.ndarray:
    """Builds alternating checkerboard comparison to inspect edge alignment continuity."""
    h = min(img_a.shape[0], img_b.shape[0])
    w = min(img_a.shape[1], img_b.shape[1])
    out = np.zeros((h, w, 3), dtype=np.uint8)

    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            y_end = min(y + block_size, h)
            x_end = min(x + block_size, w)
            block_idx = (y // block_size) + (x // block_size)
            if block_idx % 2 == 0:
                out[y:y_end, x:x_end] = img_a[y:y_end, x:x_end]
            else:
                out[y:y_end, x:x_end] = img_b[y:y_end, x:x_end]

    return out

def run_temporal_registration(
    img_ref: Image.Image,
    img_mov: Image.Image,
    ref_label: str = "Pre-Event (t0)",
    mov_label: str = "Post-Event (t1)",
    transform_model: str = "Partial Affine (Translation + Rotation + Scale)",
    detector_type: str = "SIFT",
    lowe_ratio: float = 0.75,
    ransac_thresh: float = 4.0,
    min_inliers_req: int = 15,
    min_overlap_req_pct: float = 25.0
) -> RegistrationResult:
    """
    Executes the complete, verifiable temporal registration pipeline.
    """
    t0 = time.time()

    arr_ref = np.array(img_ref.convert("RGB"))
    arr_mov = np.array(img_mov.convert("RGB"))

    h_ref, w_ref = arr_ref.shape[:2]
    h_mov, w_mov = arr_mov.shape[:2]

    # Validity masks for original images (255 where valid non-black data exists)
    # Check for empty/padded pixels
    ref_gray = cv2.cvtColor(arr_ref, cv2.COLOR_RGB2GRAY)
    mov_gray = cv2.cvtColor(arr_mov, cv2.COLOR_RGB2GRAY)
    ref_valid_mask = np.where(ref_gray > 0, 255, 0).astype(np.uint8)
    mov_valid_mask = np.where(mov_gray > 0, 255, 0).astype(np.uint8)

    # If completely valid (normal photo with non-zero pixels everywhere), fill 255
    if (ref_valid_mask == 255).mean() > 0.99:
        ref_valid_mask[:] = 255
    if (mov_valid_mask == 255).mean() > 0.99:
        mov_valid_mask[:] = 255

    # 1. Feature Detection and Matching
    active_det, kp_ref, kp_mov, raw_matches, ratio_matches = extract_and_match(
        arr_ref, arr_mov,
        detector_type=detector_type,
        lowe_ratio=lowe_ratio,
        n_features=3000
    )

    quality_warnings: List[str] = []

    if len(ratio_matches) < 4:
        quality_warnings.append(f"Insufficient landmark matches ({len(ratio_matches)} found). Scene may lack visual texture.")
        # Return failed result structure
        diag = RegistrationDiagnostics(
            reference_name=ref_label, moving_name=mov_label,
            ref_shape=arr_ref.shape, mov_shape=arr_mov.shape,
            detector=active_det, transform_model=transform_model,
            num_keypoints_ref=len(kp_ref), num_keypoints_mov=len(kp_mov),
            num_raw_matches=len(raw_matches), num_ratio_matches=len(ratio_matches),
            num_inliers=0, inlier_ratio=0.0,
            reprojection_error_median=999.0, reprojection_error_p90=999.0,
            spatial_spread_score=0.0, transformation_matrix=None,
            valid_overlap_pct_ref=0.0, valid_overlap_pct_mov=0.0,
            crop_rect=(0, 0, min(w_ref, w_mov), min(h_ref, h_mov)),
            crop_dimensions=(min(w_ref, w_mov), min(h_ref, h_mov)),
            retained_footprint_pct=0.0,
            quality_passed=False, quality_warnings=quality_warnings,
            processing_time_s=time.time() - t0
        )
        # Fallback crop
        cw, ch = min(w_ref, w_mov), min(h_ref, h_mov)
        return RegistrationResult(
            success=False, diagnostics=diag,
            ref_orig=arr_ref, mov_orig=arr_mov,
            warped_mov=arr_mov[:ch, :cw],
            ref_valid_mask=ref_valid_mask, warped_mov_valid_mask=mov_valid_mask[:ch, :cw],
            common_valid_mask=np.zeros((ch, cw), dtype=np.uint8),
            ref_cropped=arr_ref[:ch, :cw], mov_cropped=arr_mov[:ch, :cw],
            mask_cropped=np.zeros((ch, cw), dtype=np.uint8)
        )

    # 2. Geometric Verification via RANSAC
    pts_mov = np.float32([kp_mov[m.queryIdx].pt for m in ratio_matches])
    pts_ref = np.float32([kp_ref[m.trainIdx].pt for m in ratio_matches])

    is_homography = "homography" in transform_model.lower()
    M, inliers = estimate_geometric_transform(
        pts_mov, pts_ref,
        transform_model=transform_model,
        ransac_thresh=ransac_thresh
    )

    if M is None or inliers is None:
        quality_warnings.append("RANSAC geometric verification failed to estimate a valid transformation.")
        diag = RegistrationDiagnostics(
            reference_name=ref_label, moving_name=mov_label,
            ref_shape=arr_ref.shape, mov_shape=arr_mov.shape,
            detector=active_det, transform_model=transform_model,
            num_keypoints_ref=len(kp_ref), num_keypoints_mov=len(kp_mov),
            num_raw_matches=len(raw_matches), num_ratio_matches=len(ratio_matches),
            num_inliers=0, inlier_ratio=0.0,
            reprojection_error_median=999.0, reprojection_error_p90=999.0,
            spatial_spread_score=0.0, transformation_matrix=None,
            valid_overlap_pct_ref=0.0, valid_overlap_pct_mov=0.0,
            crop_rect=(0, 0, min(w_ref, w_mov), min(h_ref, h_mov)),
            crop_dimensions=(min(w_ref, w_mov), min(h_ref, h_mov)),
            retained_footprint_pct=0.0,
            quality_passed=False, quality_warnings=quality_warnings,
            processing_time_s=time.time() - t0
        )
        cw, ch = min(w_ref, w_mov), min(h_ref, h_mov)
        return RegistrationResult(
            success=False, diagnostics=diag,
            ref_orig=arr_ref, mov_orig=arr_mov,
            warped_mov=arr_mov[:ch, :cw],
            ref_valid_mask=ref_valid_mask, warped_mov_valid_mask=mov_valid_mask[:ch, :cw],
            common_valid_mask=np.zeros((ch, cw), dtype=np.uint8),
            ref_cropped=arr_ref[:ch, :cw], mov_cropped=arr_mov[:ch, :cw],
            mask_cropped=np.zeros((ch, cw), dtype=np.uint8)
        )

    # 3. Compute Metrics and Residuals
    inliers_bool = inliers.ravel() == 1
    num_inliers = int(inliers_bool.sum())
    inlier_ratio = float(num_inliers / len(ratio_matches)) if len(ratio_matches) > 0 else 0.0

    inlier_pts_mov = pts_mov[inliers_bool]
    inlier_pts_ref = pts_ref[inliers_bool]

    med_res, p90_res = compute_reprojection_residuals(inlier_pts_mov, inlier_pts_ref, M, is_homography)
    spread_score = compute_spatial_spread_score(inlier_pts_ref, (h_ref, w_ref))

    # Inspect matrix plausibility
    matrix_warnings = check_transformation_plausibility(M, is_homography)
    quality_warnings.extend(matrix_warnings)

    if spread_score < 0.06:
        quality_warnings.append(f"Inliers clustered in narrow corridor (spread: {spread_score*100:.1f}%); alignment may be unconstrained elsewhere.")

    if num_inliers < min_inliers_req:
        quality_warnings.append(f"Inlier count ({num_inliers}) below configured safety gate ({min_inliers_req}).")

    if inlier_ratio < 0.20:
        quality_warnings.append(f"Low inlier ratio ({inlier_ratio*100:.1f}%). High contamination from landscape changes or clouds.")

    if med_res > 3.8:
        quality_warnings.append(f"High median reprojection error ({med_res:.2f} px); residual sub-pixel misalignment expected.")

    # 4. Warp Moving Image and Validity Mask into Reference Frame
    if not is_homography:
        warped_mov = cv2.warpAffine(
            arr_mov, M, (w_ref, h_ref),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
        # CRITICAL: Nearest-Neighbor for validity mask to prevent black padding leakage
        warped_mov_valid_mask = cv2.warpAffine(
            mov_valid_mask, M, (w_ref, h_ref),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
    else:
        warped_mov = cv2.warpPerspective(
            arr_mov, M, (w_ref, h_ref),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
        warped_mov_valid_mask = cv2.warpPerspective(
            mov_valid_mask, M, (w_ref, h_ref),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )

    # 5. Compute Common Valid Footprint
    common_valid_mask = cv2.bitwise_and(ref_valid_mask, warped_mov_valid_mask)

    total_ref_pixels = float(np.count_nonzero(ref_valid_mask))
    total_mov_pixels = float(np.count_nonzero(mov_valid_mask))
    total_common_pixels = float(np.count_nonzero(common_valid_mask))

    overlap_pct_ref = (total_common_pixels / (total_ref_pixels + 1e-6)) * 100.0
    overlap_pct_mov = (total_common_pixels / (total_mov_pixels + 1e-6)) * 100.0

    if overlap_pct_ref < min_overlap_req_pct:
        quality_warnings.append(f"Valid overlap ({overlap_pct_ref:.1f}%) below minimum requirement ({min_overlap_req_pct:.1f}%).")

    # 6. Derive Maximal Axis-Aligned Common Rectangle Crop
    crop_rect, crop_area = find_largest_inscribed_rectangle(common_valid_mask)
    xmin, ymin, xmax, ymax = crop_rect

    crop_w = max(1, xmax - xmin)
    crop_h = max(1, ymax - ymin)

    ref_cropped = arr_ref[ymin:ymax, xmin:xmax]
    mov_cropped = warped_mov[ymin:ymax, xmin:xmax]
    mask_cropped = common_valid_mask[ymin:ymax, xmin:xmax]

    retained_pct = (crop_area / (total_ref_pixels + 1e-6)) * 100.0

    quality_passed = len(quality_warnings) == 0

    diag = RegistrationDiagnostics(
        reference_name=ref_label,
        moving_name=mov_label,
        ref_shape=arr_ref.shape,
        mov_shape=arr_mov.shape,
        detector=active_det,
        transform_model=transform_model,
        num_keypoints_ref=len(kp_ref),
        num_keypoints_mov=len(kp_mov),
        num_raw_matches=len(raw_matches),
        num_ratio_matches=len(ratio_matches),
        num_inliers=num_inliers,
        inlier_ratio=round(inlier_ratio, 4),
        reprojection_error_median=round(med_res, 2),
        reprojection_error_p90=round(p90_res, 2),
        spatial_spread_score=round(spread_score, 4),
        transformation_matrix=M,
        valid_overlap_pct_ref=round(overlap_pct_ref, 2),
        valid_overlap_pct_mov=round(overlap_pct_mov, 2),
        crop_rect=crop_rect,
        crop_dimensions=(crop_w, crop_h),
        retained_footprint_pct=round(retained_pct, 2),
        quality_passed=quality_passed,
        quality_warnings=quality_warnings,
        processing_time_s=round(time.time() - t0, 3)
    )

    # 7. Generate Visual Diagnostics
    inlier_vis = draw_matches_visualization(arr_ref, arr_mov, kp_ref, kp_mov, ratio_matches, inliers, inliers_only=True)
    all_vis = draw_matches_visualization(arr_ref, arr_mov, kp_ref, kp_mov, ratio_matches, inliers, inliers_only=False)
    footprint_vis = generate_footprint_visualization(ref_valid_mask, warped_mov_valid_mask)

    return RegistrationResult(
        success=True,
        diagnostics=diag,
        ref_orig=arr_ref,
        mov_orig=arr_mov,
        warped_mov=warped_mov,
        ref_valid_mask=ref_valid_mask,
        warped_mov_valid_mask=warped_mov_valid_mask,
        common_valid_mask=common_valid_mask,
        ref_cropped=ref_cropped,
        mov_cropped=mov_cropped,
        mask_cropped=mask_cropped,
        inlier_matches_vis=inlier_vis,
        all_matches_vis=all_vis,
        footprint_vis=footprint_vis
    )

def run_aligned_common_change_detection(
    ref_crop: np.ndarray,
    mov_crop: np.ndarray,
    valid_mask: np.ndarray,
    threshold: float = 90.0
) -> Tuple[np.ndarray, np.ndarray, float, int, int]:
    """
    Computes change detection STRICTLY inside the valid common crop.
    Masks out invalid black padding or unaligned marginal regions.
    Returns: (change_mask, diff_norm, changed_pct, changed_pixel_count, total_valid_pixels)
    """
    a = ref_crop.astype(np.float32)
    b = mov_crop.astype(np.float32)

    diff = np.sqrt(np.sum((a - b) ** 2, axis=2))

    # Mask valid data only
    valid_bool = valid_mask > 0
    total_valid = int(np.count_nonzero(valid_bool))

    if total_valid == 0:
        return np.zeros_like(diff, dtype=np.uint8), diff, 0.0, 0, 0

    change_bool = (diff > threshold) & valid_bool
    change_mask = (change_bool.astype(np.uint8)) * 255
    changed_pixels = int(np.count_nonzero(change_bool))
    changed_pct = (changed_pixels / float(total_valid)) * 100.0

    return change_mask, diff, changed_pct, changed_pixels, total_valid
