"""Computer Vision, Feature Registration, and Mosaicking Engine."""
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def compute_sift_registration(
    img1_arr: np.ndarray,
    img2_arr: np.ndarray,
    lowe_ratio: float = 0.75,
    ransac_thresh: float = 5.0,
    min_inlier_ratio: float = 0.25
) -> Dict[str, Any]:
    """
    SIFT + FLANN + RANSAC homography estimation with safety verification gates.
    """
    gray1 = cv2.cvtColor(img1_arr, cv2.COLOR_RGB2GRAY) if img1_arr.ndim == 3 else img1_arr
    gray2 = cv2.cvtColor(img2_arr, cv2.COLOR_RGB2GRAY) if img2_arr.ndim == 3 else img2_arr

    sift = cv2.SIFT_create(nfeatures=2000)
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
        return {
            "status": "REJECTED_DEGENERATE_FEATURES",
            "method": "SIFT + RANSAC",
            "keypoints_detected": len(kp1) + len(kp2) if (kp1 and kp2) else 0,
            "matches_found": 0,
            "inliers_count": 0,
            "inlier_ratio_pct": 0.0,
            "reprojection_error_px": 999.0,
            "homography_matrix": None,
            "confidence": "LOW",
            "warning": "Insufficient feature keypoints detected in scene pair."
        }

    # FLANN KD-Tree Matcher
    flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
    matches = flann.knnMatch(des1, des2, k=2)

    good_matches = []
    for m_tuple in matches:
        if len(m_tuple) == 2:
            m, n = m_tuple
            if m.distance < lowe_ratio * n.distance:
                good_matches.append(m)

    if len(good_matches) < 4:
        return {
            "status": "REJECTED_LOW_MATCHES",
            "method": "SIFT + RANSAC",
            "keypoints_detected": len(kp1) + len(kp2),
            "matches_found": len(good_matches),
            "inliers_count": 0,
            "inlier_ratio_pct": 0.0,
            "reprojection_error_px": 999.0,
            "homography_matrix": None,
            "confidence": "LOW",
            "warning": "Fewer than 4 Lowe's pruned matches found."
        }

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, ransac_thresh)

    if H is None:
        return {
            "status": "REJECTED_HOMOGRAPHY_FAILED",
            "method": "SIFT + RANSAC",
            "keypoints_detected": len(kp1) + len(kp2),
            "matches_found": len(good_matches),
            "inliers_count": 0,
            "inlier_ratio_pct": 0.0,
            "reprojection_error_px": 999.0,
            "homography_matrix": None,
            "confidence": "LOW",
            "warning": "Homography solver returned degenerate matrix."
        }

    inliers = int(mask.sum())
    total_matches = len(good_matches)
    inlier_ratio = inliers / total_matches

    # Calculate actual mean reprojection error of inliers
    dst_pts_homo = np.pad(dst_pts.reshape(-1, 2), ((0, 0), (0, 1)), constant_values=1.0)
    projected = (H @ dst_pts_homo.T).T
    projected = projected[:, :2] / (projected[:, 2:] + 1e-8)
    errors = np.linalg.norm(src_pts.reshape(-1, 2) - projected, axis=1)
    inlier_errors = errors[mask.ravel().astype(bool)]
    mean_error = float(inlier_errors.mean()) if len(inlier_errors) > 0 else 0.0

    if inlier_ratio < min_inlier_ratio:
        return {
            "status": "REJECTED_LOW_INLIERS",
            "method": "SIFT + RANSAC",
            "keypoints_detected": len(kp1) + len(kp2),
            "matches_found": total_matches,
            "inliers_count": inliers,
            "inlier_ratio_pct": round(inlier_ratio * 100, 2),
            "reprojection_error_px": round(mean_error, 2),
            "homography_matrix": H.tolist(),
            "confidence": "LOW",
            "warning": f"Inlier ratio ({inlier_ratio*100:.1f}%) below minimum safety threshold ({min_inlier_ratio*100:.0f}%)."
        }

    return {
        "status": "SUCCESS",
        "method": "SIFT + RANSAC",
        "keypoints_detected": len(kp1) + len(kp2),
        "matches_found": total_matches,
        "inliers_count": inliers,
        "inlier_ratio_pct": round(inlier_ratio * 100, 2),
        "reprojection_error_px": round(mean_error, 2),
        "homography_matrix": H.tolist(),
        "confidence": "HIGH" if inlier_ratio >= 0.50 else "MODERATE",
        "warning": None
    }
