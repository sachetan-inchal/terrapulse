import React from 'react';
import { Play, Pause, ChevronLeft, ChevronRight, TrendingUp, Activity, Layers } from 'lucide-react';
import { EnvironmentalAnalysis } from '../types';

interface TimelineScrubberProps {
  currentYear: number;
  onYearChange: (year: number) => void;
  analysis?: EnvironmentalAnalysis;
  activeTimelineView: 'historical' | 'current' | 'future';
  onViewChange: (view: 'historical' | 'current' | 'future') => void;
}

export const TimelineScrubber: React.FC<TimelineScrubberProps> = ({
  currentYear,
  onYearChange,
  analysis,
  activeTimelineView,
  onViewChange
}) => {
  const [isPlaying, setIsPlaying] = React.useState(false);

  const timelineItems = [
    { year: 1985, mission: 'Landsat 5', type: 'historical', img: 'https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?w=150&q=70' },
    { year: 1990, mission: 'Landsat 5', type: 'historical', img: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=150&q=70' },
    { year: 1995, mission: 'Landsat 5', type: 'historical', img: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=150&q=70' },
    { year: 2000, mission: 'Landsat 7', type: 'historical', img: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=150&q=70' },
    { year: 2005, mission: 'Landsat 7', type: 'historical', img: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=150&q=70' },
    { year: 2010, mission: 'Landsat 7', type: 'historical', img: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=150&q=70' },
    { year: 2015, mission: 'Landsat 8', type: 'historical', img: 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=150&q=70' },
    { year: 2020, mission: 'Sentinel-2', type: 'historical', img: 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=150&q=70' },
    { year: 2024, mission: 'PlanetScope', type: 'current', img: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=150&q=70' },
    { year: 2030, mission: 'Scenario', type: 'future', img: 'https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=150&q=70' },
    { year: 2040, mission: 'Scenario', type: 'future', img: 'https://images.unsplash.com/photo-1477959858617-67f30bc75b82?w=150&q=70' },
    { year: 2050, mission: 'Scenario', type: 'future', img: 'https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=150&q=70' },
  ];

  // Auto-play animation through timeline
  React.useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        onYearChange(prev => {
          const years = timelineItems.map(t => t.year);
          const currIdx = years.indexOf(prev);
          const nextIdx = (currIdx + 1) % years.length;
          return years[nextIdx];
        });
      }, 1400);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <div className="glass-panel p-4 rounded-xl border border-cyan-500/20 space-y-3">
      {/* Top View Selector Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
        <div className="flex space-x-2">
          {(['historical', 'current', 'future'] as const).map((view) => (
            <button
              key={view}
              onClick={() => {
                onViewChange(view);
                if (view === 'current') onYearChange(2024);
                if (view === 'historical' && currentYear > 2024) onYearChange(2020);
                if (view === 'future' && currentYear <= 2024) onYearChange(2030);
              }}
              className={`px-3 py-1 rounded-md text-xs font-semibold capitalize transition-all ${
                activeTimelineView === view
                  ? 'bg-cyan-500/20 text-cyan-accent border border-cyan-500/40 shadow-glow-cyan'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {view === 'future' ? '🔮 Future Scenarios' : `${view} View`}
            </button>
          ))}
        </div>

        {/* Current Year Badge & Controls */}
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-space-950 border border-cyan-500/30 text-cyan-accent text-xs font-mono hover:bg-cyan-500/10"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'PAUSE' : 'TIME-LAPSE'}</span>
          </button>
          <div className="text-xs font-mono font-bold text-white bg-space-950 px-3 py-1 rounded border border-slate-800">
            YEAR: <span className="text-cyan-accent">{currentYear}</span>
          </div>
        </div>
      </div>

      {/* Chronological Observation Strip */}
      <div className="grid grid-cols-12 gap-1.5 overflow-x-auto py-1">
        {timelineItems.map((item) => {
          const isSelected = currentYear === item.year;
          return (
            <div
              key={item.year}
              onClick={() => onYearChange(item.year)}
              className={`cursor-pointer rounded-lg p-1 transition-all flex flex-col items-center text-center ${
                isSelected
                  ? 'bg-cyan-500/25 border-2 border-cyan-accent shadow-glow-cyan scale-105'
                  : 'bg-space-950/70 border border-slate-800/80 hover:border-slate-600 opacity-75 hover:opacity-100'
              }`}
            >
              <div className="h-10 w-full rounded overflow-hidden bg-space-900 mb-1">
                <img src={item.img} alt={`${item.year}`} className="w-full h-full object-cover" />
              </div>
              <div className="text-[10px] font-bold text-white font-mono">{item.year}</div>
              <div className="text-[8px] text-slate-400 truncate w-full">{item.mission}</div>
            </div>
          );
        })}
      </div>

      {/* Scrub Bar Slider */}
      <div className="px-2 pt-1">
        <input
          type="range"
          min={1985}
          max={2050}
          step={5}
          value={currentYear}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="w-full accent-cyan-400 h-1.5 bg-space-950 rounded-lg cursor-pointer"
        />
        <div className="flex justify-between text-[9px] font-mono text-slate-500 mt-1">
          <span>1985 (Landsat 5 TM)</span>
          <span>2005 (Landsat 7)</span>
          <span>2024 (PlanetScope 3m)</span>
          <span className="text-purple-400">2050 (World Model Forecast)</span>
        </div>
      </div>

      {/* Quick Telemetry & Metric Cards */}
      <div className="grid grid-cols-5 gap-2 pt-2 border-t border-slate-800/80">
        <div className="bg-space-950/80 border border-slate-800 rounded-lg p-2">
          <div className="text-[9px] text-slate-400 font-mono">LAND COVER ({currentYear})</div>
          <div className="text-xs font-bold text-white mt-0.5">
            {analysis ? `${analysis.built_up_coverage_pct}% Urban` : '74.2% Built-up'}
          </div>
        </div>

        <div className="bg-space-950/80 border border-slate-800 rounded-lg p-2">
          <div className="text-[9px] text-slate-400 font-mono">MEAN NDVI INDEX</div>
          <div className="text-xs font-bold text-emerald-400 mt-0.5">
            {analysis ? `${analysis.mean_ndvi.toFixed(2)} (Degraded)` : '0.28 (Moderate)'}
          </div>
        </div>

        <div className="bg-space-950/80 border border-slate-800 rounded-lg p-2">
          <div className="text-[9px] text-slate-400 font-mono">CANOPY LOSS</div>
          <div className="text-xs font-bold text-rose-400 mt-0.5">
            -35.4% since 1985
          </div>
        </div>

        <div className="bg-space-950/80 border border-slate-800 rounded-lg p-2">
          <div className="text-[9px] text-slate-400 font-mono">URBAN EXPANSION</div>
          <div className="text-xs font-bold text-cyan-accent mt-0.5">
            +520% Impervious
          </div>
        </div>

        <div className="bg-space-950/80 border border-slate-800 rounded-lg p-2">
          <div className="text-[9px] text-slate-400 font-mono">TIME-LAPSE COVERAGE</div>
          <div className="text-xs font-bold text-purple-accent mt-0.5">
            39 Years Multi-Mission
          </div>
        </div>
      </div>
    </div>
  );
};
