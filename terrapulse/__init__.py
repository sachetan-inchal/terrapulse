"""
TerraPulse: Planetary-Scale Geospatial Computer Vision & Autonomous OSINT Engine.
Core package initialization and module exports.
"""

__version__ = "1.2.0"
__author__ = "TerraPulse Geospatial CV Team"

from terrapulse.multispectral import (
    RadiometricProcessor,
    MultiSpectralIndices,
    SCLQualityMetrics,
)
from terrapulse.change_detection import (
    BiTemporalChangeDetector,
    ChangeDetectionResult,
    LandCoverTransitionMatrix,
)
from terrapulse.osint_engine import (
    GeospatialOSINTEngine,
    OSINTIntelligenceReport,
    EcologicalThreatLevel,
)
from terrapulse.robust_matcher import (
    RobustGeospatialMatcher,
    AlignmentResult,
)

__all__ = [
    "RadiometricProcessor",
    "MultiSpectralIndices",
    "SCLQualityMetrics",
    "BiTemporalChangeDetector",
    "ChangeDetectionResult",
    "LandCoverTransitionMatrix",
    "GeospatialOSINTEngine",
    "OSINTIntelligenceReport",
    "EcologicalThreatLevel",
    "RobustGeospatialMatcher",
    "AlignmentResult",
]
