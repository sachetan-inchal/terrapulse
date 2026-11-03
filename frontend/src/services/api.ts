import type {
  LocationInfo, SatelliteScene, EnvironmentalAnalysis,
  ChangeDetectionResult, RegistrationResult, InvestigationResponse,
  FutureScenario
} from '../types';

const API_BASE = (typeof window !== 'undefined' && (window.location.port === '8000' || window.location.pathname.startsWith('/api')))
  ? '/api'
  : 'http://127.0.0.1:8000/api';

export async function fetchLocations(): Promise<LocationInfo[]> {
  try {
    const res = await fetch(`${API_BASE}/locations`);
    if (!res.ok) throw new Error('Failed to fetch locations');
    return await res.json();
  } catch (err) {
    console.warn('Backend offline, using fallback locations:', err);
    return [
      {
        id: "bengaluru",
        name: "Bengaluru, Karnataka, India",
        country: "India",
        latitude: 12.9716,
        longitude: 77.5946,
        bbox: [77.4598, 12.8334, 77.7840, 13.1426],
        default_crs: "EPSG:4326",
        target_utm: "EPSG:32643",
        description: "High-growth global IT hub undergoing intensive multi-decade urban expansion and green canopy reduction."
      }
    ];
  }
}

export async function geocodeLocation(query: string): Promise<LocationInfo> {
  const res = await fetch(`${API_BASE}/locations/geocode?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`Geocoding failed for: ${query}`);
  return await res.json();
}

export async function searchWorldwideLocations(query: string, limit: number = 8): Promise<LocationInfo[]> {
  try {
    const res = await fetch(`${API_BASE}/locations/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    if (!res.ok) throw new Error(`Worldwide search failed: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.warn('Live worldwide search failed, falling back to local geocode:', err);
    try {
      const single = await geocodeLocation(query);
      return [single];
    } catch {
      return [];
    }
  }
}

export async function fetchScenes(locationId: string = 'bengaluru', maxCloud: number = 20.0): Promise<SatelliteScene[]> {
  try {
    const res = await fetch(`${API_BASE}/scenes?location_id=${locationId}&max_cloud=${maxCloud}`);
    if (!res.ok) throw new Error('Failed to fetch scenes');
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn('Failed to fetch live STAC scenes, falling back to local benchmark:', err);
    return [
      {
        id: "S2_2024_BEN",
        mission: "Sentinel-2",
        sensor: "MSI 10m",
        acquisition_date: "2024-03-28",
        year: 2024,
        cloud_cover: 0.12,
        spatial_resolution_m: 10.0,
        thumbnail_url: "/api/imagery/tile?mission=Sentinel-2&year=2024",
        preview_url: "/api/imagery/tile?mission=Sentinel-2&year=2024",
        crs: "EPSG:32643",
        bbox: [77.4598, 12.8334, 77.7840, 13.1426]
      }
    ];
  }
}

export async function fetchChronologicalScenes(locationId: string = 'bengaluru'): Promise<SatelliteScene[]> {
  try {
    const res = await fetch(`${API_BASE}/scenes/chronological?location_id=${locationId}`);
    if (!res.ok) throw new Error('Failed to fetch chronological scenes');
    return await res.json();
  } catch (err) {
    console.warn('Failed to fetch chronological scenes, using fallback:', err);
    return [];
  }
}

export async function fetchRelatedImagery(locationId: string = 'bengaluru'): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/scenes/related?location_id=${locationId}`);
    if (!res.ok) throw new Error('Failed to fetch related imagery');
    return await res.json();
  } catch (err) {
    console.warn('Failed to fetch related imagery, using fallback:', err);
    return null;
  }
}

export async function fetchAnalysis(locationId: string, year: number): Promise<EnvironmentalAnalysis> {
  const res = await fetch(`${API_BASE}/analysis?location_id=${locationId}&year=${year}`);
  if (!res.ok) throw new Error('Analysis fetch failed');
  return await res.json();
}

export async function fetchChangeDetection(locationId: string, yearA: number, yearB: number): Promise<ChangeDetectionResult> {
  const res = await fetch(`${API_BASE}/change?location_id=${locationId}&year_a=${yearA}&year_b=${yearB}`);
  if (!res.ok) throw new Error('Change detection fetch failed');
  return await res.json();
}

export async function fetchInvestigation(query: string, locationId: string, sceneId?: string): Promise<InvestigationResponse> {
  const url = `${API_BASE}/investigator?query=${encodeURIComponent(query)}&location_id=${locationId}${sceneId ? `&scene_id=${encodeURIComponent(sceneId)}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Investigation fetch failed');
  return await res.json();
}

export function getGeoreferencedImageUrl(sceneId: string, bbox: [number, number, number, number]): string {
  return `${API_BASE}/scenes/georeferenced?scene_id=${encodeURIComponent(sceneId)}&min_lon=${bbox[0]}&min_lat=${bbox[1]}&max_lon=${bbox[2]}&max_lat=${bbox[3]}`;
}

export async function fetchSceneMeasurements(sceneId: string, bbox: [number, number, number, number]): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/scenes/measurements?scene_id=${encodeURIComponent(sceneId)}&min_lon=${bbox[0]}&min_lat=${bbox[1]}&max_lon=${bbox[2]}&max_lat=${bbox[3]}`);
    if (!res.ok) throw new Error('Measurements fetch failed');
    return await res.json();
  } catch (err) {
    console.warn('Measurements fetch failed, returning default:', err);
    return {
      scene_id: sceneId,
      mean_ndvi: 0.2107,
      vegetation_pct: 29.06,
      mean_ndwi: -0.1425,
      water_pct: 3.84,
      built_up_pct: 47.10
    };
  }
}

export async function fetchFutureScenarios(locationId: string): Promise<FutureScenario[]> {
  const res = await fetch(`${API_BASE}/future/simulate?location_id=${locationId}`);
  if (!res.ok) throw new Error('Future scenarios fetch failed');
  return await res.json();
}

export async function runRegistration(loweRatio: number = 0.75, ransacThresh: number = 5.0): Promise<RegistrationResult> {
  const res = await fetch(`${API_BASE}/vision/register?lowe_ratio=${loweRatio}&ransac_thresh=${ransacThresh}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Registration failed');
  return await res.json();
}

export async function generateReport(locationId: string, yearA: number, yearB: number, notes?: string): Promise<any> {
  const url = `${API_BASE}/reports/generate?location_id=${locationId}&year_a=${yearA}&year_b=${yearB}${notes ? `&notes=${encodeURIComponent(notes)}` : ''}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Report generation failed');
  return await res.json();
}

// =============================================================================
// Phase 6 & 7: Environmental Investigator & Streaming Infrastructure
// =============================================================================

import type {
  StationMeasurement,
  HeatmapData,
  SymptomAnalysisResult,
  ForecastResponseData,
  ResearchQueryResponseData
} from '../types/investigation';

export async function fetchEnvironmentalStations(
  indicator?: string,
  location: string = 'bengaluru'
): Promise<StationMeasurement[]> {
  const params = new URLSearchParams();
  if (indicator) params.append('indicator', indicator);
  if (location) params.append('location', location);

  const res = await fetch(`${API_BASE}/environmental/stations?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch environmental stations: ${res.statusText}`);
  return await res.json();
}

export async function fetchEnvironmentalHeatmap(
  indicator: string = 'PM2.5',
  minLon: number = 77.45,
  minLat: number = 12.80,
  maxLon: number = 77.75,
  maxLat: number = 13.15,
  power: number = 2.0,
  searchRadiusKm: number = 10.0
): Promise<HeatmapData> {
  const params = new URLSearchParams({
    indicator,
    min_lon: minLon.toString(),
    min_lat: minLat.toString(),
    max_lon: maxLon.toString(),
    max_lat: maxLat.toString(),
    power: power.toString(),
    search_radius_km: searchRadiusKm.toString()
  });

  const res = await fetch(`${API_BASE}/environmental/heatmap?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to compute IDW heatmap: ${res.statusText}`);
  return await res.json();
}

export async function postSymptomAnalysis(
  symptomQuery: string,
  location: string = 'Bengaluru'
): Promise<SymptomAnalysisResult> {
  const res = await fetch(`${API_BASE}/environmental/symptom-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symptom_query: symptomQuery, location })
  });
  if (!res.ok) throw new Error(`Symptom analysis failed: ${res.statusText}`);
  return await res.json();
}

export async function postEnvironmentalForecast(
  indicator: string = 'PM2.5',
  horizon: string = '+5 years',
  reductionPercentage: number = 30.0,
  location: string = 'Bengaluru'
): Promise<ForecastResponseData> {
  const res = await fetch(`${API_BASE}/environmental/forecast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      indicator,
      horizon,
      reduction_percentage: reductionPercentage,
      location
    })
  });
  if (!res.ok) throw new Error(`Forecast request failed: ${res.statusText}`);
  return await res.json();
}

export async function fetchEnvironmentalResearch(
  query: string,
  limit: number = 4
): Promise<ResearchQueryResponseData> {
  const params = new URLSearchParams({ q: query, limit: limit.toString() });
  const res = await fetch(`${API_BASE}/environmental/research?${params.toString()}`);
  if (!res.ok) throw new Error(`Research query failed: ${res.statusText}`);
  return await res.json();
}

export async function resetInvestigatorSession(sessionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/investigator/reset?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error(`Session reset failed: ${res.statusText}`);
  return await res.json();
}

export async function streamInvestigatorChat(
  message: string,
  sessionId: string,
  onEvent: (eventType: string, data: any) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/investigator/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal
  });

  if (!response.ok) {
    throw new Error(`Chat stream request failed with HTTP ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('ReadableStream not supported by browser.');

  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let currentEvent = '';
  let currentData: string[] = [];

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line) {
        if (currentEvent && currentData.length > 0) {
          try {
            const parsed = JSON.parse(currentData.join('\n'));
            onEvent(currentEvent, parsed);
          } catch (e) {
            console.warn('Failed to parse SSE event payload:', currentData.join('\n'), e);
          }
          currentEvent = '';
          currentData = [];
        }
      } else if (line.startsWith('event:')) {
        currentEvent = line.replace('event:', '').trim();
      } else if (line.startsWith('data:')) {
        currentData.push(line.replace('data:', '').trim());
      }
    }
  }

  // Handle any remaining event in buffer
  if (currentEvent && currentData.length > 0) {
    try {
      const parsed = JSON.parse(currentData.join('\n'));
      onEvent(currentEvent, parsed);
    } catch (e) {
      console.warn('Failed to parse trailing SSE event:', e);
    }
  }
}

