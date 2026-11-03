import React, { useState } from 'react';
import { Compass, Plus, Minus, Layers, RotateCcw, Crosshair, ExternalLink, Radio, Eye } from 'lucide-react';
import { LocationInfo, SatelliteScene } from '../types';
import { Interactive3DGlobe } from './Interactive3DGlobe';

interface GlobeMapStageProps {
  location: LocationInfo;
  scenes: SatelliteScene[];
  selectedYear: number;
  onSelectYear: (year: number) => void;
  is3DMode: boolean;
  onToggle3D: () => void;
  onZoomToRegion?: () => void;
  showObservationCards?: boolean;
}

export const GlobeMapStage: React.FC<GlobeMapStageProps> = ({
  location,
  scenes,
  selectedYear,
  onSelectYear,
  is3DMode,
  onToggle3D,
  onZoomToRegion,
  showObservationCards = false
}) => {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [globeRotation, setGlobeRotation] = useState(0);

  // 4 reference observation cards matching Screenshot 2:
  // Top-Left: Landsat 5 (1985)
  // Bottom-Left: Landsat 8 (2015)
  // Top-Right: Sentinel-2 (2020)
  // Bottom-Right: PlanetScope (2024)
  const defaultObservationCards = [
    {
      id: 'ls5_1985',
      mission: 'Landsat 5',
      year: 1985,
      date: '1985-03-12',
      res: '30m',
      pos: 'top-6 left-12',
      hasZoomBtn: true,
      thumb: '/api/imagery/tile?mission=Landsat+5&year=1985'
    },
    {
      id: 'ls8_2015',
      mission: 'Landsat 8',
      year: 2015,
      date: '2015-05-21',
      res: '30m',
      pos: 'bottom-8 left-16',
      hasZoomBtn: false,
      thumb: '/api/imagery/tile?mission=Landsat+8&year=2015'
    },
    {
      id: 's2_2020',
      mission: 'Sentinel-2',
      year: 2020,
      date: '2020-01-20',
      res: '10m',
      pos: 'top-10 right-14',
      hasZoomBtn: false,
      thumb: '/api/imagery/tile?mission=Sentinel-2&year=2020'
    },
    {
      id: 'ps_2024',
      mission: 'PlanetScope',
      year: 2024,
      date: '2024-03-28',
      res: '3m',
      pos: 'bottom-6 right-12',
      hasZoomBtn: false,
      thumb: '/api/imagery/tile?mission=Sentinel-2&year=2024'
    }
  ];

  const cards = defaultObservationCards.map(c => {
    const live = (scenes || []).find(s => s.year === c.year);
    return live ? {
      ...c,
      thumb: live.thumbnail_url,
      date: live.acquisition_date,
      mission: live.mission,
    } : c;
  });

  return (
    <div className="relative w-full h-[490px] bg-[#030713] overflow-hidden rounded-2xl border border-cyan-500/20 shadow-[0_12px_48px_rgba(0,0,0,0.6)] flex items-center justify-center select-none telemetry-grid">
      {/* Deep Space Atmosphere Glow */}
      <div className="absolute inset-0 bg-radial-gradient from-blue-950/25 via-[#030713]/80 to-[#030713] pointer-events-none" />

      {/* Orbital Telemetry Latitude / Longitude Overlay Rings */}
      <div className="absolute w-[520px] h-[520px] rounded-full border border-cyan-500/10 pointer-events-none" />
      <div className="absolute w-[680px] h-[680px] rounded-full border border-dashed border-cyan-500/5 pointer-events-none" />

      {/* Central 3D Photorealistic Earth Globe Container */}
      <div 
        className="relative transition-transform duration-700 ease-out flex items-center justify-center"
        style={{ transform: `scale(${zoomLevel})` }}
      >
        {/* Central 3D Interactive Photorealistic Earth Globe */}
        <div className="w-[370px] h-[370px] rounded-full overflow-hidden shadow-[0_0_100px_rgba(14,165,233,0.35)] border border-cyan-400/40 relative bg-[#061025]">
          <Interactive3DGlobe
            location={location}
            zoomLevel={zoomLevel}
            isRotating={false}
            className="w-full h-full"
          />
        </div>

        {/* Dynamic Glowing Tether Lines & Floating Satellite Observation Callout Cards (When Enabled) */}
        {showObservationCards && (
          <>
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" style={{ overflow: 'visible' }}>
              <line x1="50%" y1="50%" x2="22%" y2="18%" stroke="rgba(34, 211, 238, 0.45)" strokeWidth="1.5" strokeDasharray="4 3" />
              <line x1="50%" y1="50%" x2="25%" y2="82%" stroke="rgba(34, 211, 238, 0.45)" strokeWidth="1.5" strokeDasharray="4 3" />
              <line x1="50%" y1="50%" x2="78%" y2="20%" stroke="rgba(34, 211, 238, 0.45)" strokeWidth="1.5" strokeDasharray="4 3" />
              <line x1="50%" y1="50%" x2="78%" y2="80%" stroke="rgba(34, 211, 238, 0.45)" strokeWidth="1.5" strokeDasharray="4 3" />
            </svg>

            {cards.map((card) => {
              const isCurrent = selectedYear === card.year;
              return (
                <div
                  key={card.id}
                  onClick={() => onSelectYear(card.year)}
                  className={`absolute ${card.pos} z-10 cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                    isCurrent ? 'ring-2 ring-cyan-400 shadow-[0_0_24px_rgba(6,182,212,0.6)]' : 'opacity-90 hover:opacity-100'
                  }`}
                >
                  <div className="w-40 bg-[#070e24]/95 border border-cyan-500/35 rounded-xl overflow-hidden backdrop-blur-xl p-2 shadow-2xl">
                    <div className="h-22 w-full rounded-lg overflow-hidden bg-[#030612] mb-1.5 relative border border-slate-800/80">
                      <img 
                        src={card.thumb} 
                        alt={card.mission} 
                        className="w-full h-20 object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
                        }}
                      />
                      <span className="absolute bottom-1 right-1 px-1.5 py-0.5 rounded bg-[#040816]/90 text-[8px] text-cyan-300 font-mono border border-cyan-500/20">
                        {card.res}
                      </span>
                      {card.hasZoomBtn && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onZoomToRegion) onZoomToRegion();
                          }}
                          className="absolute inset-x-2 bottom-1.5 py-0.5 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-[9px] font-semibold rounded text-center shadow-lg transition-all"
                        >
                          Zoom to region
                        </button>
                      )}
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-white truncate max-w-[85px]">{card.mission}</span>
                      <span className="text-cyan-400 font-mono font-bold">({card.year})</span>
                    </div>
                    <div className="text-[9px] text-slate-400 font-mono truncate mt-0.5">
                      {card.date}
                    </div>
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>

      {/* Top-Right Mission Control Tool Strip (matching Screenshot 2) */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2 z-20">
        <button 
          onClick={() => setGlobeRotation(prev => prev + 45)}
          className="w-9 h-9 rounded-xl bg-[#070e24]/90 hover:bg-[#0c1638] border border-cyan-500/30 text-cyan-400 flex items-center justify-center shadow-lg backdrop-blur-md transition-all"
          title="Rotate Orbit"
        >
          <Compass className="w-4 h-4" />
        </button>
        <button 
          onClick={() => setZoomLevel(prev => Math.min(prev + 0.2, 2.0))}
          className="w-9 h-9 rounded-xl bg-[#070e24]/90 hover:bg-[#0c1638] border border-cyan-500/30 text-white flex items-center justify-center shadow-lg backdrop-blur-md transition-all"
          title="Zoom In"
        >
          <Plus className="w-4 h-4" />
        </button>
        <button 
          onClick={() => setZoomLevel(prev => Math.max(prev - 0.2, 0.7))}
          className="w-9 h-9 rounded-xl bg-[#070e24]/90 hover:bg-[#0c1638] border border-cyan-500/30 text-white flex items-center justify-center shadow-lg backdrop-blur-md transition-all"
          title="Zoom Out"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button 
          onClick={onToggle3D}
          className="w-9 h-9 rounded-xl bg-[#070e24]/90 hover:bg-[#0c1638] border border-cyan-500/30 text-cyan-400 flex items-center justify-center shadow-lg backdrop-blur-md transition-all"
          title="Toggle Multi-Layer View"
        >
          <Layers className="w-4 h-4" />
        </button>
      </div>

      {/* Bottom Telemetry Status Pill */}
      <div className="absolute bottom-3 left-4 px-3 py-1 rounded-lg bg-[#040816]/90 border border-cyan-500/20 text-[9px] font-mono text-slate-400 flex items-center space-x-3 backdrop-blur-md">
        <span className="flex items-center gap-1 text-cyan-300">
          <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
          <span>ORBIT ELEVATION: 786 KM</span>
        </span>
        <span className="text-slate-600">|</span>
        <span>NADIR SENSOR: MSI L2A</span>
        <span className="text-slate-600">|</span>
        <span className="text-emerald-400">GEOPOSITION LOCKED</span>
      </div>
    </div>
  );
};
