export type NavSection = 
  | 'explore'
  | 'timeseries'
  | 'computervision'
  | 'landcover'
  | 'environmental'
  | 'investigator'
  | 'evidence'
  | 'reports'
  | 'future';

export interface LocationInfo {
  id: string;
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  bbox: [number, number, number, number];
  default_crs: string;
  target_utm: string;
  description: string;
}

export interface SatelliteScene {
  id: string;
  mission: string;
  sensor: string;
  acquisition_date: string;
  year: number;
  cloud_cover: number;
  spatial_resolution_m: number;
  thumbnail_url: string;
  preview_url?: string;
  crs: string;
  bbox: [number, number, number, number];
}

export interface LandCoverClass {
  name: string;
  area_sq_km: number;
  percentage: number;
  hex_color: string;
}

export interface EnvironmentalAnalysis {
  location: string;
  observation_date: string;
  sensor: string;
  mean_ndvi: number;
  mean_ndwi: number;
  vegetation_coverage_pct: number;
  forest_coverage_pct: number;
  built_up_coverage_pct: number;
  water_coverage_pct: number;
  classes: LandCoverClass[];
  confidence_score: number;
}

export interface ChangeDetectionResult {
  baseline_date: string;
  target_date: string;
  total_area_sq_km: number;
  changed_area_sq_km: number;
  changed_percentage: number;
  urban_expansion_sq_km: number;
  canopy_loss_sq_km: number;
  water_fluctuation_sq_km: number;
  f1_score: number;
  iou_score: number;
  change_mask_url?: string;
}

export interface RegistrationResult {
  status: string;
  method: string;
  keypoints_detected: number;
  matches_found: number;
  inliers_count: number;
  inlier_ratio_pct: number;
  reprojection_error_px: number;
  homography_matrix?: number[][];
  confidence: string;
  warning?: string;
}

export interface EvidenceCitation {
  title: string;
  url: string;
}

export interface EvidenceFinding {
  finding_id: string;
  claim: string;
  category: 'OBSERVED' | 'DOCUMENTED' | 'CORRELATED' | 'POSSIBLE EXPLANATION' | 'UNKNOWN';
  source_type: string;
  time_span: string;
  confidence: 'High' | 'Medium' | 'Low';
  citations: EvidenceCitation[];
}

export interface GraphNode {
  id: string;
  label: string;
  category: 'core' | 'satellite' | 'policy' | 'infrastructure' | 'socioeconomic' | 'environmental' | 'historical';
  confidence?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface EvidenceGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface AgentStatus {
  name: string;
  desc: string;
  status: string;
}

export interface InvestigationResponse {
  query: string;
  status: string;
  region: string;
  time_window: string;
  agent_status: AgentStatus[];
  summary: string;
  findings: EvidenceFinding[];
  evidence_graph: EvidenceGraph;
}

export interface FutureScenario {
  scenario_year: number;
  model_type: string;
  projected_urban_pct: number;
  projected_vegetation_pct: number;
  projected_water_pct: number;
  assumptions: string[];
  uncertainty_margin: string;
  disclaimer: string;
}

export interface LayerState {
  landCover: boolean;
  ndvi: boolean;
  waterIndex: boolean;
  urbanHeat: boolean;
  changeDetection: boolean;
  boundaries: boolean;
}

export interface DataSourceState {
  landsat: boolean;
  sentinel: boolean;
  modis: boolean;
  planet: boolean;
  osm: boolean;
  other: boolean;
}
