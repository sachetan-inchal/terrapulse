import React, { useState } from 'react';
import { Clock, Sliders, Calendar, ArrowLeftRight } from 'lucide-react';
import { SatelliteScene } from '../types';

interface TimeSeriesWorkspaceProps {
  scenes: SatelliteScene[];
  currentYear: number;
}

export const TimeSeriesWorkspace: React.FC<TimeSeriesWorkspaceProps> = ({ scenes, currentYear }) => {
  const [sliderPos, setSliderPos] = useState(50);
  const [dateA, setDateA] = useState('1985');
  const [dateB, setDateB] = useState('2024');

  // Dynamically resolve real satellite images from scenes or STAC tile provider
  const yearA = parseInt(dateA, 10);
  const yearB = parseInt(dateB, 10);
  
  const sceneA = scenes.find(s => s.year === yearA) || scenes[scenes.length - 1];
  const sceneB = scenes.find(s => s.year === yearB) || scenes[0];

  const imgA = sceneA?.thumbnail_url || `/api/imagery/tile?mission=Landsat&year=${dateA}`;
  const imgB = sceneB?.thumbnail_url || `/api/imagery/tile?mission=Sentinel-2&year=${dateB}`;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto max-h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-cyan-accent" />
            Bi-Temporal Observation Comparison Studio
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Compare multi-decadal satellite observations with pixel-aligned split sliders and side-by-side extent locking.
          </p>
        </div>

        {/* Date Selectors */}
        <div className="flex items-center space-x-3 bg-space-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs font-mono">
          <span className="text-slate-400">Epoch A:</span>
          <select 
            value={dateA} 
            onChange={(e) => setDateA(e.target.value)}
            className="bg-transparent text-cyan-accent font-bold focus:outline-none"
          >
            {scenes.length > 0 ? (
              scenes.map(s => (
                <option key={`a-${s.id}`} value={s.year} className="bg-space-900 text-white">
                  {s.year} ({s.mission})
                </option>
              ))
            ) : (
              <>
                <option value="1985">1985 (Landsat 5)</option>
                <option value="1995">1995 (Landsat 5)</option>
                <option value="2005">2005 (Landsat 7)</option>
              </>
            )}
          </select>

          <ArrowLeftRight className="w-3.5 h-3.5 text-slate-600" />

          <span className="text-slate-400">Epoch B:</span>
          <select 
            value={dateB} 
            onChange={(e) => setDateB(e.target.value)}
            className="bg-transparent text-rose-400 font-bold focus:outline-none"
          >
            {scenes.length > 0 ? (
              scenes.map(s => (
                <option key={`b-${s.id}`} value={s.year} className="bg-space-900 text-white">
                  {s.year} ({s.mission})
                </option>
              ))
            ) : (
              <>
                <option value="2015">2015 (Landsat 8)</option>
                <option value="2020">2020 (Sentinel-2)</option>
                <option value="2024">2024 (Sentinel-2)</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Before / After Interactive Split-View Slider */}
      <div className="glass-panel p-4 rounded-xl border border-cyan-500/25 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-cyan-accent font-bold">PRE-STATE: {dateA} ({sceneA?.mission || 'Landsat'})</span>
          <span className="text-slate-400">Swipe slider horizontally to inspect transition boundary</span>
          <span className="text-rose-400 font-bold">POST-STATE: {dateB} ({sceneB?.mission || 'Sentinel-2'})</span>
        </div>

        {/* Image Split Slider Container */}
        <div className="relative w-full h-[480px] rounded-lg overflow-hidden border border-slate-800 select-none bg-space-950">
          {/* Background After Image (Epoch B) */}
          <img
            src={imgB}
            alt={`Epoch B ${dateB}`}
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* Foreground Clipped Before Image (Epoch A) */}
          <div
            className="absolute inset-y-0 left-0 overflow-hidden"
            style={{ width: `${sliderPos}%` }}
          >
            <img
              src={imgA}
              alt={`Epoch A ${dateA}`}
              className="absolute inset-0 w-full h-full object-cover max-w-none"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>

          {/* Divider Line */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-cyan-accent shadow-glow-cyan z-20 pointer-events-none"
            style={{ left: `${sliderPos}%` }}
          >
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-space-950 border-2 border-cyan-accent shadow-glow-cyan flex items-center justify-center text-cyan-accent text-[10px] font-mono">
              ↔
            </div>
          </div>

          {/* Transparent Range Input Slider on Top */}
          <input
            type="range"
            min={0}
            max={100}
            value={sliderPos}
            onChange={(e) => setSliderPos(Number(e.target.value))}
            className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-30"
          />
        </div>
      </div>
    </div>
  );
};
