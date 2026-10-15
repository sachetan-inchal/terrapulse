"""
Bi-Temporal Change Detection & Land-Cover Transition Engine.

Implements Tier 2 academic remote sensing & computer vision capabilities:
- Multi-temporal spectral difference and normalized change vector analysis
- Adaptive Otsu and statistical (k-sigma) change thresholding
- Morphological noise suppression for remote sensing artifacts
- Quantitative land-cover transition matrices (Deforestation, Urban Sprawl, Hydrological loss)
- Ground-area quantification in hectares and square kilometers
- 4-panel visual change validation synthesis
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2


class LandCoverClass(IntEnum):
    WATER = 0
    DENSE_CANOPY = 1
    MODERATE_VEGETATION = 2
    BUILT_UP_URBAN = 3
    BARE_SOIL = 4


CLASS_NAMES = {
    LandCoverClass.WATER: "Water Body",
    LandCoverClass.DENSE_CANOPY: "Dense Canopy",
    LandCoverClass.MODERATE_VEGETATION: "Moderate Vegetation",
    LandCoverClass.BUILT_UP_URBAN: "Built-Up / Urban",
    LandCoverClass.BARE_SOIL: "Bare Soil / Barren",
}

CLASS_COLORS = {
    LandCoverClass.WATER: (40, 120, 240),             # Blue
    LandCoverClass.DENSE_CANOPY: (20, 160, 40),        # Forest Green
    LandCoverClass.MODERATE_VEGETATION: (130, 210, 80),# Light Green
    LandCoverClass.BUILT_UP_URBAN: (220, 70, 70),      # Crimson / Red
    LandCoverClass.BARE_SOIL: (210, 180, 110),         # Ochre / Tan
}


@dataclass
class LandCoverTransitionMatrix:
    """Quantitative class-to-class transitions between two temporal acquisitions."""
    matrix: np.ndarray  # [N_CLASSES, N_CLASSES] transition counts
    total_pixels: int
    deforestation_hectares: float
    urban_sprawl_hectares: float
    water_loss_hectares: float
    revegetation_hectares: float
    pixel_resolution_m: float = 10.0  # Default Sentinel-2 10m resolution

    def to_markdown_table(self) -> str:
        """Formats the transition matrix as a GitHub-flavored Markdown table."""
        lines = [
            "| Initial State (t₁) \\ Final State (t₂) | Water | Dense Canopy | Mod. Veg | Urban | Bare Soil |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]
        classes = list(LandCoverClass)
        for i, c_from in enumerate(classes):
            row_vals = []
            for j in range(len(classes)):
                count = self.matrix[i, j]
                pct = (count / max(1, self.total_pixels)) * 100.0
                row_vals.append(f"{pct:.2f}%")
            lines.append(f"| **{CLASS_NAMES[c_from]}** | " + " | ".join(row_vals) + " |")

        lines.append("")
        lines.append(f"- **Deforestation Alert**: {self.deforestation_hectares:.2f} ha ({self.deforestation_hectares / 100.0:.3f} km²)")
        lines.append(f"- **Urban Encroachment**: {self.urban_sprawl_hectares:.2f} ha ({self.urban_sprawl_hectares / 100.0:.3f} km²)")
        lines.append(f"- **Water Body Depletion**: {self.water_loss_hectares:.2f} ha ({self.water_loss_hectares / 100.0:.3f} km²)")
        lines.append(f"- **Revegetation / Canopy Growth**: {self.revegetation_hectares:.2f} ha ({self.revegetation_hectares / 100.0:.3f} km²)")
        return "\n".join(lines)


@dataclass
class ChangeDetectionResult:
    """Outcome of bi-temporal change detection pipeline."""
    difference_magnitude: np.ndarray
    binary_change_mask: np.ndarray
    change_heatmap_rgb: np.ndarray
    otsu_threshold: float
    mean_change_intensity: float
    changed_pixel_ratio: float  # Percentage of scene exhibiting change
    transition_summary: Dict[str, Any] = field(default_factory=dict)
    transition_matrix: Optional[LandCoverTransitionMatrix] = None


class BiTemporalChangeDetector:
    """
    Core engine for detecting multi-spectral and morphological changes
    between two satellite observations across time (t1 -> t2).
    """

    @classmethod
    def classify_land_cover_heuristic(
        cls,
        rgb_or_multispectral: np.ndarray,
        ndvi: Optional[np.ndarray] = None,
        ndwi: Optional[np.ndarray] = None,
        ndbi: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Classifies an input scene into 5 foundational land-cover classes
        using radiometric indices or RGB heuristics when indices are not supplied.
        """
        h, w = rgb_or_multispectral.shape[:2]
        classes = np.full((h, w), LandCoverClass.BARE_SOIL, dtype=np.uint8)

        if ndvi is not None and ndwi is not None and ndbi is not None:
            # Radiometrically rigorous segmentation
            # 1. Water
            classes[ndwi > 0.05] = LandCoverClass.WATER
            # 2. Dense Canopy
            classes[(ndvi > 0.45) & (ndwi <= 0.05)] = LandCoverClass.DENSE_CANOPY
            # 3. Moderate Veg
            classes[(ndvi >= 0.20) & (ndvi <= 0.45) & (ndwi <= 0.05)] = LandCoverClass.MODERATE_VEGETATION
            # 4. Urban Built-Up
            classes[(ndbi > 0.05) & (ndvi < 0.20) & (ndwi <= 0.05)] = LandCoverClass.BUILT_UP_URBAN
            # Remainder is bare soil
        else:
            # RGB heuristic proxy (for standard 3-channel optical chips)
            img = rgb_or_multispectral.astype(np.float32)
            r, g, b = img[..., 0], img[..., 1], img[..., 2]
            
            # Water: dominant blue and low red
            water_cond = (b > r * 1.15) & (b > g * 1.05) & (b > 40)
            classes[water_cond] = LandCoverClass.WATER

            # Vegetation: dominant green
            veg_dense_cond = (g > r * 1.25) & (g > b * 1.20) & ~water_cond
            veg_mod_cond = (g > r * 1.08) & (g > b * 1.05) & ~water_cond & ~veg_dense_cond
            classes[veg_dense_cond] = LandCoverClass.DENSE_CANOPY
            classes[veg_mod_cond] = LandCoverClass.MODERATE_VEGETATION

            # Urban: high brightness, low saturation or concrete grey/terracotta
            brightness = (r + g + b) / 3.0
            urban_cond = (brightness > 140) & ~water_cond & ~veg_dense_cond & ~veg_mod_cond
            classes[urban_cond] = LandCoverClass.BUILT_UP_URBAN

        return classes

    @classmethod
    def detect_spectral_change(
        cls,
        img_t1: np.ndarray,
        img_t2: np.ndarray,
        threshold_mode: str = "otsu",
        k_sigma: float = 2.0,
        morph_cleanup: bool = True,
    ) -> ChangeDetectionResult:
        """
        Executes normalized change vector analysis (CVA) between two co-registered scenes.
        """
        if img_t1.shape != img_t2.shape:
            # Automatically resize t2 to match t1 if dimension mismatch occurs
            img_t2 = cv2.resize(img_t2, (img_t1.shape[1], img_t1.shape[0]), interpolation=cv2.INTER_LINEAR)

        t1_f = img_t1.astype(np.float32)
        t2_f = img_t2.astype(np.float32)

        # 1. Compute Euclidean spectral difference magnitude
        if t1_f.ndim == 3:
            diff_vec = t2_f - t1_f
            magnitude = np.linalg.norm(diff_vec, axis=-1)
        else:
            magnitude = np.abs(t2_f - t1_f)

        # Normalize magnitude to 0-255 uint8 range for Otsu segmentation
        m_max = float(magnitude.max())
        if m_max > 1e-6:
            norm_mag_255 = np.clip((magnitude / m_max) * 255.0, 0, 255).astype(np.uint8)
        else:
            norm_mag_255 = np.zeros(magnitude.shape, dtype=np.uint8)

        # 2. Thresholding
        if threshold_mode.lower() == "otsu":
            otsu_val, binary_mask = cv2.threshold(norm_mag_255, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            threshold_cutoff = float(otsu_val)
        else:
            # Statistical k-sigma thresholding
            mu = float(np.mean(norm_mag_255))
            sigma = float(np.std(norm_mag_255))
            threshold_cutoff = min(255.0, mu + k_sigma * sigma)
            binary_mask = np.where(norm_mag_255 > threshold_cutoff, 255, 0).astype(np.uint8)

        # 3. Morphological filtering (remove single-pixel sensor noise / small artifacts)
        if morph_cleanup:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)

        changed_ratio = float(np.sum(binary_mask > 0) / binary_mask.size * 100.0)

        # 4. Generate colorized change heatmap (using Magma/Jet colormap)
        colored_heat = cv2.applyColorMap(norm_mag_255, cv2.COLORMAP_JET)
        # Apply dark mask to unchanged regions to emphasize hot spots
        colored_heat[binary_mask == 0] = (colored_heat[binary_mask == 0] * 0.25).astype(np.uint8)
        change_heatmap_rgb = cv2.cvtColor(colored_heat, cv2.COLOR_BGR2RGB)

        # 5. Compute Land Cover Transitions
        classes_t1 = cls.classify_land_cover_heuristic(img_t1)
        classes_t2 = cls.classify_land_cover_heuristic(img_t2)
        trans_matrix = cls.compute_transition_matrix(classes_t1, classes_t2)

        summary = {
            "changed_pixel_ratio_pct": round(changed_ratio, 2),
            "mean_magnitude": round(float(np.mean(magnitude)), 2),
            "max_magnitude": round(m_max, 2),
            "threshold_used": round(threshold_cutoff, 2),
            "deforestation_ha": trans_matrix.deforestation_hectares,
            "urban_sprawl_ha": trans_matrix.urban_sprawl_hectares,
            "water_loss_ha": trans_matrix.water_loss_hectares,
            "revegetation_ha": trans_matrix.revegetation_hectares,
        }

        return ChangeDetectionResult(
            difference_magnitude=magnitude,
            binary_change_mask=binary_mask,
            change_heatmap_rgb=change_heatmap_rgb,
            otsu_threshold=threshold_cutoff,
            mean_change_intensity=float(np.mean(magnitude)),
            changed_pixel_ratio=round(changed_ratio, 2),
            transition_summary=summary,
            transition_matrix=trans_matrix,
        )

    @classmethod
    def compute_transition_matrix(
        cls,
        classes_t1: np.ndarray,
        classes_t2: np.ndarray,
        pixel_resolution_m: float = 10.0,
    ) -> LandCoverTransitionMatrix:
        """
        Builds the 5x5 land-cover transition matrix and translates pixel
        transitions into physical hectares (1 ha = 10,000 m²).
        """
        n_classes = len(LandCoverClass)
        matrix = np.zeros((n_classes, n_classes), dtype=np.int64)

        for i in range(n_classes):
            for j in range(n_classes):
                matrix[i, j] = int(np.sum((classes_t1 == i) & (classes_t2 == j)))

        pixel_area_m2 = pixel_resolution_m * pixel_resolution_m
        m2_to_ha = 1.0 / 10000.0

        # Deforestation: (Dense Canopy or Mod Veg) -> (Built-up or Bare Soil)
        deforestation_pixels = (
            matrix[LandCoverClass.DENSE_CANOPY, LandCoverClass.BUILT_UP_URBAN] +
            matrix[LandCoverClass.DENSE_CANOPY, LandCoverClass.BARE_SOIL] +
            matrix[LandCoverClass.MODERATE_VEGETATION, LandCoverClass.BUILT_UP_URBAN] +
            matrix[LandCoverClass.MODERATE_VEGETATION, LandCoverClass.BARE_SOIL]
        )

        # Urban Sprawl: (Veg or Bare Soil) -> Built-up
        urban_sprawl_pixels = (
            matrix[LandCoverClass.DENSE_CANOPY, LandCoverClass.BUILT_UP_URBAN] +
            matrix[LandCoverClass.MODERATE_VEGETATION, LandCoverClass.BUILT_UP_URBAN] +
            matrix[LandCoverClass.BARE_SOIL, LandCoverClass.BUILT_UP_URBAN]
        )

        # Water Loss: Water -> (Soil, Urban, or Veg)
        water_loss_pixels = (
            matrix[LandCoverClass.WATER, LandCoverClass.BARE_SOIL] +
            matrix[LandCoverClass.WATER, LandCoverClass.BUILT_UP_URBAN] +
            matrix[LandCoverClass.WATER, LandCoverClass.MODERATE_VEGETATION]
        )

        # Revegetation: (Soil or Urban) -> (Veg or Canopy)
        reveg_pixels = (
            matrix[LandCoverClass.BARE_SOIL, LandCoverClass.DENSE_CANOPY] +
            matrix[LandCoverClass.BARE_SOIL, LandCoverClass.MODERATE_VEGETATION]
        )

        total_pixels = int(classes_t1.size)

        return LandCoverTransitionMatrix(
            matrix=matrix,
            total_pixels=total_pixels,
            deforestation_hectares=round(deforestation_pixels * pixel_area_m2 * m2_to_ha, 2),
            urban_sprawl_hectares=round(urban_sprawl_pixels * pixel_area_m2 * m2_to_ha, 2),
            water_loss_hectares=round(water_loss_pixels * pixel_area_m2 * m2_to_ha, 2),
            revegetation_hectares=round(reveg_pixels * pixel_area_m2 * m2_to_ha, 2),
            pixel_resolution_m=pixel_resolution_m,
        )

    @classmethod
    def render_change_dashboard(
        cls,
        img_t1: np.ndarray,
        img_t2: np.ndarray,
        result: ChangeDetectionResult,
    ) -> np.ndarray:
        """
        Creates a high-contrast 2x2 multi-panel composite dashboard image:
        [Top-Left: Observation t1 | Top-Right: Observation t2]
        [Bottom-Left: Change Heatmap | Bottom-Right: Segmented Change Overlay]
        """
        h, w = img_t1.shape[:2]
        
        # Ensure 3-channel RGB for all sub-panels
        def to_rgb(im):
            if im.ndim == 2:
                return cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
            return im

        p1 = cv2.resize(to_rgb(img_t1), (w, h))
        p2 = cv2.resize(to_rgb(img_t2), (w, h))
        p3 = cv2.resize(result.change_heatmap_rgb, (w, h))

        # P4: Binary mask overlaid onto t2 in glowing red
        overlay = p2.copy()
        mask = result.binary_change_mask > 0
        overlay[mask] = (0.35 * overlay[mask] + 0.65 * np.array([255, 30, 30])).astype(np.uint8)
        p4 = overlay

        # Add title headers to each quadrant
        def add_banner(im, text):
            annotated = im.copy()
            cv2.rectangle(annotated, (0, 0), (w, 28), (15, 20, 30), -1)
            cv2.putText(annotated, text, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1, cv2.LINE_AA)
            return annotated

        p1 = add_banner(p1, "1. Acquisition t1 (Baseline)")
        p2 = add_banner(p2, "2. Acquisition t2 (Current)")
        p3 = add_banner(p3, f"3. Spectral Delta Heatmap (Mean: {result.mean_change_intensity:.1f})")
        p4 = add_banner(p4, f"4. Significant Change Mask ({result.changed_pixel_ratio:.1f}% Area)")

        top_row = np.hstack([p1, p2])
        bottom_row = np.hstack([p3, p4])
        dashboard = np.vstack([top_row, bottom_row])
        return dashboard
