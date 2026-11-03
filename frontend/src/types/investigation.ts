/**
 * Types and data contracts for TerraPulse 2.0 AI Environmental Investigator.
 */

export interface StationMeasurement {
  station_id: string;
  station_name: string;
  latitude: number;
  longitude: number;
  indicator: string;
  value: number;
  unit: string;
  timestamp: string;
  quality_flag: string;
  provenance: string;
  is_sample_data: boolean;
  sample_data_note?: string;
}

export interface HeatmapData {
  indicator: string;
  interpolation_method: string;
  bounding_box: [number, number, number, number]; // [min_lon, min_lat, max_lon, max_lat]
  coverage_percentage: number;
  total_grid_points: number;
  interpolated_points: number;
  uninterpolated_points: number;
  geojson: any;
  epistemic_notice: string;
}

export interface SymptomHypothesis {
  hypothesis_id: string;
  title: string;
  pollutant: string;
  biological_mechanism: string;
  confidence_tier: string;
  bradford_hill_score: number;
  supporting_evidence: Array<{ type: string; claim: string; source: string }>;
  conflicting_evidence: Array<{ type: string; claim: string; source: string }>;
  alternative_explanations: string[];
  missing_data: string[];
}

export interface SymptomAnalysisResult {
  symptom_detected: string;
  location: string;
  hypotheses: SymptomHypothesis[];
  uncertainty_statement: string;
  investigation_summary: string;
  academic_citations: Array<{
    title: string;
    journal?: string;
    year?: number | string;
    doi?: string;
    url?: string;
    authors?: string[];
  }>;
}

export interface ForecastScenarioPoint {
  year: number;
  predicted_value: number;
  lower_80: number;
  upper_80: number;
  lower_95: number;
  upper_95: number;
}

export interface ForecastScenarioResult {
  scenario_name: string;
  description: string;
  trajectory: ForecastScenarioPoint[];
  assumptions: string[];
}

export interface ForecastResponseData {
  indicator: string;
  unit: string;
  historical_observations: Array<{
    year: number;
    value: number;
    unit: string;
    quality_flag: string;
    provenance: string;
  }>;
  scenarios: Record<string, ForecastScenarioResult>;
  horizon_target_year: number;
  statistical_method: string;
  disclaimer: string;
}

export interface ResearchArticleItem {
  title: string;
  authors: string[];
  publication_year?: number;
  source: string;
  doi_or_url?: string;
  snippet: string;
  article_type: string;
}

export interface ResearchQueryResponseData {
  query: string;
  total_found: number;
  articles: ResearchArticleItem[];
}

export interface ActivityEventItem {
  id: string;
  eventType: 'tool_call_start' | 'tool_call_args' | 'tool_call_result' | 'clarification_needed' | 'final_response' | 'error';
  toolName?: string;
  data: any;
  timestamp: string;
  status: 'running' | 'completed' | 'failed' | 'info';
  title: string;
  summary?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  text: string;
  timestamp: string;
  clarification?: {
    slot: string;
    question: string;
    options?: string[];
  };
  investigationData?: SymptomAnalysisResult;
  forecastData?: ForecastResponseData;
  geojson?: any;
  isStreaming?: boolean;
}

