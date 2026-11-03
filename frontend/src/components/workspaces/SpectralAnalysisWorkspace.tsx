import React, { useState } from 'react';
import { 
  Sliders, Eye, Layers, Activity, Sparkles, 
  Info, BarChart3, RefreshCw, CheckCircle2, ChevronRight
} from 'lucide-react';
import { SatelliteScene, LocationInfo } from '../../types';

interface SpectralAnalysisWorkspaceProps {
  location: LocationInfo;
  scenes: SatelliteScene[];
  selectedYear: number;
}

interface SpectralPreset {
  id: string;
  name: string;
  bands: { r: string; g: string; b: string };
  description: string;
  application: string;
  previewUrl: string;
}

export const SpectralAnalysisWorkspace: React.FC<SpectralAnalysisWorkspaceProps> = ({
  location,
  scenes,
  selectedYear
}) => {
  const activeScene = scenes.find(s => s.year === selectedYear) || scenes[0];

  const presets: SpectralPreset[] = [
    {
      id: 'true_color',
      name: 'True Color Natural RGB',
      bands: { r: 'B04 (Red)', g: 'B03 (Green)', b: 'B02 (Blue)' },
      description: 'Standard human-vision spectrum composition showing natural surface appearance.',
      application: 'General baseline topography, urban footprint, water body outlines.',
      previewUrl: activeScene?.thumbnail_url || '/api/imagery/tile?mission=Sentinel-2&year=2024'
    },
    {
      id: 'false_color',
      name: 'False Color Infrared (NIR)',
      bands: { r: 'B08 (NIR)', g: 'B04 (Red)', b: 'B03 (Green)' },
      description: 'Vigorous vegetation absorbs red light and reflects strongly in the near-infrared, appearing bright crimson red.',
      application: 'Tree canopy density, crop vigor, chlorophyll dynamics, wetland boundaries.',
      previewUrl: '/api/imagery/tile?mission=Sentinel-2&year=2024'
    },
    {
      id: 'swir',
      name: 'Shortwave Infrared (SWIR Composite)',
      bands: { r: 'B12 (SWIR2)', g: 'B08 (NIR)', b: 'B04 (Red)' },
      description: 'Penetrates atmospheric haze and smoke. Delineates moisture stress, soil moisture, and active burn scars.',
      application: 'Soil moisture content, fire scars, mineral mapping, geological structures.',
      previewUrl: '/api/imagery/tile?mission=Landsat&year=2015'
    },
    {
      id: 'ndvi',
      name: 'NDVI (Normalized Difference Vegetation Index)',
      bands: { r: '(NIR - Red)', g: '/', b: '(NIR + Red)' },
      description: 'Calibrated chlorophyll absorption index spanning -1.0 to +1.0. High values (+0.6 to +0.8) indicate dense healthy tree canopies.',
      application: 'Deforestation tracking, urban canopy degradation, agricultural yields.',
      previewUrl: '/api/imagery/tile?mission=Sentinel-2&year=2020'
    },
    {
      id: 'ndwi',
      name: 'NDWI (Normalized Difference Water Index)',
      bands: { r: '(Green - NIR)', g: '/', b: '(Green + NIR)' },
      description: 'Maximizes reflectance of water bodies while attenuating soil and terrestrial vegetation reflectance.',
      application: 'Lake surface area contraction, flood mapping, reservoir storage telemetry.',
      previewUrl: '/api/imagery/tile?mission=Landsat&year=1995'
    }
  ];

  const [activePreset, setActivePreset] = useState<SpectralPreset>(presets[0]);
  const [bandR, setBandR] = useState('B04');
  const [bandG, setBandG] = useState('B03');
  const [bandB, setBandB] = useState('B02');

  const availableBands = [
    { code: 'B01', name: 'Coastal Aerosol (443 nm)' },
    { code: 'B02', name: 'Blue (490 nm)' },
    { code: 'B03', name: 'Green (560 nm)' },
    { code: 'B04', name: 'Red (665 nm)' },
    { code: 'B05', name: 'Vegetation Red Edge (705 nm)' },
    { code: 'B08', name: 'NIR Near-Infrared (842 nm)' },
    { code: 'B11', name: 'SWIR-1 (1610 nm)' },
    { code: 'B12', name: 'SWIR-2 (2190 nm)' },
  ];

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 max-w-7xl mx-auto space-y-6">
      {/* 1. Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-mono">
            <Sliders className="w-5 h-5 text-cyan-400" />
            <span>Multi-Spectral Raster & Band Composition Studio</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Perform band ratioing, index computation, and spectral composite transformations for {location.name}.
          </p>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs text-slate-300 bg-space-950 px-3 py-1.5 rounded-lg border border-slate-800">
          <span className="text-slate-400">Sensor:</span>
          <span className="text-cyan-400 font-bold">{activeScene?.sensor || 'MSI L2A / OLI'}</span>
        </div>
      </div>

      {/* 2. Preset Selector Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {presets.map((preset) => {
          const isSelected = activePreset.id === preset.id;
          return (
            <button
              key={preset.id}
              onClick={() => setActivePreset(preset)}
              className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-cyan-500/15 border-cyan-400 ring-2 ring-cyan-500/30 shadow-lg shadow-cyan-500/20'
                  : 'bg-[#070e24]/70 border-slate-800/80 hover:border-cyan-500/40 text-slate-400 hover:text-white'
              }`}
            >
              <div>
                <div className={`text-xs font-bold ${isSelected ? 'text-cyan-300' : 'text-white'}`}>
                  {preset.name}
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">
                  R: {preset.bands.r.split(' ')[0]} • G: {preset.bands.g.split(' ')[0]} • B: {preset.bands.b.split(' ')[0]}
                </div>
              </div>
              <div className="mt-3 flex items-center text-[10px] font-mono text-cyan-400 font-semibold">
                <span>Inspect Composite</span>
                <ChevronRight className="w-3 h-3 ml-1" />
              </div>
            </button>
          );
        })}
      </div>

      {/* 3. Main Display: Interactive Composite Preview (Left) + Interactive Band Selector & Spectral Profile (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left: Large Raster Composite Canvas */}
        <div className="lg:col-span-7 flex flex-col space-y-3">
          <div className="relative h-[420px] rounded-2xl overflow-hidden bg-[#030612] border border-cyan-500/30 shadow-2xl flex items-center justify-center">
            <img
              src={activePreset.previewUrl}
              alt={activePreset.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/api/imagery/tile?mission=Sentinel-2&year=2024';
              }}
            />

            {/* Overlaid Composite Name Badge */}
            <div className="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-[#040816]/90 border border-cyan-500/30 backdrop-blur-md">
              <div className="text-xs font-bold text-white font-mono">{activePreset.name}</div>
              <div className="text-[10px] text-cyan-400 font-mono">
                Formula: {activePreset.bands.r} + {activePreset.bands.g} + {activePreset.bands.b}
              </div>
            </div>

            {/* Scale Bar */}
            <div className="absolute bottom-4 right-4 px-3 py-1 rounded bg-[#040816]/90 border border-slate-700 text-[10px] font-mono text-slate-300">
              BOA Level-2A Surface Reflectance
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#070e24]/70 border border-cyan-500/20 text-xs text-slate-300">
            <strong className="text-cyan-300 font-mono uppercase">Spectral Explanation: </strong>
            {activePreset.description}
          </div>
        </div>

        {/* Right: Interactive Band Selector & Physical Response */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          {/* Custom Band Mapping Form */}
          <div className="p-4 rounded-xl bg-[#070e24]/90 border border-cyan-500/25 space-y-3">
            <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
              <Layers className="w-4 h-4" />
              <span>Custom Band Composition</span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div>
                <label className="text-red-400 font-bold block mb-1">Red Channel Assignment:</label>
                <select
                  value={bandR}
                  onChange={(e) => setBandR(e.target.value)}
                  className="w-full bg-[#030612] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-red-400"
                >
                  {availableBands.map(b => (
                    <option key={b.code} value={b.code}>{b.code} - {b.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-emerald-400 font-bold block mb-1">Green Channel Assignment:</label>
                <select
                  value={bandG}
                  onChange={(e) => setBandG(e.target.value)}
                  className="w-full bg-[#030612] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-400"
                >
                  {availableBands.map(b => (
                    <option key={b.code} value={b.code}>{b.code} - {b.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-blue-400 font-bold block mb-1">Blue Channel Assignment:</label>
                <select
                  value={bandB}
                  onChange={(e) => setBandB(e.target.value)}
                  className="w-full bg-[#030612] border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-blue-400"
                >
                  {availableBands.map(b => (
                    <option key={b.code} value={b.code}>{b.code} - {b.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Practical Remote Sensing Application */}
          <div className="p-4 rounded-xl bg-[#070e24]/90 border border-cyan-500/25 space-y-2 flex-1">
            <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>Target Remote Sensing Application</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {activePreset.application}
            </p>

            <div className="pt-3 border-t border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
              <div>Wavelength Span: 400 nm - 2200 nm</div>
              <div>Atmospheric Correction: Sen2Cor 2.10 BOA</div>
              <div className="text-emerald-400">Atmospheric Absorption Window: Clear</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

