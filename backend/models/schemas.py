"""Pydantic API Schemas & Data Contracts for Earth Temporal Intelligence."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LocationInfo(BaseModel):
    id: str
    name: str
    country: str
    latitude: float
    longitude: float
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    default_crs: str = "EPSG:4326"
    target_utm: str
    description: str
    feature_type: Optional[str] = "place"

class SatelliteScene(BaseModel):
    id: str
    mission: str         # "Landsat 5", "Landsat 8", "Sentinel-2", "PlanetScope"
    sensor: str
    acquisition_date: str # "1985-03-12"
    year: int
    cloud_cover: float   # Percentage (0.0 to 100.0)
    spatial_resolution_m: float # 10.0, 30.0, etc.
    thumbnail_url: str
    preview_url: Optional[str] = None
    crs: str
    bbox: List[float]
    footprint: Optional[Dict[str, Any]] = None

class RegistrationResult(BaseModel):
    status: str          # "SUCCESS", "REJECTED_LOW_INLIERS", "COORDINATE_REPROJECTED"
    method: str          # "SIFT + RANSAC", "Geospatial Bilinear Alignment"
    keypoints_detected: int
    matches_found: int
    inliers_count: int
    inlier_ratio_pct: float
    reprojection_error_px: float
    homography_matrix: Optional[List[List[float]]] = None
    confidence: str      # "HIGH", "MODERATE", "LOW"
    warning: Optional[str] = None

class LandCoverClass(BaseModel):
    name: str            # "Vegetation", "Forest", "Urban / Built-up", "Water Bodies", "Agriculture", "Bare Land"
    area_sq_km: float
    percentage: float
    hex_color: str

class EnvironmentalAnalysis(BaseModel):
    location: str
    observation_date: str
    sensor: str
    mean_ndvi: float
    mean_ndwi: float
    vegetation_coverage_pct: float
    forest_coverage_pct: float
    built_up_coverage_pct: float
    water_coverage_pct: float
    classes: List[LandCoverClass]
    confidence_score: float

class ChangeDetectionResult(BaseModel):
    baseline_date: str
    target_date: str
    total_area_sq_km: float
    changed_area_sq_km: float
    changed_percentage: float
    urban_expansion_sq_km: float
    canopy_loss_sq_km: float
    water_fluctuation_sq_km: float
    f1_score: Optional[float] = 0.799
    iou_score: Optional[float] = 0.665
    change_mask_url: Optional[str] = None

class EvidenceFinding(BaseModel):
    finding_id: str
    claim: str
    category: str        # "OBSERVED", "DOCUMENTED", "CORRELATED", "POSSIBLE EXPLANATION", "UNKNOWN"
    source_type: str     # "Satellite Observation", "Government / Economic", "Academic Research", "Planning Document"
    time_span: str       # "1985–2024", "2000–2020", etc.
    confidence: str      # "High", "Medium", "Low"
    citations: List[Dict[str, str]]

class GraphNode(BaseModel):
    id: str
    label: str
    category: str        # "core", "satellite", "policy", "infrastructure", "socioeconomic", "environmental", "historical"
    confidence: Optional[str] = "High"

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str

class EvidenceGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class InvestigationResponse(BaseModel):
    query: str
    status: str          # "Completed", "Researching", "Partial"
    region: str
    time_window: str
    agent_status: List[Dict[str, str]]
    summary: str
    findings: List[EvidenceFinding]
    evidence_graph: EvidenceGraph

class ReportRequest(BaseModel):
    location_id: str
    selected_dates: List[str]
    notes: Optional[str] = None

class FutureScenario(BaseModel):
    scenario_year: int   # 2030, 2040, 2050
    model_type: str      # "Spatiotemporal Transformer + Cellular Automata Dynamics"
    projected_urban_pct: float
    projected_vegetation_pct: float
    projected_water_pct: float
    assumptions: List[str]
    uncertainty_margin: str
    disclaimer: str

# ==============================================================================
# Phase 6: Conversational Investigator & Environmental REST Schemas
# ==============================================================================

class InvestigatorChatRequest(BaseModel):
    message: str = Field(..., description="Natural language user query or investigation prompt.")
    session_id: str = Field(default="default_session", description="Conversational session ID for multi-turn context.")
    location: Optional[str] = Field(None, description="Optional override or pre-resolved target location.")
    indicator: Optional[str] = Field(None, description="Optional override pollutant or indicator (e.g., PM2.5, DO).")

class StationMeasurementSchema(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    indicator: str
    value: float
    unit: str
    timestamp: str
    quality_flag: str
    provenance: str
    is_sample_data: bool = True
    sample_data_note: Optional[str] = None

class HeatmapResponseSchema(BaseModel):
    indicator: str
    interpolation_method: str = "Inverse Distance Weighting (IDW, Power=2.0)"
    bounding_box: List[float]
    coverage_percentage: float
    total_grid_points: int
    interpolated_points: int
    uninterpolated_points: int
    geojson: Dict[str, Any]
    epistemic_notice: str

class SymptomAnalysisRequest(BaseModel):
    symptom_query: str = Field(..., description="Natural language description of observed environmental anomaly.")
    location: Optional[str] = Field("Bengaluru", description="Geographic location or catchment.")

class SymptomHypothesisSchema(BaseModel):
    hypothesis_id: str
    title: str
    pollutant: str
    biological_mechanism: str
    confidence_tier: str
    bradford_hill_score: float
    supporting_evidence: List[Dict[str, Any]]
    conflicting_evidence: List[Dict[str, Any]]
    alternative_explanations: List[str]
    missing_data: List[str]

class SymptomAnalysisResponse(BaseModel):
    symptom_detected: str
    location: str
    hypotheses: List[SymptomHypothesisSchema]
    uncertainty_statement: str
    investigation_summary: str
    academic_citations: List[Dict[str, Any]]

class ForecastRequest(BaseModel):
    indicator: str = Field("PM2.5", description="Environmental metric/pollutant to project.")
    horizon: str = Field("+5 years", description="Projection horizon (+1 year, +3 years, +5 years, 2030, 2040).")
    reduction_percentage: float = Field(30.0, description="Hypothetical mitigation target percentage.")
    location: Optional[str] = Field("Bengaluru", description="Location context.")

class ForecastScenarioPoint(BaseModel):
    year: int
    predicted_value: float
    lower_80: float
    upper_80: float
    lower_95: float
    upper_95: float

class ForecastScenarioResult(BaseModel):
    scenario_name: str
    description: str
    trajectory: List[ForecastScenarioPoint]
    assumptions: List[str]

class ForecastResponse(BaseModel):
    indicator: str
    unit: str
    historical_observations: List[Dict[str, Any]]
    scenarios: Dict[str, ForecastScenarioResult]
    horizon_target_year: int
    statistical_method: str
    disclaimer: str

class ResearchArticleSchema(BaseModel):
    title: str
    authors: List[str]
    publication_year: Optional[int]
    source: str
    doi_or_url: Optional[str]
    snippet: str
    article_type: str

class ResearchQueryResponse(BaseModel):
    query: str
    total_found: int
    articles: List[ResearchArticleSchema]

