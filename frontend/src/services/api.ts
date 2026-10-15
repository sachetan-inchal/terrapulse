import type { 
  LocationInfo, SatelliteScene, EnvironmentalAnalysis, 
  ChangeDetectionResult, RegistrationResult, InvestigationResponse, 
  FutureScenario 
} from '../types';

const API_BASE = 'http://127.0.0.1:8000/api';

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
        name: "Bengaluru, Karnataka",
        country: "India",
        latitude: 12.9716,
        longitude: 77.5946,
        bbox: [77.45, 12.85, 77.75, 13.10],
        default_crs: "EPSG:4326",
        target_utm: "EPSG:32643",
        description: "High-growth global IT hub undergoing intensive multi-decade urban expansion and green canopy reduction."
      }
    ];
  }
}

export async function fetchScenes(locationId: string = 'bengaluru', maxCloud: number = 20.0): Promise<SatelliteScene[]> {
  try {
    const res = await fetch(`${API_BASE}/scenes?location_id=${locationId}&max_cloud=${maxCloud}`);
    if (!res.ok) throw new Error('Failed to fetch scenes');
    return await res.json();
  } catch (err) {
    return [
      {
        id: "LS05_1985_BEN",
        mission: "Landsat 5",
        sensor: "Thematic Mapper (TM)",
        acquisition_date: "1985-03-22",
        year: 1985,
        cloud_cover: 1.2,
        spatial_resolution_m: 30.0,
        thumbnail_url: "https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?w=400&q=80",
        crs: "EPSG:32643",
        bbox: [77.45, 12.85, 77.75, 13.10]
      },
      {
        id: "LS08_2015_BEN",
        mission: "Landsat 8",
        sensor: "Operational Land Imager (OLI)",
        acquisition_date: "2015-02-28",
        year: 2015,
        cloud_cover: 0.8,
        spatial_resolution_m: 30.0,
        thumbnail_url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=400&q=80",
        crs: "EPSG:32643",
        bbox: [77.45, 12.85, 77.75, 13.10]
      },
      {
        id: "S2A_2020_BEN",
        mission: "Sentinel-2",
        sensor: "MultiSpectral Instrument (MSI)",
        acquisition_date: "2020-01-18",
        year: 2020,
        cloud_cover: 0.4,
        spatial_resolution_m: 10.0,
        thumbnail_url: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400&q=80",
        crs: "EPSG:32643",
        bbox: [77.45, 12.85, 77.75, 13.10]
      },
      {
        id: "PS_2024_BEN",
        mission: "PlanetScope",
        sensor: "SuperDove (PSB.SD)",
        acquisition_date: "2024-03-05",
        year: 2024,
        cloud_cover: 0.1,
        spatial_resolution_m: 3.0,
        thumbnail_url: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&q=80",
        crs: "EPSG:32643",
        bbox: [77.45, 12.85, 77.75, 13.10]
      }
    ];
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

export async function fetchInvestigation(query: string, locationId: string): Promise<InvestigationResponse> {
  const res = await fetch(`${API_BASE}/investigator?query=${encodeURIComponent(query)}&location_id=${locationId}`);
  if (!res.ok) throw new Error('Investigation fetch failed');
  return await res.json();
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
