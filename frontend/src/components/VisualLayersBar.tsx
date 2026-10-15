import React from 'react';

export const VisualLayersBar: React.FC = () => {
  return (
    <div className="glass-panel p-3.5 rounded-xl border border-cyan-500/20">
      <div className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider mb-2.5">
        Visual Layers (Multi-Spectral Bands)
      </div>

      <div className="grid grid-cols-3 gap-2.5">
        {/* Layer 1: Land Cover */}
        <div className="bg-space-950/70 border border-slate-800 rounded-lg p-2 flex flex-col justify-between">
          <div className="h-16 rounded overflow-hidden mb-1.5 relative bg-gradient-to-tr from-emerald-900/60 via-amber-900/40 to-rose-900/60 border border-slate-800">
            <div className="absolute inset-0 bg-cover bg-center opacity-80" 
                 style={{ backgroundImage: `url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=200&q=70')` }} />
            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-space-950/80 text-[8px] font-mono text-white">
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
            <div className="absolute inset-0 bg-cover bg-center opacity-70 mix-blend-overlay" 
                 style={{ backgroundImage: `url('https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=200&q=70')` }} />
            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-space-950/80 text-[8px] font-mono text-white">
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
            <div className="absolute inset-0 bg-cover bg-center opacity-70" 
                 style={{ backgroundImage: `url('https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=200&q=70')` }} />
            <div className="absolute inset-0 bg-rose-500/30 mix-blend-color-dodge" />
            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-space-950/80 text-[8px] font-mono text-cyan-300">
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
