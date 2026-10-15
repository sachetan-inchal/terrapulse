import React, { useState } from 'react';
import { 
  Bot, Search, Sparkles, ExternalLink, ShieldCheck, 
  Share2, AlertTriangle, ArrowRight, CheckCircle2 
} from 'lucide-react';
import { InvestigationResponse } from '../types';

interface AIInvestigatorPanelProps {
  investigation: InvestigationResponse | null;
  onRunQuery: (query: string) => void;
  isLoading: boolean;
}

export const AIInvestigatorPanel: React.FC<AIInvestigatorPanelProps> = ({
  investigation,
  onRunQuery,
  isLoading
}) => {
  const [queryInput, setQueryInput] = useState('Why did this region change?');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (queryInput.trim()) {
      onRunQuery(queryInput);
    }
  };

  return (
    <div className="w-[420px] bg-space-900 border-l border-cyan-500/20 flex flex-col h-screen select-none shrink-0 z-20">
      {/* Top Header */}
      <div className="p-4 border-b border-cyan-500/15 flex items-center justify-between bg-space-950/50">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-950 border border-blue-500/40 flex items-center justify-center">
            <Bot className="w-5 h-5 text-cyan-accent" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">AI Earth Investigator</h2>
            <div className="flex items-center space-x-1.5 text-[10px] text-emerald-400 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>{isLoading ? 'Researching multi-modal evidence...' : 'Synthesizing evidence'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Query Bar */}
      <form onSubmit={handleSubmit} className="p-3 border-b border-slate-800 bg-space-950/30">
        <div className="flex items-center px-3 py-1.5 rounded-lg bg-space-950 border border-cyan-500/30 focus-within:border-cyan-400">
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="Ask why this region changed..."
            className="w-full bg-transparent text-xs text-white focus:outline-none placeholder-slate-500 font-sans"
          />
          <button 
            type="submit"
            disabled={isLoading}
            className="p-1 rounded bg-cyan-500/20 text-cyan-accent hover:bg-cyan-500/30 disabled:opacity-50"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>

      {/* Scrollable Content Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Sub-Agent Processing Status */}
        {investigation?.agent_status && (
          <div className="glass-panel p-3 rounded-lg space-y-1.5">
            <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider mb-1 font-bold">
              Multi-Agent Investigation Status:
            </div>
            <div className="space-y-1 text-[10px] font-mono text-slate-300">
              {investigation.agent_status.slice(0, 4).map((agent) => (
                <div key={agent.name} className="flex items-center justify-between">
                  <span className="truncate text-slate-400">• {agent.name}</span>
                  <span className="text-emerald-400 text-[9px] shrink-0 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-2.5 h-2.5" /> Done
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Evidence Graph Section */}
        <div className="glass-panel p-3 rounded-lg border border-cyan-500/25">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold text-white font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5 text-blue-400" />
              Evidence Graph
            </span>
            <span className="text-[9px] text-cyan-400 font-mono">Bipartite Multi-Modal</span>
          </div>

          {/* Interactive Node Graph Visualization Container */}
          <div className="h-48 w-full bg-space-950 rounded-lg border border-slate-800 p-2 relative overflow-hidden flex items-center justify-center">
            <div className="absolute inset-0 radar-grid opacity-20" />

            {/* Central Core Node */}
            <div className="relative z-10 px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600/30 to-cyan-500/30 border border-cyan-400/80 text-center shadow-glow-cyan">
              <div className="text-[10px] font-bold text-white font-mono">Urban Expansion Bengaluru</div>
              <div className="text-[8px] text-cyan-300 font-mono">Central Core Phenomenon</div>
            </div>

            {/* Orbiting Satellite Node */}
            <div className="absolute top-2 left-2 z-10 p-1.5 rounded bg-space-900 border border-emerald-500/60 text-[9px] text-emerald-300 font-mono">
              🛰️ Satellite Observations
            </div>

            {/* Orbiting Policy Node */}
            <div className="absolute top-2 right-2 z-10 p-1.5 rounded bg-space-900 border border-amber-500/60 text-[9px] text-amber-300 font-mono">
              📜 Master Plan & BDA
            </div>

            {/* Orbiting Infrastructure Node */}
            <div className="absolute bottom-2 left-2 z-10 p-1.5 rounded bg-space-900 border border-purple-500/60 text-[9px] text-purple-300 font-mono">
              🏗️ Tech Parks & Metro
            </div>

            {/* Orbiting Environment Node */}
            <div className="absolute bottom-2 right-2 z-10 p-1.5 rounded bg-space-900 border border-rose-500/60 text-[9px] text-rose-300 font-mono">
              🌳 Canopy & Lake Loss
            </div>

            {/* SVG Connecting Vectors */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40">
              <line x1="20%" y1="18%" x2="50%" y2="50%" stroke="#00f0ff" strokeWidth="1" strokeDasharray="3,3" />
              <line x1="80%" y1="18%" x2="50%" y2="50%" stroke="#eab308" strokeWidth="1" strokeDasharray="3,3" />
              <line x1="20%" y1="82%" x2="50%" y2="50%" stroke="#a855f7" strokeWidth="1" strokeDasharray="3,3" />
              <line x1="80%" y1="82%" x2="50%" y2="50%" stroke="#f43f5e" strokeWidth="1" strokeDasharray="3,3" />
            </svg>
          </div>
        </div>

        {/* Key Findings List with Verified Evidence Labels */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-[11px] font-semibold text-white font-mono uppercase tracking-wider">
            <span>Key Findings & Labeled Evidence</span>
            <span className="text-[9px] text-slate-400">Strict Provenance</span>
          </div>

          {investigation?.findings ? (
            investigation.findings.map((f, i) => {
              // Color badges based on requirement: OBSERVED, DOCUMENTED, CORRELATED, POSSIBLE EXPLANATION, UNKNOWN
              const badgeColors = {
                OBSERVED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
                DOCUMENTED: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
                CORRELATED: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
                'POSSIBLE EXPLANATION': 'bg-purple-500/20 text-purple-400 border-purple-500/40',
                UNKNOWN: 'bg-slate-500/20 text-slate-400 border-slate-500/40'
              };

              return (
                <div 
                  key={f.finding_id}
                  className="bg-space-950/80 border border-slate-800 rounded-lg p-3 hover:border-cyan-500/30 transition-all space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold border ${badgeColors[f.category]}`}>
                      [{f.category}]
                    </span>
                    <span className="text-[9px] font-mono text-slate-400">
                      {f.time_span} • Conf: <strong className="text-white">{f.confidence}</strong>
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed font-sans">
                    {f.claim}
                  </p>

                  {/* Citations List */}
                  {f.citations.length > 0 && (
                    <div className="pt-1 border-t border-slate-800/80 space-y-1">
                      <div className="text-[9px] text-slate-400 font-mono">Source Citations:</div>
                      {f.citations.map((c, ci) => (
                        <a
                          key={ci}
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-1 text-[10px] text-cyan-400 hover:text-cyan-300 truncate"
                        >
                          <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                          <span className="truncate">{c.title}</span>
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="text-center py-6 text-xs text-slate-500 font-mono">
              Loading verified intelligence records...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
