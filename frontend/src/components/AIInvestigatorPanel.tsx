import React, { useState } from 'react';
import { 
  Bot, Search, Sparkles, ExternalLink, ShieldCheck, 
  Share2, ArrowRight, CheckCircle2, Globe2, BookOpen,
  Building2, Newspaper, Users, Train, Trees, Check, FileText
} from 'lucide-react';
import { InvestigationResponse, EvidenceFinding } from '../types';

interface AIInvestigatorPanelProps {
  investigation: InvestigationResponse | null;
  onRunQuery: (query: string) => void;
  isLoading: boolean;
  onViewReport?: () => void;
}

export const AIInvestigatorPanel: React.FC<AIInvestigatorPanelProps> = ({
  investigation,
  onRunQuery,
  isLoading,
  onViewReport
}) => {
  const [queryInput, setQueryInput] = useState('Why did this region change?');
  const [showFullGraphModal, setShowFullGraphModal] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (queryInput.trim()) {
      onRunQuery(queryInput);
    }
  };

  // 8 Specialized Autonomous Agents matching Screenshot 2
  const specializedAgents = [
    {
      id: 'satellite',
      name: 'Satellite & Geospatial Analysis',
      desc: 'Analyzing land use, vegetation, water, urban growth.',
      icon: <Globe2 className="w-3.5 h-3.5 text-emerald-400" />,
      color: 'text-emerald-400',
      bg: 'bg-emerald-950/40 border-emerald-500/30'
    },
    {
      id: 'academic',
      name: 'Academic Research Agent',
      desc: 'Searching scientific papers and journals.',
      icon: <BookOpen className="w-3.5 h-3.5 text-purple-400" />,
      color: 'text-purple-400',
      bg: 'bg-purple-950/40 border-purple-500/30'
    },
    {
      id: 'policy',
      name: 'Policy & Government Data Agent',
      desc: 'Checking government dossiers, planning documents...',
      icon: <Building2 className="w-3.5 h-3.5 text-amber-400" />,
      color: 'text-amber-400',
      bg: 'bg-amber-950/40 border-amber-500/30'
    },
    {
      id: 'news',
      name: 'News & Media Agent',
      desc: 'Scanning historical news and archives...',
      icon: <Newspaper className="w-3.5 h-3.5 text-rose-400" />,
      color: 'text-rose-400',
      bg: 'bg-rose-950/40 border-rose-500/30'
    },
    {
      id: 'socio',
      name: 'Socioeconomic Agent',
      desc: 'Demographics, economy, employment, migration...',
      icon: <Users className="w-3.5 h-3.5 text-green-400" />,
      color: 'text-green-400',
      bg: 'bg-green-950/40 border-green-500/30'
    },
    {
      id: 'infra',
      name: 'Infrastructure Agent',
      desc: 'Roads, metro, buildings, utilities...',
      icon: <Train className="w-3.5 h-3.5 text-blue-400" />,
      color: 'text-blue-400',
      bg: 'bg-blue-950/40 border-blue-500/30'
    },
    {
      id: 'enviro',
      name: 'Environmental Agent',
      desc: 'Climate, rainfall, water resources, ecology...',
      icon: <Trees className="w-3.5 h-3.5 text-teal-400" />,
      color: 'text-teal-400',
      bg: 'bg-teal-950/40 border-teal-500/30'
    },
    {
      id: 'verify',
      name: 'Cross-verification Layer',
      desc: 'Validating facts and resolving conflicts...',
      icon: <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />,
      color: 'text-cyan-400',
      bg: 'bg-cyan-950/40 border-cyan-500/30'
    }
  ];

  // Key Findings matching Screenshot 2 table
  const defaultFindings = [
    {
      claim: 'Rapid urban expansion since 2000, especially after 2010 (direct satellite observation).',
      source: 'Satellite',
      timeSpan: '2000–2024',
      confidence: 'High'
    },
    {
      claim: 'IT industry growth and migration increased demand for housing and infrastructure.',
      source: 'Government / Economic',
      timeSpan: '1995–2020',
      confidence: 'High'
    },
    {
      claim: 'Loss of vegetation and increase in built-up area (change detection).',
      source: 'Satellite Analysis',
      timeSpan: '2000–2024',
      confidence: 'High'
    },
    {
      claim: 'Water body reduction due to encroachment and urbanization (satellite + environmental reports).',
      source: 'Satellite / Environmental',
      timeSpan: '2010–2024',
      confidence: 'Medium'
    },
    {
      claim: 'Future growth expected with planned infrastructure (metro, ring road).',
      source: 'Planning Documents',
      timeSpan: '2025+',
      confidence: 'Medium'
    }
  ];

  return (
    <div className="w-[430px] bg-[#090f1e] border-l border-[#1b253b] flex flex-col h-screen select-none shrink-0 z-20">
      {/* 1. Header with Bot Icon and Status */}
      <div className="p-3.5 border-b border-[#1b253b] flex items-center justify-between bg-[#0a101f]">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#0d1629] border border-cyan-500/40 flex items-center justify-center shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            <Bot className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="text-xs font-bold text-white flex items-center gap-2">
              AI Earth Investigator
            </div>
            <div className="flex items-center space-x-1.5 text-[10px] text-emerald-400 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>{isLoading ? 'Researching multi-source archives...' : 'Researching...'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Chat Query Input & Bubble */}
      <div className="p-3 border-b border-[#1b253b] space-y-2 bg-[#080d1a]">
        {/* User Query Bubble (Right-aligned, matching Screenshot 2) */}
        <div className="flex justify-end">
          <div className="max-w-[280px] bg-[#1d4ed8] text-white text-xs px-3 py-1.5 rounded-xl rounded-tr-none shadow-md flex items-center gap-1.5">
            <span>{queryInput}</span>
            <span className="text-[10px] opacity-75">👤</span>
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex items-center px-2.5 py-1.5 rounded-lg bg-[#050811] border border-cyan-500/30 focus-within:border-cyan-400">
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
            className="p-1 rounded bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 disabled:opacity-50 ml-1"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* 3. Scrollable Analysis & Evidence Content */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
        {/* Multi-Agent Analysis Status Box (matching Screenshot 2) */}
        <div className="bg-[#0b1222] border border-[#1e293b] rounded-lg p-3 space-y-2">
          <div className="text-[11px] font-semibold text-slate-200 flex items-center gap-1.5">
            <span className="text-cyan-400">ℹ️</span>
            I've analyzed multiple sources and found the following:
          </div>

          <div className="space-y-1.5">
            {specializedAgents.map(ag => (
              <div 
                key={ag.id}
                className="flex items-start space-x-2 text-[10px] p-1.5 rounded bg-[#090f1e]/80 border border-slate-800/80"
              >
                <div className="mt-0.5 shrink-0">{ag.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className={`font-semibold ${ag.color} leading-tight`}>
                    {ag.name}
                  </div>
                  <div className="text-slate-400 truncate text-[9px] mt-0.5">
                    {ag.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Evidence Graph Card (matching Screenshot 2) */}
        <div className="bg-[#0b1222] border border-cyan-500/30 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-white flex items-center gap-1.5 font-mono uppercase">
              <Share2 className="w-3.5 h-3.5 text-blue-400" />
              Evidence Graph
            </span>
            <button 
              onClick={() => setShowFullGraphModal(true)}
              className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1 font-mono"
            >
              View full graph →
            </button>
          </div>

          {/* Radial Graph Diagram Container */}
          <div className="h-52 w-full bg-[#050811] rounded-lg border border-slate-800 p-2 relative overflow-hidden flex items-center justify-center">
            {/* SVG Connecting Edges */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              <line x1="50%" y1="50%" x2="22%" y2="20%" stroke="#10b981" strokeWidth="1.5" strokeDasharray="2,2" />
              <line x1="50%" y1="50%" x2="78%" y2="20%" stroke="#a855f7" strokeWidth="1.5" strokeDasharray="2,2" />
              <line x1="50%" y1="50%" x2="82%" y2="50%" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="2,2" />
              <line x1="50%" y1="50%" x2="78%" y2="80%" stroke="#ec4899" strokeWidth="1.5" strokeDasharray="2,2" />
              <line x1="50%" y1="50%" x2="50%" y2="85%" stroke="#64748b" strokeWidth="1.5" strokeDasharray="2,2" />
              <line x1="50%" y1="50%" x2="22%" y2="80%" stroke="#0284c7" strokeWidth="1.5" strokeDasharray="2,2" />
              <line x1="50%" y1="50%" x2="18%" y2="50%" stroke="#14b8a6" strokeWidth="1.5" strokeDasharray="2,2" />
              <line x1="50%" y1="50%" x2="50%" y2="15%" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="2,2" />
            </svg>

            {/* Central Node: Urban Expansion Bengaluru */}
            <div className="relative z-10 px-2.5 py-1.5 rounded-lg bg-[#0d1629] border-2 border-amber-400 text-center shadow-[0_0_15px_rgba(251,191,36,0.35)]">
              <div className="text-[10px] font-bold text-amber-300 font-mono leading-tight">
                Urban Expansion
              </div>
              <div className="text-[8px] text-slate-300 font-mono">
                Bengaluru
              </div>
            </div>

            {/* Orbiting Satellite Nodes (8 nodes matching Screenshot 2) */}
            <div className="absolute top-1 left-2 p-1 rounded bg-[#090f1e] border border-emerald-500/60 text-[8px] text-emerald-300 font-mono shadow">
              🛰️ Satellite Observations
            </div>
            <div className="absolute top-1 right-2 p-1 rounded bg-[#090f1e] border border-purple-500/60 text-[8px] text-purple-300 font-mono shadow">
              🏗️ Infrastructure
            </div>
            <div className="absolute top-1/2 -translate-y-1/2 right-1 p-1 rounded bg-[#090f1e] border border-blue-500/60 text-[8px] text-blue-300 font-mono shadow">
              👥 Population Growth
            </div>
            <div className="absolute bottom-2 right-2 p-1 rounded bg-[#090f1e] border border-pink-500/60 text-[8px] text-pink-300 font-mono shadow">
              💼 Economic Factors
            </div>
            <div className="absolute bottom-1 left-1/2 -translate-x-1/2 p-1 rounded bg-[#090f1e] border border-slate-600 text-[8px] text-slate-300 font-mono shadow">
              ❓ Hypotheses
            </div>
            <div className="absolute bottom-2 left-2 p-1 rounded bg-[#090f1e] border border-sky-500/60 text-[8px] text-sky-300 font-mono shadow">
              📜 Historical Events
            </div>
            <div className="absolute top-1/2 -translate-y-1/2 left-1 p-1 rounded bg-[#090f1e] border border-teal-500/60 text-[8px] text-teal-300 font-mono shadow">
              🌳 Environmental Impact
            </div>
            <div className="absolute top-1 left-1/2 -translate-x-1/2 p-1 rounded bg-[#090f1e] border border-amber-500/60 text-[8px] text-amber-300 font-mono shadow">
              🏛️ Policy & Planning
            </div>
          </div>
        </div>

        {/* Key Findings Table (matching Screenshot 2) */}
        <div className="bg-[#0b1222] border border-[#1e293b] rounded-lg p-3 space-y-2.5">
          <div className="text-[11px] font-bold text-white font-mono uppercase">
            Key Findings
          </div>

          <div className="space-y-2 text-xs">
            {defaultFindings.map((finding, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-[#090f1e] border border-slate-800 flex items-start justify-between gap-2"
              >
                <div className="space-y-1">
                  <div className="text-[10px] text-slate-200 leading-snug">
                    <strong className="text-cyan-400 font-mono mr-1">{idx + 1}.</strong>
                    {finding.claim}
                  </div>
                  <div className="text-[9px] text-slate-400 font-mono">
                    {finding.source} • {finding.timeSpan}
                  </div>
                </div>
                <span
                  className={`px-1.5 py-0.5 rounded text-[8px] font-bold font-mono shrink-0 border ${
                    finding.confidence === 'High'
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                      : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                  }`}
                >
                  ● {finding.confidence}
                </span>
              </div>
            ))}
          </div>

          <div className="text-[9px] text-slate-400 font-mono pt-1 text-center border-t border-slate-800/80">
            All claims are backed by sources with location, date and evidence type.
          </div>

          {/* View Full Report Button (matching Screenshot 2) */}
          <button
            onClick={() => {
              if (onViewReport) onViewReport();
            }}
            className="w-full py-2 bg-[#2563eb] hover:bg-[#1d4ed8] text-white text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-md"
          >
            <FileText className="w-3.5 h-3.5" />
            View Full Report →
          </button>
        </div>
      </div>
    </div>
  );
};
