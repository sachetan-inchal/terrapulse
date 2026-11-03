import React, { useState } from 'react';
import { 
  Globe2, Satellite, Sliders, Layers, Clock, 
  GitCompare, Activity, Cpu, FileText, Database, 
  CheckSquare, Square, ToggleLeft, ToggleRight, ChevronDown, ChevronRight
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
  const [dataSourcesOpen, setDataSourcesOpen] = useState(true);
  const [layersOpen, setLayersOpen] = useState(true);

  const navItems: { id: NavSection; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: '1. Overview', icon: <Globe2 className="w-4 h-4" /> },
    { id: 'imagery', label: '2. Satellite Imagery', icon: <Satellite className="w-4 h-4" /> },
    { id: 'spectral', label: '3. Spectral Analysis', icon: <Sliders className="w-4 h-4" /> },
    { id: 'landcover', label: '4. Land Cover & Vegetation', icon: <Layers className="w-4 h-4" /> },
    { id: 'historical', label: '5. Historical Analysis', icon: <Clock className="w-4 h-4" /> },
    { id: 'changedetection', label: '6. Change Detection', icon: <GitCompare className="w-4 h-4" /> },
    { id: 'indicators', label: '7. Environmental Indicators', icon: <Activity className="w-4 h-4" /> },
    { id: 'computervision', label: '8. Computer Vision', icon: <Cpu className="w-4 h-4" /> },
    { id: 'reports', label: '9. Reports & Exports', icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-72 bg-[#040816] border-r border-cyan-500/20 flex flex-col h-screen select-none shrink-0 z-30">
      {/* Top Branding / Logo */}
      <div className="p-4 border-b border-cyan-500/15 flex items-center space-x-3 bg-[#030612]">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/40">
          <Globe2 className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-xs font-bold tracking-wider text-white uppercase font-mono">
            Earth Observation
          </h1>
          <p className="text-[9px] text-cyan-400 font-mono tracking-widest uppercase">
            Explorer Studio
          </p>
        </div>
      </div>

      {/* Scrollable Navigation Body */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {/* 9 Workspaces Navigation */}
        <div className="space-y-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 px-2 mb-1.5 font-bold">
            Workspaces
          </div>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-mono transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600/30 to-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/20 font-bold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#070e24]'
                }`}
              >
                <span className={isActive ? 'text-cyan-400' : 'text-slate-500'}>
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Collapsible Data Sources Checklist */}
        <div className="border-t border-slate-800/80 pt-3">
          <button
            onClick={() => setDataSourcesOpen(!dataSourcesOpen)}
            className="w-full flex items-center justify-between mb-2 px-1 text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider hover:text-white"
          >
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              <span>Data Providers</span>
            </span>
            {dataSourcesOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>
          
          {dataSourcesOpen && (
            <div className="space-y-1 text-xs text-slate-400 px-1 font-mono">
              {[
                { key: 'landsat', label: 'Landsat 5-9 (USGS)' },
                { key: 'sentinel', label: 'Sentinel-2 (ESA)' },
                { key: 'modis', label: 'MODIS (NASA)' },
                { key: 'planet', label: 'PlanetScope (Open)' },
                { key: 'osm', label: 'OpenStreetMap' },
              ].map(({ key, label }) => {
                const checked = dataSources[key as keyof DataSourceState];
                return (
                  <button
                    key={key}
                    onClick={() => onDataSourceToggle(key as keyof DataSourceState)}
                    className="w-full flex items-center space-x-2 py-1 hover:text-slate-200 transition-colors"
                  >
                    {checked ? (
                      <CheckSquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    ) : (
                      <Square className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                    )}
                    <span className="text-[11px]">{label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Collapsible Layer Toggles */}
        <div className="border-t border-slate-800/80 pt-3">
          <button
            onClick={() => setLayersOpen(!layersOpen)}
            className="w-full flex items-center justify-between mb-2 px-1 text-[11px] font-semibold text-slate-300 font-mono uppercase tracking-wider hover:text-white"
          >
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              <span>Quick Layers</span>
            </span>
            {layersOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>

          {layersOpen && (
            <div className="space-y-1.5 text-xs text-slate-400 px-1 font-mono">
              {[
                { key: 'landCover', label: 'Land Cover LULC', color: 'text-emerald-400' },
                { key: 'ndvi', label: 'NDVI Vegetation', color: 'text-green-400' },
                { key: 'waterIndex', label: 'Water Index (NDWI)', color: 'text-sky-400' },
                { key: 'urbanHeat', label: 'Urban Heat (LST)', color: 'text-rose-400' },
                { key: 'changeDetection', label: 'Change Mask', color: 'text-amber-400' },
                { key: 'boundaries', label: 'Boundaries', color: 'text-purple-400' },
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
                      <ToggleRight className="w-4 h-4 text-cyan-400" />
                    ) : (
                      <ToggleLeft className="w-4 h-4 text-slate-600 group-hover:text-slate-500" />
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Bottom Mission Status */}
      <div className="p-3 border-t border-cyan-500/15 bg-[#030612] flex items-center space-x-2.5">
        <div className="w-7 h-7 rounded-full bg-cyan-950 border border-cyan-500/40 flex items-center justify-center shrink-0">
          <Globe2 className="w-4 h-4 text-cyan-400 animate-pulse" />
        </div>
        <div className="text-[10px] text-slate-400 leading-tight font-mono">
          <div className="font-semibold text-slate-300">Planetary STAC Engine</div>
          <div className="text-emerald-400">Level-2A BOA Calibrated</div>
        </div>
      </div>
    </aside>
  );
};
