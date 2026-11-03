import React, { useState, useEffect } from 'react';
import {
  Globe2, Search, X, Image as ImageIcon, MapPin, BarChart3, User,
  Calendar, CheckSquare, Square, Layers, Compass, Plus, Minus,
  ChevronLeft, ChevronRight, Download, Crosshair, Loader2, Activity,
  Filter
} from 'lucide-react';
import {
  LocationInfo, SatelliteScene, LayerState, DataSourceState,
  AppInterfaceMode
} from '../types';
import { InteractiveSatelliteMap } from './InteractiveSatelliteMap';
import { Interactive3DGlobe } from './Interactive3DGlobe';
import { RealMeasurements } from '../context/GeoContext';

interface EarthObservationExplorerProps {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  scenes: SatelliteScene[];
  chronologicalScenes: SatelliteScene[];
  selectedScene: SatelliteScene | null;
  overlayUrl: string;
  overlayBounds: [[number, number], [number, number]];
  measurements: RealMeasurements | null;
  onSelectScene: (scene: SatelliteScene) => void;
  onSelectLocation: (loc: LocationInfo) => void;
  onSearchLocation: (query: string) => Promise<void>;
  isSearching: boolean;
  dataSources: DataSourceState;
  onDataSourceToggle: (key: keyof DataSourceState) => void;
  onSwitchMode: (mode: AppInterfaceMode) => void;
}

export const EarthObservationExplorer: React.FC<EarthObservationExplorerProps> = ({
  currentLocation,
  availableLocations,
  scenes,
  chronologicalScenes,
  selectedScene,
  overlayUrl,
  overlayBounds,
  measurements,
  onSelectScene,
  onSelectLocation,
  onSearchLocation,
  isSearching,
  dataSources,
  onDataSourceToggle,
  onSwitchMode,
}) => {
  const [searchQuery, setSearchQuery] = useState(currentLocation.name.split(',')[0]);
  const [selectedDecade, setSelectedDecade] = useState<string>('all');
  const [showAllDates, setShowAllDates] = useState(false);
  const [viewMode, setViewMode] = useState<'map' | 'globe'>('map');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [isRotating, setIsRotating] = useState(false);
  const [activeTabNav, setActiveTabNav] = useState<'imagery' | 'locations' | 'analytics'>('imagery');

  useEffect(() => {
    setSearchQuery(currentLocation.name.split(',')[0]);
  }, [currentLocation]);

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    await onSearchLocation(searchQuery);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
  };

  const lat = currentLocation.latitude;
  const lon = currentLocation.longitude;
  const coordStr = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}, ${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`;

  // Filter scenes based on active data source toggles
  const filteredScenes = scenes.filter(sc => {
    const isLandsat = sc.mission.toLowerCase().includes('landsat');
    const isSentinel = sc.mission.toLowerCase().includes('sentinel');
    if (isLandsat && !dataSources.landsat) return false;
    if (isSentinel && !dataSources.sentinel) return false;
    return true;
  });

  // Authentic chronological observations list derived solely from retrieved STAC observations
  const chronoList = chronologicalScenes.length > 0 
    ? chronologicalScenes.filter(sc => {
        const isLandsat = sc.mission.toLowerCase().includes('landsat');
        const isSentinel = sc.mission.toLowerCase().includes('sentinel');
        if (isLandsat && !dataSources.landsat) return false;
        if (isSentinel && !dataSources.sentinel) return false;
        return true;
      })
    : filteredScenes;

  // Compute actual decade breakdown from real observations
  const decadesMap: { [key: string]: number } = {};
  filteredScenes.forEach(sc => {
    const dec = `${Math.floor(sc.year / 10) * 10}s`;
    decadesMap[dec] = (decadesMap[dec] || 0) + 1;
  });

  const availableDecades = Object.keys(decadesMap).sort().reverse();

  // Apply decade filter to gallery
  const applyDecadeFilter = (items: SatelliteScene[]) => {
    if (selectedDecade === 'all') return items;
    const dec = parseInt(selectedDecade.replace('s', ''), 10);
    return items.filter(it => it.year >= dec && it.year < dec + 10);
  };

  // Group 1: Real observations at this location
  const groupSameLocation = applyDecadeFilter(filteredScenes);

  // Group 2: Clear sky scenes (< 5% cloud)
  const groupClearSky = applyDecadeFilter(filteredScenes.filter(s => s.cloud_cover < 5.0));

  // Group 3: MultiSpectral Sentinel-2 10m scenes
  const groupSentinel = applyDecadeFilter(filteredScenes.filter(s => s.mission.toLowerCase().includes('sentinel')));

  const handleScrollLeft = () => {
    setCarouselIndex(prev => Math.max(0, prev - 2));
  };

  const handleScrollRight = () => {
    setCarouselIndex(prev => Math.min(Math.max(0, chronoList.length - 8), prev + 2));
  };

  return (
    <div className="flex flex-col h-screen bg-[#070b14] text-slate-100 overflow-hidden font-sans select-none">
      {/* 1. TOP HEADER BAR */}
      <header className="h-14 bg-[#0a101f] border-b border-[#1b253b] px-5 flex items-center justify-between shrink-0 z-30">
        {/* Brand Logo & Title */}
        <div className="flex items-center space-x-3 shrink-0">
          <div className="w-8 h-8 rounded-full bg-[#1e40af]/40 border border-[#3b82f6]/60 flex items-center justify-center shadow-[0_0_12px_rgba(59,130,246,0.5)]">
            <Globe2 className="w-5 h-5 text-[#60a5fa]" />
          </div>
          <div>
            <div className="text-sm font-bold tracking-wide text-white flex items-center gap-2">
              Earth Observation Archive
            </div>
            <div className="text-[10px] text-slate-400 tracking-wider">
              Search • Discover • Compare • Analyze
            </div>
          </div>
        </div>

        {/* Global Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex items-center w-[460px] mx-4">
          <div className="relative flex-1 flex items-center bg-[#0d1629] border border-[#1e293b] rounded-l-md px-3 py-1.5 focus-within:border-[#38bdf8] transition-all">
            <Search className="w-4 h-4 text-slate-400 mr-2 shrink-0" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search worldwide locations (e.g. Bengaluru, Tokyo)..."
              className="w-full bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none"
            />
            {searchQuery && (
              <button type="button" onClick={handleClearSearch} className="text-slate-400 hover:text-white p-0.5">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className="px-4 py-1.5 bg-[#2563eb] hover:bg-[#1d4ed8] text-white text-xs font-medium rounded-r-md transition-colors disabled:opacity-50 shrink-0 flex items-center gap-1.5"
          >
            {isSearching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Search'}
          </button>
        </form>

        {/* Header Right Actions & Mode Switcher */}
        <div className="flex items-center space-x-4 shrink-0 text-xs text-slate-300">
          {/* Interface Mode Switcher Pill */}
          <div className="flex items-center bg-[#0d1629] p-0.5 rounded-lg border border-[#1e293b]">
            <button
              onClick={() => onSwitchMode('explorer')}
              className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[#2563eb] text-white shadow-sm flex items-center gap-1.5"
            >
              <Globe2 className="w-3.5 h-3.5" />
              Explorer
            </button>
            <button
              onClick={() => onSwitchMode('investigator')}
              className="px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-white flex items-center gap-1.5"
            >
              <span>🤖</span>
              AI Investigator
            </button>
          </div>

          <div className="flex items-center space-x-3 text-slate-400">
            <button 
              onClick={() => setActiveTabNav('imagery')}
              className={`flex items-center space-x-1.5 hover:text-white ${activeTabNav === 'imagery' ? 'text-white font-medium' : ''}`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              <span className="text-[11px]">Imagery ({filteredScenes.length})</span>
            </button>
            <button 
              onClick={() => setActiveTabNav('locations')}
              className={`flex items-center space-x-1.5 hover:text-white ${activeTabNav === 'locations' ? 'text-white font-medium' : ''}`}
            >
              <MapPin className="w-3.5 h-3.5" />
              <span className="text-[11px]">Locations ({availableLocations.length})</span>
            </button>
            <button 
              onClick={() => setActiveTabNav('analytics')}
              className={`flex items-center space-x-1.5 hover:text-white ${activeTabNav === 'analytics' ? 'text-white font-medium' : ''}`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span className="text-[11px]">Analytics</span>
            </button>
            <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
              <User className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>
      </header>

      {/* 2. MAIN 3-PANEL WORKSPACE */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL: Search Results, Data Sources & Filters */}
        <aside className="w-64 bg-[#0a101f] border-r border-[#1b253b] p-3.5 flex flex-col justify-between shrink-0 overflow-y-auto">
          <div className="space-y-4">
            {/* Search Results Card */}
            <div>
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Search Results
              </div>
              <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-2.5">
                <div className="flex items-start space-x-2">
                  <MapPin className="w-4 h-4 text-[#38bdf8] shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-white leading-tight">
                      {currentLocation.name}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                      {coordStr}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Found Relevant Imagery Counts */}
            <div className="space-y-1.5 text-xs">
              <div className="text-[11px] text-slate-400 font-medium">
                Found relevant imagery
              </div>
              <div className="space-y-1 text-slate-300 font-mono text-[11px]">
                <div className="flex items-center justify-between py-0.5 border-b border-slate-800/60">
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <ImageIcon className="w-3.5 h-3.5 text-[#38bdf8]" />
                    Satellite scenes
                  </span>
                  <span className="font-bold text-white">{filteredScenes.length}</span>
                </div>
                <div className="flex items-center justify-between py-0.5 border-b border-slate-800/60">
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <Calendar className="w-3.5 h-3.5 text-[#a855f7]" />
                    Cloud-free (&lt;5%)
                  </span>
                  <span className="font-bold text-white">{filteredScenes.filter(s => s.cloud_cover < 5.0).length}</span>
                </div>
                <div className="flex items-center justify-between py-0.5">
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <Layers className="w-3.5 h-3.5 text-[#10b981]" />
                    Sentinel-2 MSI (10m)
                  </span>
                  <span className="font-bold text-white">{filteredScenes.filter(s => s.mission.includes('Sentinel')).length}</span>
                </div>
              </div>
            </div>

            {/* Sources Checklist */}
            <div>
              <div className="text-[11px] text-slate-400 font-medium mb-1.5">
                Satellite Sources
              </div>
              <div className="space-y-1.5 text-xs">
                {[
                  { key: 'sentinel', label: 'Sentinel-2 L2A (10m)' },
                  { key: 'landsat', label: 'Landsat C2 L2 (30m)' },
                ].map(({ key, label }) => {
                  const checked = dataSources[key as keyof DataSourceState];
                  return (
                    <button
                      key={key}
                      onClick={() => onDataSourceToggle(key as keyof DataSourceState)}
                      className="w-full flex items-center space-x-2 text-left hover:text-white text-slate-300"
                    >
                      {checked ? (
                        <CheckSquare className="w-3.5 h-3.5 text-[#2563eb]" />
                      ) : (
                        <Square className="w-3.5 h-3.5 text-slate-600" />
                      )}
                      <span className="text-[11px] truncate">{label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* View Toggle (Map vs 3D Globe) */}
          <div className="pt-3 border-t border-[#1b253b]">
            <div className="text-[11px] text-slate-400 font-medium mb-1.5">
              View
            </div>
            <div className="grid grid-cols-2 gap-1.5 p-1 bg-[#0f172a] rounded-lg border border-[#1e293b]">
              <button
                onClick={() => setViewMode('map')}
                className={`py-1 rounded text-xs font-medium transition-all ${
                  viewMode === 'map'
                    ? 'bg-[#2563eb] text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Map
              </button>
              <button
                onClick={() => setViewMode('globe')}
                className={`py-1 rounded text-xs font-medium transition-all ${
                  viewMode === 'globe'
                    ? 'bg-[#2563eb] text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                3D Globe
              </button>
            </div>
          </div>
        </aside>

        {/* CENTER VIEWPORT: 2D Satellite Map + Large 3D Earth Globe */}
        <main className="flex-1 relative bg-[#050811] flex flex-col overflow-hidden">
          {/* Top-Right Globe & Map Controls */}
          <div className="absolute top-4 right-4 z-20 flex flex-col space-y-1.5">
            <button
              onClick={() => setIsRotating(!isRotating)}
              className={`w-8 h-8 rounded-lg bg-[#0f172a]/90 hover:bg-[#1e293b] border border-[#1e293b] flex items-center justify-center shadow-lg backdrop-blur-md transition-all ${
                isRotating ? 'text-cyan-300 border-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.5)]' : 'text-slate-300 hover:text-white'
              }`}
              title="Toggle Auto-Rotation"
            >
              <Compass className="w-4 h-4 text-[#38bdf8]" />
            </button>
            <button
              onClick={() => setZoomLevel(prev => Math.min(prev + 0.2, 2.2))}
              className="w-8 h-8 rounded-lg bg-[#0f172a]/90 hover:bg-[#1e293b] border border-[#1e293b] text-slate-300 hover:text-white flex items-center justify-center shadow-lg backdrop-blur-md"
              title="Zoom In"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              onClick={() => setZoomLevel(prev => Math.max(prev - 0.2, 0.7))}
              className="w-8 h-8 rounded-lg bg-[#0f172a]/90 hover:bg-[#1e293b] border border-[#1e293b] text-slate-300 hover:text-white flex items-center justify-center shadow-lg backdrop-blur-md"
              title="Zoom Out"
            >
              <Minus className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode(prev => prev === 'map' ? 'globe' : 'map')}
              className="w-8 h-8 rounded-lg bg-[#0f172a]/90 hover:bg-[#1e293b] border border-[#1e293b] text-slate-300 hover:text-white flex items-center justify-center shadow-lg backdrop-blur-md"
              title="Toggle Map / 3D Globe"
            >
              <Layers className="w-4 h-4 text-[#38bdf8]" />
            </button>
          </div>

          {/* Canvas Area with Left 2D Satellite Map Overlay & Center 3D Globe */}
          <div className="flex-1 relative flex items-center justify-center overflow-hidden">
            {/* Background Deep Space Starfield & Orbit Grid */}
            <div className="absolute inset-0 bg-[#070b14] bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />

            {/* Left 2D Satellite Map Sub-Card */}
            <div className="absolute left-6 top-6 bottom-14 w-[350px] bg-[#0b1222]/95 border border-[#1e293b] rounded-xl overflow-hidden shadow-2xl flex flex-col z-10 backdrop-blur-md">
              {/* Card Header */}
              <div className="px-3 py-2 bg-[#0d1629] border-b border-[#1e293b] flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs font-semibold text-white truncate">
                  <MapPin className="w-3.5 h-3.5 text-[#38bdf8]" />
                  <span>{currentLocation.name.split(',')[0]} (2D Basemap + COG)</span>
                </div>
              </div>

              {/* Interactive 2D Satellite Map with Real Georeferenced Sentinel-2 COG Overlay */}
              <div className="flex-1 relative overflow-hidden bg-slate-950">
                <InteractiveSatelliteMap
                  location={currentLocation}
                  selectedScene={selectedScene}
                  overlayUrl={overlayUrl}
                  overlayBounds={overlayBounds}
                />
              </div>
            </div>

            {/* Large Interactive 3D Earth Globe in the Center */}
            <div className="relative flex items-center justify-center w-[460px] h-[460px]">
              <Interactive3DGlobe
                location={currentLocation}
                selectedScene={selectedScene}
                zoomLevel={zoomLevel}
                isRotating={isRotating}
                className="w-full h-full"
              />
            </div>
          </div>

          {/* Bottom Viewport Status Bar with Real Environmental Stats */}
          <div className="h-9 bg-[#0a101f]/95 border-t border-[#1b253b] px-4 flex items-center justify-between text-xs font-mono text-slate-400 shrink-0 z-20">
            <div className="flex items-center space-x-2 overflow-hidden">
              <span className="w-2 h-2 rounded-full bg-[#38bdf8] animate-pulse shrink-0" />
              <span className="text-slate-300 shrink-0">
                {currentLocation.name.split(',')[0]}
              </span>
              {selectedScene && (
                <span className="text-[10px] text-cyan-400 bg-cyan-950/60 border border-cyan-500/30 px-2 py-0.5 rounded truncate max-w-[280px]">
                  Scene: {selectedScene.id} ({selectedScene.acquisition_date})
                </span>
              )}
            </div>

            <div className="flex items-center space-x-4 text-[11px] shrink-0">
              {measurements && measurements.mean_ndvi !== 0 && (
                <div className="flex items-center space-x-3 text-[10px]">
                  <span className="text-emerald-400">
                    NDVI: <strong>{measurements.mean_ndvi.toFixed(3)}</strong>
                  </span>
                  <span className="text-emerald-300">
                    Veg: <strong>{measurements.vegetation_pct}%</strong>
                  </span>
                  <span className="text-blue-400">
                    Water: <strong>{measurements.water_pct}%</strong>
                  </span>
                  <span className="text-rose-400">
                    Built-up: <strong>{measurements.built_up_pct}%</strong>
                  </span>
                </div>
              )}
              <span>
                Lat: <strong className="text-white">{Math.abs(lat).toFixed(4)}° {lat >= 0 ? 'N' : 'S'}</strong>
              </span>
              <span>
                Lon: <strong className="text-white">{Math.abs(lon).toFixed(4)}° {lon >= 0 ? 'E' : 'W'}</strong>
              </span>
            </div>
          </div>
        </main>

        {/* RIGHT PANEL: Related Satellite Imagery Gallery (Grouped by Real Observations) */}
        <aside className="w-[430px] bg-[#0a101f] border-l border-[#1b253b] flex flex-col shrink-0 overflow-y-auto">
          {/* Header & Decade Filters */}
          <div className="p-3.5 border-b border-[#1b253b]">
            <div className="text-xs font-bold text-white mb-2 flex items-center justify-between">
              <span>Related Imagery <span className="text-slate-400 font-normal">({filteredScenes.length} observations)</span></span>
              {selectedScene && (
                <span className="text-[9px] text-[#38bdf8] font-mono">
                  Active: {selectedScene.mission}
                </span>
              )}
            </div>
            {/* Decade Filter Tabs */}
            <div className="flex flex-wrap gap-1 text-[11px] font-mono">
              <button
                onClick={() => setSelectedDecade('all')}
                className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                  selectedDecade === 'all'
                    ? 'bg-[#2563eb] text-white font-bold'
                    : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
                }`}
              >
                All ({filteredScenes.length})
              </button>
              {availableDecades.map(dec => (
                <button
                  key={dec}
                  onClick={() => setSelectedDecade(dec)}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                    selectedDecade === dec
                      ? 'bg-[#2563eb] text-white font-bold'
                      : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
                  }`}
                >
                  {dec} ({decadesMap[dec]})
                </button>
              ))}
            </div>
          </div>

          {/* Group 1: Same Location Temporal Observations */}
          <div className="p-3.5 border-b border-[#1b253b]/70 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-white flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-[#38bdf8]" />
                Temporal Observations ({currentLocation.name.split(',')[0]})
              </span>
              <span className="text-[9px] text-slate-400 font-mono">
                {groupSameLocation.length} scenes
              </span>
            </div>
            <div className="grid grid-cols-5 gap-1.5">
              {groupSameLocation.slice(0, 5).map(scene => (
                <div
                  key={scene.id}
                  onClick={() => onSelectScene(scene)}
                  className={`bg-[#0f172a] border rounded p-1 cursor-pointer transition-all hover:scale-105 ${
                    selectedScene?.id === scene.id ? 'border-[#38bdf8] ring-1 ring-[#38bdf8]' : 'border-[#1e293b] hover:border-[#38bdf8]'
                  }`}
                >
                  <div className="h-14 w-full rounded overflow-hidden bg-slate-900 mb-1 relative">
                    <img
                      src={scene.thumbnail_url}
                      alt={scene.mission}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/api/scenes/georeferenced?scene_id=' + scene.id;
                      }}
                    />
                    <span className="absolute bottom-0.5 right-0.5 bg-black/80 text-[7px] text-white px-1 rounded">
                      {scene.cloud_cover.toFixed(1)}% cl
                    </span>
                  </div>
                  <div className="text-[9px] font-bold text-white truncate">{scene.mission}</div>
                  <div className="text-[8px] text-slate-400 font-mono">{scene.acquisition_date.split(' ')[0]}</div>
                  <div className="text-[7.5px] text-[#38bdf8] font-mono truncate">{scene.spatial_resolution_m}m</div>
                </div>
              ))}
            </div>
          </div>

          {/* Group 2: Clear Sky Observations (< 5% cloud) */}
          <div className="p-3.5 border-b border-[#1b253b]/70 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-white flex items-center gap-1.5">
                <Crosshair className="w-3.5 h-3.5 text-emerald-400" />
                Clear Sky Observations (Cloud &lt; 5%)
              </span>
              <span className="text-[9px] text-emerald-400 font-mono">
                {groupClearSky.length} scenes
              </span>
            </div>
            <div className="grid grid-cols-5 gap-1.5">
              {groupClearSky.slice(0, 5).map(scene => (
                <div
                  key={scene.id}
                  onClick={() => onSelectScene(scene)}
                  className={`bg-[#0f172a] border rounded p-1 cursor-pointer transition-all hover:scale-105 ${
                    selectedScene?.id === scene.id ? 'border-emerald-400 ring-1 ring-emerald-400' : 'border-[#1e293b] hover:border-emerald-400'
                  }`}
                >
                  <div className="h-14 w-full rounded overflow-hidden bg-slate-900 mb-1 relative">
                    <img
                      src={scene.thumbnail_url}
                      alt={scene.mission}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/api/scenes/georeferenced?scene_id=' + scene.id;
                      }}
                    />
                    <span className="absolute bottom-0.5 right-0.5 bg-emerald-950/80 text-[7px] text-emerald-300 px-1 rounded border border-emerald-500/30">
                      {scene.cloud_cover.toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-[9px] font-bold text-white truncate">{scene.mission}</div>
                  <div className="text-[8px] text-slate-400 font-mono">{scene.acquisition_date.split(' ')[0]}</div>
                  <div className="text-[7.5px] text-emerald-400 font-mono truncate">{scene.spatial_resolution_m}m</div>
                </div>
              ))}
            </div>
          </div>

          {/* Group 3: Sentinel-2 MultiSpectral Optical */}
          <div className="p-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-white flex items-center gap-1.5">
                <ImageIcon className="w-3.5 h-3.5 text-[#38bdf8]" />
                Sentinel-2 MSI Optical Observations (10m)
              </span>
              <span className="text-[9px] text-[#38bdf8] font-mono">
                {groupSentinel.length} scenes
              </span>
            </div>
            <div className="grid grid-cols-5 gap-1.5">
              {groupSentinel.slice(0, 5).map(scene => (
                <div
                  key={scene.id}
                  onClick={() => onSelectScene(scene)}
                  className={`bg-[#0f172a] border rounded p-1 cursor-pointer transition-all hover:scale-105 ${
                    selectedScene?.id === scene.id ? 'border-[#38bdf8] ring-1 ring-[#38bdf8]' : 'border-[#1e293b] hover:border-[#38bdf8]'
                  }`}
                >
                  <div className="h-14 w-full rounded overflow-hidden bg-slate-900 mb-1 relative">
                    <img
                      src={scene.thumbnail_url}
                      alt={scene.mission}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/api/scenes/georeferenced?scene_id=' + scene.id;
                      }}
                    />
                    <span className="absolute bottom-0.5 right-0.5 bg-cyan-950/80 text-[7px] text-cyan-300 px-1 rounded border border-cyan-500/30">
                      10m
                    </span>
                  </div>
                  <div className="text-[9px] font-bold text-white truncate">{scene.mission}</div>
                  <div className="text-[8px] text-slate-400 font-mono">{scene.acquisition_date.split(' ')[0]}</div>
                  <div className="text-[7.5px] text-[#38bdf8] font-mono truncate">{scene.id.split('_')[0]}</div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* 3. BOTTOM CHRONOLOGICAL SATELLITE OBSERVATIONS TIMELINE STRIP */}
      <footer className="h-32 bg-[#090f1e] border-t border-[#1b253b] px-4 py-2.5 flex flex-col justify-between shrink-0 z-30">
        {/* Timeline Header & Date Toggles */}
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-white flex items-center gap-2">
            <span>Chronological Satellite Observations</span>
            <span className="text-[10px] text-slate-400 font-mono font-normal">
              ({chronoList.length} authenticated STAC records)
            </span>
          </div>
          <div className="flex items-center space-x-3 text-xs">
            <label className="flex items-center space-x-2 text-slate-400 text-[11px] cursor-pointer">
              <span>Show all dates</span>
              <input
                type="checkbox"
                checked={showAllDates}
                onChange={(e) => setShowAllDates(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-[#2563eb]"
              />
            </label>
            <button
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800"
              title="Download Observation Records"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Carousel Strip with Scroll Controls */}
        <div className="flex items-center space-x-2 relative">
          <button
            onClick={handleScrollLeft}
            disabled={carouselIndex === 0}
            className="w-6 h-16 rounded bg-[#0f172a] hover:bg-[#1e293b] text-slate-300 disabled:opacity-30 border border-[#1e293b] flex items-center justify-center shrink-0 z-10"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {/* Chronological Observation Cards */}
          <div className="flex-1 grid grid-cols-12 gap-1.5 overflow-hidden">
            {chronoList.slice(carouselIndex, carouselIndex + 12).map((scene, idx) => {
              const isSelected = selectedScene?.id === scene.id;
              return (
                <div
                  key={scene.id || idx}
                  onClick={() => onSelectScene(scene)}
                  className={`bg-[#0f172a] border rounded p-1 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-[#38bdf8] shadow-[0_0_10px_rgba(56,189,248,0.5)] ring-1 ring-[#38bdf8]'
                      : 'border-[#1e293b] hover:border-slate-600'
                  }`}
                >
                  <div className="h-10 w-full rounded overflow-hidden bg-slate-950 mb-1 relative">
                    <img
                      src={scene.thumbnail_url}
                      alt={scene.mission}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/api/scenes/georeferenced?scene_id=' + scene.id;
                      }}
                    />
                    <span className="absolute bottom-0 right-0 px-1 bg-black/80 text-[7px] text-cyan-300 font-mono">
                      {scene.cloud_cover.toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-[8.5px] font-bold text-white font-mono truncate">
                    {scene.acquisition_date.split(' ')[0]}
                  </div>
                  <div className="text-[8px] text-slate-400 truncate">
                    {scene.mission}
                  </div>
                  <div className="text-[7.5px] text-[#38bdf8] font-mono">
                    ({scene.spatial_resolution_m} m)
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleScrollRight}
            disabled={carouselIndex >= Math.max(0, chronoList.length - 12)}
            className="w-6 h-16 rounded bg-[#0f172a] hover:bg-[#1e293b] text-slate-300 disabled:opacity-30 border border-[#1e293b] flex items-center justify-center shrink-0 z-10"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </footer>
    </div>
  );
};
