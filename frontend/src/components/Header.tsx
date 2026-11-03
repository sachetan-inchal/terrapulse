import React, { useState } from 'react';
import { Search, MapPin, Crosshair, ChevronDown, Check, Loader2, Globe2, Radio, Activity, ShieldCheck } from 'lucide-react';
import { LocationInfo, AppInterfaceMode } from '../types';

interface HeaderProps {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  onSelectLocation: (loc: LocationInfo) => void;
  onSearchLocation: (query: string) => Promise<void>;
  onZoomToRegion: () => void;
  isSearching: boolean;
  interfaceMode: AppInterfaceMode;
  onSwitchMode: (mode: AppInterfaceMode) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentLocation,
  availableLocations,
  onSelectLocation,
  onSearchLocation,
  onZoomToRegion,
  isSearching,
  interfaceMode,
  onSwitchMode
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [typedQuery, setTypedQuery] = useState('');

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedQuery.trim()) return;
    await onSearchLocation(typedQuery);
    setDropdownOpen(false);
  };

  return (
    <header className="h-16 bg-[#040816]/95 border-b border-cyan-500/15 px-6 flex items-center justify-between backdrop-blur-xl z-30 shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
      {/* 1. Global Platform Branding & Location Search Bar with Popover */}
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

        <div className="relative w-[420px]">
          <div 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center justify-between px-3.5 py-2 rounded-lg bg-[#070d1e]/90 border border-cyan-500/25 hover:border-cyan-400/60 cursor-pointer transition-all shadow-inner"
          >
            <div className="flex items-center space-x-2.5 overflow-hidden">
              <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <div className="truncate">
                <span className="text-xs font-semibold text-white">{currentLocation.name}</span>
                <span className="text-[10px] text-cyan-400/80 ml-2 font-mono">
                  {currentLocation.latitude.toFixed(4)}°N, {currentLocation.longitude.toFixed(4)}°E
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-1.5">
              {isSearching && <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />}
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            </div>
          </div>

          {/* Dynamic Search & Presets Dropdown */}
          {dropdownOpen && (
            <div className="absolute top-12 left-0 w-full bg-[#070e24] border border-cyan-500/30 rounded-xl shadow-2xl p-3.5 z-50 backdrop-blur-xl">
              {/* Direct Input Form */}
              <form onSubmit={handleSearchSubmit} className="flex items-center px-3 py-2 mb-2 bg-[#030612] rounded-lg border border-cyan-500/30 focus-within:border-cyan-400">
                <Search className="w-3.5 h-3.5 text-cyan-400 mr-2 shrink-0" />
                <input
                  type="text"
                  value={typedQuery}
                  onChange={(e) => setTypedQuery(e.target.value)}
                  placeholder="Search any global location or coordinate (e.g. Paris, Tokyo, Cairo)..."
                  className="w-full bg-transparent text-xs text-white focus:outline-none placeholder-slate-500 font-sans"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={isSearching || !typedQuery.trim()}
                  className="ml-2 px-3 py-1 rounded bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/40 text-[10px] font-mono font-bold disabled:opacity-40 transition-all"
                >
                  {isSearching ? 'Geocoding...' : 'Resolve'}
                </button>
              </form>

              <div className="text-[9px] text-slate-400 font-mono uppercase px-1 mb-1.5 tracking-wider">
                Preset Research Corridors:
              </div>
              <div className="max-h-52 overflow-y-auto space-y-1">
                {availableLocations.map(loc => {
                  const isSelected = loc.id === currentLocation.id;
                  return (
                    <button
                      key={loc.id}
                      onClick={() => {
                        onSelectLocation(loc);
                        setDropdownOpen(false);
                        setTypedQuery('');
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-xs transition-colors ${
                        isSelected ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-300 hover:bg-[#0c1633]'
                      }`}
                    >
                      <div>
                        <div className="font-semibold text-white">{loc.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {loc.country} • UTM {loc.target_utm} • BBox: [{loc.bbox.map(b => b.toFixed(2)).join(', ')}]
                        </div>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-cyan-400" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2. Center Actions & Interface Mode Switcher Pill */}
      <div className="flex items-center space-x-3.5">
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
