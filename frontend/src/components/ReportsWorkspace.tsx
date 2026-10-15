import React, { useState } from 'react';
import { FileText, Download, CheckCircle, RefreshCw, Printer } from 'lucide-react';
import { generateReport } from '../services/api';

export const ReportsWorkspace: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [analystNotes, setAnalystNotes] = useState('Assessment prepared for regional environmental intelligence review.');

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

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto max-h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-accent" />
            Automated Geospatial Intelligence Reports
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Generate and export reproducible environmental reports with satellite metadata, change statistics, and evidence citations.
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-space-950 font-bold text-xs shadow-glow-cyan disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Synthesizing...' : 'Generate New Assessment'}</span>
        </button>
      </div>

      {/* Analyst Notes Input */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
        <label className="text-xs font-mono text-slate-300 block">
          Analyst Context & Scope Notes:
        </label>
        <textarea
          value={analystNotes}
          onChange={(e) => setAnalystNotes(e.target.value)}
          rows={2}
          className="w-full bg-space-950/80 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-sans"
        />
      </div>

      {/* Generated Report Viewer */}
      {report && (
        <div className="glass-panel p-6 rounded-xl border border-cyan-500/30 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <div className="text-sm font-bold text-white font-mono">{report.title}</div>
              <div className="text-xs text-slate-400 font-mono mt-0.5">{report.timestamp}</div>
            </div>
            <button
              onClick={handleDownload}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-space-950 border border-cyan-500/40 text-cyan-accent text-xs font-mono hover:bg-cyan-500/20 shadow-glow-cyan"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Markdown Report</span>
            </button>
          </div>

          <div className="bg-space-950 p-5 rounded-lg font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto border border-slate-800">
            {report.markdown_content}
          </div>
        </div>
      )}
    </div>
  );
};
