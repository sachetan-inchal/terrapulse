import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { OverviewWorkspace } from './components/workspaces/OverviewWorkspace';
import { SatelliteImageryWorkspace } from './components/workspaces/SatelliteImageryWorkspace';
import { SpectralAnalysisWorkspace } from './components/workspaces/SpectralAnalysisWorkspace';
import { LandCoverWorkspace } from './components/LandCoverWorkspace';
import { HistoricalAnalysisWorkspace } from './components/workspaces/HistoricalAnalysisWorkspace';
import { ChangeDetectionWorkspace } from './components/workspaces/ChangeDetectionWorkspace';
import { EnvironmentalIndicatorsWorkspace } from './components/workspaces/EnvironmentalIndicatorsWorkspace';
import { CVTechnicalWorkspace } from './components/CVTechnicalWorkspace';
import { ReportsWorkspace } from './components/ReportsWorkspace';
import { InvestigationWorkspace } from './components/investigation/InvestigationWorkspace';
import { NavSection } from './types';
import { GeoProvider, useGeoContext } from './context/GeoContext';

const MainAppContent: React.FC = () => {
  const {
    currentLocation,
    availableLocations,
    scenes,
    selectedScene,
    selectedYear,
    measurements,
    analysis,
    changeData,
    isSearching,
    interfaceMode,
    activeTimelineView,
    layers,
    dataSources,
    selectLocation,
    searchLocation,
    selectScene,
    selectYear,
    toggleLayer,
    toggleDataSource,
    setInterfaceMode,
    setActiveTimelineView,
    zoomToRegion
  } = useGeoContext();

  // Overview is the clean default screen
  const [activeTab, setActiveTab] = useState<NavSection>('overview');
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

  // MODE B: Dedicated Modular Earth Observation Explorer (9 Workspaces)
  return (
    <div className="flex h-screen bg-[#030612] text-slate-100 overflow-hidden font-sans">
      {/* 1. Left Sidebar Navigation (9 Workspaces) */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        layers={layers}
        onLayerToggle={toggleLayer}
        dataSources={dataSources}
        onDataSourceToggle={toggleDataSource}
      />

      {/* 2. Main Center Application Shell */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header Bar */}
        <Header
          currentLocation={currentLocation}
          availableLocations={availableLocations}
          onSelectLocation={selectLocation}
          onSearchLocation={searchLocation}
          onZoomToRegion={zoomToRegion}
          isSearching={isSearching}
          interfaceMode={interfaceMode}
          onSwitchMode={setInterfaceMode}
          selectedYear={selectedYear}
          onSelectYear={selectYear}
        />

        {/* Dynamic Center Stage Workspace (One Active Workspace at a Time) */}
        <main className="flex-1 overflow-hidden flex flex-col">
          {activeTab === 'overview' && (
            <OverviewWorkspace
              location={currentLocation}
              scenes={scenes}
              selectedYear={selectedYear}
              onSelectYear={selectYear}
              is3DMode={is3DMode}
              onToggle3D={() => setIs3DMode(!is3DMode)}
              onZoomToRegion={zoomToRegion}
              layers={layers}
              onLayerToggle={toggleLayer}
              measurements={measurements}
              onOpenInvestigator={() => setInterfaceMode('investigator')}
            />
          )}

          {activeTab === 'imagery' && (
            <SatelliteImageryWorkspace
              location={currentLocation}
              scenes={scenes}
              selectedScene={selectedScene}
              onSelectScene={selectScene}
              selectedYear={selectedYear}
              onSelectYear={selectYear}
              dataSources={dataSources}
              onDataSourceToggle={toggleDataSource}
              onZoomToRegion={zoomToRegion}
            />
          )}

          {activeTab === 'spectral' && (
            <SpectralAnalysisWorkspace
              location={currentLocation}
              scenes={scenes}
              selectedYear={selectedYear}
            />
          )}

          {activeTab === 'landcover' && (
            <LandCoverWorkspace
              analysis={analysis}
              currentYear={selectedYear}
            />
          )}

          {activeTab === 'historical' && (
            <HistoricalAnalysisWorkspace
              location={currentLocation}
              scenes={scenes}
              currentYear={selectedYear}
              onYearChange={selectYear}
              analysis={analysis}
              activeTimelineView={activeTimelineView}
              onViewChange={setActiveTimelineView}
            />
          )}

          {activeTab === 'changedetection' && (
            <ChangeDetectionWorkspace
              location={currentLocation}
              scenes={scenes}
              changeData={changeData}
            />
          )}

          {activeTab === 'indicators' && (
            <EnvironmentalIndicatorsWorkspace
              location={currentLocation}
              scenes={scenes}
              measurements={measurements}
            />
          )}

          {activeTab === 'computervision' && (
            <CVTechnicalWorkspace
              changeData={changeData}
              scenes={scenes}
            />
          )}

          {activeTab === 'reports' && (
            <ReportsWorkspace />
          )}
        </main>
      </div>
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
