import React, { useState } from 'react';
import { Search, MapPin, Crosshair, ChevronDown, Check, Loader2 } from 'lucide-react';
import { LocationInfo } from '../types';

interface HeaderProps {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  onSelectLocation: (loc: LocationInfo) => void;
  onSearchLocation: (query: string) => Promise<void>;
  onZoomToRegion: () => void;
  isSearching: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentLocation,
  availableLocations,
  onSelectLocation,
  onSearchLocation,
  onZoomToRegion,
  isSearching
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
    <header className="h-16 bg-space-900/90 border-b border-cyan-500/20 px-6 flex items-center justify-between backdrop-blur-md z-20">
      {/* Location Search Bar with Popover */}
      <div className="relative w-[480px]">
        <div 
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="flex items-center justify-between px-3.5 py-2 rounded-lg bg-space-950/80 border border-cyan-500/30 hover:border-cyan-400 cursor-pointer transition-all shadow-inner"
        >
          <div className="flex items-center space-x-2.5 overflow-hidden">
            <MapPin className="w-4 h-4 text-cyan-accent shrink-0" />
            <div className="truncate">
              <span className="text-xs font-semibold text-white">{currentLocation.name}</span>
              <span className="text-[10px] text-slate-400 ml-1.5 font-mono">
                {currentLocation.latitude.toFixed(4)}° N, {currentLocation.longitude.toFixed(4)}° E
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-1.5">
            {isSearching && <Loader2 className="w-3.5 h-3.5 text-cyan-accent animate-spin" />}
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          </div>
        </div>

        {/* Dynamic Search & Presets Dropdown */}
        {dropdownOpen && (
          <div className="absolute top-12 left-0 w-full bg-space-900 border border-cyan-500/40 rounded-lg shadow-2xl p-3 z-50">
            {/* Direct Input Form */}
            <form onSubmit={handleSearchSubmit} className="flex items-center px-3 py-2 mb-2 bg-space-950 rounded border border-cyan-500/40 focus-within:border-cyan-accent">
              <Search className="w-3.5 h-3.5 text-cyan-accent mr-2 shrink-0" />
              <input
                type="text"
                value={typedQuery}
                onChange={(e) => setTypedQuery(e.target.value)}
                placeholder="Type ANY city, region, or address (e.g. Paris, Tokyo, Cairo)..."
                className="w-full bg-transparent text-xs text-white focus:outline-none placeholder-slate-500 font-sans"
                autoFocus
              />
              <button
                type="submit"
                disabled={isSearching || !typedQuery.trim()}
                className="ml-2 px-2.5 py-1 rounded bg-cyan-500/20 text-cyan-accent hover:bg-cyan-500/40 text-[10px] font-mono font-bold disabled:opacity-40"
              >
                {isSearching ? 'Geocoding...' : 'Search'}
              </button>
            </form>

            <div className="text-[10px] text-slate-400 font-mono uppercase px-1 mb-1 tracking-wider">
              Quick Preset Study Regions:
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
                    className={`w-full flex items-center justify-between px-3 py-2 rounded text-left text-xs transition-colors ${
                      isSelected ? 'bg-cyan-500/20 text-cyan-accent' : 'text-slate-300 hover:bg-space-800'
                    }`}
                  >
                    <div>
                      <div className="font-medium text-white">{loc.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {loc.country} • UTM {loc.target_utm} • BBox: [{loc.bbox.map(b => b.toFixed(2)).join(', ')}]
                      </div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-cyan-accent" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Center Action: Zoom to Region Button */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onZoomToRegion}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/25 border border-cyan-500/40 text-cyan-accent text-xs font-medium transition-all shadow-glow-cyan"
        >
          <Crosshair className="w-3.5 h-3.5" />
          <span>Reset Bounding Extent</span>
        </button>

        <div className="h-4 w-px bg-slate-800" />

        {/* Live System Telemetry Badges */}
        <div className="flex items-center space-x-2 font-mono text-[10px]">
          <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/40 text-emerald-400">
            ● SENTINEL-2 STAC: LIVE
          </span>
          <span className="px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/40 text-blue-400">
            ● CRS: {currentLocation.target_utm}
          </span>
          <span className="px-2 py-0.5 rounded bg-purple-500/15 border border-purple-500/40 text-purple-400">
            ● S2 RES: 10m
          </span>
        </div>
      </div>
    </header>
  );
};
