import React from 'react';

interface VisualLayersBarProps {
  previewUrl?: string;
}

export const VisualLayersBar: React.FC<VisualLayersBarProps> = ({ previewUrl }) => {
  const satelliteImg = previewUrl || '/api/imagery/tile?mission=Sentinel-2&year=2024';

  return (
    <div className="glass-panel p-3.5 rounded-xl border border-cyan-500/20">
      <div className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider mb-2.5">
        Visual Layers (Multi-Spectral Bands)
      </div>

      <div className="grid grid-cols-3 gap-2.5">
        {/* Layer 1: Land Cover */}
        <div className="bg-space-950/70 border border-slate-800 rounded-lg p-2 flex flex-col justify-between">
          <div className="h-16 rounded overflow-hidden mb-1.5 relative bg-gradient-to-tr from-emerald-900/60 via-amber-900/40 to-rose-900/60 border border-slate-800">
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-85" 
              style={{ backgroundImage: `url('${satelliteImg}')` }} 
            />
            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-space-950/80 text-[8px] font-mono text-cyan-accent border border-cyan-500/30">
              AI Seg Net
            </span>
          </div>
          <div className="text-[10px] font-semibold text-white mb-1">Land Cover</div>
          <div className="flex items-center justify-between text-[8px] text-slate-400 font-mono">
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />Veg</span>
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-blue-400" />Water</span>
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" />Agri</span>
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-rose-400" />Urban</span>
          </div>
        </div>

        {/* Layer 2: NDVI */}
        <div className="bg-space-950/70 border border-slate-800 rounded-lg p-2 flex flex-col justify-between">
          <div className="h-16 rounded overflow-hidden mb-1.5 relative border border-slate-800 bg-gradient-to-r from-red-600 via-yellow-500 to-green-500">
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-75 mix-blend-overlay" 
              style={{ backgroundImage: `url('${satelliteImg}')` }} 
            />
            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-space-950/80 text-[8px] font-mono text-emerald-300 border border-emerald-500/30">
              NIR/Red Ratio
            </span>
          </div>
          <div className="text-[10px] font-semibold text-white mb-1">NDVI Index</div>
          <div className="flex items-center justify-between text-[8px] text-slate-400 font-mono">
            <span>-0.2 (Arid)</span>
            <div className="h-1 flex-1 mx-2 rounded bg-gradient-to-r from-red-500 via-yellow-400 to-emerald-500" />
            <span>+0.8 (Canopy)</span>
          </div>
        </div>

        {/* Layer 3: Change Detection */}
        <div className="bg-space-950/70 border border-slate-800 rounded-lg p-2 flex flex-col justify-between">
          <div className="h-16 rounded overflow-hidden mb-1.5 relative border border-slate-800 bg-gradient-to-br from-blue-950 via-slate-900 to-rose-950">
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-85" 
              style={{ backgroundImage: `url('/api/imagery/change_mask')` }} 
            />
            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-space-950/80 text-[8px] font-mono text-rose-300 border border-rose-500/30">
              Siamese U-Net
            </span>
          </div>
          <div className="text-[10px] font-semibold text-white mb-1">Change Detection</div>
          <div className="flex items-center justify-between text-[8px] text-slate-400 font-mono">
            <span>Static: 0.0</span>
            <span className="text-rose-400 font-bold">Disturbance &gt; 0.5</span>
          </div>
        </div>
      </div>
    </div>
  );
};

