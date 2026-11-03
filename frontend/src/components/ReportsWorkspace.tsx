import React, { useState } from 'react';
import { 
  FileText, Download, CheckCircle, RefreshCw, 
  Printer, Image, Database, BookOpen, ExternalLink, ShieldCheck
} from 'lucide-react';
import { generateReport } from '../services/api';

export const ReportsWorkspace: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [analystNotes, setAnalystNotes] = useState('Assessment prepared for regional environmental intelligence and planetary change review.');

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await generateReport('bengaluru', 1985, 2024, analystNotes);
      setReport(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    const blob = new Blob([report.markdown_content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${report.report_id}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportGeoJSON = () => {
    const geojsonData = {
      type: "FeatureCollection",
      metadata: {
        title: "TerraPulse Environmental Report Export",
        generated_at: new Date().toISOString(),
        crs: "EPSG:4326"
      },
      features: [
        {
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [[[77.4598, 12.8334], [77.784, 12.8334], [77.784, 13.1426], [77.4598, 13.1426], [77.4598, 12.8334]]]
          },
          properties: {
            location: "Bengaluru, Karnataka, India",
            mean_ndvi: 0.2282,
            vegetation_coverage_pct: 23.5,
            built_up_coverage_pct: 54.0,
            water_coverage_pct: 3.2
          }
        }
      ]
    };

    const blob = new Blob([JSON.stringify(geojsonData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `terrapulse_aoi_export_${Date.now()}.geojson`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrintPDF = () => {
    window.print();
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 max-w-7xl mx-auto space-y-6">
      {/* 1. Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-mono">
            <FileText className="w-5 h-5 text-cyan-400" />
            <span>Reports, Exports & Reproducibility Studio</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Generate, verify, and export reproducible analytical reports, GeoJSON datasets, and high-resolution raster evidence.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-mono font-bold text-xs shadow-md shadow-cyan-500/20 disabled:opacity-50 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Synthesizing...' : 'Generate Comprehensive Assessment'}</span>
          </button>
        </div>
      </div>

      {/* 2. Export Actions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Export High-Resolution Map Image */}
        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-2 flex flex-col justify-between">
          <div>
            <div className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
              <Image className="w-4 h-4 text-cyan-400" />
              <span>Export High-Resolution Raster</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Download current observation snapshot as a georeferenced PNG raster with scale bar and orientation legend.
            </p>
          </div>
          <a
            href="/api/imagery/tile?mission=Sentinel-2&year=2024"
            download="terrapulse_highres_satellite_map.png"
            target="_blank"
            rel="noreferrer"
            className="py-2 px-3 rounded-lg bg-[#030612] hover:bg-slate-800 border border-cyan-500/30 text-cyan-300 text-xs font-mono font-bold text-center flex items-center justify-center gap-1.5 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Map Image (PNG)</span>
          </a>
        </div>

        {/* Export GeoJSON AOI & Classifications */}
        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-2 flex flex-col justify-between">
          <div>
            <div className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
              <Database className="w-4 h-4 text-emerald-400" />
              <span>Export GeoJSON Feature Set</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Download vector study area boundaries, zonal statistics, and polygon telemetry in EPSG:4326 format.
            </p>
          </div>
          <button
            onClick={handleExportGeoJSON}
            className="py-2 px-3 rounded-lg bg-[#030612] hover:bg-slate-800 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-bold text-center flex items-center justify-center gap-1.5 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download GeoJSON Dataset</span>
          </button>
        </div>

        {/* Export Printable PDF */}
        <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-2 flex flex-col justify-between">
          <div>
            <div className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
              <Printer className="w-4 h-4 text-purple-400" />
              <span>Printable Assessment PDF</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Render print-ready environmental diagnostic dossier with executive summary and causal evidence.
            </p>
          </div>
          <button
            onClick={handlePrintPDF}
            className="py-2 px-3 rounded-lg bg-[#030612] hover:bg-slate-800 border border-purple-500/30 text-purple-300 text-xs font-mono font-bold text-center flex items-center justify-center gap-1.5 transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print / Save as PDF</span>
          </button>
        </div>
      </div>

      {/* 3. Analyst Notes Input */}
      <div className="p-4 rounded-xl bg-[#070e24]/80 border border-slate-800 space-y-2">
        <label className="text-xs font-mono text-slate-300 block font-bold">
          Analyst Context & Scope Notes:
        </label>
        <textarea
          value={analystNotes}
          onChange={(e) => setAnalystNotes(e.target.value)}
          rows={2}
          className="w-full bg-[#030612] border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-sans"
        />
      </div>

      {/* 4. Generated Report Viewer */}
      {report ? (
        <div className="p-6 rounded-xl bg-[#070e24]/90 border border-cyan-500/30 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <div className="text-sm font-bold text-white font-mono">{report.title}</div>
              <div className="text-xs text-slate-400 font-mono mt-0.5">{report.timestamp}</div>
            </div>
            <button
              onClick={handleDownload}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-[#030612] border border-cyan-500/40 text-cyan-300 text-xs font-mono hover:bg-cyan-500/20 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Markdown Report</span>
            </button>
          </div>

          <div className="bg-[#030612] p-5 rounded-lg font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto border border-slate-800">
            {report.markdown_content}
          </div>
        </div>
      ) : (
        <div className="p-8 rounded-xl bg-[#070e24]/50 border border-dashed border-slate-800 text-center space-y-2">
          <FileText className="w-8 h-8 text-slate-500 mx-auto" />
          <div className="text-sm font-mono text-slate-400">No Assessment Synthesized Yet</div>
          <div className="text-xs text-slate-500 font-mono">
            Click "Generate Comprehensive Assessment" above to run multi-agent synthesis across Landsat, Sentinel-2, and ground telemetry.
          </div>
        </div>
      )}

      {/* 5. Provenance & Research Citations */}
      <div className="p-4 rounded-xl bg-[#070e24]/80 border border-cyan-500/20 space-y-2">
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <BookOpen className="w-4 h-4 text-cyan-400" />
          <span>Scientific Citations & Provenance Integrity</span>
        </div>
        <div className="text-[11px] text-slate-400 font-mono space-y-1">
          <div>• USGS / NASA Landsat Program (Landsat 5 TM, Landsat 8 OLI, Landsat 9 OLI-2) via Microsoft Planetary Computer STAC.</div>
          <div>• European Space Agency (ESA) Copernicus Sentinel-2 MSI Multi-Spectral Instrument (Level-2A BOA Surface Reflectance).</div>
          <div>• Central Pollution Control Board (CPCB) Continuous Ambient Air Quality Monitoring (CAAQMS) Telemetry Network.</div>
        </div>
      </div>
    </div>
  );
};
