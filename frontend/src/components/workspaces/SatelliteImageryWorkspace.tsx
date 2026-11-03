import React, { useState } from 'react';
import { 
  Database, Image as ImageIcon, Calendar, Filter, Check, 
  ExternalLink, Layers, Sparkles, Sliders, CheckSquare, Square,
  Clock, Cloud, Satellite, Eye, Radio, Crosshair
} from 'lucide-react';
import { SatelliteScene, LocationInfo, DataSourceState } from '../../types';

interface SatelliteImageryWorkspaceProps {
  location: LocationInfo;
  scenes: SatelliteScene[];
  selectedScene: SatelliteScene | null;
  onSelectScene: (scene: SatelliteScene) => void;
  selectedYear: number;
  onSelectYear: (year: number) => void;
  dataSources: DataSourceState;
  onDataSourceToggle: (key: keyof DataSourceState) => void;
  onZoomToRegion: () => void;
}

export const SatelliteImageryWorkspace: React.FC<SatelliteImageryWorkspaceProps> = ({
  location,
  scenes,
  selectedScene,
  onSelectScene,
  selectedYear,
  onSelectYear,
  dataSources,
  onDataSourceToggle,
  onZoomToRegion
}) => {
  const [providerFilter, setProviderFilter] = useState<'all' | 'landsat' | 'sentinel'>('all');
  const [maxCloudCover, setMaxCloudCover] = useState<number>(30);
  const [inspectedScene, setInspectedScene] = useState<SatelliteScene | null>(selectedScene || scenes[0] || null);

  const filteredScenes = scenes.filter((scene) => {
    const isLandsat = scene.mission.toLowerCase().includes('landsat');
    const isSentinel = scene.mission.toLowerCase().includes('sentinel');

    if (providerFilter === 'landsat' && !isLandsat) return false;
    if (providerFilter === 'sentinel' && !isSentinel) return false;

    if (scene.cloud_cover && scene.cloud_cover > maxCloudCover) return false;

    return true;
  });

  const activeScene = inspectedScene || selectedScene || scenes[0];

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 max-w-7xl mx-auto space-y-5">
      {/* 1. Header & Provider Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-mono">
            <Satellite className="w-5 h-5 text-cyan-400" />
            <span>Satellite Imagery & Scene Catalog</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse and inspect multi-temporal Landsat (USGS) and Sentinel-2 (ESA) surface reflectance observations for {location.name}.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onZoomToRegion}
            className="px-3 py-1.5 rounded-lg bg-sky-600/30 hover:bg-sky-600/50 border border-sky-400/40 text-xs font-semibold text-white flex items-center gap-1.5 transition-all"
          >
            <Crosshair className="w-3.5 h-3.5 text-cyan-300" />
            <span>Recenter Study Area</span>
          </button>
        </div>
      </div>

      {/* 2. Provider Filters & Cloud Cover Threshold */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-xl bg-[#070e24]/80 border border-cyan-500/20 backdrop-blur-md">
        {/* Provider Toggle */}
        <div className="space-y-1.5 md:col-span-2">
          <label className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span>Satellite Provider Filter</span>
          </label>
          <div className="flex items-center space-x-2">
            {[
              { id: 'all', label: 'All Missions' },
              { id: 'sentinel', label: 'Sentinel-2 (10m ESA)' },
              { id: 'landsat', label: 'Landsat 5-9 (30m USGS)' }
            ].map(p => (
              <button
                key={p.id}
                onClick={() => setProviderFilter(p.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                  providerFilter === p.id
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-bold'
                    : 'bg-[#030612] text-slate-400 border border-slate-800 hover:text-white'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Cloud Cover Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-[11px] font-mono text-slate-400">
            <span className="flex items-center gap-1">
              <Cloud className="w-3.5 h-3.5 text-cyan-400" />
              <span>Max Cloud Cover:</span>
            </span>
            <span className="text-cyan-300 font-bold">{maxCloudCover}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={50}
            step={5}
            value={maxCloudCover}
            onChange={(e) => setMaxCloudCover(parseInt(e.target.value, 10))}
            className="w-full accent-cyan-400 cursor-pointer"
          />
        </div>

        {/* Indexed Count */}
        <div className="flex flex-col justify-center items-end text-right">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Available Scenes</span>
          <span className="text-lg font-mono font-bold text-cyan-300">
            {filteredScenes.length} / {scenes.length}
          </span>
        </div>
      </div>

      {/* 3. Main Body: Scene Grid (Left 65%) + Metadata Inspector (Right 35%) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-5 overflow-hidden min-h-0">
        
        {/* Scenes Grid */}
        <div className="lg:col-span-2 overflow-y-auto pr-1 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {filteredScenes.map((scene) => {
              const isSelected = (selectedScene?.id === scene.id) || (selectedYear === scene.year);
              const isInspected = inspectedScene?.id === scene.id;

              return (
                <div
                  key={scene.id}
                  onClick={() => {
                    setInspectedScene(scene);
                    onSelectScene(scene);
                    onSelectYear(scene.year);
                  }}
                  className={`p-3 rounded-xl border transition-all cursor-pointer bg-[#070e24]/70 hover:bg-[#0c1638] ${
                    isInspected
                      ? 'border-cyan-400 ring-2 ring-cyan-500/30 shadow-lg shadow-cyan-500/20'
                      : 'border-slate-800/80 hover:border-cyan-500/40'
                  }`}
                >
                  <div className="relative h-36 rounded-lg overflow-hidden bg-[#030612] mb-2.5 border border-slate-800">
                    <img
                      src={scene.thumbnail_url}
                      alt={scene.mission}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
                      }}
                    />
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-[#040816]/90 text-[10px] text-cyan-300 font-mono font-bold border border-cyan-500/30">
                      {scene.year}
                    </div>
                    <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-[#040816]/90 text-[10px] text-slate-300 font-mono border border-slate-700">
                      {scene.spatial_resolution_m}m Res
                    </div>
                    {isSelected && (
                      <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-emerald-500/90 text-[10px] text-white font-mono font-bold flex items-center gap-1 shadow">
                        <Check className="w-3 h-3" />
                        <span>Active Scene</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-xs font-semibold text-white">
                    <span className="truncate">{scene.mission}</span>
                    <span className="text-[10px] font-mono text-cyan-400">{scene.cloud_cover.toFixed(1)}% Cloud</span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">
                    Date: {scene.acquisition_date}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Scene Metadata Inspector (Right) */}
        <div className="p-4 rounded-xl bg-[#070e24]/90 border border-cyan-500/25 flex flex-col justify-between overflow-y-auto">
          {activeScene ? (
            <div className="space-y-4">
              <div className="pb-3 border-b border-cyan-500/20">
                <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold flex items-center gap-1.5">
                  <Satellite className="w-4 h-4" />
                  <span>Scene Metadata Inspector</span>
                </div>
                <div className="text-sm font-bold text-white mt-1 break-all font-mono">
                  {activeScene.id}
                </div>
              </div>

              {/* Attributes Table */}
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                  <span className="text-slate-400">Mission:</span>
                  <span className="text-white font-semibold">{activeScene.mission}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                  <span className="text-slate-400">Sensor:</span>
                  <span className="text-cyan-300 font-semibold">{activeScene.sensor}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                  <span className="text-slate-400">Acquisition:</span>
                  <span className="text-white">{activeScene.acquisition_date}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                  <span className="text-slate-400">Ground Resolution:</span>
                  <span className="text-emerald-400 font-bold">{activeScene.spatial_resolution_m} meters / pixel</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                  <span className="text-slate-400">Cloud Fraction:</span>
                  <span className="text-amber-400">{activeScene.cloud_cover.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                  <span className="text-slate-400">Coordinate Ref (CRS):</span>
                  <span className="text-slate-300">{activeScene.crs || location.target_utm}</span>
                </div>
                <div className="flex flex-col py-1.5 border-b border-slate-800/80">
                  <span className="text-slate-400 mb-1">Bounding Box (WGS84):</span>
                  <span className="text-[11px] text-cyan-400/90 bg-[#030612] p-1.5 rounded">
                    [{activeScene.bbox.map(b => b.toFixed(4)).join(', ')}]
                  </span>
                </div>
              </div>

              {/* Set Active Button */}
              <button
                onClick={() => {
                  onSelectScene(activeScene);
                  onSelectYear(activeScene.year);
                }}
                className="w-full py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-mono text-xs font-bold transition-all shadow-md shadow-cyan-500/20 flex items-center justify-center gap-2"
              >
                <Check className="w-4 h-4" />
                <span>Select as Active Observation</span>
              </button>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 font-mono text-xs">
              Select a scene from the gallery to inspect STAC metadata.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

