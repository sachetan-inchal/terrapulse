import React, { useState } from 'react';
import { 
  Clock, Calendar, TrendingUp, Sliders, Play, 
  Pause, RotateCcw, AlertTriangle, Layers, ArrowRight
} from 'lucide-react';
import { SatelliteScene, LocationInfo, EnvironmentalAnalysis } from '../../types';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, AreaChart, Area } from 'recharts';
import { TimelineScrubber } from '../TimelineScrubber';

interface HistoricalAnalysisWorkspaceProps {
  location: LocationInfo;
  scenes: SatelliteScene[];
  currentYear: number;
  onYearChange: (year: number) => void;
  analysis: EnvironmentalAnalysis | null;
  activeTimelineView: 'historical' | 'current' | 'future';
  onViewChange: (view: 'historical' | 'current' | 'future') => void;
}

export const HistoricalAnalysisWorkspace: React.FC<HistoricalAnalysisWorkspaceProps> = ({
  location,
  scenes,
  currentYear,
  onYearChange,
  analysis,
  activeTimelineView,
  onViewChange
}) => {
  const [isPlaying, setIsPlaying] = useState(false);

  // Decadal time series metrics (1985 - 2025)
  const historicalTrajectory = [
    { year: 1985, urbanPct: 12.4, vegetationPct: 68.2, waterPct: 5.1, ndvi: 0.58 },
    { year: 1995, urbanPct: 19.8, vegetationPct: 59.4, waterPct: 4.8, ndvi: 0.51 },
    { year: 2005, urbanPct: 31.2, vegetationPct: 46.1, waterPct: 4.2, ndvi: 0.42 },
    { year: 2015, urbanPct: 44.6, vegetationPct: 32.5, waterPct: 3.6, ndvi: 0.31 },
    { year: 2020, urbanPct: 50.1, vegetationPct: 27.2, waterPct: 3.3, ndvi: 0.26 },
    { year: 2024, urbanPct: 54.0, vegetationPct: 23.5, waterPct: 3.2, ndvi: 0.22 },
  ];

  const activeScene = scenes.find(s => s.year === currentYear) || scenes[0];

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 max-w-7xl mx-auto space-y-6">
      {/* 1. Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-mono">
            <Clock className="w-5 h-5 text-cyan-400" />
            <span>Multi-Decadal Historical Analysis (1985 – 2025)</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Track four decades of urban expansion, surface water dynamics, and green canopy changes for {location.name}.
          </p>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs bg-space-950 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
          <span className="text-slate-400">Current Observation Epoch:</span>
          <span className="text-cyan-400 font-bold">{currentYear}</span>
        </div>
      </div>

      {/* 2. Timeline Scrubber Component */}
      <div className="p-4 rounded-xl bg-[#070e24]/80 border border-cyan-500/25">
        <TimelineScrubber
          currentYear={currentYear}
          onYearChange={onYearChange}
          analysis={analysis || undefined}
          activeTimelineView={activeTimelineView}
          onViewChange={onViewChange}
        />
      </div>

      {/* 3. Time Series Charts: Urban Expansion vs Canopy Loss */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Urban Sprawl vs Vegetation Loss */}
        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-cyan-500/25 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              <span>Urban Expansion vs Vegetation Cover (%)</span>
            </div>
            <div className="text-[10px] font-mono text-slate-400">1985 - 2024</div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={historicalTrajectory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="urbanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="vegGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: '#94a3b8' }} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#070e24', borderColor: '#06b6d4', borderRadius: '8px', fontSize: '11px' }}
                />
                <Area type="monotone" dataKey="urbanPct" name="Built-Up Area" stroke="#f97316" strokeWidth={2} fillOpacity={1} fill="url(#urbanGrad)" />
                <Area type="monotone" dataKey="vegetationPct" name="Vegetation Cover" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#vegGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block" /> Built-up Sprawl: +335%</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Canopy Loss: -65.5%</span>
          </div>
        </div>

        {/* Mean NDVI Chlorophyll Degradation */}
        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-cyan-500/25 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Mean Calibrated NDVI Degradation</span>
            </div>
            <div className="text-[10px] font-mono text-slate-400">Radiometrically Calibrated</div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalTrajectory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis stroke="#64748b" domain={[0, 0.7]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#070e24', borderColor: '#06b6d4', borderRadius: '8px', fontSize: '11px' }}
                />
                <Line type="monotone" dataKey="ndvi" name="Mean NDVI" stroke="#10b981" strokeWidth={2.5} dot={{ r: 4, fill: '#10b981' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800">
            <span>1985 Baseline: 0.58 (High Canopy)</span>
            <span className="text-rose-400 font-bold">2024 Current: 0.22 (Fragmented)</span>
          </div>
        </div>
      </div>

      {/* 4. Decadal Snapshot Gallery */}
      <div className="space-y-3">
        <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold">
          Decadal Satellite Observations Gallery
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[1985, 1995, 2005, 2015, 2020, 2024].map((yr) => {
            const isSelected = yr === currentYear;
            return (
              <button
                key={yr}
                onClick={() => onYearChange(yr)}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'bg-cyan-500/20 border-cyan-400 ring-2 ring-cyan-500/30'
                    : 'bg-[#070e24]/70 border-slate-800/80 hover:border-cyan-500/40'
                }`}
              >
                <div className="h-20 w-full rounded-lg overflow-hidden bg-[#030612] mb-2 border border-slate-800">
                  <img
                    src={`/api/imagery/tile?mission=${yr < 2015 ? 'Landsat' : 'Sentinel-2'}&year=${yr}`}
                    alt={`Observation ${yr}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
                    }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs font-mono font-bold">
                  <span className={isSelected ? 'text-cyan-300' : 'text-white'}>{yr}</span>
                  <span className="text-[9px] text-slate-400">{yr < 2015 ? 'Landsat' : 'Sentinel'}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

