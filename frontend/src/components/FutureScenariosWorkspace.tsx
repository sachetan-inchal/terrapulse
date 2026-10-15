import React, { useState, useEffect } from 'react';
import { Sparkles, AlertCircle, Info, TrendingUp, Cpu } from 'lucide-react';
import { FutureScenario } from '../types';
import { fetchFutureScenarios } from '../services/api';

export const FutureScenariosWorkspace: React.FC = () => {
  const [scenarios, setScenarios] = useState<FutureScenario[]>([]);
  const [activeYear, setActiveYear] = useState<number>(2030);

  useEffect(() => {
    fetchFutureScenarios('bengaluru').then(setScenarios).catch(console.error);
  }, []);

  const activeScenario = scenarios.find(s => s.scenario_year === activeYear) || scenarios[0];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto max-h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-purple-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-accent" />
            Spatiotemporal Future Land-Cover Simulator (2030–2050)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Conditioned generative land dynamics modeling based on historical multi-decadal trends and approved infrastructure corridors.
          </p>
        </div>
        <div className="px-3 py-1 rounded bg-purple-500/15 border border-purple-500/40 text-purple-400 text-xs font-mono font-bold">
          ● EXPERIMENTAL PROJECTION
        </div>
      </div>

      {/* Scientific Disclaimer Alert */}
      <div className="bg-amber-950/30 border border-amber-500/40 p-3.5 rounded-xl flex items-start space-x-3 text-xs text-amber-200">
        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <strong className="font-mono uppercase text-amber-400">Model Disclaimer & Scientific Boundary:</strong> Projected scenarios represent probabilistic model outputs derived from Spatiotemporal Transformers and Cellular Automata dynamics. They are explicitly NOT guaranteed observations.
        </div>
      </div>

      {/* Scenario Year Selector Buttons */}
      <div className="flex space-x-3">
        {[2030, 2040, 2050].map((yr) => (
          <button
            key={yr}
            onClick={() => setActiveYear(yr)}
            className={`flex-1 p-4 rounded-xl border text-left transition-all ${
              activeYear === yr
                ? 'bg-purple-950/40 border-purple-400 shadow-glow-purple'
                : 'glass-panel border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-lg font-bold text-white font-mono">{yr} Scenario</div>
            <div className="text-xs text-purple-300 font-mono mt-1">
              +{yr - 2024} Years Forecasting Horizon
            </div>
          </button>
        ))}
      </div>

      {/* Active Scenario Details */}
      {activeScenario && (
        <div className="grid grid-cols-3 gap-6">
          {/* Quantitative Projections */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-4">
            <div className="text-xs font-bold text-white font-mono uppercase tracking-wider">
              Projected LULC Distribution
            </div>
            <div className="space-y-3 font-mono">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Urban / Built-up</span>
                  <strong className="text-rose-400">{activeScenario.projected_urban_pct}%</strong>
                </div>
                <div className="w-full bg-space-950 h-2 rounded-full overflow-hidden">
                  <div className="bg-rose-500 h-full rounded-full" style={{ width: `${activeScenario.projected_urban_pct}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Vegetation & Canopy</span>
                  <strong className="text-emerald-400">{activeScenario.projected_vegetation_pct}%</strong>
                </div>
                <div className="w-full bg-space-950 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${activeScenario.projected_vegetation_pct}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Surface Water Bodies</span>
                  <strong className="text-sky-400">{activeScenario.projected_water_pct}%</strong>
                </div>
                <div className="w-full bg-space-950 h-2 rounded-full overflow-hidden">
                  <div className="bg-sky-500 h-full rounded-full" style={{ width: `${activeScenario.projected_water_pct}%` }} />
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 font-mono">
              Uncertainty Margin: <strong className="text-white">{activeScenario.uncertainty_margin}</strong>
            </div>
          </div>

          {/* Model Assumptions */}
          <div className="col-span-2 glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
            <div className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-accent" />
              Model Conditioning Assumptions
            </div>
            <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
              {activeScenario.assumptions.map((asm, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-purple-400 font-mono">[{i + 1}]</span>
                  <span>{asm}</span>
                </li>
              ))}
            </ul>

            <div className="p-3 rounded-lg bg-space-950/80 border border-slate-800 text-[11px] text-slate-400">
              <strong className="text-slate-200">Architecture:</strong> {activeScenario.model_type}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
