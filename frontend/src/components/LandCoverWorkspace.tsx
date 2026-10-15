import React from 'react';
import { Layers, PieChart, Activity, Droplet, Trees, Building2 } from 'lucide-react';
import { EnvironmentalAnalysis } from '../types';

interface LandCoverWorkspaceProps {
  analysis: EnvironmentalAnalysis | null;
  currentYear: number;
}

export const LandCoverWorkspace: React.FC<LandCoverWorkspaceProps> = ({ analysis, currentYear }) => {
  if (!analysis) return null;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto max-h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-accent" />
            Land Cover & Environmental Spectral Analysis ({currentYear})
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Quantified land use / land cover (LULC) distributions, true dense tree canopy separation, and multispectral vegetation/water indices.
          </p>
        </div>
        <div className="text-xs font-mono bg-space-950 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
          SENSOR: <strong className="text-cyan-accent">{analysis.sensor}</strong>
        </div>
      </div>

      {/* Critical Scientific Guardrail Notice */}
      <div className="bg-blue-950/40 border border-blue-500/30 p-3 rounded-xl flex items-start space-x-3 text-xs text-slate-300">
        <Activity className="w-4 h-4 text-cyan-accent shrink-0 mt-0.5" />
        <div>
          <strong className="text-cyan-accent font-mono uppercase">Methodological Integrity Note:</strong> NDVI measures chlorophyll absorption and green reflectance. It is not an uncalibrated proxy for tree canopy. Dense forest cover is classified separately from herbaceous vegetation, golf courses, or lawns.
        </div>
      </div>

      {/* Class Statistics Grid */}
      <div className="grid grid-cols-5 gap-3">
        {analysis.classes.map((cls) => (
          <div key={cls.name} className="glass-panel p-3.5 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cls.hex_color }} />
              <span className="text-[10px] font-mono text-slate-400">{cls.percentage}%</span>
            </div>
            <div className="text-xs font-bold text-white">{cls.name}</div>
            <div className="text-sm font-mono font-bold" style={{ color: cls.hex_color }}>
              {cls.area_sq_km} km²
            </div>
          </div>
        ))}
      </div>

      {/* Indices & Water Dynamics */}
      <div className="grid grid-cols-2 gap-4">
        {/* NDVI */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-white font-mono flex items-center gap-2">
              <Trees className="w-4 h-4 text-emerald-400" />
              Normalized Difference Vegetation Index (NDVI)
            </div>
            <span className="text-xs font-mono font-bold text-emerald-400">{analysis.mean_ndvi.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Computed as (NIR - Red) / (NIR + Red) across calibrated spectral bands. Values &gt; 0.4 indicate healthy photosynthesizing canopy, while &lt; 0.2 represents bare soil or concrete.
          </p>
          <div className="h-2 w-full rounded-full bg-gradient-to-r from-red-500 via-amber-400 to-emerald-500 relative">
            <div 
              className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-space-950 shadow-md"
              style={{ left: `${Math.max(0, Math.min(100, (analysis.mean_ndvi + 0.2) / 1.0 * 100))}%` }}
            />
          </div>
        </div>

        {/* NDWI */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-white font-mono flex items-center gap-2">
              <Droplet className="w-4 h-4 text-sky-400" />
              Normalized Difference Water Index (NDWI)
            </div>
            <span className="text-xs font-mono font-bold text-sky-400">{analysis.mean_ndwi.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Computed as (Green - NIR) / (Green + NIR). Enhances open water bodies (lakes, wetlands, reservoirs) while suppressing soil and vegetation noise.
          </p>
          <div className="h-2 w-full rounded-full bg-gradient-to-r from-slate-700 via-sky-600 to-blue-500 relative">
            <div 
              className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-space-950 shadow-md"
              style={{ left: `${Math.max(0, Math.min(100, (analysis.mean_ndwi + 0.3) / 0.6 * 100))}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
