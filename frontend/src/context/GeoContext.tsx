import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  LocationInfo, SatelliteScene, EnvironmentalAnalysis,
  ChangeDetectionResult, InvestigationResponse, LayerState,
  DataSourceState, AppInterfaceMode
} from '../types';
import {
  fetchLocations, fetchScenes, fetchChronologicalScenes,
  fetchAnalysis, fetchChangeDetection, fetchInvestigation,
  geocodeLocation, getGeoreferencedImageUrl, fetchSceneMeasurements
} from '../services/api';

export interface RealMeasurements {
  scene_id: string;
  date: string;
  sensor: string;
  cloud_cover: number;
  spatial_resolution_m: number;
  mean_ndvi: number;
  vegetation_pct: number;
  mean_ndwi: number;
  water_pct: number;
  mean_ndbi?: number;
  built_up_pct: number;
  bbox: [number, number, number, number];
  calculation_status?: string;
}

export interface SharedGeoState {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  aoi: [number, number, number, number];
  selectedSource: string;
  selectedScene: SatelliteScene | null;
  selectedYear: number;
  scenes: SatelliteScene[];
  chronologicalScenes: SatelliteScene[];
  georeferencedOverlayUrl: string;
  overlayBounds: [[number, number], [number, number]];
  measurements: RealMeasurements | null;
  analysis: EnvironmentalAnalysis | null;
  changeData: ChangeDetectionResult | null;
  investigation: InvestigationResponse | null;
  investigating: boolean;
  userQuery: string;
  isSearching: boolean;
  interfaceMode: AppInterfaceMode;
  activeTimelineView: 'historical' | 'current' | 'future';
  layers: LayerState;
  dataSources: DataSourceState;

  // Actions
  selectLocation: (loc: LocationInfo) => void;
  searchLocation: (query: string) => Promise<void>;
  selectScene: (scene: SatelliteScene) => void;
  selectYear: (year: number) => void;
  runInvestigationQuery: (query: string) => Promise<void>;
  toggleLayer: (key: keyof LayerState) => void;
  toggleDataSource: (key: keyof DataSourceState) => void;
  setInterfaceMode: (mode: AppInterfaceMode) => void;
  setActiveTimelineView: (view: 'historical' | 'current' | 'future') => void;
  zoomToRegion: () => void;
}

const GeoContext = createContext<SharedGeoState | null>(null);

export const GeoProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [interfaceMode, setInterfaceMode] = useState<AppInterfaceMode>('investigator');
  const [locations, setLocations] = useState<LocationInfo[]>([]);
  const [currentLocation, setCurrentLocation] = useState<LocationInfo>({
    id: "bengaluru",
    name: "Bengaluru, Karnataka, India",
    country: "India",
    latitude: 12.9716,
    longitude: 77.5946,
    bbox: [77.45, 12.90, 77.70, 13.10],
    default_crs: "EPSG:4326",
    target_utm: "EPSG:32643",
    description: "High-growth global IT hub undergoing intensive multi-decade urban expansion and green canopy reduction."
  });

  const [scenes, setScenes] = useState<SatelliteScene[]>([]);
  const [chronologicalScenes, setChronologicalScenes] = useState<SatelliteScene[]>([]);
  const [selectedScene, setSelectedScene] = useState<SatelliteScene | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const [selectedSource, setSelectedSource] = useState<string>('sentinel');
  const [measurements, setMeasurements] = useState<RealMeasurements | null>(null);
  const [analysis, setAnalysis] = useState<EnvironmentalAnalysis | null>(null);
  const [changeData, setChangeData] = useState<ChangeDetectionResult | null>(null);
  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const [userQuery, setUserQuery] = useState('Why did this region change?');
  const [isSearching, setIsSearching] = useState(false);
  const [activeTimelineView, setActiveTimelineView] = useState<'historical' | 'current' | 'future'>('current');

  const [layers, setLayers] = useState<LayerState>({
    landCover: true,
    ndvi: true,
    waterIndex: false,
    urbanHeat: false,
    changeDetection: true,
    boundaries: true
  });

  const [dataSources, setDataSources] = useState<DataSourceState>({
    landsat: true,
    sentinel: true,
    modis: false,
    planet: true,
    osm: true,
    other: false
  });

  // Calculate Leaflet LatLngBounds from bbox [min_lon, min_lat, max_lon, max_lat]
  const aoi = currentLocation.bbox;
  const overlayBounds: [[number, number], [number, number]] = [
    [aoi[1], aoi[0]], // [south, west]
    [aoi[3], aoi[2]]  // [north, east]
  ];

  const georeferencedOverlayUrl = selectedScene
    ? getGeoreferencedImageUrl(selectedScene.id, aoi)
    : getGeoreferencedImageUrl('default', aoi);

  // 1. Load initial locations
  useEffect(() => {
    fetchLocations().then(locs => {
      setLocations(locs);
      if (locs.length > 0) setCurrentLocation(locs[0]);
    }).catch(console.error);
  }, []);

  // 2. Fetch real STAC scenes, chronological scenes, and base analysis on location change
  useEffect(() => {
    fetchScenes(currentLocation.id).then(sc => {
      setScenes(sc);
      if (sc.length > 0) {
        setSelectedScene(sc[0]);
        setSelectedYear(sc[0].year);
      }
    }).catch(console.error);

    fetchChronologicalScenes(currentLocation.id).then(setChronologicalScenes).catch(console.error);
    fetchAnalysis(currentLocation.id, selectedYear).then(setAnalysis).catch(console.error);
    fetchChangeDetection(currentLocation.id, 1985, selectedYear).then(setChangeData).catch(console.error);
  }, [currentLocation]);

  // 3. Compute real environmental measurements whenever selectedScene changes
  useEffect(() => {
    if (selectedScene) {
      fetchSceneMeasurements(selectedScene.id, currentLocation.bbox).then(m => {
        setMeasurements(m);
      }).catch(console.error);
    }
  }, [selectedScene, currentLocation]);

  // 4. Initial investigation synthesis with real context
  useEffect(() => {
    fetchInvestigation(userQuery, currentLocation.id, selectedScene?.id).then(setInvestigation).catch(console.error);
  }, [currentLocation, selectedScene]);

  const searchLocation = async (query: string) => {
    setIsSearching(true);
    try {
      const geocoded = await geocodeLocation(query);
      if (geocoded) {
        setCurrentLocation(geocoded);
        setLocations(prev => {
          if (!prev.find(l => l.id === geocoded.id)) {
            return [geocoded, ...prev];
          }
          return prev;
        });
      }
    } catch (err) {
      console.error('Failed to geocode location:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const selectScene = (scene: SatelliteScene) => {
    setSelectedScene(scene);
    setSelectedYear(scene.year);
  };

  const selectYear = (year: number) => {
    setSelectedYear(year);
    // Find matching real scene
    const match = scenes.find(s => s.year === year);
    if (match) setSelectedScene(match);
  };

  const runInvestigationQuery = async (query: string) => {
    setUserQuery(query);
    setInvestigating(true);
    try {
      const res = await fetchInvestigation(query, currentLocation.id, selectedScene?.id);
      setInvestigation(res);
    } catch (err) {
      console.error('Investigation failed:', err);
    } finally {
      setInvestigating(false);
    }
  };

  const toggleLayer = (key: keyof LayerState) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleDataSource = (key: keyof DataSourceState) => {
    setDataSources(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const zoomToRegion = () => {
    setSelectedYear(2025);
  };

  return (
    <GeoContext.Provider
      value={{
        currentLocation,
        availableLocations: locations,
        aoi,
        selectedSource,
        selectedScene,
        selectedYear,
        scenes,
        chronologicalScenes,
        georeferencedOverlayUrl,
        overlayBounds,
        measurements,
        analysis,
        changeData,
        investigation,
        investigating,
        userQuery,
        isSearching,
        interfaceMode,
        activeTimelineView,
        layers,
        dataSources,
        selectLocation: setCurrentLocation,
        searchLocation,
        selectScene,
        selectYear,
        runInvestigationQuery,
        toggleLayer,
        toggleDataSource,
        setInterfaceMode,
        setActiveTimelineView,
        zoomToRegion
      }}
    >
      {children}
    </GeoContext.Provider>
  );
};

export const useGeoContext = () => {
  const ctx = useContext(GeoContext);
  if (!ctx) throw new Error('useGeoContext must be used within GeoProvider');
  return ctx;
};

