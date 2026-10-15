import React, { useState } from 'react';
import { Compass, Plus, Minus, Eye, Layers, Maximize2 } from 'lucide-react';
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

  // Callouts array matching reference screenshot: Landsat 5 (1985), Landsat 8 (2015), Sentinel-2 (2020), PlanetScope (2024)
  const calloutScenes = [
    {
      mission: 'Landsat 5',
      year: 1985,
      res: '30m',
      pos: 'top-10 left-12',
      arrow: 'after:right-[-20px] after:top-[40%]',
      img: 'https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?w=300&q=75'
    },
    {
      mission: 'Landsat 8',
      year: 2015,
      res: '30m',
      pos: 'bottom-20 left-16',
      arrow: 'after:right-[-20px] after:top-[30%]',
      img: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=300&q=75'
    },
    {
      mission: 'Sentinel-2',
      year: 2020,
      res: '10m',
      pos: 'top-12 right-16',
      arrow: 'after:left-[-20px] after:top-[40%]',
      img: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300&q=75'
    },
    {
      mission: 'PlanetScope',
      year: 2024,
      res: '3.0m',
      pos: 'bottom-24 right-12',
      arrow: 'after:left-[-20px] after:top-[30%]',
      img: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=300&q=75'
    }
  ];

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
              backgroundImage: `url('https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=800&q=80')`,
              filter: 'contrast(1.15) brightness(0.95)'
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
            <div className="mt-1 px-2.5 py-0.5 rounded bg-space-950/90 border border-cyan-400/60 backdrop-blur-md shadow-lg text-center">
              <div className="text-[11px] font-bold text-white tracking-wide">{location.name.split(',')[0]}</div>
              <div className="text-[9px] text-cyan-400 font-mono">
                {location.latitude.toFixed(2)}°N, {location.longitude.toFixed(2)}°E
              </div>
            </div>
          </div>
        </div>

        {/* Floating Satellite Observation Callout Cards */}
        {calloutScenes.map((c) => {
          const isCurrent = selectedYear === c.year;
          return (
            <div
              key={c.year}
              onClick={() => onSelectYear(c.year)}
              className={`absolute ${c.pos} z-10 cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                isCurrent ? 'ring-2 ring-cyan-accent shadow-glow-cyan' : 'opacity-85 hover:opacity-100'
              }`}
            >
              <div className="w-32 bg-space-900/90 border border-cyan-500/40 rounded-lg overflow-hidden backdrop-blur-md p-1.5 shadow-xl">
                <div className="h-16 w-full rounded overflow-hidden bg-space-950 mb-1 relative">
                  <img src={c.img} alt={c.mission} className="w-full h-full object-cover" />
                  <span className="absolute bottom-1 right-1 px-1 py-0.2 rounded bg-space-950/80 text-[8px] text-cyan-300 font-mono">
                    {c.res}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-semibold text-white">{c.mission}</span>
                  <span className="text-cyan-400 font-mono font-bold">({c.year})</span>
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
      <div className="absolute bottom-3 left-4 flex items-center space-x-2 text-[10px] font-mono text-slate-400 bg-space-950/70 border border-slate-800 px-3 py-1 rounded-full backdrop-blur-md">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span>PROJECTION: ORBITAL WGS-84 / UTM ZONE {location.target_utm.split(':')[1]}</span>
      </div>
    </div>
  );
};
