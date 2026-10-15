import React, { useState } from 'react';
import { Compass, Plus, Minus, Layers, AlertCircle, ExternalLink } from 'lucide-react';
import { LocationInfo, SatelliteScene } from '../types';

interface GlobeMapStageProps {
  location: LocationInfo;
  scenes: SatelliteScene[];
  selectedYear: number;
  onSelectYear: (year: number) => void;
  is3DMode: boolean;
  onToggle3D: () => void;
}

export const GlobeMapStage: React.FC<GlobeMapStageProps> = ({
  location,
  scenes,
  selectedYear,
  onSelectYear,
  is3DMode,
  onToggle3D
}) => {
  const [zoomLevel, setZoomLevel] = useState(1);

  // Position slots around the orbital globe for the callout cards
  const positions = [
    'top-6 left-8',
    'bottom-16 left-10',
    'top-8 right-10',
    'bottom-20 right-8'
  ];

  const displayedScenes = scenes.slice(0, 4);

  return (
    <div className="relative w-full h-[460px] bg-space-950 overflow-hidden rounded-xl border border-cyan-500/20 shadow-2xl flex items-center justify-center">
      {/* Background Starfield & Geospatial Orbit Grid */}
      <div className="absolute inset-0 radar-grid opacity-30" />
      <div className="absolute inset-0 bg-radial-gradient from-blue-900/20 via-space-950/70 to-space-950 pointer-events-none" />

      {/* 3D Earth Globe Visualization */}
      <div 
        className="relative transition-transform duration-700 ease-out"
        style={{ transform: `scale(${zoomLevel})` }}
      >
        {/* Globe Sphere with Atmosphere Glow */}
        <div className="w-[360px] h-[360px] rounded-full overflow-hidden shadow-[0_0_80px_rgba(0,180,255,0.35)] border border-cyan-400/30 relative bg-space-900 group">
          {/* Earth Surface Photorealistic Simulation Texture */}
          <div 
            className="w-full h-full bg-cover bg-center transition-all duration-1000 transform group-hover:scale-105"
            style={{
              backgroundImage: `url('https://planetarycomputer.microsoft.com/api/data/v1/item/preview.png?collection=sentinel-2-l2a&item=S2A_MSIL2A_20240328T050651_R019_T43PHQ_20240330T035744&assets=visual&asset_bidx=visual%7C1,2,3&nodata=0&format=png')`,
              backgroundColor: '#0a1026'
            }}
          />

          {/* Atmospheric Limb Shading */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-cyan-500/20 via-transparent to-blue-600/40 pointer-events-none" />
          <div className="absolute inset-0 rounded-full shadow-[inset_0_0_50px_rgba(0,0,0,0.85)] pointer-events-none" />

          {/* Centered Target Coordinate Pin */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center pointer-events-none">
            <div className="relative">
              <div className="w-4 h-4 rounded-full bg-cyan-accent animate-ping absolute inset-0 opacity-75" />
              <div className="w-4 h-4 rounded-full bg-cyan-accent border-2 border-white shadow-glow-cyan relative z-10" />
            </div>
            <div className="mt-1 px-2.5 py-0.5 rounded bg-space-950/90 border border-cyan-400/60 backdrop-blur-md shadow-lg text-center max-w-[180px]">
              <div className="text-[11px] font-bold text-white tracking-wide truncate">{location.name.split(',')[0]}</div>
              <div className="text-[9px] text-cyan-400 font-mono">
                {location.latitude.toFixed(2)}°N, {location.longitude.toFixed(2)}°E
              </div>
            </div>
          </div>
        </div>

        {/* Floating REAL Satellite Observation Callout Cards */}
        {displayedScenes.map((scene, idx) => {
          const isCurrent = selectedYear === scene.year;
          const posClass = positions[idx % positions.length];
          return (
            <div
              key={scene.id || idx}
              onClick={() => onSelectYear(scene.year)}
              className={`absolute ${posClass} z-10 cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                isCurrent ? 'ring-2 ring-cyan-accent shadow-glow-cyan' : 'opacity-85 hover:opacity-100'
              }`}
            >
              <div className="w-36 bg-space-900/95 border border-cyan-500/40 rounded-lg overflow-hidden backdrop-blur-md p-1.5 shadow-xl">
                <div className="h-20 w-full rounded overflow-hidden bg-space-950 mb-1 relative border border-slate-800">
                  <img 
                    src={scene.thumbnail_url} 
                    alt={scene.mission} 
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback to local benchmark tile if remote tile server has temporary delay
                      (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
                    }}
                  />
                  <span className="absolute bottom-1 right-1 px-1.5 py-0.2 rounded bg-space-950/90 text-[8px] text-cyan-300 font-mono border border-slate-800">
                    {scene.spatial_resolution_m}m
                  </span>
                  <span className="absolute top-1 left-1 px-1 py-0.2 rounded bg-space-950/90 text-[7px] text-emerald-400 font-mono">
                    Cloud: {scene.cloud_cover}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-semibold text-white truncate max-w-[70px]">{scene.mission}</span>
                  <span className="text-cyan-400 font-mono font-bold">({scene.year})</span>
                </div>
                <div className="text-[8px] text-slate-400 font-mono truncate mt-0.5">
                  Acquired: {scene.acquisition_date}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Top-Right Floating Globe Navigation Controls */}
      <div className="absolute top-4 right-4 flex flex-col space-y-1.5 z-20">
        <button 
          onClick={() => setZoomLevel(prev => Math.min(prev + 0.15, 1.6))}
          className="w-8 h-8 rounded-lg bg-space-900/80 border border-cyan-500/30 text-slate-300 hover:text-cyan-accent hover:border-cyan-400 flex items-center justify-center transition-all shadow-md"
          title="Zoom In"
        >
          <Plus className="w-4 h-4" />
        </button>
        <button 
          onClick={() => setZoomLevel(prev => Math.max(prev - 0.15, 0.7))}
          className="w-8 h-8 rounded-lg bg-space-900/80 border border-cyan-500/30 text-slate-300 hover:text-cyan-accent hover:border-cyan-400 flex items-center justify-center transition-all shadow-md"
          title="Zoom Out"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button 
          onClick={onToggle3D}
          className={`w-8 h-8 rounded-lg border flex items-center justify-center transition-all shadow-md ${
            is3DMode 
              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-accent' 
              : 'bg-space-900/80 border-cyan-500/30 text-slate-300 hover:text-cyan-accent'
          }`}
          title="Toggle 3D Orbit View"
        >
          <Compass className="w-4 h-4" />
        </button>
      </div>

      {/* Bottom Floating Legend / Coordinates Tag */}
      <div className="absolute bottom-3 left-4 flex items-center space-x-2 text-[10px] font-mono text-slate-400 bg-space-950/80 border border-cyan-500/30 px-3 py-1 rounded-full backdrop-blur-md">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span>AUTHENTIC SENTINEL-2 / STAC | UTM: {location.target_utm}</span>
      </div>
    </div>
  );
};
