import React, { useState } from 'react';
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
import { EarthObservationExplorer } from './components/EarthObservationExplorer';
import { InvestigationWorkspace } from './components/investigation/InvestigationWorkspace';
import { NavSection } from './types';
import { GeoProvider, useGeoContext } from './context/GeoContext';

const MainAppContent: React.FC = () => {
  const {
    currentLocation,
    availableLocations,
    scenes,
    chronologicalScenes,
    selectedScene,
    selectedYear,
    georeferencedOverlayUrl,
    overlayBounds,
    measurements,
    analysis,
    changeData,
    investigation,
    investigating,
    isSearching,
    interfaceMode,
    activeTimelineView,
    layers,
    dataSources,
    selectLocation,
    searchLocation,
    selectScene,
    selectYear,
    runInvestigationQuery,
    toggleLayer,
    toggleDataSource,
    setInterfaceMode,
    setActiveTimelineView,
    zoomToRegion
  } = useGeoContext();

  const [activeTab, setActiveTab] = useState<NavSection>('explore');
  const [is3DMode, setIs3DMode] = useState(true);

  // MODE A: Dedicated AI Environmental Investigator Workspace
  if (interfaceMode === 'investigator') {
    return (
      <InvestigationWorkspace
        currentLocation={currentLocation}
        availableLocations={availableLocations}
        onSelectLocation={selectLocation}
        onSearchLocation={searchLocation}
        onSwitchMode={setInterfaceMode}
        scenes={scenes}
        selectedScene={selectedScene}
        onSelectScene={selectScene}
      />
    );
  }

  // MODE B: Full Earth Observation Explorer (Preserving original 3D globe, timeline, pipeline, and tools)
  return (
    <div className="flex h-screen bg-space-950 text-slate-100 overflow-hidden font-sans">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={(tab) => {
          if (tab === 'investigator') {
            setInterfaceMode('investigator');
          } else {
            setActiveTab(tab);
          }
        }}
        layers={layers}
        onLayerToggle={toggleLayer}
        dataSources={dataSources}
        onDataSourceToggle={toggleDataSource}
      />

      {/* 2. Main Center Workspace */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <Header
          currentLocation={currentLocation}
          availableLocations={availableLocations}
          onSelectLocation={selectLocation}
          onSearchLocation={searchLocation}
          onZoomToRegion={zoomToRegion}
          isSearching={isSearching}
          interfaceMode={interfaceMode}
          onSwitchMode={setInterfaceMode}
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
                onSelectYear={selectYear}
                is3DMode={is3DMode}
                onToggle3D={() => setIs3DMode(!is3DMode)}
              />

              {/* Processing Pipeline & Visual Multi-spectral Layers */}
              <div className="grid grid-cols-2 gap-3.5">
                <PipelineVisualizer />
                <VisualLayersBar previewUrl={scenes[0]?.thumbnail_url} />
              </div>

              {/* Bottom Multi-Decade Timeline Scrubber */}
              <TimelineScrubber
                currentYear={selectedYear}
                onYearChange={selectYear}
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
            <CVTechnicalWorkspace changeData={changeData} scenes={scenes} />
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
                onRunQuery={runInvestigationQuery}
                isLoading={investigating}
              />
            </div>
          )}
        </div>
      </div>

      {/* 3. Persistent Right-Side AI Investigator & Evidence Graph Panel (in Explorer mode) */}
      {activeTab === 'explore' && (
        <AIInvestigatorPanel
          investigation={investigation}
          onRunQuery={runInvestigationQuery}
          isLoading={investigating}
        />
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <GeoProvider>
      <MainAppContent />
    </GeoProvider>
  );
};

export default App;
