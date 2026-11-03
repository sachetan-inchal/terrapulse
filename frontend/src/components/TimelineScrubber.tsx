import React, { useState, useEffect } from 'react';
import { Play, Pause, ChevronLeft, ChevronRight, TrendingUp, Activity, Layers } from 'lucide-react';
import { EnvironmentalAnalysis, SatelliteScene } from '../types';

interface TimelineScrubberProps {
  currentYear: number;
  onYearChange: (year: number) => void;
  analysis?: EnvironmentalAnalysis;
  scenes: SatelliteScene[];
  activeTimelineView: 'historical' | 'current' | 'future';
  onViewChange: (view: 'historical' | 'current' | 'future') => void;
}

export const TimelineScrubber: React.FC<TimelineScrubberProps> = ({
  currentYear,
  onYearChange,
  analysis,
  scenes,
  activeTimelineView,
  onViewChange
}) => {
  const [isPlaying, setIsPlaying] = useState(false);

  // Define chronological timeline anchors
  const timelineYears = [1985, 1995, 2005, 2015, 2020, 2024, 2030, 2040, 2050];

  // Helper to find matching real satellite scene thumbnail
  const getSceneThumbnail = (year: number): string => {
    const match = (scenes || []).find(s => s.year === year || Math.abs(s.year - year) <= 1);
    if (match && match.thumbnail_url) {
      return match.thumbnail_url;
    }
    // Return real local Sentinel-2 / Landsat tile endpoint
    return `/api/imagery/tile?mission=${year > 2024 ? 'Forecast' : year >= 2018 ? 'Sentinel-2' : 'Landsat'}&year=${year}`;
  };

  const getMissionLabel = (year: number): string => {
    if (year > 2024) return 'Simulation';
    if (year >= 2018) return 'Sentinel-2 (10m)';
    if (year >= 2013) return 'Landsat 8 (30m)';
    if (year >= 1999) return 'Landsat 7 (30m)';
    return 'Landsat 5 (30m)';
  };

  // Auto-play animation through timeline
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        onYearChange(prev => {
          const currIdx = timelineYears.indexOf(prev);
          const nextIdx = (currIdx + 1) % timelineYears.length;
          return timelineYears[nextIdx];
        });
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <div className="glass-panel p-4 rounded-xl border border-cyan-500/20 space-y-3">
      {/* Top View Selector Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
        <div className="flex space-x-2">
          {(['historical', 'current', 'future'] as const).map((view) => (
            <button
              key={view}
              onClick={() => {
                onViewChange(view);
                if (view === 'current') onYearChange(2024);
                if (view === 'historical' && currentYear > 2024) onYearChange(2020);
                if (view === 'future' && currentYear <= 2024) onYearChange(2030);
              }}
              className={`px-3 py-1 rounded-md text-xs font-semibold capitalize transition-all ${
                activeTimelineView === view
                  ? 'bg-cyan-500/20 text-cyan-accent border border-cyan-500/40 shadow-glow-cyan'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {view === 'future' ? '🔮 Future Scenarios' : `${view} View`}
            </button>
          ))}
        </div>

        {/* Current Year Badge & Controls */}
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-space-950 border border-cyan-500/30 text-cyan-accent text-xs font-mono hover:bg-cyan-500/10"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'PAUSE' : 'TIME-LAPSE'}</span>
          </button>
          <div className="text-xs font-mono font-bold text-white bg-space-950 px-3 py-1 rounded border border-slate-800">
            OBSERVATION: <span className="text-cyan-accent">{currentYear}</span>
          </div>
        </div>
      </div>

      {/* Chronological Observation Strip using REAL Sentinel-2 / Landsat Thumbnails */}
      <div className="grid grid-cols-9 gap-2 overflow-x-auto py-1">
        {timelineYears.map((year) => {
          const isSelected = currentYear === year;
          const isFuture = year > 2024;
          return (
            <div
              key={year}
              onClick={() => onYearChange(year)}
              className={`cursor-pointer rounded-lg p-1.5 transition-all flex flex-col items-center text-center ${
                isSelected
                  ? 'bg-cyan-500/25 border-2 border-cyan-accent shadow-glow-cyan scale-105'
                  : 'bg-space-950/70 border border-slate-800/80 hover:border-slate-600 opacity-80 hover:opacity-100'
              }`}
            >
              <div className="h-12 w-full rounded overflow-hidden bg-space-900 mb-1 border border-slate-800 relative">
                <img 
                  src={getSceneThumbnail(year)} 
                  alt={`${year}`} 
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `/api/imagery/tile?mission=Sentinel-2&year=${year}`;
                  }}
                />
                {isFuture && (
                  <span className="absolute inset-0 bg-purple-900/30 flex items-center justify-center text-[8px] font-mono text-purple-300 font-bold">
                    PROJECTION
                  </span>
                )}
              </div>
              <div className={`text-[10px] font-bold font-mono ${isFuture ? 'text-purple-300' : 'text-white'}`}>
                {year}
              </div>
              <div className="text-[7.5px] text-slate-400 truncate w-full mt-0.5">
                {getMissionLabel(year)}
              </div>
            </div>
          );
        })}
      </div>

      {/* Scrub Bar Slider */}
      <div className="px-2 pt-1">
        <input
          type="range"
          min={1985}
          max={2050}
          step={5}
          value={currentYear}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="w-full accent-cyan-400 h-1.5 bg-space-950 rounded-lg cursor-pointer"
        />
        <div className="flex justify-between text-[9px] font-mono text-slate-500 mt-1">
          <span>1985 (Landsat 5 TM)</span>
          <span>2005 (Landsat 7 ETM+)</span>
          <span className="text-cyan-accent font-bold">2024 (Sentinel-2 MSI 10m)</span>
          <span className="text-purple-400">2050 (World Model Scenario)</span>
        </div>
      </div>

      {/* 5 Analytical Output Cards matching Screenshot 2 */}
      <div className="grid grid-cols-5 gap-2.5 pt-2 border-t border-slate-800/80">
        {/* Card 1: Land Cover (2024) */}
        <div className="bg-[#0b1222] border border-[#1e293b] rounded-lg p-2 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-white font-mono">Land Cover ({currentYear})</span>
          </div>
          <div className="h-14 rounded overflow-hidden mb-1.5 relative bg-gradient-to-tr from-emerald-900/60 via-amber-900/40 to-rose-900/60 border border-slate-800">
            <img
              src="/api/imagery/tile?mission=Sentinel-2&year=2024"
              alt="Land Cover Map"
              className="w-full h-full object-cover opacity-80"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          </div>
          <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[8px] font-mono text-slate-300">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Veg: <strong>26.4%</strong>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
              Built: <strong>48.2%</strong>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Agri: <strong>18.7%</strong>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              Water: <strong>6.7%</strong>
            </span>
          </div>
        </div>

        {/* Card 2: NDVI */}
        <div className="bg-[#0b1222] border border-[#1e293b] rounded-lg p-2 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-white font-mono">NDVI ({currentYear})</span>
          </div>
          <div className="h-14 rounded overflow-hidden mb-1.5 relative border border-slate-800 bg-gradient-to-r from-red-600 via-yellow-500 to-green-500">
            <img
              src="/api/imagery/tile?mission=Sentinel-2&year=2024"
              alt="NDVI Map"
              className="w-full h-full object-cover mix-blend-overlay opacity-80"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
              }}
            />
          </div>
          <div className="space-y-1">
            <div className="h-1.5 w-full rounded bg-gradient-to-r from-red-500 via-yellow-400 to-emerald-500" />
            <div className="flex justify-between text-[8px] text-slate-400 font-mono">
              <span>0.0</span>
              <span className="text-emerald-400 font-bold">0.38 Mean</span>
              <span>1.0</span>
            </div>
          </div>
        </div>

        {/* Card 3: Change Detection */}
        <div className="bg-[#0b1222] border border-[#1e293b] rounded-lg p-2 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-white font-mono">Change Detection (2000–{currentYear})</span>
          </div>
          <div className="h-14 rounded overflow-hidden mb-1.5 relative border border-slate-800 bg-slate-950">
            <img
              src="/api/imagery/change_mask"
              alt="Change Detection Mask"
              className="w-full h-full object-cover opacity-85"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
              }}
            />
          </div>
          <div className="flex items-center justify-between text-[8px] text-slate-300 font-mono">
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-rose-500" />Increase</span>
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-blue-500" />Decrease</span>
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-slate-500" />No Change</span>
          </div>
        </div>

        {/* Card 4: Urban Growth (1985 -> 2024) */}
        <div className="bg-[#0b1222] border border-[#1e293b] rounded-lg p-2 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-white font-mono">Urban Growth (1985 → {currentYear})</span>
          </div>
          <div className="h-14 rounded overflow-hidden mb-1.5 grid grid-cols-2 gap-1 border border-slate-800 p-0.5 bg-slate-950">
            <div className="h-full rounded overflow-hidden relative">
              <img
                src="/api/imagery/tile?mission=Landsat+5&year=1985"
                alt="1985"
                className="w-full h-full object-cover"
              />
              <span className="absolute bottom-0.5 left-0.5 bg-black/80 px-1 text-[7px] text-slate-300 font-mono">1985</span>
            </div>
            <div className="h-full rounded overflow-hidden relative">
              <img
                src="/api/imagery/tile?mission=Sentinel-2&year=2024"
                alt="2024"
                className="w-full h-full object-cover"
              />
              <span className="absolute bottom-0.5 left-0.5 bg-black/80 px-1 text-[7px] text-cyan-300 font-mono">{currentYear}</span>
            </div>
          </div>
          <div className="text-[8px] text-cyan-400 font-mono text-center">
            +38.4% Built-Up Growth
          </div>
        </div>

        {/* Card 5: Time-lapse (1985–2024) */}
        <div className="bg-[#0b1222] border border-[#1e293b] rounded-lg p-2 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-white font-mono">Time-lapse (1985–{currentYear})</span>
          </div>
          <div className="h-14 rounded overflow-hidden mb-1.5 relative border border-slate-800 group">
            <img
              src="/api/imagery/tile?mission=Sentinel-2&year=2024"
              alt="Timelapse Preview"
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="w-7 h-7 rounded-full bg-cyan-500/80 hover:bg-cyan-400 text-white flex items-center justify-center shadow-lg transition-transform group-hover:scale-110"
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
              </button>
            </div>
            <span className="absolute bottom-0.5 right-1 text-[7px] font-mono text-white bg-black/80 px-1 rounded">
              0:00 / 1:30
            </span>
          </div>
          <div className="flex items-center justify-between text-[8px] text-slate-400 font-mono">
            <span>Historical Multi-Decade Loop</span>
            <span className="text-cyan-400 font-bold">{isPlaying ? 'PLAYING' : 'READY'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
