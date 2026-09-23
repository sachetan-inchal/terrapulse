import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Ensure standard streams handle Unicode gracefully on Windows
if sys.platform == 'win32':
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def generate_sample_tiles(path1='tile_left.jpg', path2='tile_right.jpg'):
    """Generates two overlapping synthetic aerial/landscape tiles for testing."""
    print("-> No input images provided/found. Generating synthetic sample tiles for demonstration...")
    np.random.seed(42)
    h, w = 600, 900
    base = np.zeros((h, w, 3), dtype=np.uint8)

    # Background terrain (meadow/field tone)
    base[:] = (65, 120, 70)

    # River / Road curve
    pts_road = np.array([[0, 280], [300, 310], [600, 260], [900, 290]], np.int32)
    cv2.polylines(base, [pts_road], isClosed=False, color=(50, 50, 60), thickness=36)
    cv2.polylines(base, [pts_road], isClosed=False, color=(240, 240, 240), thickness=3, lineType=cv2.LINE_AA)

    # River water
    pts_river = np.array([[150, 0], [280, 200], [420, 400], [490, 600]], np.int32)
    cv2.polylines(base, [pts_river], isClosed=False, color=(180, 110, 40), thickness=48)

    # Buildings / Agricultural fields / Structures (giving rich SIFT keypoints)
    cv2.rectangle(base, (60, 60), (220, 220), (140, 175, 195), -1)
    cv2.rectangle(base, (80, 80), (140, 140), (80, 90, 140), -1)
    cv2.rectangle(base, (150, 100), (200, 180), (120, 70, 70), -1)

    cv2.rectangle(base, (320, 70), (520, 230), (110, 160, 130), -1)
    for x in range(330, 510, 25):
        cv2.line(base, (x, 75), (x, 225), (70, 110, 80), 2)

    cv2.rectangle(base, (580, 80), (820, 240), (130, 140, 180), -1)
    cv2.rectangle(base, (610, 110), (700, 200), (90, 110, 150), -1)
    cv2.rectangle(base, (720, 120), (790, 180), (60, 80, 120), -1)

    cv2.rectangle(base, (220, 380), (450, 560), (125, 150, 165), -1)
    cv2.circle(base, (330, 470), 50, (40, 180, 220), -1)
    cv2.circle(base, (650, 430), 65, (70, 190, 110), -1)

    # Rich feature textures (trees, field markings)
    for _ in range(350):
        rx = np.random.randint(20, w - 20)
        ry = np.random.randint(20, h - 20)
        rc = (int(np.random.randint(30, 80)), int(np.random.randint(80, 170)), int(np.random.randint(40, 90)))
        cv2.circle(base, (rx, ry), np.random.randint(3, 10), rc, -1)

    # Add realistic sensor noise and subtle lighting
    noise = np.random.randint(0, 25, base.shape, dtype=np.uint8)
    base = cv2.add(base, noise)

    # Cut into two tiles with 40% overlap
    # Tile 1 covers [0 to 580]
    tile_left = base[:, :580]
    # Tile 2 covers [360 to 900]
    tile_right = base[:, 360:]

    cv2.imwrite(path1, tile_left)
    cv2.imwrite(path2, tile_right)
    print(f"-> Created sample tiles: '{path1}' and '{path2}'")
    return path1, path2


def robust_tile_stitch(img1_path, img2_path, output_path='stitched_result.jpg'):
    print(f"Loading images:\n 1. {img1_path}\n 2. {img2_path}")
    
    # Read images in color
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    
    if img1 is None or img2 is None:
        print("[ERROR] Could not load one or both images. Check file paths.")
        return None

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # 1. Initialize SIFT (Scale-Invariant Feature Transform)
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    print(f"-> SIFT Features detected: Image 1: {len(kp1)} | Image 2: {len(kp2)}")

    if des1 is None or des2 is None or len(kp1) < 5 or len(kp2) < 5:
        print("[ERROR] Not enough features found in images for matching.")
        return None

    # 2. FLANN-based Matcher (Fast Library for Approximate Nearest Neighbors)
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(des1, des2, k=2)

    # 3. Apply Lowe's Ratio Test to eliminate ambiguous matches
    good_matches = []
    for pair in matches:
        if len(pair) == 2:
            m, n = pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

    print(f"-> Matches passing Lowe's ratio test: {len(good_matches)}")

    if len(good_matches) < 10:
        print("[WARNING] Too few good matches. These images might not overlap or have too much seasonal drift.")
        return None

    # 4. Extract point coordinates for Homography calculation
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 5. Compute Homography matrix with RANSAC outlier rejection
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    
    if H is None:
        print("[ERROR] RANSAC failed to compute a homography matrix.")
        return None

    matches_mask = mask.ravel().tolist()
    inlier_count = sum(matches_mask)
    inlier_ratio = inlier_count / len(matches_mask)
    
    print(f"-> RANSAC Evaluation: {inlier_count}/{len(matches_mask)} inliers kept ({inlier_ratio*100:.1f}% quality score)")

    # Safety gate: reject low-confidence alignments
    if inlier_ratio < 0.25:
        print("[ERROR] Alignment Rejected: Inlier ratio is too low for a reliable mathematical stitch.")
        return None

    # 6. Full-bounding-box Warp and Stitch images together
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    # Calculate warped corners of img1 mapped onto img2 frame
    corners1 = np.float32([[0, 0], [0, h1], [w1, h1], [w1, 0]]).reshape(-1, 1, 2)
    warped_corners1 = cv2.perspectiveTransform(corners1, H)
    corners2 = np.float32([[0, 0], [0, h2], [w2, h2], [w2, 0]]).reshape(-1, 1, 2)
    all_corners = np.concatenate((warped_corners1, corners2), axis=0)

    # Find the bounding coordinates
    [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

    # Offset translation matrix to prevent negative coordinate clipping
    translation = [-x_min, -y_min]
    H_trans = np.array([
        [1, 0, translation[0]],
        [0, 1, translation[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    canvas_w = int(x_max - x_min)
    canvas_h = int(y_max - y_min)

    # Warp img1 with compensation for the translation
    stitched_canvas = cv2.warpPerspective(img1, H_trans @ H, (canvas_w, canvas_h))

    # Place img2 onto canvas using translation offset
    ty, tx = translation[1], translation[0]
    sub_canvas = stitched_canvas[ty:ty+h2, tx:tx+w2]
    
    # Blend/overlay: where img2 has content, place it; in overlap, smoothly blend
    mask2 = np.any(img2 > 0, axis=-1)
    mask_canvas = np.any(sub_canvas > 0, axis=-1)
    overlap = mask2 & mask_canvas
    
    # Feather/average in overlap area to avoid harsh seam
    sub_canvas[mask2 & ~overlap] = img2[mask2 & ~overlap]
    if np.any(overlap):
        sub_canvas[overlap] = (0.5 * sub_canvas[overlap] + 0.5 * img2[overlap]).astype(np.uint8)
    
    stitched_canvas[ty:ty+h2, tx:tx+w2] = sub_canvas

    # Save output image
    cv2.imwrite(output_path, stitched_canvas)
    print(f"[OK] Mosaic successfully stitched and saved to: {output_path} (Resolution: {canvas_w}x{canvas_h})")

    # 7. Visualize Results
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Draw top matching lines to visually verify correctness
    match_visualization = cv2.drawMatches(img1, kp1, img2, kp2, good_matches[:30], None, 
                                          matchesMask=matches_mask[:30], flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    
    axes[0].imshow(cv2.cvtColor(match_visualization, cv2.COLOR_BGR2RGB))
    axes[0].set_title(f"RANSAC Feature Matches (Inliers: {inlier_ratio*100:.1f}%)")
    axes[0].axis('off')

    axes[1].imshow(cv2.cvtColor(stitched_canvas, cv2.COLOR_BGR2RGB))
    axes[1].set_title("Stitched Mosaic Result")
    axes[1].axis('off')

    plt.tight_layout()
    print("-> Rendering visualization window...")
    try:
        plt.show()
    except Exception as e:
        print(f"[INFO] Interactive GUI display skipped ({e}). Result image is saved at: {output_path}")

    return stitched_canvas


if __name__ == "__main__":
    # Check command line arguments: python gemini-code.py <img1> <img2>
    if len(sys.argv) >= 3:
        img1_file = sys.argv[1]
        img2_file = sys.argv[2]
    else:
        # Check if default test images exist in the working directory
        img1_file = 'tile_left.jpg'
        img2_file = 'tile_right.jpg'
        if not (os.path.exists(img1_file) and os.path.exists(img2_file)):
            generate_sample_tiles(img1_file, img2_file)

    robust_tile_stitch(img1_file, img2_file)
