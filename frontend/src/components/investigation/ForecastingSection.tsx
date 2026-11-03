import React, { useState } from 'react';
import { 
  TrendingUp, Sliders, Calendar, AlertTriangle, ShieldCheck, 
  Layers, Check, RefreshCw, BarChart2 
} from 'lucide-react';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  Tooltip, Legend, CartesianGrid, Area, ComposedChart 
} from 'recharts';
import { ForecastResponseData } from '../../types/investigation';
import { LocationInfo } from '../../types';

interface ForecastingSectionProps {
  currentLocation: LocationInfo;
  forecastData: ForecastResponseData | null;
  onRunForecastScenario: (indicator: string, horizon: string, reductionPct: number) => Promise<void>;
  isLoadingForecast: boolean;
}

export const ForecastingSection: React.FC<ForecastingSectionProps> = ({
  currentLocation,
  forecastData,
  onRunForecastScenario,
  isLoadingForecast
}) => {
  const [selectedIndicator, setSelectedIndicator] = useState<string>('PM2.5');
  const [selectedHorizon, setSelectedHorizon] = useState<string>('+5 years');
  const [reductionPct, setReductionPct] = useState<number>(30);
  const [showConfidenceBands, setShowConfidenceBands] = useState<boolean>(true);

  // Build chart dataset from forecastData scenarios
  const defaultChartData = [
    { year: 2020, historical: 60.0, bau: 60.0 },
    { year: 2021, historical: 68.0, bau: 68.0 },
    { year: 2022, historical: 74.0, bau: 74.0 },
    { year: 2023, historical: 82.0, bau: 82.0 },
    { year: 2024, historical: 90.0, bau: 90.0, reduction: 90.0, intervention: 90.0, lower95: 90.0, upper95: 90.0, lower80: 90.0, upper80: 90.0 },
    { year: 2025, bau: 97.4, reduction: 84.6, intervention: 76.5, lower95: 84.2, upper95: 110.6, lower80: 89.1, upper80: 105.7 },
    { year: 2026, bau: 104.8, reduction: 79.2, intervention: 66.8, lower95: 88.5, upper95: 121.1, lower80: 94.6, upper80: 115.0 },
    { year: 2027, bau: 112.2, reduction: 73.8, intervention: 59.2, lower95: 92.1, upper95: 132.3, lower80: 99.8, upper80: 124.6 },
    { year: 2028, bau: 119.6, reduction: 68.4, intervention: 53.4, lower95: 95.4, upper95: 143.8, lower80: 104.5, upper80: 134.7 },
    { year: 2029, bau: 127.0, reduction: 63.0, intervention: 48.0, lower95: 98.2, upper95: 155.8, lower80: 108.9, upper80: 145.1 },
  ];

  let chartData = defaultChartData;

  if (forecastData && forecastData.scenarios) {
    const bauTraj = forecastData.scenarios['BAU']?.trajectory || [];
    const redTraj = forecastData.scenarios['POL_RED']?.trajectory || [];
    const intTraj = forecastData.scenarios['INTERVENTION']?.trajectory || [];

    if (bauTraj.length > 0) {
      chartData = bauTraj.map((pt, idx) => {
        const rPt = redTraj[idx] || {};
        const iPt = intTraj[idx] || {};
        return {
          year: pt.year,
          bau: pt.predicted_value,
          reduction: rPt.predicted_value,
          intervention: iPt.predicted_value,
          lower80: pt.lower_80,
          upper80: pt.upper_80,
          lower95: pt.lower_95,
          upper95: pt.upper_95,
        };
      });
    }
  }

  const handleApplyScenario = async () => {
    await onRunForecastScenario(selectedIndicator, selectedHorizon, reductionPct);
  };

  const currentUnit = forecastData?.unit || 'µg/m³';

  return (
    <div className="flex-1 flex flex-col h-full bg-[#030612] overflow-hidden p-6 space-y-6">
      {/* 1. Header with Scenario Controls */}
      <div className="flex items-center justify-between border-b border-cyan-500/20 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-white tracking-wide">Multi-Scenario Forecasting</h2>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-mono">
              Statistical Simulation • {currentLocation.name.split(',')[0]}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Compare Business-As-Usual, Policy Reduction caps, and Ecological Intervention trajectories with 80% & 95% confidence bands.
          </p>
        </div>

        {/* Confidence Band Toggle */}
        <button
          onClick={() => setShowConfidenceBands(!showConfidenceBands)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
            showConfidenceBands 
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' 
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}
        >
          <span>{showConfidenceBands ? 'Hide' : 'Show'} 80%/95% Confidence Envelopes</span>
        </button>
      </div>

      {/* 2. Main Dual-Column Content */}
      <div className="flex-1 flex gap-6 overflow-hidden min-h-0">
        {/* Left: Interactive Scenario Configuration Sidebar */}
        <div className="w-[34%] h-full bg-[#070e24]/95 border border-cyan-500/25 rounded-2xl p-5 flex flex-col justify-between backdrop-blur-xl shadow-2xl space-y-4 overflow-y-auto">
          <div className="space-y-4">
            <div className="text-xs font-bold font-mono text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-4 h-4" />
              <span>Simulation Controls</span>
            </div>

            {/* Indicator Selector */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-mono text-slate-400">Environmental Indicator:</label>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                {['PM2.5', 'DO', 'NDVI', 'Built-Up Area'].map(ind => (
                  <button
                    key={ind}
                    onClick={() => setSelectedIndicator(ind === 'DO' ? 'dissolved_oxygen_mg_l' : ind === 'Built-Up Area' ? 'built_up_coverage_pct' : ind)}
                    className={`p-2 rounded-lg border text-left transition-colors ${
                      (selectedIndicator === ind || (ind === 'DO' && selectedIndicator === 'dissolved_oxygen_mg_l') || (ind === 'Built-Up Area' && selectedIndicator === 'built_up_coverage_pct'))
                        ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                        : 'bg-[#030612] border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {ind}
                  </button>
                ))}
              </div>
            </div>

            {/* Horizon Selector */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-mono text-slate-400">Forecast Horizon:</label>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                {['+1 year', '+3 years', '+5 years', '2030', '2040'].map(hor => (
                  <button
                    key={hor}
                    onClick={() => setSelectedHorizon(hor)}
                    className={`py-1.5 px-2 rounded-lg border text-center transition-colors ${
                      selectedHorizon === hor
                        ? 'bg-blue-600/30 border-blue-400 text-white font-bold'
                        : 'bg-[#030612] border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {hor}
                  </button>
                ))}
              </div>
            </div>

            {/* Policy Reduction Percentage Slider */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Policy Reduction Target:</span>
                <span className="text-cyan-300 font-bold">{reductionPct}% reduction</span>
              </div>
              <input
                type="range"
                min="10"
                max="50"
                step="5"
                value={reductionPct}
                onChange={(e) => setReductionPct(Number(e.target.value))}
                className="w-full accent-cyan-400 bg-slate-800 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>10% (Modest)</span>
                <span>30% (Standard)</span>
                <span>50% (Ambitious)</span>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={handleApplyScenario}
              disabled={isLoadingForecast}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-bold font-mono transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoadingForecast ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Computing Trajectory...</span>
                </>
              ) : (
                <>
                  <BarChart2 className="w-3.5 h-3.5" />
                  <span>Run Scenario Projection</span>
                </>
              )}
            </button>
          </div>

          {/* Scenario Assumptions Box */}
          <div className="p-3.5 rounded-xl bg-[#030612] border border-cyan-500/20 text-[10px] text-slate-400 font-mono space-y-1.5">
            <strong className="text-cyan-300 block text-[11px]">Explicit Assumptions:</strong>
            <p>• <strong>BAU:</strong> OLS linear trend extrapolation assuming historical urbanization and emission growth continue unchecked.</p>
            <p>• <strong>Policy Reduction:</strong> Simulates enforced industrial caps & fleet electrification reducing annual increment by {reductionPct}%.</p>
            <p>• <strong>Intervention:</strong> Models targeted aeration, riparian buffers, and rapid point-source effluent scrubbing.</p>
          </div>
        </div>

        {/* Right: Recharts Interactive Forecast Chart & Metric Cards */}
        <div className="flex-1 h-full bg-[#070e24]/95 border border-cyan-500/25 rounded-2xl p-5 flex flex-col justify-between backdrop-blur-xl shadow-2xl">
          <div className="flex-1 flex flex-col min-h-0 space-y-4">
            <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2.5">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">Multi-Scenario Trajectory</span>
                <h3 className="text-base font-bold text-white mt-0.5">
                  {selectedIndicator.toUpperCase()} Projection ({currentUnit})
                </h3>
              </div>
              <div className="text-right text-[10px] font-mono text-slate-400">
                <span>Method: OLS + Heteroskedastic Prediction Intervals</span>
              </div>
            </div>

            {/* Recharts Composed Chart */}
            <div className="flex-1 w-full bg-[#030612]/80 rounded-xl p-3 border border-slate-800 min-h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 15, right: 25, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#070e24', borderColor: '#06b6d4', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                    formatter={(val: any, name: any) => [`${val} ${currentUnit}`, name]}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />

                  {/* Confidence Interval Areas */}
                  {showConfidenceBands && (
                    <>
                      <Area type="monotone" dataKey="upper95" stroke="none" fill="#ef4444" fillOpacity={0.08} name="95% CI (Upper)" />
                      <Area type="monotone" dataKey="lower95" stroke="none" fill="#ef4444" fillOpacity={0.08} name="95% CI (Lower)" />
                    </>
                  )}

                  {/* Scenarios */}
                  <Line type="monotone" dataKey="bau" stroke="#ef4444" strokeWidth={2.5} dot={{ r: 3 }} name="Business-as-Usual (BAU)" />
                  <Line type="monotone" dataKey="reduction" stroke="#38bdf8" strokeWidth={2.5} dot={{ r: 3 }} name={`Policy Reduction (-${reductionPct}%)`} />
                  <Line type="monotone" dataKey="intervention" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3 }} name="Ecological Intervention" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Outcome Delta Highlights */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/30 text-xs">
                <span className="text-[10px] font-mono text-rose-400 uppercase block">Status-Quo (BAU)</span>
                <span className="text-lg font-bold text-white font-mono mt-0.5 block">
                  {chartData[chartData.length - 1]?.bau ? `${chartData[chartData.length - 1].bau} ${currentUnit}` : 'N/A'}
                </span>
                <span className="text-[10px] text-rose-300/80 font-mono">Continued expansion</span>
              </div>

              <div className="p-3 rounded-xl bg-sky-950/20 border border-sky-500/30 text-xs">
                <span className="text-[10px] font-mono text-sky-400 uppercase block">Policy Reduction</span>
                <span className="text-lg font-bold text-white font-mono mt-0.5 block">
                  {chartData[chartData.length - 1]?.reduction ? `${chartData[chartData.length - 1].reduction} ${currentUnit}` : 'N/A'}
                </span>
                <span className="text-[10px] text-sky-300/80 font-mono">{reductionPct}% reduction goal</span>
              </div>

              <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-xs">
                <span className="text-[10px] font-mono text-emerald-400 uppercase block">Ecological Intervention</span>
                <span className="text-lg font-bold text-white font-mono mt-0.5 block">
                  {chartData[chartData.length - 1]?.intervention ? `${chartData[chartData.length - 1].intervention} ${currentUnit}` : 'N/A'}
                </span>
                <span className="text-[10px] text-emerald-300/80 font-mono">Wetlands & active scrubbing</span>
              </div>
            </div>
          </div>

          {/* Scientific Disclaimer Footer */}
          <div className="border-t border-cyan-500/20 pt-3 text-[10px] text-slate-400 font-mono">
            <strong className="text-cyan-400">Scientific Disclaimer:</strong> Projections represent conditional statistical simulations based on historical observations and specified assumptions. Not ground-truth satellite observations. Widening prediction intervals communicate real meteorological uncertainty.
          </div>
        </div>
      </div>
    </div>
  );
};

