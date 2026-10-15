"""Analytical Computer Vision & Homography Stitcher Component.

Integrates classical feature-based stitching from 'gemini-code.py' / 'extras/cv_stitcher.py':
- SIFT (Scale-Invariant Feature Transform) keypoint extraction
- FLANN KD-Tree Nearest Neighbor Matching
- Lowe's Ratio Distance Pruning
- RANSAC Perspective Homography Estimation & Warping
"""

from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def render_tab_cv_stitcher():
    st.markdown(
        """
        <div class="section-header">
            <div class="section-title">📐 Analytical SIFT & RANSAC Homography Engine</div>
            <div>
                <span class="tech-badge badge-cyan">SIFT Detector</span>
                <span class="tech-badge badge-emerald">FLANN KD-Tree</span>
                <span class="tech-badge badge-purple">RANSAC Homography</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Classical geometric computer vision pipeline. Detects scale-invariant visual keypoints, matches visual feature descriptors
        across overlapping adjacent satellite chips, rejects outlier correspondences via RANSAC, and calculates the 3×3 projective
        homography matrix $\mathbf{H}$ to warp and stitch tiles into an aligned scene.
        """
    )

    p_left = ROOT_DIR / "tile_left.jpg"
    p_right = ROOT_DIR / "tile_right.jpg"

    col_ctrl, col_prev = st.columns([1, 2])

    with col_ctrl:
        st.markdown("### ⚙️ Geometric Parameters")
        lowe_ratio = st.slider("Lowe's Ratio Distance Gate", min_value=0.50, max_value=0.90, value=0.75, step=0.05,
                               help="Rejects ambiguous matches where closest neighbor distance is too close to second-nearest.")
        ransac_thresh = st.slider("RANSAC Inlier Reprojection Threshold (px)", min_value=1.0, max_value=10.0, value=5.0, step=0.5)
        min_inlier_pct = st.slider("Safety Inlier Ratio Rejection Gate (%)", min_value=10, max_value=50, value=25)

        run_cv_btn = st.button("🚀 Detect Keypoints & Solve Homography", key="btn_run_cv_stitch")

    with col_prev:
        c1, c2 = st.columns(2)
        with c1:
            if p_left.exists():
                st.image(Image.open(p_left), caption="Reference Spatial Tile (Left)", use_container_width=True)
        with c2:
            if p_right.exists():
                st.image(Image.open(p_right), caption="Adjacent Spatial Tile (Right)", use_container_width=True)

    if not run_cv_btn:
        st.info("Click 'Detect Keypoints & Solve Homography' to execute SIFT extraction and perspective warping.")
        return

    with st.spinner("Executing SIFT detector and FLANN KD-Tree matching..."):
        if not p_left.exists() or not p_right.exists():
            st.error("tile_left.jpg or tile_right.jpg not found in workspace.")
            return

        img1 = cv2.imread(str(p_left))
        img2 = cv2.imread(str(p_right))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(gray1, None)
        kp2, des2 = sift.detectAndCompute(gray2, None)

        # FLANN matching
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)

        matches = flann.knnMatch(des1, des2, k=2)

        good_matches = []
        for m, n in matches:
            if m.distance < lowe_ratio * n.distance:
                good_matches.append(m)

        if len(good_matches) < 4:
            st.error(f"Insufficient good matches ({len(good_matches)} < 4) to estimate homography.")
            return

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, ransac_thresh)

        if H is None:
            st.error("Homography estimation failed (degenerate point configuration).")
            return

        inliers = int(mask.sum())
        total_matches = len(good_matches)
        inlier_ratio = (inliers / total_matches) * 100.0

        # Telemetry KPIs
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total SIFT Keypoints", f"{len(kp1) + len(kp2):,}")
        with m2:
            st.metric("Lowe's Pruned Matches", f"{total_matches:,}")
        with m3:
            st.metric("RANSAC Inliers", f"{inliers:,}")
        with m4:
            status_color = "normal" if inlier_ratio >= min_inlier_pct else "inverse"
            st.metric("Inlier Ratio", f"{inlier_ratio:.1f}%", delta="Verified" if inlier_ratio >= min_inlier_pct else "Low Confidence", delta_color=status_color)

        # Draw matches visualization
        match_draw = cv2.drawMatches(
            cv2.cvtColor(img1, cv2.COLOR_BGR2RGB), kp1,
            cv2.cvtColor(img2, cv2.COLOR_BGR2RGB), kp2,
            good_matches[:50], None,
            matchColor=(0, 240, 255),
            singlePointColor=(16, 185, 129),
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )

        st.subheader("1. Inlier Correspondence Lines (Top 50 Verified Matches)")
        st.image(match_draw, use_container_width=True)

        # Warp perspective and stitch
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]

        pts2 = np.float32([[0, 0], [0, h2], [w2, h2], [w2, 0]]).reshape(-1, 1, 2)
        pts2_transformed = cv2.perspectiveTransform(pts2, H)
        pts1 = np.float32([[0, 0], [0, h1], [w1, h1], [w1, 0]]).reshape(-1, 1, 2)

        all_pts = np.concatenate((pts1, pts2_transformed), axis=0)
        [x_min, y_min] = np.int32(all_pts.min(axis=0).ravel() - 0.5)
        [x_max, y_max] = np.int32(all_pts.max(axis=0).ravel() + 0.5)

        translation_dist = [-x_min, -y_min]
        H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

        stitched_w = min(x_max - x_min, 2400)
        stitched_h = min(y_max - y_min, 2400)

        output_img = cv2.warpPerspective(img2, H_translation.dot(H), (stitched_w, stitched_h))
        output_img[translation_dist[1]:h1 + translation_dist[1], translation_dist[0]:w1 + translation_dist[0]] = img1

        st.subheader("2. Final Seamless Homography-Stitched Mosaic")
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), caption=f"Stitched Output Canvas: {stitched_w} × {stitched_h} px", use_container_width=True)
