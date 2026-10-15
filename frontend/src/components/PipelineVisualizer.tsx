import React from 'react';
import { Search, ScanLine, Compass, Grid, Database, ArrowRight } from 'lucide-react';

export const PipelineVisualizer: React.FC = () => {
  const steps = [
    { title: 'Search & Fetch', sub: '(open sources)', icon: <Search className="w-4 h-4 text-cyan-accent" /> },
    { title: 'Overlap Detection', sub: '& Feature Extraction', icon: <ScanLine className="w-4 h-4 text-blue-400" /> },
    { title: 'Image Registration', sub: '& Alignment (SIFT)', icon: <Compass className="w-4 h-4 text-purple-accent" /> },
    { title: 'Stitching & Mosaics', sub: '(temporal archive)', icon: <Grid className="w-4 h-4 text-emerald-accent" /> },
    { title: 'Store & Index', sub: '(spatio-temporal)', icon: <Database className="w-4 h-4 text-amber-400" /> },
  ];

  return (
    <div className="glass-panel p-3.5 rounded-xl border border-cyan-500/20">
      <div className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider mb-2.5 flex items-center justify-between">
        <span>Image Processing Pipeline</span>
        <span className="text-[9px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded font-mono">
          ● REAL-TIME ENGINE ACTIVE
        </span>
      </div>

      <div className="flex items-center justify-between gap-1 overflow-x-auto py-1">
        {steps.map((step, idx) => (
          <React.Fragment key={step.title}>
            <div className="flex-1 min-w-[110px] bg-space-950/70 border border-slate-800 rounded-lg p-2 flex flex-col items-center text-center transition-all hover:border-cyan-500/40">
              <div className="w-7 h-7 rounded-md bg-space-900 border border-cyan-500/30 flex items-center justify-center mb-1.5 shadow-sm">
                {step.icon}
              </div>
              <div className="text-[10px] font-bold text-white leading-tight">{step.title}</div>
              <div className="text-[8px] text-slate-500 font-mono mt-0.5">{step.sub}</div>
            </div>
            {idx < steps.length - 1 && (
              <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0 opacity-70" />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
