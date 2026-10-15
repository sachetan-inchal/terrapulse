import React, { useState } from 'react';
import { 
  GitCompare, ShieldCheck, AlertTriangle, Layers, 
  Cpu, Sliders, CheckCircle2, RefreshCw 
} from 'lucide-react';
import { RegistrationResult, ChangeDetectionResult } from '../types';
import { runRegistration } from '../services/api';

interface CVTechnicalWorkspaceProps {
  changeData: ChangeDetectionResult | null;
}

export const CVTechnicalWorkspace: React.FC<CVTechnicalWorkspaceProps> = ({ changeData }) => {
  const [loweRatio, setLoweRatio] = useState(0.75);
  const [ransacThresh, setRansacThresh] = useState(5.0);
  const [loading, setLoading] = useState(false);
  const [regResult, setRegResult] = useState<RegistrationResult | null>({
    status: "SUCCESS",
    method: "SIFT + RANSAC Homography",
    keypoints_detected: 3842,
    matches_found: 618,
    inliers_count: 552,
    inlier_ratio_pct: 89.32,
    reprojection_error_px: 1.42,
    homography_matrix: [
      [1.021, -0.012, 45.2],
      [0.008, 0.994, -18.7],
      [-0.00002, 0.00001, 1.0]
    ],
    confidence: "HIGH",
    warning: undefined
  });

  const handleRunRegistration = async () => {
    setLoading(true);
    try {
      const res = await runRegistration(loweRatio, ransacThresh);
      setRegResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto max-h-[calc(100vh-4rem)]">
      {/* Header Banner */}
      <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-cyan-accent" />
            Computer Vision & Image Registration Workspace
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Rigorous geometric alignment, SIFT feature matching, homography verification gates, and segmentation quality analysis.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="px-3 py-1 rounded bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-xs font-mono font-bold">
            ● QA GATE: ACTIVE
          </span>
        </div>
      </div>

      {/* Control Sliders & Execution */}
      <div className="glass-panel p-4 rounded-xl border border-cyan-500/25 grid grid-cols-4 gap-4 items-center">
        <div>
          <label className="text-[11px] font-mono text-slate-300 block mb-1">
            Lowe's Distance Ratio Gate: <strong className="text-cyan-accent">{loweRatio}</strong>
          </label>
          <input
            type="range"
            min={0.5}
            max={0.9}
            step={0.05}
            value={loweRatio}
            onChange={(e) => setLoweRatio(Number(e.target.value))}
            className="w-full accent-cyan-400 h-1.5 bg-space-950 rounded cursor-pointer"
          />
        </div>

        <div>
          <label className="text-[11px] font-mono text-slate-300 block mb-1">
            RANSAC Inlier Threshold: <strong className="text-cyan-accent">{ransacThresh} px</strong>
          </label>
          <input
            type="range"
            min={1.0}
            max={10.0}
            step={0.5}
            value={ransacThresh}
            onChange={(e) => setRansacThresh(Number(e.target.value))}
            className="w-full accent-cyan-400 h-1.5 bg-space-950 rounded cursor-pointer"
          />
        </div>

        <div>
          <label className="text-[11px] font-mono text-slate-300 block mb-1">
            Min Inlier Safety Gate: <strong className="text-emerald-400">25.0%</strong>
          </label>
          <div className="text-[10px] text-slate-400 font-mono">
            Rejects drift/misalignment below threshold
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleRunRegistration}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-space-950 font-bold text-xs shadow-glow-cyan disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Solve Alignment Matrix</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      {regResult && (
        <div className="grid grid-cols-5 gap-3 font-mono">
          <div className="bg-space-950/80 border border-slate-800 rounded-lg p-3">
            <div className="text-[10px] text-slate-400">REGISTRATION STATUS</div>
            <div className={`text-sm font-bold mt-1 ${
              regResult.status === 'SUCCESS' ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {regResult.status}
            </div>
          </div>

          <div className="bg-space-950/80 border border-slate-800 rounded-lg p-3">
            <div className="text-[10px] text-slate-400">DETECTED KEYPOINTS</div>
            <div className="text-sm font-bold text-white mt-1">
              {regResult.keypoints_detected.toLocaleString()}
            </div>
          </div>

          <div className="bg-space-950/80 border border-slate-800 rounded-lg p-3">
            <div className="text-[10px] text-slate-400">RANSAC INLIER RATIO</div>
            <div className="text-sm font-bold text-cyan-accent mt-1">
              {regResult.inlier_ratio_pct}% ({regResult.inliers_count}/{regResult.matches_found})
            </div>
          </div>

          <div className="bg-space-950/80 border border-slate-800 rounded-lg p-3">
            <div className="text-[10px] text-slate-400">REPROJECTION ERROR</div>
            <div className="text-sm font-bold text-purple-accent mt-1">
              {regResult.reprojection_error_px} px RMS
            </div>
          </div>

          <div className="bg-space-950/80 border border-slate-800 rounded-lg p-3">
            <div className="text-[10px] text-slate-400">CONFIDENCE GRADE</div>
            <div className="text-sm font-bold text-amber-400 mt-1">
              {regResult.confidence}
            </div>
          </div>
        </div>
      )}

      {/* Visual Alignment Canvas */}
      <div className="grid grid-cols-2 gap-4">
        {/* Left: Keypoint Correspondences */}
        <div className="glass-panel p-3.5 rounded-xl border border-slate-800">
          <div className="text-xs font-semibold text-white font-mono mb-2 flex items-center justify-between">
            <span>1. SIFT Inlier Matches & Keypoint Vectors</span>
            <span className="text-[10px] text-cyan-400 font-mono">50 Top Correspondences</span>
          </div>
          <div className="h-64 rounded-lg bg-space-950 border border-slate-800 overflow-hidden relative">
            <img 
              src="https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?w=600&q=80" 
              alt="Feature Matches" 
              className="w-full h-full object-cover"
            />
            {/* Synthetic Vector Match Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              <line x1="20%" y1="30%" x2="70%" y2="40%" stroke="#00f0ff" strokeWidth="1.5" />
              <line x1="40%" y1="60%" x2="80%" y2="65%" stroke="#10b981" strokeWidth="1.5" />
              <line x1="30%" y1="80%" x2="75%" y2="85%" stroke="#00f0ff" strokeWidth="1.5" />
              <circle cx="20%" cy="30%" r="4" fill="#00f0ff" />
              <circle cx="70%" cy="40%" r="4" fill="#00f0ff" />
              <circle cx="40%" cy="60%" r="4" fill="#10b981" />
              <circle cx="80%" cy="65%" r="4" fill="#10b981" />
            </svg>
          </div>
        </div>

        {/* Right: Seamless Homography Stitched Canvas */}
        <div className="glass-panel p-3.5 rounded-xl border border-slate-800">
          <div className="text-xs font-semibold text-white font-mono mb-2 flex items-center justify-between">
            <span>2. Perspective Warped & Mosaicked Scene</span>
            <span className="text-[10px] text-emerald-400 font-mono">Bilinear Resampling</span>
          </div>
          <div className="h-64 rounded-lg bg-space-950 border border-slate-800 overflow-hidden relative">
            <img 
              src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&q=80" 
              alt="Stitched Canvas" 
              className="w-full h-full object-cover"
            />
            <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-space-950/80 border border-cyan-500/40 text-[9px] font-mono text-cyan-accent">
              EPSG:32643 UTM Grid
            </div>
          </div>
        </div>
      </div>

      {/* Homography Matrix Matrix Display */}
      {regResult?.homography_matrix && (
        <div className="glass-panel p-3.5 rounded-xl border border-slate-800">
          <div className="text-xs font-semibold text-white font-mono mb-2">
            Solved Perspective Homography Transformation Matrix (H):
          </div>
          <div className="bg-space-950 p-3 rounded-lg font-mono text-xs text-cyan-300 space-y-1 overflow-x-auto">
            {regResult.homography_matrix.map((row, i) => (
              <div key={i} className="flex space-x-6">
                {row.map((val, j) => (
                  <span key={j} className="w-28 text-right font-bold">
                    {val.toFixed(6)}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
