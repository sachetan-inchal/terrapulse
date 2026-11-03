import React, { useState } from 'react';
import { 
  Activity, CheckCircle2, AlertTriangle, Loader2, BookOpen, 
  Layers, Flame, Cpu, TrendingUp, ChevronDown, ChevronUp, Terminal 
} from 'lucide-react';
import { ActivityEventItem } from '../../types/investigation';

interface ActivityStreamTrayProps {
  events: ActivityEventItem[];
  isInvestigating: boolean;
}

export const ActivityStreamTray: React.FC<ActivityStreamTrayProps> = ({ events, isInvestigating }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const getToolIcon = (toolName?: string, eventType?: string) => {
    if (!toolName) {
      if (eventType === 'clarification_needed') return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
      if (eventType === 'final_response') return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      return <Activity className="w-3.5 h-3.5 text-cyan-400" />;
    }

    const t = toolName.toLowerCase();
    if (t.includes('academic') || t.includes('news') || t.includes('research')) {
      return <BookOpen className="w-3.5 h-3.5 text-indigo-400" />;
    }
    if (t.includes('idw') || t.includes('surface') || t.includes('spatial')) {
      return <Layers className="w-3.5 h-3.5 text-cyan-400" />;
    }
    if (t.includes('gi_star') || t.includes('hotspot')) {
      return <Flame className="w-3.5 h-3.5 text-rose-400" />;
    }
    if (t.includes('symptom')) {
      return <Cpu className="w-3.5 h-3.5 text-purple-400" />;
    }
    if (t.includes('forecast')) {
      return <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />;
    }
    return <Activity className="w-3.5 h-3.5 text-cyan-400" />;
  };

  return (
    <div className="bg-[#040816]/95 border-t border-cyan-500/20 backdrop-blur-xl shadow-2xl transition-all">
      {/* Header Bar */}
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        className="px-4 py-2 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition-colors select-none"
      >
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-[10px]">
            <Terminal className="w-3 h-3" />
            <span>AI INVESTIGATOR ACTIVITY STREAM</span>
          </div>
          {isInvestigating ? (
            <span className="flex items-center gap-1.5 text-[11px] text-cyan-300 font-mono animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin text-cyan-400" />
              <span>Executing Strands Tools...</span>
            </span>
          ) : (
            <span className="text-[11px] text-slate-400 font-mono">
              {events.length === 0 ? 'Agent standby' : `${events.length} tool actions recorded`}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-3 text-slate-400 text-xs">
          <span className="text-[10px] font-mono text-slate-500">Live Server-Sent Events (SSE)</span>
          {isExpanded ? <ChevronDown className="w-4 h-4 text-cyan-400" /> : <ChevronUp className="w-4 h-4 text-cyan-400" />}
        </div>
      </div>

      {/* Expanded Events Carousel / List */}
      {isExpanded && (
        <div className="px-4 py-2.5 max-h-40 overflow-y-auto font-mono text-xs space-y-1.5 border-t border-slate-800/60 bg-[#02050f]/80">
          {events.length === 0 ? (
            <div className="text-slate-500 py-3 text-center text-[11px] italic">
              No tool executions yet. Ask an environmental question to trigger research and spatial analysis.
            </div>
          ) : (
            events.map((evt) => (
              <div 
                key={evt.id}
                className="flex items-start justify-between p-2 rounded bg-[#070e24]/80 border border-slate-800/80 hover:border-cyan-500/30 transition-colors gap-3"
              >
                <div className="flex items-start gap-2.5 min-w-0">
                  <div className="mt-0.5 shrink-0">
                    {evt.status === 'running' ? (
                      <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                    ) : evt.status === 'failed' ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    ) : (
                      getToolIcon(evt.toolName, evt.eventType)
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200 truncate">{evt.title}</span>
                      {evt.toolName && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                          {evt.toolName}
                        </span>
                      )}
                    </div>
                    {evt.summary && (
                      <p className="text-[11px] text-slate-400 truncate mt-0.5 font-sans">
                        {evt.summary}
                      </p>
                    )}
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 shrink-0 font-mono">
                  {evt.timestamp}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

