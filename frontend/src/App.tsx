import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { GlobeMapStage } from './components/GlobeMapStage';
import { PipelineVisualizer } from './components/PipelineVisualizer';
import { VisualLayersBar } from './components/VisualLayersBar';
import { TimelineScrubber } from './components/TimelineScrubber';
import { AIInvestigatorPanel } from './components/AIInvestigatorPanel';
import { CVTechnicalWorkspace } from './components/CVTechnicalWorkspace';
import { TimeSeriesWorkspace } from './components/TimeSeriesWorkspace';
import { LandCoverWorkspace } from './components/LandCoverWorkspace';
import { FutureScenariosWorkspace } from './components/FutureScenariosWorkspace';
import { ReportsWorkspace } from './components/ReportsWorkspace';

import { 
  NavSection, LocationInfo, SatelliteScene, 
  EnvironmentalAnalysis, ChangeDetectionResult, 
  InvestigationResponse, LayerState, DataSourceState 
} from './types';
import { 
  fetchLocations, fetchScenes, fetchAnalysis, 
  fetchChangeDetection, fetchInvestigation 
} from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavSection>('explore');
  const [locations, setLocations] = useState<LocationInfo[]>([]);
  const [currentLocation, setCurrentLocation] = useState<LocationInfo>({
    id: "bengaluru",
    name: "Bengaluru, Karnataka",
    country: "India",
    latitude: 12.9716,
    longitude: 77.5946,
    bbox: [77.45, 12.85, 77.75, 13.10],
    default_crs: "EPSG:4326",
    target_utm: "EPSG:32643",
    description: "High-growth global IT hub undergoing intensive multi-decade urban expansion and green canopy reduction."
  });

  const [scenes, setScenes] = useState<SatelliteScene[]>([]);
  const [selectedYear, setSelectedYear] = useState<number>(2024);
  const [analysis, setAnalysis] = useState<EnvironmentalAnalysis | null>(null);
  const [changeData, setChangeData] = useState<ChangeDetectionResult | null>(null);
  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const [activeTimelineView, setActiveTimelineView] = useState<'historical' | 'current' | 'future'>('current');
  const [is3DMode, setIs3DMode] = useState(true);

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

  // Load initial datasets
  useEffect(() => {
    fetchLocations().then(locs => {
      setLocations(locs);
      if (locs.length > 0) setCurrentLocation(locs[0]);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    fetchScenes(currentLocation.id).then(setScenes).catch(console.error);
    fetchAnalysis(currentLocation.id, selectedYear).then(setAnalysis).catch(console.error);
    fetchChangeDetection(currentLocation.id, 1985, selectedYear).then(setChangeData).catch(console.error);
    fetchInvestigation("Why did this region change?", currentLocation.id).then(setInvestigation).catch(console.error);
  }, [currentLocation, selectedYear]);

  const handleRunInvestigation = async (query: string) => {
    setInvestigating(true);
    try {
      const res = await fetchInvestigation(query, currentLocation.id);
      setInvestigation(res);
    } catch (err) {
      console.error(err);
    } finally {
      setInvestigating(false);
    }
  };

  const handleLayerToggle = (key: keyof LayerState) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleDataSourceToggle = (key: keyof DataSourceState) => {
    setDataSources(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex h-screen bg-space-950 text-slate-100 overflow-hidden font-sans">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        layers={layers}
        onLayerToggle={handleLayerToggle}
        dataSources={dataSources}
        onDataSourceToggle={handleDataSourceToggle}
      />

      {/* 2. Main Center Workspace */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <Header
          currentLocation={currentLocation}
          availableLocations={locations}
          onSelectLocation={setCurrentLocation}
          onZoomToRegion={() => setSelectedYear(2024)}
        />

        {/* Dynamic Center Stage Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'explore' && (
            <div className="p-4 space-y-3.5">
              {/* Globe / Map Stage */}
              <GlobeMapStage
                location={currentLocation}
                scenes={scenes}
                selectedYear={selectedYear}
                onSelectYear={setSelectedYear}
                is3DMode={is3DMode}
                onToggle3D={() => setIs3DMode(!is3DMode)}
              />

              {/* Processing Pipeline & Visual Multi-spectral Layers */}
              <div className="grid grid-cols-2 gap-3.5">
                <PipelineVisualizer />
                <VisualLayersBar />
              </div>

              {/* Bottom Multi-Decade Timeline Scrubber */}
              <TimelineScrubber
                currentYear={selectedYear}
                onYearChange={setSelectedYear}
                analysis={analysis || undefined}
                activeTimelineView={activeTimelineView}
                onViewChange={setActiveTimelineView}
              />
            </div>
          )}

          {activeTab === 'timeseries' && (
            <TimeSeriesWorkspace scenes={scenes} currentYear={selectedYear} />
          )}

          {activeTab === 'computervision' && (
            <CVTechnicalWorkspace changeData={changeData} />
          )}

          {(activeTab === 'landcover' || activeTab === 'environmental') && (
            <LandCoverWorkspace analysis={analysis} currentYear={selectedYear} />
          )}

          {activeTab === 'future' && (
            <FutureScenariosWorkspace />
          )}

          {activeTab === 'reports' && (
            <ReportsWorkspace />
          )}

          {(activeTab === 'investigator' || activeTab === 'evidence') && (
            <div className="p-6 max-w-4xl mx-auto">
              <div className="text-sm font-bold font-mono text-cyan-accent mb-4">
                Full-Screen AI Investigator & Multi-Agent Evidence View
              </div>
              <AIInvestigatorPanel
                investigation={investigation}
                onRunQuery={handleRunInvestigation}
                isLoading={investigating}
              />
            </div>
          )}
        </div>
      </div>

      {/* 3. Persistent Right-Side AI Investigator & Evidence Graph Panel */}
      {activeTab === 'explore' && (
        <AIInvestigatorPanel
          investigation={investigation}
          onRunQuery={handleRunInvestigation}
          isLoading={investigating}
        />
      )}
    </div>
  );
};

export default App;
