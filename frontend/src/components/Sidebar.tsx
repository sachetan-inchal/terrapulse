import React from 'react';
import { 
  Globe2, Clock, GitCompare, Layers, Activity, Bot, 
  Share2, FileText, Sparkles, Database, CheckSquare, 
  Square, ToggleLeft, ToggleRight 
} from 'lucide-react';
import { NavSection, LayerState, DataSourceState } from '../types';

interface SidebarProps {
  activeTab: NavSection;
  onTabChange: (tab: NavSection) => void;
  layers: LayerState;
  onLayerToggle: (key: keyof LayerState) => void;
  dataSources: DataSourceState;
  onDataSourceToggle: (key: keyof DataSourceState) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  layers,
  onLayerToggle,
  dataSources,
  onDataSourceToggle
}) => {
  const navItems: { id: NavSection; label: string; icon: React.ReactNode }[] = [
    { id: 'explore', label: 'Explore', icon: <Globe2 className="w-4 h-4" /> },
    { id: 'timeseries', label: 'Time Series', icon: <Clock className="w-4 h-4" /> },
    { id: 'computervision', label: 'Computer Vision', icon: <GitCompare className="w-4 h-4" /> },
    { id: 'landcover', label: 'Land Cover', icon: <Layers className="w-4 h-4" /> },
    { id: 'environmental', label: 'Environmental Layers', icon: <Activity className="w-4 h-4" /> },
    { id: 'investigator', label: 'AI Investigator', icon: <Bot className="w-4 h-4" /> },
    { id: 'evidence', label: 'Evidence Graph', icon: <Share2 className="w-4 h-4" /> },
    { id: 'reports', label: 'Reports', icon: <FileText className="w-4 h-4" /> },
    { id: 'future', label: 'Future Scenarios', icon: <Sparkles className="w-4 h-4 text-purple-accent" /> },
  ];

  return (
    <aside className="w-72 bg-space-900 border-r border-cyan-500/20 flex flex-col h-screen select-none shrink-0 z-30">
      {/* Top Branding / Logo */}
      <div className="p-4 border-b border-cyan-500/15 flex items-center space-x-3 bg-space-950/40">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-glow-cyan">
          <Globe2 className="w-5 h-5 text-space-950" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-wider text-white uppercase font-mono">
            Earth Temporal
          </h1>
          <p className="text-[10px] text-cyan-400 font-mono tracking-widest">
            INTELLIGENCE v2.0
          </p>
        </div>
      </div>

      {/* Scrollable Navigation Body */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {/* Navigation Sections */}
        <div className="space-y-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-accent border border-cyan-500/40 shadow-glow-cyan'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-space-800/60'
                }`}
              >
                <span className={isActive ? 'text-cyan-accent' : 'text-slate-500'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Data Sources Checklist */}
        <div className="border-t border-slate-800/80 pt-4">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              Data Sources
            </span>
          </div>
          <div className="space-y-1.5 text-xs text-slate-400 px-1">
            {[
              { key: 'landsat', label: 'Landsat (USGS)' },
              { key: 'sentinel', label: 'Sentinel (ESA)' },
              { key: 'modis', label: 'MODIS (NASA)' },
              { key: 'planet', label: 'Planet (Open)' },
              { key: 'osm', label: 'OpenStreetMap' },
              { key: 'other', label: 'Other Open Sources' },
            ].map(({ key, label }) => {
              const checked = dataSources[key as keyof DataSourceState];
              return (
                <button
                  key={key}
                  onClick={() => onDataSourceToggle(key as keyof DataSourceState)}
                  className="w-full flex items-center space-x-2 py-1 hover:text-slate-200"
                >
                  {checked ? (
                    <CheckSquare className="w-3.5 h-3.5 text-cyan-accent shrink-0" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                  )}
                  <span className="text-[11px]">{label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Layers Controls Checklist */}
        <div className="border-t border-slate-800/80 pt-4">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              Layers
            </span>
          </div>
          <div className="space-y-2 text-xs text-slate-400 px-1">
            {[
              { key: 'landCover', label: 'Land Cover (AI Segmentation)', color: 'text-emerald-400' },
              { key: 'ndvi', label: 'NDVI (Vegetation Index)', color: 'text-green-400' },
              { key: 'waterIndex', label: 'Water Index (NDWI)', color: 'text-sky-400' },
              { key: 'urbanHeat', label: 'Urban Heat (LST)', color: 'text-rose-400' },
              { key: 'changeDetection', label: 'Change Detection', color: 'text-amber-400' },
              { key: 'boundaries', label: 'Administrative Boundaries', color: 'text-purple-400' },
            ].map(({ key, label, color }) => {
              const active = layers[key as keyof LayerState];
              return (
                <button
                  key={key}
                  onClick={() => onLayerToggle(key as keyof LayerState)}
                  className="w-full flex items-center justify-between py-1 group hover:text-slate-200"
                >
                  <span className={`text-[11px] ${color}`}>{label}</span>
                  {active ? (
                    <ToggleRight className="w-4 h-4 text-cyan-accent" />
                  ) : (
                    <ToggleLeft className="w-4 h-4 text-slate-600 group-hover:text-slate-500" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom Footer Info */}
      <div className="p-3 border-t border-cyan-500/15 bg-space-950/60 flex items-center space-x-2.5">
        <div className="w-7 h-7 rounded-full bg-cyan-950 border border-cyan-500/40 flex items-center justify-center shrink-0">
          <Globe2 className="w-4 h-4 text-cyan-accent animate-pulse" />
        </div>
        <div className="text-[10px] text-slate-400 leading-tight">
          <div className="font-semibold text-slate-300">Open Earth Intelligence</div>
          <div className="text-slate-500">Multimodal Satellite & AI</div>
        </div>
      </div>
    </aside>
  );
};
