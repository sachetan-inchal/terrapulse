import React, { useState } from 'react';
import { 
  FileText, TrendingUp, BookOpen, AlertOctagon, ExternalLink, 
  ShieldCheck, HelpCircle, ArrowUpRight, BarChart2, Check, AlertTriangle, Layers 
} from 'lucide-react';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  Tooltip, Legend, CartesianGrid, Area, ComposedChart 
} from 'recharts';
import { 
  SymptomAnalysisResult, ForecastResponseData, ResearchQueryResponseData 
} from '../../types/investigation';

interface AnalyticalReportPanelProps {
  symptomResult: SymptomAnalysisResult | null;
  forecastData: ForecastResponseData | null;
  researchData?: ResearchQueryResponseData | null;
  onRunForecastScenario?: (indicator: string, horizon: string, reductionPct: number) => void;
  isLoadingForecast?: boolean;
}

export const AnalyticalReportPanel: React.FC<AnalyticalReportPanelProps> = ({
  symptomResult,
  forecastData,
  researchData,
  onRunForecastScenario,
  isLoadingForecast
}) => {
  const [activeTab, setActiveTab] = useState<'hypotheses' | 'forecast' | 'literature' | 'limitations'>('hypotheses');
  const [selectedHorizon, setSelectedHorizon] = useState<string>('+5 years');
  const [selectedIndicator, setSelectedIndicator] = useState<string>('PM2.5');

  // Format forecast data for Recharts
  const prepareChartData = () => {
    if (!forecastData || !forecastData.scenarios) return [];

    const bau = forecastData.scenarios.BAU?.trajectory || [];
    const pol = forecastData.scenarios.POL_RED?.trajectory || [];
    const interv = forecastData.scenarios.INTERVENTION?.trajectory || [];

    // Map by year
    const years = Array.from(new Set([
      ...bau.map(p => p.year),
      ...pol.map(p => p.year),
      ...interv.map(p => p.year)
    ])).sort((a, b) => a - b);

    return years.map(yr => {
      const bPt = bau.find(p => p.year === yr);
      const pPt = pol.find(p => p.year === yr);
      const iPt = interv.find(p => p.year === yr);

      return {
        year: yr,
        BAU: bPt?.predicted_value,
        Policy_Reduction: pPt?.predicted_value,
        Intervention: iPt?.predicted_value,
        lower_80: bPt?.lower_80,
        upper_80: bPt?.upper_80,
        lower_95: bPt?.lower_95,
        upper_95: bPt?.upper_95,
        // Band width for Recharts area rendering
        ci_95_band: bPt ? [bPt.lower_95, bPt.upper_95] : undefined,
        ci_80_band: bPt ? [bPt.lower_80, bPt.upper_80] : undefined
      };
    });
  };

  const chartData = prepareChartData();

  const handleHorizonChange = (horizon: string) => {
    setSelectedHorizon(horizon);
    if (onRunForecastScenario) {
      onRunForecastScenario(selectedIndicator, horizon, 30.0);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#050b1a]/95 border-l border-cyan-500/20 backdrop-blur-xl">
      {/* Panel Tab Navigation */}
      <div className="flex items-center border-b border-cyan-500/20 bg-[#030612]/90 px-3 pt-2">
        <button
          onClick={() => setActiveTab('hypotheses')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono font-semibold border-b-2 transition-all ${
            activeTab === 'hypotheses'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10 rounded-t-lg'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Causal Hypotheses</span>
        </button>

        <button
          onClick={() => setActiveTab('forecast')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono font-semibold border-b-2 transition-all ${
            activeTab === 'forecast'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10 rounded-t-lg'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Forecasting</span>
        </button>

        <button
          onClick={() => setActiveTab('literature')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono font-semibold border-b-2 transition-all ${
            activeTab === 'literature'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10 rounded-t-lg'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Research Papers</span>
        </button>

        <button
          onClick={() => setActiveTab('limitations')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono font-semibold border-b-2 transition-all ${
            activeTab === 'limitations'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10 rounded-t-lg'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertOctagon className="w-3.5 h-3.5" />
          <span>Uncertainty</span>
        </button>
      </div>

      {/* Tab Contents Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* TAB 1: Causal Hypotheses */}
        {activeTab === 'hypotheses' && (
          <div className="space-y-4">
            {!symptomResult ? (
              <div className="py-12 text-center text-slate-500 font-mono text-xs">
                No active symptom investigation loaded. Ask a question about environmental anomalies or fish mortality.
              </div>
            ) : (
              <>
                {/* Synthesis Verdict Banner */}
                <div className="p-3.5 rounded-xl bg-[#070e24] border border-cyan-500/30 space-y-2 shadow-inner">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold">
                      MULTIDISCIPLINARY SYNTHESIS VERDICT
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                      Target: {symptomResult.location}
                    </span>
                  </div>
                  <p className="text-xs text-slate-200 leading-relaxed font-sans">
                    {symptomResult.investigation_summary}
                  </p>
                </div>

                {/* Ranked Hypotheses Cards */}
                <div className="space-y-3">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                    Ranked Hypotheses (Bradford Hill Criteria):
                  </div>

                  {symptomResult.hypotheses.map((h, idx) => (
                    <div
                      key={h.hypothesis_id}
                      className="p-3.5 rounded-xl bg-[#070e24]/90 border border-slate-800 hover:border-cyan-500/40 transition-all space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-mono text-xs font-bold">
                              {idx + 1}
                            </span>
                            <h4 className="text-xs font-bold text-white">{h.title}</h4>
                          </div>
                          <p className="text-[11px] text-slate-300 mt-1 font-sans">
                            {h.biological_mechanism}
                          </p>
                        </div>

                        <div className="text-right shrink-0">
                          <span className={`text-[9px] font-mono px-2 py-0.5 rounded border font-semibold ${
                            h.confidence_tier.includes('HIGH')
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                              : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          }`}>
                            {h.confidence_tier.replace(/_/g, ' ')}
                          </span>
                          <div className="text-[10px] font-mono text-slate-400 mt-1">
                            Index: <strong className="text-cyan-400">{h.bradford_hill_score}</strong>
                          </div>
                        </div>
                      </div>

                      {/* Evidence breakdown */}
                      <div className="space-y-1 text-[11px] pt-1 border-t border-slate-800/80">
                        {h.supporting_evidence.length > 0 && (
                          <div className="flex items-start gap-1.5 text-emerald-400">
                            <Check className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                            <span className="text-slate-300">
                              <strong className="text-emerald-400">Supporting:</strong> {h.supporting_evidence[0].claim}
                            </span>
                          </div>
                        )}

                        {h.alternative_explanations.length > 0 && (
                          <div className="flex items-start gap-1.5 text-amber-400">
                            <HelpCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                            <span className="text-slate-300">
                              <strong className="text-amber-400">Rival Alternative:</strong> {h.alternative_explanations[0]}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Scientific Integrity Disclaimer */}
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-[10px] text-slate-400 font-mono flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <span>{symptomResult.uncertainty_statement}</span>
                </div>
              </>
            )}
          </div>
        )}

        {/* TAB 2: Forecasting & Scenarios */}
        {activeTab === 'forecast' && (
          <div className="space-y-4">
            {/* Horizon & Indicator Controls */}
            <div className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                  Projection Horizon:
                </span>
                <span className="text-[10px] font-mono text-cyan-400">
                  Target: {forecastData?.horizon_target_year || 2030}
                </span>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {['+1 year', '+3 years', '+5 years', '2030', '2040'].map((h) => (
                  <button
                    key={h}
                    onClick={() => handleHorizonChange(h)}
                    className={`px-2.5 py-1 rounded-md text-[10px] font-mono transition-colors ${
                      selectedHorizon === h
                        ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-400 font-bold'
                        : 'bg-slate-800/80 text-slate-400 hover:text-white'
                    }`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            {/* Recharts Multi-Scenario Trajectory */}
            <div className="p-3.5 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs font-bold text-white flex items-center gap-2">
                  <span>Scenario Trajectories: {forecastData?.indicator || 'PM2.5'}</span>
                  <span className="text-[10px] font-mono text-slate-400">({forecastData?.unit || 'µg/m³'})</span>
                </div>
                {isLoadingForecast && (
                  <span className="text-[10px] font-mono text-cyan-400 animate-pulse">Recalculating...</span>
                )}
              </div>

              {chartData.length > 0 ? (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#070e24',
                          borderColor: '#06b6d4',
                          borderRadius: '8px',
                          fontSize: '11px',
                          fontFamily: 'monospace'
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '8px' }} />

                      {/* 95% Confidence Interval band */}
                      <Area
                        type="monotone"
                        dataKey="upper_95"
                        stroke="none"
                        fill="#38bdf8"
                        fillOpacity={0.12}
                        name="95% CI Range"
                      />

                      {/* Trajectories */}
                      <Line
                        type="monotone"
                        dataKey="BAU"
                        stroke="#ef4444"
                        strokeWidth={2}
                        name="Business-As-Usual"
                        dot={{ r: 3 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="Policy_Reduction"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        name="Policy Reduction (-30%)"
                        strokeDasharray="4 4"
                      />
                      <Line
                        type="monotone"
                        dataKey="Intervention"
                        stroke="#10b981"
                        strokeWidth={2}
                        name="Ecological Intervention"
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="py-12 text-center text-slate-500 font-mono text-xs">
                  Run an investigation or ask a future projection question to render statistical forecast models.
                </div>
              )}

              {/* Scenarios Assumptions Cards */}
              {forecastData?.scenarios && (
                <div className="space-y-2 pt-2 border-t border-slate-800 text-[11px] font-mono">
                  <div className="text-[10px] uppercase font-bold text-slate-400">
                    Model Assumptions:
                  </div>
                  {Object.entries(forecastData.scenarios).map(([key, sc]: [string, any]) => (
                    <div key={key} className="p-2 rounded bg-slate-900/60 border border-slate-800/80">
                      <div className="font-semibold text-cyan-300">{sc.scenario_name}</div>
                      <p className="text-[10px] text-slate-400 font-sans mt-0.5">{sc.description}</p>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-[10px] text-slate-500 italic font-mono">
                {forecastData?.disclaimer || "OLS trend projection with heteroskedastic 80% & 95% prediction intervals. Model projection, not ground-truth satellite observation."}
              </p>
            </div>
          </div>
        )}

        {/* TAB 3: Scientific Research Papers */}
        {activeTab === 'literature' && (
          <div className="space-y-3">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Aggregated Academic & News Literature:
            </div>

            {symptomResult?.academic_citations && symptomResult.academic_citations.length > 0 ? (
              symptomResult.academic_citations.map((cite, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-[#070e24]/90 border border-slate-800 hover:border-cyan-500/30 transition-all space-y-1.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-xs font-semibold text-white leading-snug">{cite.title}</h4>
                    {cite.doi && (
                      <a
                        href={cite.doi.startsWith('http') ? cite.doi : `https://doi.org/${cite.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 shrink-0 p-1 rounded hover:bg-slate-800"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                    <span>{cite.journal || 'Academic Journal'}</span>
                    {cite.year && <span>• {cite.year}</span>}
                  </div>
                </div>
              ))
            ) : researchData?.articles && researchData.articles.length > 0 ? (
              researchData.articles.map((art, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-[#070e24]/90 border border-slate-800 hover:border-cyan-500/30 transition-all space-y-1.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-xs font-semibold text-white leading-snug">{art.title}</h4>
                    {art.doi_or_url && (
                      <a
                        href={art.doi_or_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 shrink-0 p-1 rounded hover:bg-slate-800"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300">{art.source}</span>
                    <span>{art.publication_year || 'Unknown year'}</span>
                  </div>
                  <p className="text-[11px] text-slate-300 font-sans line-clamp-2">{art.snippet}</p>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-slate-500 font-mono text-xs">
                No research citations currently retrieved. Inquire about environmental symptoms to retrieve papers from OpenAlex, Europe PMC, and Crossref.
              </div>
            )}
          </div>
        )}

        {/* TAB 4: Missing Data & Epistemic Limitations */}
        {activeTab === 'limitations' && (
          <div className="space-y-3.5">
            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 font-mono space-y-1.5">
              <div className="flex items-center gap-2 font-bold uppercase text-amber-300 text-[11px]">
                <AlertTriangle className="w-4 h-4" />
                <span>Epistemic Causality Checklist</span>
              </div>
              <p className="font-sans text-[11px] leading-relaxed">
                Bradford Hill causal inference requires ruling out rival hypotheses and unmeasured chemical factors before declaring proven causation.
              </p>
            </div>

            <div className="space-y-2">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Missing Telemetry Required to Establish Causality:
              </div>

              {symptomResult?.hypotheses && symptomResult.hypotheses.flatMap(h => h.missing_data).length > 0 ? (
                Array.from(new Set(symptomResult.hypotheses.flatMap(h => h.missing_data))).map((item, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-[#070e24] border border-slate-800 text-xs text-slate-300 font-mono flex items-center gap-2"
                  >
                    <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0"></span>
                    <span>{item}</span>
                  </div>
                ))
              ) : (
                <div className="p-3 rounded-lg bg-[#070e24] border border-slate-800 text-xs text-slate-400 font-mono">
                  - Continuous diurnal Dissolved Oxygen (DO) minimums (nighttime nadir)<br/>
                  - Surfactant / LAS chemical mass spectrometry assays<br/>
                  - Total Nitrogen (TN) & Total Phosphorus (TP) lake stoichiometry
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
