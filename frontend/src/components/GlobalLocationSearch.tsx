import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, MapPin, ChevronDown, Check, Loader2, X, 
  Globe2, Compass, Waves, Mountain, Trees, Building2, 
  Landmark, Crosshair, AlertCircle
} from 'lucide-react';
import { LocationInfo } from '../types';
import { searchWorldwideLocations } from '../services/api';

interface GlobalLocationSearchProps {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  onSelectLocation: (loc: LocationInfo) => void;
  onSearchLocation: (query: string) => Promise<void>;
  isSearching?: boolean;
  placeholder?: string;
  className?: string;
}

export const GlobalLocationSearch: React.FC<GlobalLocationSearchProps> = ({
  currentLocation,
  availableLocations,
  onSelectLocation,
  onSearchLocation,
  isSearching = false,
  placeholder = "Search any global city, lake, mountain, forest or coordinate...",
  className = ""
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [typedQuery, setTypedQuery] = useState('');
  const [suggestions, setSuggestions] = useState<LocationInfo[]>([]);
  const [isSearchingLive, setIsSearchingLive] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced live worldwide search
  useEffect(() => {
    const q = typedQuery.trim();
    if (q.length < 2) {
      setSuggestions([]);
      setIsSearchingLive(false);
      setSearchError(null);
      return;
    }

    setIsSearchingLive(true);
    setSearchError(null);

    const timer = setTimeout(async () => {
      try {
        const results = await searchWorldwideLocations(q, 8);
        setSuggestions(results);
        if (results.length === 0) {
          setSearchError(`No worldwide places found matching "${q}". Try coordinates (e.g. 40.7128, -74.0060) or general region.`);
        }
      } catch (err: any) {
        console.warn('Live worldwide search failed:', err);
        setSearchError('Worldwide search temporary rate limit or timeout. Press Enter to force resolve.');
      } finally {
        setIsSearchingLive(false);
      }
    }, 320);

    return () => clearTimeout(timer);
  }, [typedQuery]);

  const handleSelect = (loc: LocationInfo) => {
    onSelectLocation(loc);
    setDropdownOpen(false);
    setTypedQuery('');
    setSuggestions([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedQuery.trim()) return;

    if (suggestions.length > 0) {
      handleSelect(suggestions[0]);
      return;
    }

    setIsSearchingLive(true);
    try {
      await onSearchLocation(typedQuery);
      setDropdownOpen(false);
      setTypedQuery('');
      setSuggestions([]);
    } catch (err: any) {
      setSearchError(err?.message || 'Location resolution failed. Please verify spelling or coordinates.');
    } finally {
      setIsSearchingLive(false);
    }
  };

  // Helper to render categorical feature badge
  const renderFeatureBadge = (featType?: string) => {
    const ft = (featType || '').toLowerCase();
    if (ft.includes('water') || ft.includes('lake') || ft.includes('river')) {
      return (
        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-sky-500/20 text-sky-300 border border-sky-500/30">
          <Waves className="w-2.5 h-2.5" />
          <span>Water</span>
        </span>
      );
    }
    if (ft.includes('mountain') || ft.includes('peak') || ft.includes('volcano')) {
      return (
        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
          <Mountain className="w-2.5 h-2.5" />
          <span>Mountain</span>
        </span>
      );
    }
    if (ft.includes('forest') || ft.includes('wood') || ft.includes('park') || ft.includes('nature')) {
      return (
        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          <Trees className="w-2.5 h-2.5" />
          <span>Ecology</span>
        </span>
      );
    }
    if (ft.includes('coordinate')) {
      return (
        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
          <Crosshair className="w-2.5 h-2.5" />
          <span>Coordinate</span>
        </span>
      );
    }
    if (ft.includes('administrative') || ft.includes('boundary')) {
      return (
        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30">
          <Landmark className="w-2.5 h-2.5" />
          <span>Admin</span>
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
        <Building2 className="w-2.5 h-2.5" />
        <span>Place</span>
      </span>
    );
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* 1. Main Search Trigger Pill */}
      <div 
        onClick={() => {
          setDropdownOpen(!dropdownOpen);
          setTimeout(() => inputRef.current?.focus(), 50);
        }}
        className="flex items-center justify-between px-3.5 py-2 rounded-lg bg-[#070d1e]/90 border border-cyan-500/25 hover:border-cyan-400/60 cursor-pointer transition-all shadow-inner"
      >
        <div className="flex items-center space-x-2.5 overflow-hidden">
          <MapPin className={`w-3.5 h-3.5 shrink-0 ${currentLocation && currentLocation.id ? 'text-cyan-400' : 'text-slate-500'}`} />
          <div className="truncate">
            {currentLocation && currentLocation.id ? (
              <>
                <span className="text-xs font-semibold text-white">{currentLocation.name}</span>
                <span className="text-[10px] text-cyan-400/80 ml-2 font-mono">
                  {currentLocation.latitude.toFixed(4)}°N, {currentLocation.longitude.toFixed(4)}°E
                </span>
              </>
            ) : (
              <span className="text-xs text-slate-400 font-mono italic">
                {placeholder || "Search any global city, lake, mountain, forest or coordinate..."}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-1.5 ml-2">
          {currentLocation && currentLocation.id && renderFeatureBadge(currentLocation.feature_type)}
          {(isSearching || isSearchingLive) && <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />}
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        </div>
      </div>

      {/* 2. Dynamic Worldwide Search Popover Dropdown */}
      {dropdownOpen && (
        <div className="absolute top-12 left-0 w-full min-w-[420px] max-w-[560px] bg-[#070e24] border border-cyan-500/35 rounded-xl shadow-2xl p-3 z-50 backdrop-blur-xl">
          {/* Direct Search Form */}
          <form onSubmit={handleSubmit} className="flex items-center px-3 py-2 mb-2 bg-[#030612] rounded-lg border border-cyan-500/30 focus-within:border-cyan-400 shadow-inner">
            <Search className="w-3.5 h-3.5 text-cyan-400 mr-2 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={typedQuery}
              onChange={(e) => setTypedQuery(e.target.value)}
              placeholder={placeholder}
              className="w-full bg-transparent text-xs text-white focus:outline-none placeholder-slate-500 font-sans"
              autoFocus
            />
            {typedQuery && (
              <button 
                type="button" 
                onClick={() => {
                  setTypedQuery('');
                  setSuggestions([]);
                }}
                className="text-slate-400 hover:text-white mr-1.5"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              type="submit"
              disabled={isSearchingLive || !typedQuery.trim()}
              className="px-2.5 py-1 rounded bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-[10px] font-mono font-bold disabled:opacity-40 transition-all shrink-0 shadow-sm"
            >
              {isSearchingLive ? 'Searching...' : 'Resolve'}
            </button>
          </form>

          {/* Live Search Status or Errors */}
          {isSearchingLive && (
            <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-cyan-300 font-mono">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
              <span>Querying global OpenStreetMap database...</span>
            </div>
          )}

          {searchError && (
            <div className="flex items-start gap-2 p-2 my-1 rounded bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300 font-mono">
              <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
              <span>{searchError}</span>
            </div>
          )}

          {/* Autocomplete Results from Worldwide Search */}
          {suggestions.length > 0 && (
            <div className="space-y-1 mt-1 max-h-72 overflow-y-auto">
              <div className="text-[9px] text-cyan-400 font-mono uppercase px-1 pb-1 font-bold tracking-wider flex items-center justify-between border-b border-cyan-500/20">
                <span>Worldwide Matching Places ({suggestions.length})</span>
                <span className="text-slate-500">OpenStreetMap / Nominatim</span>
              </div>
              {suggestions.map((loc) => {
                const isSelected = loc.id === currentLocation.id;
                return (
                  <button
                    key={loc.id}
                    onClick={() => handleSelect(loc)}
                    className={`w-full flex items-start justify-between p-2.5 rounded-lg text-left text-xs transition-all ${
                      isSelected
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                        : 'text-slate-300 hover:bg-[#0c1633] border border-transparent hover:border-slate-800'
                    }`}
                  >
                    <div className="space-y-0.5 pr-2">
                      <div className="font-semibold text-white flex items-center gap-1.5 flex-wrap">
                        <span>{loc.name.split(',')[0]}</span>
                        {renderFeatureBadge(loc.feature_type)}
                      </div>
                      <div className="text-[11px] text-slate-400 truncate max-w-sm">
                        {loc.name}
                      </div>
                      <div className="text-[10px] text-cyan-400/80 font-mono flex items-center gap-2">
                        <span>Lat: {loc.latitude.toFixed(4)}°, Lon: {loc.longitude.toFixed(4)}°</span>
                        <span>•</span>
                        <span>UTM {loc.target_utm}</span>
                      </div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-cyan-400 shrink-0 mt-1" />}
                  </button>
                );
              })}
            </div>
          )}

          {/* Fallback to Presets as Suggestions when not searching */}
          {suggestions.length === 0 && !isSearchingLive && (
            <div className="mt-1">
              <div className="text-[9px] text-slate-400 font-mono uppercase px-1 pb-1 tracking-wider flex items-center justify-between border-b border-slate-800">
                <span>Suggested Research Corridors (Optional Presets)</span>
                <span className="text-slate-500">Type above to search worldwide</span>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-1 mt-1">
                {availableLocations.map((loc) => {
                  const isSelected = loc.id === currentLocation.id;
                  return (
                    <button
                      key={loc.id}
                      onClick={() => handleSelect(loc)}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left text-xs transition-colors ${
                        isSelected 
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' 
                          : 'text-slate-300 hover:bg-[#0c1633]'
                      }`}
                    >
                      <div className="truncate">
                        <span className="font-semibold text-white">{loc.name.split(',')[0]}</span>
                        <span className="text-[10px] text-slate-400 font-mono ml-2">
                          {loc.country} • {loc.latitude.toFixed(2)}°N, {loc.longitude.toFixed(2)}°E
                        </span>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-cyan-400" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

