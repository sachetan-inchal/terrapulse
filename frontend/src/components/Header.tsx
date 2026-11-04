import React from 'react';
import { Crosshair, Globe2, Radio, Activity, ShieldCheck, Calendar } from 'lucide-react';
import { LocationInfo, AppInterfaceMode } from '../types';
import { GlobalLocationSearch } from './GlobalLocationSearch';

interface HeaderProps {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  onSelectLocation: (loc: LocationInfo) => void;
  onSearchLocation: (query: string) => Promise<void>;
  onZoomToRegion: () => void;
  isSearching: boolean;
  interfaceMode: AppInterfaceMode;
  onSwitchMode: (mode: AppInterfaceMode) => void;
  selectedYear?: number;
  onSelectYear?: (year: number) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentLocation,
  availableLocations,
  onSelectLocation,
  onSearchLocation,
  onZoomToRegion,
  isSearching,
  interfaceMode,
  onSwitchMode,
  selectedYear = 2024,
  onSelectYear
}) => {
  return (
    <header className="h-16 bg-[#040816]/95 border-b border-cyan-500/15 px-6 flex items-center justify-between backdrop-blur-xl z-30 shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
      {/* 1. Global Platform Branding & Worldwide Dynamic Location Search */}
      <div className="flex items-center space-x-5">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/40">
            <Radio className="w-4 h-4 text-white animate-pulse" />
          </div>
          <div>
            <div className="text-xs font-bold tracking-wider uppercase text-white font-mono flex items-center gap-1.5">
              <span>TerraPulse</span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">ORBIT-OS</span>
            </div>
            <div className="text-[9px] text-slate-400 font-mono tracking-tight">Earth Observation & AI Investigation Platform</div>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800/80" />

        {/* Dynamic Worldwide Geocoding Search Bar */}
        <GlobalLocationSearch
          currentLocation={currentLocation}
          availableLocations={availableLocations}
          onSelectLocation={onSelectLocation}
          onSearchLocation={onSearchLocation}
          isSearching={isSearching}
          className="w-[420px]"
        />
      </div>

      {/* 2. Center Actions & Interface Mode Switcher Pill */}
      <div className="flex items-center space-x-3.5">
        {/* Date / Observation Period Selector */}
        {onSelectYear && (
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#070d1e] border border-cyan-500/25 text-xs font-mono">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
            <select
              value={selectedYear}
              onChange={(e) => onSelectYear(parseInt(e.target.value, 10))}
              className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
            >
              {[1985, 1995, 2005, 2015, 2020, 2024, 2025].map(yr => (
                <option key={yr} value={yr} className="bg-[#070e24] text-white">
                  Epoch {yr}
                </option>
              ))}
            </select>
          </div>
        )}

        <button
          onClick={onZoomToRegion}
          className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-xs font-semibold transition-all shadow-[0_0_15px_rgba(2,132,199,0.35)] border border-sky-400/30"
        >
          <Crosshair className="w-3.5 h-3.5" />
          <span>Zoom to region</span>
        </button>

        <div className="h-5 w-px bg-slate-800" />

        {/* Interface Switcher Pill (Matching Screenshot 1 & 2 duality) */}
        <div className="flex items-center bg-[#070e24] p-1 rounded-xl border border-cyan-500/20 shadow-inner">
          <button
            onClick={() => onSwitchMode('explorer')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              interfaceMode === 'explorer'
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold shadow-md shadow-cyan-500/20 border border-cyan-400/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe2 className="w-3.5 h-3.5" />
            <span>Earth Observation Explorer</span>
          </button>
          <button
            onClick={() => onSwitchMode('investigator')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              interfaceMode === 'investigator'
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold shadow-md shadow-cyan-500/20 border border-cyan-400/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>AI Earth Investigator</span>
          </button>
          <button
            onClick={() => onSwitchMode('qa_workbench')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              interfaceMode === 'qa_workbench'
                ? 'bg-gradient-to-r from-purple-600 to-cyan-600 text-white font-semibold shadow-md shadow-purple-500/20 border border-purple-400/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
            <span>GeoAgent QA / Testing Workbench</span>
          </button>
        </div>
      </div>

      {/* 3. Live Telemetry & Mission Control Badges */}
      <div className="flex items-center space-x-2.5 font-mono text-[10px]">
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>PLANETARY COMPUTER: CONNECTED</span>
        </span>
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-500/30 text-blue-300 shadow-sm">
          <ShieldCheck className="w-3 h-3 text-blue-400" />
          <span>COG L2A ACTIVE</span>
        </span>
      </div>
    </header>
  );
};
