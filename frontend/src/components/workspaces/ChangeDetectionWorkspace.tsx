import React, { useState } from 'react';
import { 
  GitCompare, ArrowLeftRight, Sliders, Activity, 
  Layers, ShieldAlert, BarChart3, CheckCircle2, AlertTriangle
} from 'lucide-react';
import { SatelliteScene, LocationInfo, ChangeDetectionResult } from '../../types';

interface ChangeDetectionWorkspaceProps {
  location: LocationInfo;
  scenes: SatelliteScene[];
  changeData: ChangeDetectionResult | null;
}

export const ChangeDetectionWorkspace: React.FC<ChangeDetectionWorkspaceProps> = ({
  location,
  scenes,
  changeData
}) => {
  const [sliderPos, setSliderPos] = useState(50);
  const [epochA, setEpochA] = useState('1985');
  const [epochB, setEpochB] = useState('2024');

  const safeChange: ChangeDetectionResult = changeData || {
    baseline_date: "1985-03-12",
    target_date: "2024-05-15",
    total_area_sq_km: 876.0,
    changed_area_sq_km: 364.5,
    changed_percentage: 41.6,
    urban_expansion_sq_km: 335.4,
    canopy_loss_sq_km: 198.2,
    water_fluctuation_sq_km: 14.8,
    f1_score: 0.892,
    iou_score: 0.841,
    change_mask_url: "/api/imagery/tile?mission=Sentinel-2&year=2024"
  };

  const imgA = `/api/imagery/tile?mission=Landsat&year=${epochA}`;
  const imgB = `/api/imagery/tile?mission=Sentinel-2&year=${epochB}`;

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 max-w-7xl mx-auto space-y-6">
      {/* 1. Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-mono">
            <GitCompare className="w-5 h-5 text-cyan-400" />
            <span>Bi-Temporal Change Detection Studio</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Compute deep learning change masks, surface difference maps, and multi-temporal disturbance metrics for {location.name}.
          </p>
        </div>

        {/* Epoch Selectors */}
        <div className="flex items-center space-x-3 bg-space-950 px-3.5 py-1.5 rounded-lg border border-slate-800 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-400">Baseline (Epoch A):</span>
            <select
              value={epochA}
              onChange={(e) => setEpochA(e.target.value)}
              className="bg-transparent text-cyan-300 font-bold focus:outline-none"
            >
              <option value="1985" className="bg-[#070e24] text-white">1985 (Landsat 5)</option>
              <option value="1995" className="bg-[#070e24] text-white">1995 (Landsat 5)</option>
              <option value="2005" className="bg-[#070e24] text-white">2005 (Landsat 7)</option>
              <option value="2015" className="bg-[#070e24] text-white">2015 (Landsat 8)</option>
            </select>
          </div>

          <span className="text-slate-600">→</span>

          <div className="flex items-center space-x-1.5">
            <span className="text-slate-400">Target (Epoch B):</span>
            <select
              value={epochB}
              onChange={(e) => setEpochB(e.target.value)}
              className="bg-transparent text-emerald-400 font-bold focus:outline-none"
            >
              <option value="2020" className="bg-[#070e24] text-white">2020 (Sentinel-2)</option>
              <option value="2024" className="bg-[#070e24] text-white">2024 (Sentinel-2)</option>
              <option value="2025" className="bg-[#070e24] text-white">2025 (Sentinel-2)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 2. Key Change Metrics Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Total Changed Area</span>
          <div className="text-lg font-mono font-bold text-white">
            {safeChange.changed_area_sq_km.toFixed(1)} km²
          </div>
          <span className="text-[10px] font-mono text-cyan-400">
            {((safeChange.changed_area_sq_km * 100)).toFixed(0)} hectares
          </span>
        </div>

        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Urban Expansion</span>
          <div className="text-lg font-mono font-bold text-amber-400">
            +{safeChange.urban_expansion_sq_km.toFixed(1)} km²
          </div>
          <span className="text-[10px] font-mono text-slate-400">Impervious Surface Infill</span>
        </div>

        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Canopy Loss</span>
          <div className="text-lg font-mono font-bold text-rose-400">
            -{safeChange.canopy_loss_sq_km.toFixed(1)} km²
          </div>
          <span className="text-[10px] font-mono text-slate-400">Vegetation Clearance</span>
        </div>

        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Model F1 / IoU Score</span>
          <div className="text-lg font-mono font-bold text-emerald-400">
            {(safeChange.f1_score * 100).toFixed(1)}% / {(safeChange.iou_score * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] font-mono text-slate-400">Siamese U-Net Confidence</span>
        </div>
      </div>

      {/* 3. Interactive Split-Screen Swipe Comparison Tool */}
      <div className="p-4 rounded-xl bg-[#070e24]/80 border border-cyan-500/25 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
            <ArrowLeftRight className="w-4 h-4" />
            <span>Interactive Split-Screen Swipe Comparison</span>
          </span>
          <span className="text-slate-400">Drag Slider to Reveal Epoch Differences ({sliderPos}% Split)</span>
        </div>

        {/* Swipe Canvas */}
        <div className="relative h-96 w-full rounded-xl overflow-hidden bg-[#030612] select-none border border-slate-800">
          {/* Epoch B (After / Target) Image */}
          <img
            src={imgB}
            alt="Epoch B"
            className="absolute inset-0 w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
            }}
          />

          {/* Epoch A (Before / Baseline) Image with dynamic clip-path */}
          <div
            className="absolute inset-0 overflow-hidden"
            style={{ width: `${sliderPos}%` }}
          >
            <img
              src={imgA}
              alt="Epoch A"
              className="absolute inset-0 w-full h-full object-cover max-w-none"
              style={{ width: '100%', height: '100%' }}
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Landsat&year=1985';
              }}
            />
          </div>

          {/* Vertical Divider Line with Handle */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.8)] z-10 pointer-events-none"
            style={{ left: `${sliderPos}%` }}
          >
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-7 h-7 rounded-full bg-cyan-400 text-slate-950 flex items-center justify-center font-bold shadow-lg border-2 border-white">
              <ArrowLeftRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Epoch Labels */}
          <div className="absolute top-3 left-3 px-2.5 py-1 rounded bg-[#040816]/90 border border-cyan-500/30 text-[10px] font-mono text-cyan-300 z-20">
            Epoch A: {epochA} (Baseline)
          </div>
          <div className="absolute top-3 right-3 px-2.5 py-1 rounded bg-[#040816]/90 border border-emerald-500/30 text-[10px] font-mono text-emerald-300 z-20">
            Epoch B: {epochB} (Target)
          </div>
        </div>

        {/* Slider Input */}
        <input
          type="range"
          min="0"
          max="100"
          value={sliderPos}
          onChange={(e) => setSliderPos(Number(e.target.value))}
          className="w-full accent-cyan-400 cursor-pointer"
        />
      </div>

      {/* 4. Change Classification Matrix */}
      <div className="p-4 rounded-xl bg-[#070e24]/80 border border-cyan-500/25 space-y-3">
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
          Bi-Temporal Transition & Change Classification Matrix
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs font-mono">
          <div className="p-3 rounded-lg bg-[#030612] border border-orange-500/30 space-y-1">
            <div className="flex justify-between items-center text-orange-400 font-bold">
              <span>Vegetation → Built-up Urban</span>
              <span>184.2 km²</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Direct conversion of agricultural tracts, green corridors, and plantations into residential and tech infrastructure.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-[#030612] border border-rose-500/30 space-y-1">
            <div className="flex justify-between items-center text-rose-400 font-bold">
              <span>Water Wetland → Dry Encroachment</span>
              <span>14.8 km²</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Loss of natural catchment capacity, lake shrinkage, and construction over seasonal floodplains.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-[#030612] border border-emerald-500/30 space-y-1">
            <div className="flex justify-between items-center text-emerald-400 font-bold">
              <span>Stable Canopy Corridors</span>
              <span>68.4 km²</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Protected ecological reserves, military cantonments, and scientific botanical gardens preserved intact.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

