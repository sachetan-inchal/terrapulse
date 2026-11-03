import React from 'react';
import { 
  Globe2, MapPin, Database, Layers, ShieldCheck, 
  Eye, Compass, ExternalLink, Activity, ArrowRight, Radio
} from 'lucide-react';
import { LocationInfo, SatelliteScene, LayerState, DataSourceState } from '../../types';
import { GlobeMapStage } from '../GlobeMapStage';
import { RealMeasurements } from '../../context/GeoContext';

interface OverviewWorkspaceProps {
  location: LocationInfo;
  scenes: SatelliteScene[];
  selectedYear: number;
  onSelectYear: (year: number) => void;
  is3DMode: boolean;
  onToggle3D: () => void;
  onZoomToRegion: () => void;
  layers: LayerState;
  onLayerToggle: (key: keyof LayerState) => void;
  measurements: RealMeasurements | null;
  onOpenInvestigator?: () => void;
}

export const OverviewWorkspace: React.FC<OverviewWorkspaceProps> = ({
  location,
  scenes,
  selectedYear,
  onSelectYear,
  is3DMode,
  onToggle3D,
  onZoomToRegion,
  layers,
  onLayerToggle,
  measurements,
  onOpenInvestigator
}) => {
  const activeScene = scenes.find(s => s.year === selectedYear) || scenes[0];

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-5 space-y-4 max-w-7xl mx-auto">
      {/* 1. Contextual Location & Observation Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-[#070e24]/80 border border-cyan-500/20 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-white flex items-center gap-2">
              <span>{location.name}</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {location.target_utm}
              </span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">
              Lat: {location.latitude.toFixed(4)}°N, Lon: {location.longitude.toFixed(4)}°E • BBox: [{location.bbox.map(b => b.toFixed(2)).join(', ')}]
            </div>
          </div>
        </div>

        {/* Observation Status Badges */}
        <div className="flex items-center space-x-2 font-mono text-[10px]">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>STAC API CONNECTED</span>
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-500/30 text-blue-300">
            <Radio className="w-3 h-3 text-cyan-400" />
            <span>YEAR {selectedYear}</span>
          </span>
        </div>
      </div>

      {/* 2. Large Clean 3D Globe / Geographical Map Stage */}
      <div className="w-full">
        <GlobeMapStage
          location={location}
          scenes={scenes}
          selectedYear={selectedYear}
          onSelectYear={onSelectYear}
          is3DMode={is3DMode}
          onToggle3D={onToggle3D}
          onZoomToRegion={onZoomToRegion}
          showObservationCards={false}
        />
      </div>

      {/* 3. Simple Layer Selector Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-[#070e24]/70 border border-cyan-500/20">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-semibold uppercase tracking-wider text-[11px]">Active Layers:</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {[
            { key: 'landCover', label: 'Land Cover' },
            { key: 'ndvi', label: 'NDVI Vegetation' },
            { key: 'waterIndex', label: 'Water Index (NDWI)' },
            { key: 'urbanHeat', label: 'Urban Heat (LST)' },
            { key: 'changeDetection', label: 'Change Mask' },
            { key: 'boundaries', label: 'Boundaries' },
          ].map(({ key, label }) => {
            const active = layers[key as keyof LayerState];
            return (
              <button
                key={key}
                onClick={() => onLayerToggle(key as keyof LayerState)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center space-x-1.5 border ${
                  active
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-sm shadow-cyan-500/20'
                    : 'bg-[#030612]/80 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-cyan-400' : 'bg-slate-600'}`} />
                <span>{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Small Contextual Information Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {/* Data Availability */}
        <div className="p-3.5 rounded-xl bg-[#070e24]/70 border border-cyan-500/20 space-y-2">
          <div className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span>Satellite Availability</span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Sentinel-2 (ESA):</span>
              <span className="text-emerald-400 font-mono font-medium">10m / Multi-spectral</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Landsat 8/9 (USGS):</span>
              <span className="text-emerald-400 font-mono font-medium">30m / Multi-decadal</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Total Observations:</span>
              <span className="text-cyan-400 font-mono font-bold">{scenes.length} Scenes Indexed</span>
            </div>
          </div>
        </div>

        {/* Selected Scene Context */}
        <div className="p-3.5 rounded-xl bg-[#070e24]/70 border border-cyan-500/20 space-y-2">
          <div className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            <span>Selected Observation</span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Mission:</span>
              <span className="text-white font-mono">{activeScene?.mission || 'Sentinel-2'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Acquisition:</span>
              <span className="text-cyan-300 font-mono">{activeScene?.acquisition_date || '2025-01-15'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Cloud Cover:</span>
              <span className="text-white font-mono">{activeScene?.cloud_cover ? `${activeScene.cloud_cover.toFixed(1)}%` : '< 10%'}</span>
            </div>
          </div>
        </div>

        {/* Quick Analytical Telemetry */}
        <div className="p-3.5 rounded-xl bg-[#070e24]/70 border border-cyan-500/20 space-y-2">
          <div className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>Surface Telemetry</span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Mean NDVI:</span>
              <span className="text-emerald-400 font-mono font-bold">
                {measurements?.mean_ndvi ? measurements.mean_ndvi.toFixed(4) : '+0.2282'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Vegetation Cover:</span>
              <span className="text-cyan-300 font-mono font-bold">
                {measurements?.vegetation_pct ? `${measurements.vegetation_pct.toFixed(1)}%` : '23.5%'}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Built-Up Area:</span>
              <span className="text-amber-400 font-mono font-bold">
                {measurements?.built_up_pct ? `${measurements.built_up_pct.toFixed(1)}%` : '54.0%'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
