"""
TerraPulse Unified Command-Line Interface (CLI).

Provides unified command-line entry points for:
- Multi-spectral radiometric processing (NDVI, NDWI, NDBI, SCL)
- Bi-temporal change detection and transition matrix analysis
- Autonomous geospatial OSINT intelligence dossier generation
- Illumination-invariant feature stitching
"""

import argparse
import sys
import os
import cv2
import numpy as np

# Ensure standard streams handle Unicode gracefully on Windows
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from terrapulse.multispectral import RadiometricProcessor
from terrapulse.change_detection import BiTemporalChangeDetector
from terrapulse.osint_engine import GeospatialOSINTEngine
from terrapulse.robust_matcher import RobustGeospatialMatcher


def run_multispectral_cli(args):
    """Processes radiometric indices and false-color composites."""
    print("🛰️ [TerraPulse] Executing Multi-Spectral Radiometric Processor...")
    
    # Check if sample or explicit images are provided
    if args.input:
        img = cv2.imread(args.input)
        if img is None:
            print(f"[ERROR] Could not read input image: {args.input}")
            sys.exit(1)
        # For a standard 3-channel image, treat G as Green, R as Red, and synthesized NIR from R/G
        b, g, r = cv2.split(img)
        # Synthesize NIR proxy for demonstration when raw multi-spectral COG is not passed
        nir = np.clip(g.astype(np.float32) * 1.35 + r.astype(np.float32) * 0.2, 0, 255).astype(np.uint8)
        bands = {"B02": b, "B03": g, "B04": r, "B08": nir}
    else:
        print("[INFO] Generating synthetic Sentinel-2 multi-spectral scene (512x512)...")
        np.random.seed(42)
        h, w = 512, 512
        r = np.random.randint(30, 180, (h, w), dtype=np.uint8)
        g = np.random.randint(40, 200, (h, w), dtype=np.uint8)
        b = np.random.randint(20, 150, (h, w), dtype=np.uint8)
        nir = np.random.randint(50, 240, (h, w), dtype=np.uint8)
        bands = {"B02": b, "B03": g, "B04": r, "B08": nir}

    indices = RadiometricProcessor.process_all_indices(bands)
    print("\n✅ Radiometric Surface Telemetry:")
    for k, v in indices.statistics.items():
        print(f"  • {k}: {v}")

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        ndvi_rgb = RadiometricProcessor.colorize_index(indices.ndvi, "ndvi")
        ndwi_rgb = RadiometricProcessor.colorize_index(indices.ndwi, "ndwi")
        ndbi_rgb = RadiometricProcessor.colorize_index(indices.ndbi, "ndbi")
        cir_composite = RadiometricProcessor.generate_false_color_composite(bands, "cir")

        cv2.imwrite(os.path.join(args.output_dir, "ndvi_heatmap.png"), cv2.cvtColor(ndvi_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(args.output_dir, "ndwi_heatmap.png"), cv2.cvtColor(ndwi_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(args.output_dir, "ndbi_heatmap.png"), cv2.cvtColor(ndbi_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(args.output_dir, "cir_composite.png"), cv2.cvtColor(cir_composite, cv2.COLOR_RGB2BGR))
        print(f"\n📁 Exported radiometric layers to: '{args.output_dir}'")


def run_change_cli(args):
    """Executes bi-temporal change detection between t1 and t2."""
    print("🛰️ [TerraPulse] Executing Bi-Temporal Change Detection Engine...")
    
    img1 = cv2.imread(args.t1) if args.t1 and os.path.exists(args.t1) else None
    img2 = cv2.imread(args.t2) if args.t2 and os.path.exists(args.t2) else None

    if img1 is None or img2 is None:
        print("[INFO] Sample inputs not found. Simulating temporal urban encroachment...")
        img1 = np.full((400, 600, 3), (40, 140, 50), dtype=np.uint8)  # Forest/meadow
        cv2.rectangle(img1, (100, 100), (200, 200), (180, 100, 40), -1)  # Lake
        img2 = img1.copy()
        # Urban expansion at t2
        cv2.rectangle(img2, (250, 80), (450, 320), (180, 180, 190), -1)  # New concrete district
        cv2.rectangle(img2, (150, 100), (200, 200), (90, 110, 100), -1)  # Partially drained lake

    result = BiTemporalChangeDetector.detect_spectral_change(img1, img2, threshold_mode=args.threshold)
    print("\n✅ Change Detection Telemetry:")
    for k, v in result.transition_summary.items():
        print(f"  • {k}: {v}")

    if result.transition_matrix:
        print("\n📊 Land-Cover Transition Summary:")
        print(result.transition_matrix.to_markdown_table())

    if args.output:
        dashboard = BiTemporalChangeDetector.render_change_dashboard(img1, img2, result)
        cv2.imwrite(args.output, dashboard)
        print(f"\n📁 Saved 4-panel change validation dashboard to: '{args.output}'")


def run_osint_cli(args):
    """Synthesizes an OSINT intelligence report from change metrics."""
    print("🛰️ [TerraPulse] Synthesizing Autonomous OSINT Intelligence Dossier...")
    report = GeospatialOSINTEngine.analyze_change_intelligence(
        region_query=args.region,
        bbox=[float(x) for x in args.bbox.split(",")] if args.bbox else [77.5, 12.8, 77.8, 13.1],
        timeframe=args.timeframe,
        total_area_ha=args.area,
        deforestation_ha=args.deforestation,
        urban_sprawl_ha=args.urban,
        water_loss_ha=args.water,
        revegetation_ha=args.revegetation,
    )

    print(f"\n✅ Ecological Vulnerability Index: {report.ecological_vulnerability_index:.1f}/100")
    print(f"✅ Threat Status: {report.threat_level.value}\n")

    if args.json:
        print(report.to_json())
    else:
        print(report.to_markdown())

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            if args.output_file.endswith(".json"):
                f.write(report.to_json())
            else:
                f.write(report.to_markdown())
        print(f"\n📁 Saved OSINT dossier to: '{args.output_file}'")


def run_stitch_cli(args):
    """Executes robust illumination-invariant stitching between two tiles."""
    print("🛰️ [TerraPulse] Executing Illumination-Invariant Geospatial Matcher...")
    img1 = cv2.imread(args.left) if args.left and os.path.exists(args.left) else None
    img2 = cv2.imread(args.right) if args.right and os.path.exists(args.right) else None

    if img1 is None or img2 is None:
        print("[ERROR] Please provide valid --left and --right image paths.")
        sys.exit(1)

    result = RobustGeospatialMatcher.match_and_align(img1, img2)
    print(f"Status: {result.status_message}")
    if result.is_valid and result.stitched_image is not None and args.output:
        cv2.imwrite(args.output, result.stitched_image)
        print(f"📁 Stitched mosaic saved to: '{args.output}'")


def main():
    parser = argparse.ArgumentParser(
        prog="terrapulse",
        description="TerraPulse: Planetary-Scale Remote Sensing, Computer Vision & OSINT Platform"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available TerraPulse engines")

    # 1. Multi-spectral
    p_multi = subparsers.add_parser("multispectral", help="Radiometric index processing (NDVI, NDWI, NDBI, SCL)")
    p_multi.add_argument("--input", "-i", type=str, default="", help="Path to input optical image")
    p_multi.add_argument("--output-dir", "-o", type=str, default="radiometric_outputs", help="Output directory")

    # 2. Change Detection
    p_change = subparsers.add_parser("change", help="Bi-temporal change detection and transition matrix")
    p_change.add_argument("--t1", type=str, default="tile_left.jpg", help="Observation epoch t1")
    p_change.add_argument("--t2", type=str, default="tile_right.jpg", help="Observation epoch t2")
    p_change.add_argument("--threshold", type=str, default="otsu", choices=["otsu", "sigma"], help="Thresholding strategy")
    p_change.add_argument("--output", "-o", type=str, default="change_dashboard.jpg", help="Output path for change dashboard")

    # 3. OSINT
    p_osint = subparsers.add_parser("osint", help="Autonomous geospatial OSINT intelligence dossier")
    p_osint.add_argument("--region", "-r", type=str, default="Bengaluru", help="Study region or coordinate location")
    p_osint.add_argument("--bbox", type=str, default="77.5,12.8,77.8,13.1", help="Bounding box (min_lon,min_lat,max_lon,max_lat)")
    p_osint.add_argument("--timeframe", "-t", type=str, default="2020-01-01 to 2025-01-01", help="Observation date range")
    p_osint.add_argument("--area", type=float, default=250.0, help="Total area evaluated in hectares")
    p_osint.add_argument("--deforestation", type=float, default=18.4, help="Canopy loss in hectares")
    p_osint.add_argument("--urban", type=float, default=42.1, help="Urban encroachment in hectares")
    p_osint.add_argument("--water", type=float, default=6.2, help="Water loss in hectares")
    p_osint.add_argument("--revegetation", type=float, default=2.1, help="Revegetation in hectares")
    p_osint.add_argument("--json", action="store_true", help="Output in raw JSON format")
    p_osint.add_argument("--output-file", "-o", type=str, default="", help="Save report to file (.md or .json)")

    # 4. Stitch
    p_stitch = subparsers.add_parser("stitch", help="Illumination-invariant geospatial feature stitching")
    p_stitch.add_argument("--left", "-l", type=str, default="tile_left.jpg", help="Left tile path")
    p_stitch.add_argument("--right", "-r", type=str, default="tile_right.jpg", help="Right tile path")
    p_stitch.add_argument("--output", "-o", type=str, default="stitched_result.jpg", help="Output mosaic path")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "multispectral":
        run_multispectral_cli(args)
    elif args.command == "change":
        run_change_cli(args)
    elif args.command == "osint":
        run_osint_cli(args)
    elif args.command == "stitch":
        run_stitch_cli(args)


if __name__ == "__main__":
    main()
