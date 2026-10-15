import React, { useState } from 'react';
import { Search, MapPin, ZoomIn, Crosshair, ChevronDown, Check } from 'lucide-react';
import { LocationInfo } from '../types';

interface HeaderProps {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  onSelectLocation: (loc: LocationInfo) => void;
  onZoomToRegion: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentLocation,
  availableLocations,
  onSelectLocation,
  onZoomToRegion
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = availableLocations.filter(loc =>
    loc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    loc.country.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <header className="h-16 bg-space-900/90 border-b border-cyan-500/20 px-6 flex items-center justify-between backdrop-blur-md z-20">
      {/* Location Search Bar with Popover */}
      <div className="relative w-96">
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
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-1" />
        </div>

        {/* Dropdown Menu */}
        {dropdownOpen && (
          <div className="absolute top-12 left-0 w-full bg-space-900 border border-cyan-500/40 rounded-lg shadow-2xl p-2 z-50">
            <div className="flex items-center px-2 py-1.5 mb-2 bg-space-950 rounded border border-slate-800">
              <Search className="w-3.5 h-3.5 text-slate-400 mr-2 shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search city, address, or coords..."
                className="w-full bg-transparent text-xs text-white focus:outline-none placeholder-slate-500 font-sans"
                autoFocus
              />
            </div>
            <div className="max-h-56 overflow-y-auto space-y-1">
              {filtered.map(loc => {
                const isSelected = loc.id === currentLocation.id;
                return (
                  <button
                    key={loc.id}
                    onClick={() => {
                      onSelectLocation(loc);
                      setDropdownOpen(false);
                      setSearchQuery('');
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded text-left text-xs transition-colors ${
                      isSelected ? 'bg-cyan-500/20 text-cyan-accent' : 'text-slate-300 hover:bg-space-800'
                    }`}
                  >
                    <div>
                      <div className="font-medium text-white">{loc.name}</div>
                      <div className="text-[10px] text-slate-400">{loc.country} • UTM {loc.target_utm}</div>
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
          <span>Zoom to Region</span>
        </button>

        <div className="h-4 w-px bg-slate-800" />

        {/* Live System Telemetry Badges */}
        <div className="flex items-center space-x-2 font-mono text-[10px]">
          <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/40 text-emerald-400">
            ● STAC: CONNECTED
          </span>
          <span className="px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/40 text-blue-400">
            ● CRS: {currentLocation.target_utm}
          </span>
          <span className="px-2 py-0.5 rounded bg-purple-500/15 border border-purple-500/40 text-purple-400">
            ● RES: 3.0m–30m
          </span>
        </div>
      </div>
    </header>
  );
};
