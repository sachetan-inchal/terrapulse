"""
Multi-Spectral Radiometric Analytics & Atmospheric Masking Engine.

Implements Tier 2 academic remote sensing capabilities:
- Automated radiometric indices: NDVI, NDWI, NDBI, SAVI, BSI, EVI
- Sentinel-2 Scene Classification Layer (SCL) cloud and cloud-shadow masking
- False-color composite generation (CIR, Urban False Color, Agriculture)
- Ecological surface classification and canopy coverage metrics
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Any
import numpy as np


@dataclass
class MultiSpectralIndices:
    """Container for computed radiometric indices and surface distribution metrics."""
    ndvi: np.ndarray
    ndwi: np.ndarray
    ndbi: np.ndarray
    savi: Optional[np.ndarray] = None
    bsi: Optional[np.ndarray] = None
    evi: Optional[np.ndarray] = None
    statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SCLQualityMetrics:
    """Atmospheric quality metrics derived from Sentinel-2 Scene Classification Layer."""
    valid_mask: np.ndarray
    cloud_mask: np.ndarray
    shadow_mask: np.ndarray
    water_mask: np.ndarray
    vegetation_mask: np.ndarray
    bare_soil_mask: np.ndarray
    clear_sky_percentage: float
    cloud_contamination_percentage: float
    shadow_percentage: float
    quality_score: float  # 0.0 - 100.0


class RadiometricProcessor:
    """
    High-performance radiometric analysis and index processing engine for
    Sentinel-2 and multi-spectral satellite imagery.
    """

    EPSILON = 1e-7

    # Sentinel-2 SCL class definitions
    SCL_NO_DATA = 0
    SCL_SATURATED = 1
    SCL_DARK_FEATURE = 2
    SCL_CLOUD_SHADOW = 3
    SCL_VEGETATION = 4
    SCL_NOT_VEGETATED = 5
    SCL_WATER = 6
    SCL_UNCLASSIFIED = 7
    SCL_CLOUD_MED_PROB = 8
    SCL_CLOUD_HIGH_PROB = 9
    SCL_THIN_CIRRUS = 10
    SCL_SNOW_ICE = 11

    @classmethod
    def compute_ndvi(cls, nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """
        Normalized Difference Vegetation Index (NDVI):
        NDVI = (NIR - Red) / (NIR + Red)
        Range: [-1.0, 1.0]. High values (>0.4) indicate dense green canopy.
        """
        nir_f = nir.astype(np.float32)
        red_f = red.astype(np.float32)
        denom = nir_f + red_f
        denom = np.where(np.abs(denom) < cls.EPSILON, cls.EPSILON, denom)
        ndvi = (nir_f - red_f) / denom
        return np.clip(ndvi, -1.0, 1.0)

    @classmethod
    def compute_ndwi(cls, green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Normalized Difference Water Index (NDWI, McFeeters 1996):
        NDWI = (Green - NIR) / (Green + NIR)
        Range: [-1.0, 1.0]. Positive values (>0.0) typically delineate open water bodies.
        """
        green_f = green.astype(np.float32)
        nir_f = nir.astype(np.float32)
        denom = green_f + nir_f
        denom = np.where(np.abs(denom) < cls.EPSILON, cls.EPSILON, denom)
        ndwi = (green_f - nir_f) / denom
        return np.clip(ndwi, -1.0, 1.0)

    @classmethod
    def compute_ndbi(cls, swir: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Normalized Difference Built-up Index (NDBI, Zha et al. 2003):
        NDBI = (SWIR - NIR) / (SWIR + NIR)
        Range: [-1.0, 1.0]. Positive values indicate built-up urban infrastructure & impervious surfaces.
        """
        swir_f = swir.astype(np.float32)
        nir_f = nir.astype(np.float32)
        denom = swir_f + nir_f
        denom = np.where(np.abs(denom) < cls.EPSILON, cls.EPSILON, denom)
        ndbi = (swir_f - nir_f) / denom
        return np.clip(ndbi, -1.0, 1.0)

    @classmethod
    def compute_savi(cls, nir: np.ndarray, red: np.ndarray, l_factor: float = 0.5) -> np.ndarray:
        """
        Soil-Adjusted Vegetation Index (SAVI, Huete 1988):
        SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
        L = 0.5 is optimal for intermediate vegetation densities.
        """
        nir_f = nir.astype(np.float32)
        red_f = red.astype(np.float32)
        denom = nir_f + red_f + l_factor
        denom = np.where(np.abs(denom) < cls.EPSILON, cls.EPSILON, denom)
        savi = ((nir_f - red_f) / denom) * (1.0 + l_factor)
        return np.clip(savi, -1.0, 1.5)

    @classmethod
    def compute_bsi(cls, swir: np.ndarray, red: np.ndarray, nir: np.ndarray, blue: np.ndarray) -> np.ndarray:
        """
        Bare Soil Index (BSI):
        BSI = ((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))
        Separates bare agricultural ground and construction earth from built structures.
        """
        swir_f = swir.astype(np.float32)
        red_f = red.astype(np.float32)
        nir_f = nir.astype(np.float32)
        blue_f = blue.astype(np.float32)

        num = (swir_f + red_f) - (nir_f + blue_f)
        denom = (swir_f + red_f) + (nir_f + blue_f)
        denom = np.where(np.abs(denom) < cls.EPSILON, cls.EPSILON, denom)
        bsi = num / denom
        return np.clip(bsi, -1.0, 1.0)

    @classmethod
    def compute_evi(cls, nir: np.ndarray, red: np.ndarray, blue: np.ndarray,
                    g: float = 2.5, c1: float = 6.0, c2: float = 7.5, l: float = 1.0) -> np.ndarray:
        """
        Enhanced Vegetation Index (EVI):
        EVI = G * (NIR - Red) / (NIR + C1*Red - C2*Blue + L)
        High sensitivity in high biomass regions with reduced atmospheric aerosol interference.
        """
        nir_f = nir.astype(np.float32)
        red_f = red.astype(np.float32)
        blue_f = blue.astype(np.float32)

        num = nir_f - red_f
        denom = nir_f + (c1 * red_f) - (c2 * blue_f) + l
        denom = np.where(np.abs(denom) < cls.EPSILON, cls.EPSILON, denom)
        evi = g * (num / denom)
        return np.clip(evi, -1.0, 2.5)

    @classmethod
    def process_all_indices(cls, bands: Dict[str, np.ndarray]) -> MultiSpectralIndices:
        """
        Processes all standard indices given a dictionary of bands.
        Expected band keys: 'B02' (Blue), 'B03' (Green), 'B04' (Red), 'B08' (NIR), and optional 'B11' (SWIR).
        If SWIR is missing, synthesized or NIR-based proxy is utilized safely.
        """
        red = bands.get("B04")
        nir = bands.get("B08")
        green = bands.get("B03")
        blue = bands.get("B02")
        swir = bands.get("B11")

        if red is None or nir is None:
            raise ValueError("Both 'B04' (Red) and 'B08' (NIR) bands are required for radiometric calculation.")

        # If SWIR is not directly provided, use approximation based on red/green ratio
        if swir is None:
            swir = np.clip(red.astype(np.float32) * 1.15, 0, np.iinfo(red.dtype).max if hasattr(red.dtype, 'type') else 65535.0).astype(red.dtype)

        ndvi = cls.compute_ndvi(nir, red)
        ndwi = cls.compute_ndwi(green if green is not None else red, nir)
        ndbi = cls.compute_ndbi(swir, nir)

        savi = cls.compute_savi(nir, red)
        bsi = cls.compute_bsi(swir, red, nir, blue if blue is not None else red)
        evi = cls.compute_evi(nir, red, blue if blue is not None else red)

        # Calculate high-level surface statistics
        total_pixels = ndvi.size
        dense_veg_pct = float(np.sum(ndvi > 0.45) / total_pixels * 100.0)
        moderate_veg_pct = float(np.sum((ndvi >= 0.20) & (ndvi <= 0.45)) / total_pixels * 100.0)
        water_pct = float(np.sum(ndwi > 0.05) / total_pixels * 100.0)
        urban_pct = float(np.sum(ndbi > 0.05) / total_pixels * 100.0)
        bare_soil_pct = float(np.sum(bsi > 0.10) / total_pixels * 100.0)

        stats = {
            "total_pixels": int(total_pixels),
            "ndvi_mean": float(np.mean(ndvi)),
            "ndvi_std": float(np.std(ndvi)),
            "ndwi_mean": float(np.mean(ndwi)),
            "ndbi_mean": float(np.mean(ndbi)),
            "dense_vegetation_pct": round(dense_veg_pct, 2),
            "moderate_vegetation_pct": round(moderate_veg_pct, 2),
            "water_body_pct": round(water_pct, 2),
            "built_up_urban_pct": round(urban_pct, 2),
            "bare_soil_pct": round(bare_soil_pct, 2),
        }

        return MultiSpectralIndices(
            ndvi=ndvi,
            ndwi=ndwi,
            ndbi=ndbi,
            savi=savi,
            bsi=bsi,
            evi=evi,
            statistics=stats,
        )

    @classmethod
    def parse_scl(cls, scl: np.ndarray) -> SCLQualityMetrics:
        """
        Parses Sentinel-2 Scene Classification Layer (SCL) to construct
        valid pixel masks, cloud masks, and atmospheric reliability metrics.
        """
        total = scl.size
        if total == 0:
            raise ValueError("Empty SCL array provided.")

        cloud_mask = (
            (scl == cls.SCL_CLOUD_MED_PROB) |
            (scl == cls.SCL_CLOUD_HIGH_PROB) |
            (scl == cls.SCL_THIN_CIRRUS)
        )
        shadow_mask = (scl == cls.SCL_CLOUD_SHADOW)
        water_mask = (scl == cls.SCL_WATER)
        veg_mask = (scl == cls.SCL_VEGETATION)
        bare_mask = (scl == cls.SCL_NOT_VEGETATED)

        # Clear-sky valid mask: exclude clouds, cloud shadows, saturated, and no-data
        invalid_mask = cloud_mask | shadow_mask | (scl == cls.SCL_NO_DATA) | (scl == cls.SCL_SATURATED)
        valid_mask = ~invalid_mask

        clear_sky_pct = float(np.sum(valid_mask) / total * 100.0)
        cloud_pct = float(np.sum(cloud_mask) / total * 100.0)
        shadow_pct = float(np.sum(shadow_mask) / total * 100.0)

        # Quality score penalties based on cloud and shadow contamination
        quality_score = max(0.0, 100.0 - (cloud_pct * 1.5) - (shadow_pct * 2.0))

        return SCLQualityMetrics(
            valid_mask=valid_mask,
            cloud_mask=cloud_mask,
            shadow_mask=shadow_mask,
            water_mask=water_mask,
            vegetation_mask=veg_mask,
            bare_soil_mask=bare_mask,
            clear_sky_percentage=round(clear_sky_pct, 2),
            cloud_contamination_percentage=round(cloud_pct, 2),
            shadow_percentage=round(shadow_pct, 2),
            quality_score=round(quality_score, 2),
        )

    @classmethod
    def generate_false_color_composite(
        cls,
        bands: Dict[str, np.ndarray],
        composite_type: str = "cir",
        stretch_percentiles: Tuple[float, float] = (2.0, 98.0)
    ) -> np.ndarray:
        """
        Synthesizes standard multi-spectral false-color composites:
        - 'cir' (Color Infrared): NIR (B08) -> Red, Red (B04) -> Green, Green (B03) -> Blue.
          Highlights plant biomass in deep red/magenta.
        - 'urban': SWIR (B11) -> Red, NIR (B08) -> Green, Red (B04) -> Blue.
          Highlights concrete, steel, and urban footprints.
        - 'agriculture': SWIR (B11) -> Red, NIR (B08) -> Green, Blue (B02) -> Blue.
          Differentiates crop health and moisture levels.
        """
        def stretch(band_arr: np.ndarray) -> np.ndarray:
            p_low, p_high = np.percentile(band_arr, stretch_percentiles)
            if p_high - p_low < cls.EPSILON:
                return np.zeros_like(band_arr, dtype=np.uint8)
            norm = np.clip((band_arr.astype(np.float32) - p_low) / (p_high - p_low), 0.0, 1.0)
            return (norm * 255.0).astype(np.uint8)

        b02 = bands.get("B02")
        b03 = bands.get("B03")
        b04 = bands.get("B04")
        b08 = bands.get("B08")
        b11 = bands.get("B11")

        if b04 is None or b08 is None:
            raise ValueError("Bands 'B04' and 'B08' are mandatory for composite synthesis.")

        comp_type = composite_type.lower()
        if comp_type == "cir":
            # NIR -> R, Red -> G, Green -> B
            r_ch = stretch(b08)
            g_ch = stretch(b04)
            b_ch = stretch(b03 if b03 is not None else b04)
        elif comp_type == "urban":
            # SWIR -> R, NIR -> G, Red -> B
            swir = b11 if b11 is not None else (b04.astype(np.float32) * 1.2).astype(b04.dtype)
            r_ch = stretch(swir)
            g_ch = stretch(b08)
            b_ch = stretch(b04)
        elif comp_type == "agriculture":
            # SWIR -> R, NIR -> G, Blue -> B
            swir = b11 if b11 is not None else (b04.astype(np.float32) * 1.2).astype(b04.dtype)
            r_ch = stretch(swir)
            g_ch = stretch(b08)
            b_ch = stretch(b02 if b02 is not None else b04)
        else:
            raise ValueError(f"Unknown composite type: '{composite_type}'. Choose 'cir', 'urban', or 'agriculture'.")

        return np.dstack([r_ch, g_ch, b_ch])

    @classmethod
    def colorize_index(cls, index_array: np.ndarray, index_name: str = "ndvi") -> np.ndarray:
        """
        Renders a floating-point radiometric index array [-1.0, 1.0] into
        an aesthetically graded 8-bit RGB heatmap.
        """
        norm = np.clip((index_array + 1.0) / 2.0, 0.0, 1.0)
        h, w = index_array.shape
        rgb = np.zeros((h, w, 3), dtype=np.uint8)

        idx = index_name.lower()
        if idx == "ndvi":
            # Low: Brown/Sand -> Middle: Yellow -> High: Lush Emerald Green
            # Red channel
            rgb[..., 0] = np.clip((1.0 - norm) * 255.0 * 1.2, 0, 255).astype(np.uint8)
            # Green channel
            rgb[..., 1] = np.clip(norm * 255.0 * 1.1, 0, 255).astype(np.uint8)
            # Blue channel
            rgb[..., 2] = np.clip((1.0 - np.abs(norm - 0.5) * 2.0) * 80.0, 0, 255).astype(np.uint8)
        elif idx == "ndwi":
            # Deep Navy to Cyan / Azure for water bodies
            rgb[..., 0] = np.clip((1.0 - norm) * 180.0, 0, 255).astype(np.uint8)
            rgb[..., 1] = np.clip(norm * 200.0 + 30.0, 0, 255).astype(np.uint8)
            rgb[..., 2] = np.clip(norm * 255.0, 0, 255).astype(np.uint8)
        elif idx == "ndbi":
            # Violet/Gray to Vivid Orange/Red for urban built-up areas
            rgb[..., 0] = np.clip(norm * 255.0, 0, 255).astype(np.uint8)
            rgb[..., 1] = np.clip((1.0 - norm) * 120.0 + norm * 60.0, 0, 255).astype(np.uint8)
            rgb[..., 2] = np.clip((1.0 - norm) * 180.0, 0, 255).astype(np.uint8)
        else:
            # Grayscale fallback
            gray = (norm * 255.0).astype(np.uint8)
            rgb[..., 0] = gray
            rgb[..., 1] = gray
            rgb[..., 2] = gray

        return rgb
