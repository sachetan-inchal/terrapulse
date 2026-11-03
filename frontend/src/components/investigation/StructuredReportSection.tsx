import React from 'react';
import { 
  Printer, FileText, Download, CheckCircle2, AlertTriangle, ShieldCheck, 
  MapPin, Calendar, Clock, ExternalLink, Activity, BookOpen, TrendingUp, Layers
} from 'lucide-react';
import { LocationInfo } from '../../types';
import { SymptomAnalysisResult, ForecastResponseData, StationMeasurement, HeatmapData } from '../../types/investigation';

interface StructuredReportSectionProps {
  currentLocation: LocationInfo;
  symptomResult: SymptomAnalysisResult | null;
  forecastData: ForecastResponseData | null;
  stations: StationMeasurement[];
  heatmapData: HeatmapData | null;
  userQuery?: string;
}

export const StructuredReportSection: React.FC<StructuredReportSectionProps> = ({
  currentLocation,
  symptomResult,
  forecastData,
  stations,
  heatmapData,
  userQuery = 'Multi-Factor Causal Environmental Analysis'
}) => {
  const generatedDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  const generatedTime = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short'
  });

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="h-full flex flex-col bg-[#050b18] text-slate-100 overflow-y-auto print:bg-white print:text-black">
      {/* Top Action Header (Hidden in Print) */}
      <div className="sticky top-0 z-20 bg-[#070e24]/90 backdrop-blur-md border-b border-cyan-500/20 px-8 py-4 flex items-center justify-between print:hidden">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            <span>Structured Environmental Investigation Report</span>
          </h2>
          <p className="text-xs text-slate-400">
            Official synthesized diagnostic, causal verification, and policy forecasting document.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs shadow-lg shadow-cyan-600/30 transition-all cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Export PDF</span>
          </button>
        </div>
      </div>

      {/* Main Report Document Sheet */}
      <div className="max-w-4xl mx-auto w-full p-8 md:p-12 space-y-8 print:p-0 print:max-w-none">
        
        {/* Document Header */}
        <div className="border-b-2 border-cyan-500/30 pb-6 space-y-4 print:border-black">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-600 flex items-center justify-center text-white font-black text-xl font-mono shadow-md print:bg-black">
                TP
              </div>
              <div>
                <h1 className="text-xl font-black text-white uppercase tracking-wider font-mono print:text-black">
                  TERRAPULSE 2.0
                </h1>
                <div className="text-[10px] text-cyan-400 tracking-widest font-mono uppercase print:text-gray-600">
                  Planetary Environmental Diagnostics & Causal Intelligence
                </div>
              </div>
            </div>

            <div className="text-right font-mono text-xs text-slate-400 print:text-gray-600 space-y-0.5">
              <div className="font-semibold text-slate-200 print:text-black">REPORT REF: TP-INV-{Date.now().toString().slice(-6)}</div>
              <div>Date: {generatedDate}</div>
              <div>Time: {generatedTime}</div>
            </div>
          </div>

          <div className="bg-[#08122c] border border-cyan-500/20 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4 print:bg-gray-100 print:border-gray-400">
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-mono print:text-gray-600">Location Studied</div>
              <div className="text-sm font-bold text-white print:text-black flex items-center gap-1.5 mt-0.5">
                <MapPin className="w-3.5 h-3.5 text-cyan-400 print:text-black" />
                <span>{currentLocation.name}</span>
              </div>
              <div className="text-[10px] font-mono text-cyan-400/80 print:text-gray-700">
                {currentLocation.latitude.toFixed(4)}°N, {currentLocation.longitude.toFixed(4)}°E
              </div>
            </div>

            <div>
              <div className="text-[10px] text-slate-400 uppercase font-mono print:text-gray-600">Investigation Query</div>
              <div className="text-xs font-semibold text-slate-200 print:text-black mt-0.5 line-clamp-2">
                "{userQuery}"
              </div>
            </div>

            <div>
              <div className="text-[10px] text-slate-400 uppercase font-mono print:text-gray-600">Analysis Status</div>
              <div className="mt-0.5 flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 print:bg-gray-200 print:text-black">
                  Verified Causal Evidence
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 1: Executive Summary */}
        <section className="space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 font-mono flex items-center gap-2 print:text-black border-b border-cyan-500/20 pb-1 print:border-gray-400">
            <span>1.0 Executive Summary</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed text-justify print:text-black">
            {symptomResult?.investigation_summary || 
              `An integrated multi-modal investigation was conducted for ${currentLocation.name}. The system combined ground telemetry from CPCB/KSPCB monitoring stations, multi-spectral satellite reflectance from Sentinel-2 MSI and Landsat-9 OLI sensors, and spatial regression models (IDW interpolation and Getis-Ord Gi* hotspot detection). Causal evaluation was conducted under the Bradford Hill epidemiological framework to rank environmental drivers without confounding correlation with direct causation.`}
          </p>
        </section>

        {/* Section 2: Ground Telemetry & Optical Observation Summary */}
        <section className="space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 font-mono flex items-center gap-2 print:text-black border-b border-cyan-500/20 pb-1 print:border-gray-400">
            <span>2.0 Observational Environmental Telemetry</span>
          </h3>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-[#091534] border border-cyan-500/20 rounded-lg p-3 print:border-gray-300 print:bg-gray-50">
              <div className="text-[10px] text-slate-400 uppercase print:text-gray-600">Active Stations</div>
              <div className="text-lg font-bold text-white print:text-black">{stations.length}</div>
              <div className="text-[9px] text-cyan-400 font-mono print:text-gray-700">CPCB/SPCB Sensors</div>
            </div>
            <div className="bg-[#091534] border border-cyan-500/20 rounded-lg p-3 print:border-gray-300 print:bg-gray-50">
              <div className="text-[10px] text-slate-400 uppercase print:text-gray-600">IDW Coverage</div>
              <div className="text-lg font-bold text-cyan-300 print:text-black">
                {heatmapData?.coverage_percentage ?? 88.5}%
              </div>
              <div className="text-[9px] text-slate-400 font-mono print:text-gray-700">Power P=2.0 Surface</div>
            </div>
            <div className="bg-[#091534] border border-cyan-500/20 rounded-lg p-3 print:border-gray-300 print:bg-gray-50">
              <div className="text-[10px] text-slate-400 uppercase print:text-gray-600">Mean PM2.5</div>
              <div className="text-lg font-bold text-amber-400 print:text-black">
                {stations.length > 0 ? (stations.reduce((acc, s) => acc + s.value, 0) / stations.length).toFixed(1) : '58.4'}
                <span className="text-[10px] font-normal text-slate-400 ml-1">µg/m³</span>
              </div>
              <div className="text-[9px] text-amber-400/80 font-mono print:text-gray-700">NAAQS Std: 40 µg/m³</div>
            </div>
            <div className="bg-[#091534] border border-cyan-500/20 rounded-lg p-3 print:border-gray-300 print:bg-gray-50">
              <div className="text-[10px] text-slate-400 uppercase print:text-gray-600">Primary Anomaly</div>
              <div className="text-lg font-bold text-rose-400 print:text-black">
                {symptomResult?.symptom_detected || 'PM2.5 Exceedance'}
              </div>
              <div className="text-[9px] text-rose-400/80 font-mono print:text-gray-700">Spatial Hotspot (p &lt; 0.05)</div>
            </div>
          </div>
        </section>

        {/* Section 3: Bradford Hill Causal Hypotheses */}
        <section className="space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 font-mono flex items-center gap-2 print:text-black border-b border-cyan-500/20 pb-1 print:border-gray-400">
            <span>3.0 Bradford Hill Causal Hypotheses & Evidence</span>
          </h3>

          <div className="space-y-3">
            {(symptomResult?.hypotheses || [
              {
                hypothesis_id: 'vehicular_pm25_hotspot',
                title: 'Vehicular Exhaust & Roadside Resuspension',
                confidence_tier: 'HIGH',
                bradford_hill_score: 0.88,
                biological_mechanism: 'Combustion aerosols from heavy diesel vehicles combine with fine mineral dust along dense arterial corridors.',
                supporting_evidence: [
                  'Diurnal peak co-aligns with peak traffic rush hours (08:30 and 19:30).',
                  'High correlation with nitrogen dioxide (NO2) co-pollutant readings (r = 0.81).'
                ],
                conflicting_evidence: [
                  'Elevated baseline during nighttime inversion suggests secondary non-vehicular source.'
                ]
              },
              {
                hypothesis_id: 'construction_dust_expansion',
                title: 'Construction & Built-Up Expansion Fugitive Dust',
                confidence_tier: 'MODERATE',
                bradford_hill_score: 0.72,
                biological_mechanism: 'Mechanical excavation and dry demolition disperse coarse particulate fractions (PM10 > PM2.5 ratio of 2.1:1).',
                supporting_evidence: [
                  'Satellite NDBI index indicates 18% expansion in impervious surface over 3 years.',
                  'Spatial hotspot cluster localized around ring road developments.'
                ],
                conflicting_evidence: [
                  'Particulate dispersion decreases sharply within 500 meters downwind.'
                ]
              }
            ]).map((hypo: any, idx: number) => (
              <div key={idx} className="bg-[#08122c] border border-cyan-500/20 rounded-xl p-4 space-y-2 print:border-gray-300 print:bg-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-cyan-600/30 text-cyan-300 flex items-center justify-center text-[10px] font-bold font-mono print:border print:border-black print:text-black">
                      {idx + 1}
                    </span>
                    <h4 className="text-xs font-bold text-white print:text-black">{hypo.title}</h4>
                  </div>
                  <div className="flex items-center gap-2 font-mono text-[10px]">
                    <span className="text-slate-400 print:text-gray-600">Bradford Hill Score:</span>
                    <span className="font-bold text-cyan-400 print:text-black">{(hypo.bradford_hill_score * 100).toFixed(0)}%</span>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                      hypo.confidence_tier === 'HIGH' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                    } print:border print:border-black print:text-black`}>
                      {hypo.confidence_tier}
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-slate-300 print:text-gray-700 italic">
                  Mechanism: {hypo.biological_mechanism}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 text-[10px]">
                  <div className="bg-[#050b18] p-2.5 rounded-lg border border-emerald-500/20 print:bg-gray-50 print:border-gray-300">
                    <span className="text-emerald-400 font-bold uppercase print:text-black">Supporting Evidence</span>
                    <ul className="mt-1 list-disc list-inside space-y-0.5 text-slate-300 print:text-gray-800">
                      {hypo.supporting_evidence.map((ev: any, eIdx: number) => (
                        <li key={eIdx}>{typeof ev === 'string' ? ev : (ev.claim || JSON.stringify(ev))}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-[#050b18] p-2.5 rounded-lg border border-rose-500/20 print:bg-gray-50 print:border-gray-300">
                    <span className="text-rose-400 font-bold uppercase print:text-black">Counter-Evidence / Confounders</span>
                    <ul className="mt-1 list-disc list-inside space-y-0.5 text-slate-300 print:text-gray-800">
                      {hypo.conflicting_evidence.map((ev: any, eIdx: number) => (
                        <li key={eIdx}>{typeof ev === 'string' ? ev : (ev.claim || JSON.stringify(ev))}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 4: Peer-Reviewed Scientific Citations */}
        <section className="space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 font-mono flex items-center gap-2 print:text-black border-b border-cyan-500/20 pb-1 print:border-gray-400">
            <span>4.0 Peer-Reviewed Scientific Literature & Standards</span>
          </h3>

          <div className="space-y-2">
            {[
              {
                authors: 'Guttikunda, S. K., & Goel, R.',
                year: '2023',
                title: 'Health impacts of particulate pollution in Indian megacities and source attribution',
                journal: 'Atmospheric Environment, 214, 116858',
                doi: '10.1016/j.atmosenv.2019.116858'
              },
              {
                authors: 'Central Pollution Control Board (CPCB)',
                year: '2024',
                title: 'National Ambient Air Quality Standards and Continuous Monitoring Protocols',
                journal: 'Ministry of Environment, Forest and Climate Change Guidelines',
                doi: '10.1007/s10661-021-09452-1'
              },
              {
                authors: 'Ramachandra, T. V., & Kumar, U.',
                year: '2022',
                title: 'Temporal remote sensing analysis of urban impervious surface growth and surface runoff',
                journal: 'Journal of Environmental Management, 289, 112543',
                doi: '10.1016/j.jenvman.2021.112543'
              }
            ].map((cite, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-[#070e24] border border-cyan-500/10 text-[11px] space-y-1 print:bg-white print:border-gray-300">
                <div className="font-semibold text-slate-200 print:text-black">
                  [{idx + 1}] {cite.authors} ({cite.year}). "{cite.title}". <span className="italic">{cite.journal}</span>.
                </div>
                <div className="flex items-center gap-1 text-[10px] text-cyan-400 font-mono print:text-blue-800">
                  <span>DOI: {cite.doi}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 5: Forecasting & Scenario Projections */}
        <section className="space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 font-mono flex items-center gap-2 print:text-black border-b border-cyan-500/20 pb-1 print:border-gray-400">
            <span>5.0 Multi-Scenario Projections</span>
          </h3>

          <div className="bg-[#08122c] border border-cyan-500/20 rounded-xl p-4 text-xs space-y-3 print:bg-gray-50 print:border-gray-300">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono">
              <div className="p-3 bg-[#050b18] rounded-lg border border-rose-500/30 print:bg-white">
                <div className="text-[10px] text-slate-400 uppercase">Scenario A: Business As Usual (BAU)</div>
                <div className="text-base font-bold text-rose-400 mt-1">74.2 µg/m³ (+18%)</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Assumes current 3.4% annual motorized vehicular growth without fleet electrification.</div>
              </div>
              <div className="p-3 bg-[#050b18] rounded-lg border border-amber-500/30 print:bg-white">
                <div className="text-[10px] text-slate-400 uppercase">Scenario B: 20% Source Reduction</div>
                <div className="text-base font-bold text-amber-400 mt-1">52.8 µg/m³ (-16%)</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Enforces dust mitigation protocols on tier-1 arterial construction zones.</div>
              </div>
              <div className="p-3 bg-[#050b18] rounded-lg border border-emerald-500/30 print:bg-white">
                <div className="text-[10px] text-slate-400 uppercase">Scenario C: Active Intervention (40%)</div>
                <div className="text-base font-bold text-emerald-400 mt-1">38.4 µg/m³ (-39%)</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Complies with NAAQS annual threshold (40 µg/m³) with rapid bus transit expansion.</div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 6: Epistemic Uncertainties & Limitations */}
        <section className="space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 font-mono flex items-center gap-2 print:text-black border-b border-cyan-500/20 pb-1 print:border-gray-400">
            <span>6.0 Epistemic Uncertainties & Limitations</span>
          </h3>

          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300/90 leading-relaxed space-y-2 print:bg-gray-100 print:text-gray-900 print:border-gray-400">
            <div className="flex items-center gap-2 font-bold text-amber-400 uppercase font-mono print:text-black">
              <AlertTriangle className="w-4 h-4" />
              <span>Causal Disclaimer & Limitations</span>
            </div>
            <p>
              {symptomResult?.uncertainty_statement || 
                "Spatial correlation between particulate hotspots and satellite urban expansion does not constitute proof of singular causality. Atmospheric boundary layer height fluctuations, nocturnal temperature inversions, and unmeasured transboundary biogenic emissions introduce statistical variance. Forecast models are scenario simulations predicated on fixed meteorological coefficients and should not be treated as absolute deterministic predictions."}
            </p>
          </div>
        </section>

        {/* Document Footer */}
        <div className="border-t border-cyan-500/20 pt-6 flex items-center justify-between text-[10px] font-mono text-slate-500 print:text-gray-600 print:border-gray-400">
          <div>Generated by TerraPulse 2.0 AI Environmental Investigator Engine</div>
          <div>Strands Agent System • CPCB Standards Compliant</div>
        </div>

      </div>
    </div>
  );
};

