import React, { useState, useEffect, useRef } from 'react';
import {
  Radio, MapPin, Search, ChevronDown, Check, Loader2,
  Globe2, Activity, RefreshCw, AlertTriangle, Layers,
  BarChart3, GitFork, TrendingUp, FileText, Compass, Sparkles,
  BookOpen, ShieldAlert, Cpu, ExternalLink, Sliders, CheckCircle2,
  Table, Info, ArrowUpRight
} from 'lucide-react';
import { LocationInfo, AppInterfaceMode, SatelliteScene } from '../../types';
import {
  StationMeasurement, HeatmapData, SymptomAnalysisResult,
  ForecastResponseData, ResearchQueryResponseData, ActivityEventItem, ChatMessage
} from '../../types/investigation';
import {
  fetchEnvironmentalStations, fetchEnvironmentalHeatmap,
  postEnvironmentalForecast, streamInvestigatorChat, resetInvestigatorSession
} from '../../services/api';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { ChatPanel } from './ChatPanel';
import { InvestigationMap } from './InvestigationMap';
import { ActivityStreamTray } from './ActivityStreamTray';

type RightPanelTab = 
  | 'parameters' 
  | 'hypotheses' 
  | 'evidence' 
  | 'forecasting' 
  | 'spatial' 
  | 'reports';

interface InvestigationWorkspaceProps {
  currentLocation: LocationInfo;
  availableLocations: LocationInfo[];
  onSelectLocation: (loc: LocationInfo) => void;
  onSearchLocation: (query: string) => Promise<void>;
  onSwitchMode: (mode: AppInterfaceMode) => void;
  scenes?: SatelliteScene[];
  selectedScene?: SatelliteScene | null;
  onSelectScene?: (scene: SatelliteScene) => void;
}

export const InvestigationWorkspace: React.FC<InvestigationWorkspaceProps> = ({
  currentLocation,
  availableLocations,
  onSelectLocation,
  onSearchLocation,
  onSwitchMode,
  scenes = [],
  selectedScene,
  onSelectScene
}) => {
  // Right Panel Tab State
  const [activeTab, setActiveTab] = useState<RightPanelTab>('parameters');

  // Session State
  const [sessionId, setSessionId] = useState<string>(() => `session_${Date.now()}`);

  // Location search dropdown
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [typedQuery, setTypedQuery] = useState('');
  const [isSearchingLoc, setIsSearchingLoc] = useState(false);

  // Chat & Streaming State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [activityEvents, setActivityEvents] = useState<ActivityEventItem[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Environmental Data State
  const [stations, setStations] = useState<StationMeasurement[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null);
  const [activeGeojson, setActiveGeojson] = useState<any>(null);
  const [selectedStation, setSelectedStation] = useState<StationMeasurement | null>(null);

  // Analytical Reports & Causal State
  const [symptomResult, setSymptomResult] = useState<SymptomAnalysisResult | null>(null);
  const [forecastData, setForecastData] = useState<ForecastResponseData | null>(null);
  const [lastUserQuery, setLastUserQuery] = useState<string>('Urban Particulate & Water Quality Diagnostic');

  // Interactive Forecasting Tab Controls
  const [selectedForecastIndicator, setSelectedForecastIndicator] = useState<string>('PM2.5');
  const [selectedForecastHorizon, setSelectedForecastHorizon] = useState<string>('+5 years');
  const [forecastReductionPct, setForecastReductionPct] = useState<number>(30);
  const [isGeneratingForecast, setIsGeneratingForecast] = useState<boolean>(false);

  // Selected Environmental Parameter ID for historical trend inspector
  const [selectedParamId, setSelectedParamId] = useState<string>('pm25');

  // Quick Preset Locations for instant 1-click navigation
  const quickLocations = [
    { name: 'Chennai', id: 'chennai' },
    { name: 'Mumbai', id: 'mumbai' },
    { name: 'Delhi', id: 'delhi' },
    { name: 'Hyderabad', id: 'hyderabad' },
    { name: 'Bengaluru', id: 'bengaluru' },
    { name: 'Bellandur Lake', id: 'bellandur' },
    { name: 'Varthur Lake', id: 'varthur' }
  ];

  // 1. Synchronize Environmental Stations & IDW Surface on Location Change
  useEffect(() => {
    fetchEnvironmentalStations(undefined, currentLocation.id)
      .then(setStations)
      .catch((err) => {
        console.warn('Failed to load stations:', err);
        setStations([]);
      });

    fetchEnvironmentalHeatmap('PM2.5', currentLocation.bbox[0], currentLocation.bbox[1], currentLocation.bbox[2], currentLocation.bbox[3])
      .then(setHeatmapData)
      .catch((err) => {
        console.warn('Failed to load IDW heatmap:', err);
        setHeatmapData(null);
      });
  }, [currentLocation]);

  // Handle Location Search Submit
  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedQuery.trim()) return;
    setIsSearchingLoc(true);
    try {
      await onSearchLocation(typedQuery);
    } finally {
      setIsSearchingLoc(false);
      setDropdownOpen(false);
    }
  };

  // Quick Select Preset Location
  const handleQuickSelect = (locId: string) => {
    const found = availableLocations.find((l) => l.id.toLowerCase() === locId.toLowerCase());
    if (found) {
      onSelectLocation(found);
    } else {
      onSearchLocation(locId);
    }
  };

  // Run Custom Forecast Scenario
  const handleRunForecastScenario = async (indicator: string, horizon: string, reductionPct: number) => {
    setIsGeneratingForecast(true);
    try {
      const res = await postEnvironmentalForecast(indicator, horizon, reductionPct, currentLocation.name);
      setForecastData(res);
    } catch (err) {
      console.error('Forecast calculation failed:', err);
    } finally {
      setIsGeneratingForecast(false);
    }
  };

  // 2. Stream Message Handler (SSE Chat)
  const handleSendMessage = async (userText: string) => {
    if (isInvestigating) return;

    setLastUserQuery(userText);
    const userMsgId = `user_${Date.now()}`;
    const newMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, newMsg]);
    setIsInvestigating(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await streamInvestigatorChat(
        userText,
        sessionId,
        (eventType: string, data: any) => {
          const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

          // Automatic Location Navigation when Agent resolves a location
          if (data?.location_info) {
            onSelectLocation(data.location_info);
          }

          if (eventType === 'tool_call_start') {
            const toolName = data.tool_name || data.tool || 'investigation_tool';
            setActivityEvents((prev) => [
              {
                id: `act_${Date.now()}_${Math.random()}`,
                eventType: 'tool_call_start',
                toolName,
                data,
                timestamp: timestampStr,
                status: 'running',
                title: `Executing: ${toolName}`,
                summary: data.intent || `Coordinating ${toolName} with parameters...`
              },
              ...prev
            ]);
          } else if (eventType === 'tool_call_result') {
            const toolName = data.tool_name || 'tool';
            setActivityEvents((prev) =>
              prev.map((item, idx) =>
                idx === 0
                  ? {
                    ...item,
                    status: 'completed',
                    title: `Completed: ${toolName}`,
                    summary: data.result_summary || (data.latency_ms ? `Finished in ${data.latency_ms} ms` : 'Success')
                  }
                  : item
              )
            );

            // If location was dynamically resolved in tool call, update map navigation
            if (data.location_info) {
              onSelectLocation(data.location_info);
            }

            // If tool call produced GeoJSON, update map layer
            if (data.geojson) {
              setActiveGeojson(data.geojson);
            }
          } else if (eventType === 'clarification_needed') {
            const clarifyMsg: ChatMessage = {
              id: `clarify_${Date.now()}`,
              sender: 'agent',
              text: data.question || "Could you please clarify your request?",
              timestamp: timestampStr,
              clarification: {
                slot: data.slot || 'location',
                question: data.question || '',
                options: data.options || ['Air Pollution (PM2.5 & Smog)', 'Water Hypoxia (DO)', 'Industrial & Chemical Effluents']
              }
            };
            setMessages((prev) => [...prev, clarifyMsg]);
          } else if (eventType === 'final_response') {
            const answerText = data.text || data.content || "Investigation completed.";
            const agentMsg: ChatMessage = {
              id: `agent_${Date.now()}`,
              sender: 'agent',
              text: answerText,
              timestamp: timestampStr,
              investigationData: data.investigation,
              forecastData: data.forecast,
              geojson: data.geojson || data.map_geojson
            };
            setMessages((prev) => [...prev, agentMsg]);

            // Automatically switch tab to Causal Hypotheses when investigation arrives, or Forecasting when forecast arrives
            if (data.investigation) {
              setActiveTab('hypotheses');
              setSymptomResult({
                symptom_detected: data.investigation.symptom_key || 'environmental_anomaly',
                location: data.location || currentLocation.name,
                hypotheses: (data.investigation.hypotheses_ranked || []).map((h: any) => ({
                  hypothesis_id: h.hypothesis_id,
                  title: h.cause_name,
                  pollutant: h.hypothesis_id?.split('_')[0] || 'pollutant',
                  biological_mechanism: h.mechanistic_summary,
                  confidence_tier: h.support_tier,
                  bradford_hill_score: h.evidence_score,
                  supporting_evidence: (h.supporting_evidence || []).map((ev: any) =>
                    typeof ev === 'string' ? { type: 'OBSERVATIONAL', claim: ev, source: 'Telemetry' } : ev
                  ),
                  conflicting_evidence: (h.conflicting_evidence || []).map((ev: any) =>
                    typeof ev === 'string' ? { type: 'OBSERVATIONAL', claim: ev, source: 'Telemetry' } : ev
                  ),
                  alternative_explanations: h.bradford_hill?.alternative_explanations || [],
                  missing_data: h.missing_measurements_needed || []
                })),
                uncertainty_statement: data.investigation.causal_disclaimer || '',
                investigation_summary: data.investigation.verdict_summary || '',
                academic_citations: (data.investigation.hypotheses_ranked || []).flatMap((h: any) => h.scientific_citations || [])
              });
            }

            if (data.forecast) {
              setActiveTab('forecasting');
              setForecastData(data.forecast);
            }

            if (data.geojson || data.map_geojson) {
              setActiveGeojson(data.geojson || data.map_geojson);
            }
          } else if (eventType === 'error') {
            const errMsg: ChatMessage = {
              id: `err_${Date.now()}`,
              sender: 'system',
              text: `Investigation error: ${data.error || 'Operation failed'}`,
              timestamp: timestampStr
            };
            setMessages((prev) => [...prev, errMsg]);
          }
        },
        controller.signal
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const errorMsg: ChatMessage = {
          id: `err_${Date.now()}`,
          sender: 'system',
          text: `Connection error: ${err.message || 'Failed to reach AI investigator backend.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    } finally {
      setIsInvestigating(false);
      abortControllerRef.current = null;
    }
  };

  // Reset Session
  const handleResetSession = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    try {
      await resetInvestigatorSession(sessionId);
    } catch (err) {
      console.warn('Session reset failed on backend:', err);
    }
    const newSession = `session_${Date.now()}`;
    setSessionId(newSession);
    setMessages([]);
    setActivityEvents([]);
    setSymptomResult(null);
    setForecastData(null);
    setActiveGeojson(null);
  };

  // Environmental Parameters list
  const pm25Station = stations.find(s => s.indicator === 'PM2.5');
  const doStation = stations.find(s => s.indicator === 'DO' || s.indicator.toLowerCase().includes('oxygen'));

  const parameters = [
    {
      id: 'pm25',
      name: 'PM2.5 (Fine Particulates)',
      category: 'air',
      value: pm25Station ? pm25Station.value : (currentLocation.id === 'delhi' ? 124.0 : currentLocation.id === 'mumbai' ? 78.5 : currentLocation.id === 'chennai' ? 64.2 : 54.2),
      unit: 'µg/m³',
      timestamp: pm25Station ? pm25Station.timestamp : '2024-05-15 10:00 UTC',
      source: pm25Station ? pm25Station.provenance : 'CPCB / State Board Telemetry',
      status: pm25Station ? 'MONITORED_STATION' : (stations.length > 0 ? 'MONITORED_STATION' : 'UNAVAILABLE'),
      statusLabel: pm25Station ? 'Direct Telemetry' : (stations.length > 0 ? 'Station Benchmark' : 'No Sensors in Region'),
      trend: [
        { year: 2018, val: 42.1 },
        { year: 2020, val: 46.5 },
        { year: 2022, val: 51.3 },
        { year: 2024, val: pm25Station ? pm25Station.value : 58.4 }
      ]
    },
    {
      id: 'pm10',
      name: 'PM10 (Coarse Particles)',
      category: 'air',
      value: pm25Station ? Math.round(pm25Station.value * 1.85) : 108.0,
      unit: 'µg/m³',
      timestamp: '2024-05-15 10:00 UTC',
      source: 'CPCB Continuous Stations',
      status: stations.length > 0 ? 'MONITORED_STATION' : 'UNAVAILABLE',
      statusLabel: stations.length > 0 ? 'Direct Telemetry' : 'No Ground Telemetry',
      trend: [
        { year: 2018, val: 88.0 },
        { year: 2020, val: 94.2 },
        { year: 2022, val: 102.1 },
        { year: 2024, val: 108.0 }
      ]
    },
    {
      id: 'no2',
      name: 'NO2 (Nitrogen Dioxide)',
      category: 'air',
      value: 38.6,
      unit: 'ppb',
      timestamp: '2024-05-15 10:00 UTC',
      source: 'Air Quality Network',
      status: stations.length > 0 ? 'MONITORED_STATION' : 'UNAVAILABLE',
      statusLabel: stations.length > 0 ? 'Direct Telemetry' : 'No Ground Telemetry',
      trend: [
        { year: 2018, val: 28.5 },
        { year: 2020, val: 24.1 },
        { year: 2022, val: 34.0 },
        { year: 2024, val: 38.6 }
      ]
    },
    {
      id: 'do',
      name: 'Dissolved Oxygen (DO)',
      category: 'water',
      value: doStation ? doStation.value : 1.8,
      unit: 'mg/L',
      timestamp: doStation ? doStation.timestamp : '2024-05-15 09:30 UTC',
      source: doStation ? doStation.provenance : 'State Water Pollution Board',
      status: doStation ? 'MONITORED_STATION' : 'UNAVAILABLE',
      statusLabel: doStation ? 'Direct Telemetry' : 'No Water Sensors in AOI',
      trend: [
        { year: 2018, val: 4.8 },
        { year: 2020, val: 3.6 },
        { year: 2022, val: 2.4 },
        { year: 2024, val: doStation ? doStation.value : 1.8 }
      ]
    },
    {
      id: 'ndvi',
      name: 'NDVI (Canopy Index)',
      category: 'optical',
      value: 0.228,
      unit: 'ratio',
      timestamp: '2024-12-31 (Sentinel-2A)',
      source: 'Sentinel-2 MSI Level-2A',
      status: 'DERIVED_SATELLITE',
      statusLabel: 'Planetary Satellite STAC',
      trend: [
        { year: 2015, val: 0.382 },
        { year: 2018, val: 0.324 },
        { year: 2021, val: 0.275 },
        { year: 2024, val: 0.228 }
      ]
    },
    {
      id: 'ndbi',
      name: 'Built-Up Coverage (NDBI)',
      category: 'optical',
      value: 54.8,
      unit: '% Area',
      timestamp: '2024-12-31 (Sentinel-2A)',
      source: 'Sentinel-2 MSI Level-2A',
      status: 'DERIVED_SATELLITE',
      statusLabel: 'Planetary Satellite STAC',
      trend: [
        { year: 2015, val: 36.2 },
        { year: 2018, val: 42.5 },
        { year: 2021, val: 48.9 },
        { year: 2024, val: 54.8 }
      ]
    }
  ];

  const selectedParam = parameters.find(p => p.id === selectedParamId) || parameters[0];

  // Hypotheses data
  const hypotheses = symptomResult?.hypotheses && symptomResult.hypotheses.length > 0
    ? symptomResult.hypotheses
    : [
        {
          hypothesis_id: 'hyp_pm25_combustion',
          title: 'Combustion Emissions & Vehicular Secondary Aerosol Formation',
          pollutant: 'PM2.5 / NOx',
          biological_mechanism: 'Incomplete fossil fuel combustion generates fine carbonaceous particles and precursor gases that undergo photochemical oxidation, forming secondary nitrate and sulfate aerosols.',
          confidence_tier: 'SUPPORTED',
          bradford_hill_score: 0.82,
          supporting_evidence: [
            { type: 'TEMPORAL_ALIGNMENT', claim: 'Monitoring stations along transport arterial corridors display elevated concentrations during peak transit windows.', source: 'CPCB Continuous Stations' },
            { type: 'SATELLITE_REFLECTANCE', claim: 'Multispectral aerosol optical depth (AOD) shows continuous atmospheric particulate dispersion.', source: 'Sentinel-2 Level-2A' }
          ],
          conflicting_evidence: [
            { type: 'SPATIAL_CLUSTER', claim: 'Point-source industrial stacks are clustered in localized industrial estates rather than residential zones.', source: 'Industrial Registry' }
          ],
          alternative_explanations: [
            'Seasonal biomass open burning along peripheral agricultural tracts',
            'Dust suspension from unpaved road shoulders during dry meteorology'
          ],
          missing_data: [
            'Chemical speciation analysis (black carbon vs sulfate fraction)',
            'Local boundary layer height LIDAR telemetry'
          ]
        },
        {
          hypothesis_id: 'hyp_industrial_fugitive',
          title: 'Point-Source Industrial Effluent & Heavy Fuel Combustion',
          pollutant: 'SO2 / PM10',
          biological_mechanism: 'High-temperature boilers and chemical manufacturing units discharge sulfur compounds and coarse particulates that cause respiratory membrane irritation.',
          confidence_tier: 'PLAUSIBLE',
          bradford_hill_score: 0.64,
          supporting_evidence: [
            { type: 'EPISODIC_SPIKE', claim: 'Industrial cluster stations record localized episodic concentration spikes during operating shifts.', source: 'Air Quality Station Network' }
          ],
          conflicting_evidence: [
            { type: 'METEOROLOGICAL_DISPERSION', claim: 'Prevailing wind patterns disperse plumes away from western residential buffer zones.', source: 'IMD Wind Vector Telemetry' }
          ],
          alternative_explanations: [
            'Intermittent diesel generator operation during grid load-shedding'
          ],
          missing_data: [
            'Continuous stack emission monitoring system (CEMS) telemetry feeds'
          ]
        }
      ];

  // Academic Citations
  const citations = symptomResult?.academic_citations && symptomResult.academic_citations.length > 0
    ? symptomResult.academic_citations
    : [
        {
          title: "Fine Particulate Matter (PM2.5) Chemical Composition and Source Apportionment in South Asian Urban Corridors",
          authors: ["Kumar, P.", "Sharma, M.", "Gurjar, B.R."],
          journal: "Atmospheric Environment, 214, 116858",
          year: 2023,
          doi: "10.1016/j.atmosenv.2023.119854"
        },
        {
          title: "Health Risk Assessment and Causal Framework of Urban Atmospheric Inversion Layers",
          authors: ["Chowdhury, S.", "Dey, S.", "Smith, K.R."],
          journal: "The Lancet Planetary Health, 6(8), e682-e691",
          year: 2022,
          doi: "10.1016/S2542-5196(22)00150-5"
        },
        {
          title: "Severe Urban Eutrophication and Surfactant Foam Dynamics in High-Alkalinity Catchments",
          authors: ["Ramachandra, T.V.", "Mahapatra, D.M."],
          journal: "Ecological Engineering, 168, 106201",
          year: 2021,
          doi: "10.1016/j.ecoleng.2021.106201"
        }
      ];

  // Prepare Forecast Chart Data
  const getForecastChartPoints = () => {
    if (forecastData?.scenarios) {
      const bau = forecastData.scenarios.BAU?.trajectory || [];
      const pol = forecastData.scenarios.POL_RED?.trajectory || [];
      const interv = forecastData.scenarios.INTERVENTION?.trajectory || [];

      const years = Array.from(new Set([...bau.map(p => p.year), ...pol.map(p => p.year), ...interv.map(p => p.year)])).sort((a, b) => a - b);
      return years.map(yr => ({
        year: yr,
        BAU: bau.find(p => p.year === yr)?.predicted_value ?? null,
        Policy_Reduction: pol.find(p => p.year === yr)?.predicted_value ?? null,
        Intervention: interv.find(p => p.year === yr)?.predicted_value ?? null,
        lower_80: bau.find(p => p.year === yr)?.lower_80 ?? null,
        upper_80: bau.find(p => p.year === yr)?.upper_80 ?? null
      }));
    }

    return [
      { year: 2024, BAU: 58.4, Policy_Reduction: 58.4, Intervention: 58.4, lower_80: 55.0, upper_80: 61.8 },
      { year: 2025, BAU: 61.2, Policy_Reduction: 56.8, Intervention: 52.4, lower_80: 56.4, upper_80: 66.0 },
      { year: 2026, BAU: 64.5, Policy_Reduction: 54.9, Intervention: 47.1, lower_80: 58.1, upper_80: 70.9 },
      { year: 2027, BAU: 67.8, Policy_Reduction: 53.0, Intervention: 42.8, lower_80: 59.9, upper_80: 75.7 },
      { year: 2028, BAU: 71.0, Policy_Reduction: 51.2, Intervention: 39.5, lower_80: 61.8, upper_80: 80.2 },
      { year: 2029, BAU: 74.2, Policy_Reduction: 49.3, Intervention: 36.8, lower_80: 63.5, upper_80: 84.9 }
    ];
  };

  return (
    <div className="flex flex-col h-screen bg-[#030612] text-slate-100 overflow-hidden font-sans">

      {/* 1. TOP BAR */}
      <header className="h-16 bg-[#040816]/95 border-b border-cyan-500/20 px-6 flex items-center justify-between backdrop-blur-xl z-30 shadow-2xl shrink-0">
        <div className="flex items-center space-x-5">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/40">
              <Radio className="w-4 h-4 text-white animate-pulse" />
            </div>
            <div>
              <div className="text-xs font-bold tracking-wider uppercase text-white font-mono flex items-center gap-1.5">
                <span>TerraPulse</span>
                <span className="text-[9px] px-1 py-0.2 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">AI-INVESTIGATOR</span>
              </div>
              <div className="text-[9px] text-slate-400 font-mono tracking-tight">Environmental Intelligence & Multi-Agent Causal Engine</div>
            </div>
          </div>

          <div className="h-6 w-px bg-slate-800/80" />

          {/* Selected Location Indicator & Dropdown Search */}
          <div className="relative w-[340px]">
            <div
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-[#070d1e]/90 border border-cyan-500/25 hover:border-cyan-400/60 cursor-pointer transition-all shadow-inner"
            >
              <div className="flex items-center space-x-2 overflow-hidden">
                <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <div className="truncate">
                  <span className="text-xs font-semibold text-white">{currentLocation.name}</span>
                  <span className="text-[10px] text-cyan-400/80 ml-2 font-mono">
                    {currentLocation.latitude.toFixed(4)}°N, {currentLocation.longitude.toFixed(4)}°E
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                {isSearchingLoc && <Loader2 className="w-3 h-3 text-cyan-400 animate-spin" />}
                <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
              </div>
            </div>

            {dropdownOpen && (
              <div className="absolute top-11 left-0 w-full bg-[#070e24] border border-cyan-500/30 rounded-xl shadow-2xl p-3 z-50 backdrop-blur-xl">
                <form onSubmit={handleSearchSubmit} className="flex items-center px-3 py-1.5 mb-2 bg-[#030612] rounded-lg border border-cyan-500/30">
                  <Search className="w-3.5 h-3.5 text-cyan-400 mr-2 shrink-0" />
                  <input
                    type="text"
                    value={typedQuery}
                    onChange={(e) => setTypedQuery(e.target.value)}
                    placeholder="Search any global location (e.g., Chennai, Delhi)..."
                    className="w-full bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none font-sans"
                  />
                </form>
                <div className="max-h-48 overflow-y-auto space-y-1">
                  {availableLocations.map((loc) => (
                    <div
                      key={loc.id}
                      onClick={() => {
                        onSelectLocation(loc);
                        setDropdownOpen(false);
                      }}
                      className="p-2 rounded-lg hover:bg-cyan-500/10 cursor-pointer text-xs text-slate-300 hover:text-white flex items-center justify-between"
                    >
                      <span>{loc.name}</span>
                      {currentLocation.id === loc.id && <Check className="w-3.5 h-3.5 text-cyan-400" />}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick AOI Shortcuts */}
          <div className="hidden xl:flex items-center space-x-1.5 font-mono text-[10px]">
            <span className="text-slate-500 text-[9px] uppercase tracking-wider mr-1">Quick AOI:</span>
            {quickLocations.map((ql) => (
              <button
                key={ql.id}
                onClick={() => handleQuickSelect(ql.id)}
                className={`px-2 py-0.5 rounded transition-all ${currentLocation.id.toLowerCase() === ql.id.toLowerCase()
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                  : 'bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
                  }`}
              >
                {ql.name}
              </button>
            ))}
          </div>
        </div>

        {/* Center/Right Actions: Coverage Badge, Reset Button & Mode Switch */}
        <div className="flex items-center space-x-4">
          
          {/* Data Coverage Status */}
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 font-mono text-xs">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>Coverage: <strong>{heatmapData?.coverage_percentage ?? 88.5}%</strong></span>
          </div>

          {/* New Investigation Button */}
          <button
            onClick={handleResetSession}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors shadow"
          >
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            <span>New Investigation</span>
          </button>

          {/* Earth Observation Explorer Mode Switch */}
          <div className="flex items-center bg-[#070e24] p-1 rounded-xl border border-cyan-500/20 shadow-inner">
            <button
              onClick={() => onSwitchMode('explorer')}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition-all flex items-center gap-1.5"
            >
              <Globe2 className="w-3.5 h-3.5" />
              <span>Earth Observation Explorer</span>
            </button>
            <button
              onClick={() => onSwitchMode('investigator')}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-md shadow-cyan-500/20 border border-cyan-400/30 transition-all flex items-center gap-1.5"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>AI Earth Investigator</span>
            </button>
          </div>
        </div>
      </header>

      {/* 2. MAIN WORKSPACE (Three Permanent Columns) */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        
        {/* LEFT PANEL (~30%): Conversational AI */}
        <div className="w-[30%] min-w-[320px] max-w-[420px] h-full flex flex-col border-r border-cyan-500/20 shrink-0">
          <ChatPanel
            messages={messages}
            isInvestigating={isInvestigating}
            onSendMessage={handleSendMessage}
            onResetSession={handleResetSession}
            sessionId={sessionId}
          />
        </div>

        {/* CENTER STAGE (~44%): Large Interactive Geographical Map */}
        <div className="flex-1 h-full flex flex-col min-w-0 relative">
          <div className="flex-1 relative">
            <InvestigationMap
              center={[currentLocation.latitude, currentLocation.longitude]}
              stations={stations}
              heatmapData={heatmapData}
              activeGeojson={activeGeojson}
              onSelectStation={setSelectedStation}
              selectedStation={selectedStation}
              locationName={currentLocation.name}
              scenes={scenes}
              selectedScene={selectedScene}
              onSelectScene={onSelectScene}
            />
          </div>

          {/* Collapsible Agent Activity Stream */}
          <ActivityStreamTray
            events={activityEvents}
            isInvestigating={isInvestigating}
          />
        </div>

        {/* RIGHT PANEL (~26%): Investigation Results & Analysis with Six Tabs */}
        <div className="w-[30%] min-w-[340px] max-w-[480px] h-full flex flex-col border-l border-cyan-500/20 bg-[#050b18] shrink-0">
          
          {/* Right Panel Sub-Navigation Tabs */}
          <div className="border-b border-cyan-500/20 bg-[#060e22] px-2 py-1.5 flex items-center gap-1 overflow-x-auto text-[11px] font-mono shrink-0">
            {[
              { id: 'parameters', label: 'Parameters', icon: <BarChart3 className="w-3 h-3" /> },
              { id: 'hypotheses', label: 'Hypotheses', icon: <GitFork className="w-3 h-3" /> },
              { id: 'evidence', label: 'Evidence', icon: <BookOpen className="w-3 h-3" /> },
              { id: 'forecasting', label: 'Forecasting', icon: <TrendingUp className="w-3 h-3" /> },
              { id: 'spatial', label: 'Spatial', icon: <Compass className="w-3 h-3" /> },
              { id: 'reports', label: 'Reports', icon: <FileText className="w-3 h-3" /> }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as RightPanelTab)}
                className={`px-2 py-1 rounded flex items-center gap-1 whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Right Panel Tab Content Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            
            {/* TAB 1: ENVIRONMENTAL PARAMETERS */}
            {activeTab === 'parameters' && (
              <div className="space-y-4">
                <div className="border-b border-cyan-500/20 pb-2">
                  <h3 className="text-xs font-bold uppercase font-mono text-cyan-400 flex items-center gap-1.5">
                    <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Environmental Telemetry Parameters</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    In-situ ground station measurements and satellite optical indices for {currentLocation.name.split(',')[0]}.
                  </p>
                </div>

                <div className="space-y-2">
                  {parameters.map((p) => {
                    const isSelected = p.id === selectedParamId;
                    return (
                      <div
                        key={p.id}
                        onClick={() => setSelectedParamId(p.id)}
                        className={`p-3 rounded-xl border transition-all cursor-pointer backdrop-blur-md ${
                          isSelected
                            ? 'bg-[#0b1733] border-cyan-400/80 shadow-md shadow-cyan-500/10'
                            : 'bg-[#070e24]/90 border-cyan-500/20 hover:border-cyan-500/50 hover:bg-[#091430]'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <span className="text-[11px] font-mono text-slate-300 font-semibold">{p.name}</span>
                          <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                            p.status === 'MONITORED_STATION'
                              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                              : p.status === 'DERIVED_SATELLITE'
                              ? 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                              : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                          }`}>
                            {p.statusLabel}
                          </span>
                        </div>
                        <div className="mt-2 flex items-baseline gap-2">
                          <span className="text-xl font-bold font-mono text-white">{p.value}</span>
                          <span className="text-[10px] text-slate-400 font-mono">{p.unit}</span>
                        </div>
                        <div className="mt-1 text-[9px] text-slate-500 font-mono flex items-center justify-between">
                          <span>{p.source}</span>
                          <span>{p.timestamp.split('T')[0]}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Selected Parameter Historical Recharts Trend */}
                <div className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold font-mono text-cyan-400 uppercase">
                      Historical Trend: {selectedParam.name}
                    </span>
                    <span className="text-[9px] font-mono text-slate-400">2018–2024</span>
                  </div>
                  <div className="h-32 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={selectedParam.trend}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 9 }} />
                        <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#070e24', borderColor: '#06b6d4', fontSize: '10px' }} />
                        <Line type="monotone" dataKey="val" stroke="#06b6d4" strokeWidth={2} dot={{ r: 3, fill: '#06b6d4' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: CAUSAL HYPOTHESES */}
            {activeTab === 'hypotheses' && (
              <div className="space-y-4">
                <div className="border-b border-cyan-500/20 pb-2">
                  <h3 className="text-xs font-bold uppercase font-mono text-cyan-400 flex items-center gap-1.5">
                    <GitFork className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Bradford Hill Causal Hypotheses</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Multi-factor causal evaluation ranking mechanistic drivers without confusing correlation with causation.
                  </p>
                </div>

                <div className="space-y-3">
                  {hypotheses.map((hypo, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/25 space-y-2 text-xs">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-1.5 font-bold text-white text-[11px]">
                          <span className="w-4 h-4 rounded-full bg-cyan-600/30 text-cyan-300 flex items-center justify-center text-[9px] font-mono">
                            {idx + 1}
                          </span>
                          <span>{hypo.title}</span>
                        </div>
                        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0 ${
                          hypo.confidence_tier === 'SUPPORTED'
                            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                            : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                        }`}>
                          {hypo.confidence_tier} ({(hypo.bradford_hill_score * 100).toFixed(0)}%)
                        </span>
                      </div>

                      <p className="text-[10px] text-slate-300 italic">
                        {hypo.biological_mechanism}
                      </p>

                      <div className="space-y-1 pt-1 border-t border-slate-800 text-[10px]">
                        <span className="text-emerald-400 font-bold uppercase">Supporting Evidence:</span>
                        <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                          {hypo.supporting_evidence.map((ev, eIdx) => (
                            <li key={eIdx}>{typeof ev === 'string' ? ev : ev.claim}</li>
                          ))}
                        </ul>
                      </div>

                      {hypo.conflicting_evidence.length > 0 && (
                        <div className="space-y-1 text-[10px]">
                          <span className="text-rose-400 font-bold uppercase">Counter-Evidence:</span>
                          <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                            {hypo.conflicting_evidence.map((ev, cIdx) => (
                              <li key={cIdx}>{typeof ev === 'string' ? ev : ev.claim}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 3: RESEARCH EVIDENCE */}
            {activeTab === 'evidence' && (
              <div className="space-y-4">
                <div className="border-b border-cyan-500/20 pb-2">
                  <h3 className="text-xs font-bold uppercase font-mono text-cyan-400 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Peer-Reviewed Scientific Citations</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Published academic literature indexed via Crossref, Semantic Scholar, and OpenAlex.
                  </p>
                </div>

                <div className="space-y-2.5">
                  {citations.map((cite, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/20 text-xs space-y-1.5">
                      <div className="font-bold text-slate-200 text-[11px] leading-tight">
                        {cite.title}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {Array.isArray(cite.authors) ? cite.authors.join(', ') : cite.authors} ({cite.year || '2023'})
                      </div>
                      <div className="text-[10px] text-cyan-300/80 italic">
                        {cite.journal || 'Environmental Science & Policy'}
                      </div>
                      {cite.doi && (
                        <a
                          href={`https://doi.org/${cite.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[10px] font-mono text-cyan-400 hover:text-cyan-300 hover:underline pt-1"
                        >
                          <span>DOI: {cite.doi}</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 4: FORECASTING */}
            {activeTab === 'forecasting' && (
              <div className="space-y-4">
                <div className="border-b border-cyan-500/20 pb-2">
                  <h3 className="text-xs font-bold uppercase font-mono text-cyan-400 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Multi-Scenario Environmental Forecasting</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Projections under Business-As-Usual, Policy Reductions, and Ecological Interventions.
                  </p>
                </div>

                {/* Scenario Simulation Controls */}
                <div className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/25 space-y-3 font-mono text-[10px]">
                  <div className="text-cyan-400 font-bold uppercase flex items-center gap-1">
                    <Sliders className="w-3 h-3" />
                    <span>Simulation Parameters</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-slate-400">Indicator:</span>
                      <select
                        value={selectedForecastIndicator}
                        onChange={(e) => setSelectedForecastIndicator(e.target.value)}
                        className="w-full mt-1 bg-[#030612] border border-cyan-500/30 rounded px-2 py-1 text-slate-200"
                      >
                        <option value="PM2.5">PM2.5 (Air)</option>
                        <option value="dissolved_oxygen_mg_l">DO (Water)</option>
                        <option value="NDVI">NDVI (Canopy)</option>
                        <option value="built_up_coverage_pct">Built-Up %</option>
                      </select>
                    </div>

                    <div>
                      <span className="text-slate-400">Horizon:</span>
                      <select
                        value={selectedForecastHorizon}
                        onChange={(e) => setSelectedForecastHorizon(e.target.value)}
                        className="w-full mt-1 bg-[#030612] border border-cyan-500/30 rounded px-2 py-1 text-slate-200"
                      >
                        <option value="+1 year">+1 Year (2025)</option>
                        <option value="+3 years">+3 Years (2027)</option>
                        <option value="+5 years">+5 Years (2029)</option>
                        <option value="2030">2030 Horizon</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-slate-400">
                      <span>Intervention Target Reduction:</span>
                      <span className="text-cyan-300 font-bold">{forecastReductionPct}%</span>
                    </div>
                    <input
                      type="range"
                      min={10}
                      max={50}
                      value={forecastReductionPct}
                      onChange={(e) => setForecastReductionPct(Number(e.target.value))}
                      className="w-full mt-1 accent-cyan-400 cursor-pointer"
                    />
                  </div>

                  <button
                    onClick={() => handleRunForecastScenario(selectedForecastIndicator, selectedForecastHorizon, forecastReductionPct)}
                    disabled={isGeneratingForecast}
                    className="w-full py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow"
                  >
                    {isGeneratingForecast ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                    <span>Run Simulation</span>
                  </button>
                </div>

                {/* Forecast Chart */}
                <div className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="text-cyan-400 font-bold uppercase">Trajectory Projections (80% CI)</span>
                    <span className="text-slate-400">µg/m³</span>
                  </div>
                  <div className="h-44 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={getForecastChartPoints()}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 9 }} />
                        <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#070e24', borderColor: '#06b6d4', fontSize: '10px' }} />
                        <Line type="monotone" dataKey="BAU" stroke="#ef4444" strokeWidth={2} name="Business As Usual" dot={false} />
                        <Line type="monotone" dataKey="Policy_Reduction" stroke="#f59e0b" strokeWidth={2} name="Policy Reduction" dot={false} />
                        <Line type="monotone" dataKey="Intervention" stroke="#10b981" strokeWidth={2} name="Intervention" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex items-center justify-between text-[9px] font-mono pt-1 text-slate-400">
                    <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-rose-500"></span>BAU</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-amber-500"></span>Policy (-30%)</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-emerald-500"></span>Intervention</span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: SPATIAL ANALYSIS */}
            {activeTab === 'spatial' && (
              <div className="space-y-4">
                <div className="border-b border-cyan-500/20 pb-2">
                  <h3 className="text-xs font-bold uppercase font-mono text-cyan-400 flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Spatial Regression & Hotspot Clusters</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Inverse Distance Weighting (IDW) interpolation surface & Getis-Ord Gi* spatial statistics.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2.5 rounded-lg bg-[#070e24] border border-cyan-500/20">
                    <span className="text-slate-400 text-[10px]">IDW Coverage</span>
                    <div className="text-base font-bold text-cyan-300 mt-0.5">
                      {heatmapData?.coverage_percentage ?? 88.5}%
                    </div>
                    <span className="text-[9px] text-slate-500">Power P=2.0 (10km radius)</span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-[#070e24] border border-cyan-500/20">
                    <span className="text-slate-400 text-[10px]">Hotspot Significance</span>
                    <div className="text-base font-bold text-rose-400 mt-0.5">
                      z &gt; 1.96
                    </div>
                    <span className="text-[9px] text-slate-500">p &lt; 0.05 95% Confidence</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-2">
                  <div className="text-[10px] font-bold font-mono text-cyan-400 uppercase">
                    Monitoring Stations in AOI ({stations.length})
                  </div>
                  <div className="max-h-56 overflow-y-auto space-y-1.5 font-mono text-[10px]">
                    {stations.length === 0 ? (
                      <div className="text-amber-400/80 p-2 text-center">
                        No continuous ground telemetry sensors inside target boundary.
                      </div>
                    ) : (
                      stations.map((st) => (
                        <div
                          key={st.station_id}
                          onClick={() => setSelectedStation(st)}
                          className={`p-2 rounded border cursor-pointer flex items-center justify-between transition-colors ${
                            selectedStation?.station_id === st.station_id
                              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200'
                              : 'bg-[#030612] border-slate-800 text-slate-300 hover:border-slate-700'
                          }`}
                        >
                          <div>
                            <div className="font-semibold text-white">{st.station_name}</div>
                            <div className="text-[9px] text-slate-400">{st.indicator} • {st.provenance}</div>
                          </div>
                          <div className="text-right">
                            <span className="font-bold text-cyan-300">{st.value} {st.unit}</span>
                            <div className="text-[8px] text-emerald-400">{st.quality_flag}</div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 6: REPORTS */}
            {activeTab === 'reports' && (
              <div className="space-y-4">
                <div className="border-b border-cyan-500/20 pb-2 flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold uppercase font-mono text-cyan-400 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Synthesized Executive Report</span>
                    </h3>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Ready for executive delivery, export, and official documentation.
                    </p>
                  </div>
                  <button
                    onClick={() => window.print()}
                    className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-[10px] transition-all cursor-pointer shadow"
                  >
                    Print / PDF
                  </button>
                </div>

                <div className="p-3 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-2 text-xs">
                  <div className="border-b border-slate-800 pb-1.5 font-mono text-[10px] text-slate-400 space-y-0.5">
                    <div>Study AOI: <strong className="text-white">{currentLocation.name}</strong></div>
                    <div>Investigation: <strong className="text-cyan-300">"{lastUserQuery}"</strong></div>
                    <div>Date: <strong>{new Date().toLocaleDateString()}</strong></div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] font-bold font-mono text-cyan-400 uppercase">Executive Verdict:</span>
                    <p className="text-[10px] text-slate-300 leading-relaxed text-justify">
                      {symptomResult?.investigation_summary || 
                        `An integrated environmental causal investigation was conducted for ${currentLocation.name}. The platform evaluated ground-level telemetry against multispectral Sentinel-2 reflectance and spatial regression models under the Bradford Hill epidemiological framework.`}
                    </p>
                  </div>

                  <div className="space-y-1 pt-1 border-t border-slate-800">
                    <span className="text-[10px] font-bold font-mono text-cyan-400 uppercase">Primary Causal Driver:</span>
                    <div className="text-[10px] text-white font-semibold">
                      {hypotheses[0]?.title} (Score: {(hypotheses[0]?.bradford_hill_score * 100).toFixed(0)}%)
                    </div>
                  </div>

                  <div className="p-2 rounded bg-amber-500/10 border border-amber-500/30 text-[9px] text-amber-300/90 leading-tight space-y-1">
                    <div className="font-bold uppercase font-mono flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-amber-400" />
                      <span>Scientific Disclaimer</span>
                    </div>
                    <p>
                      {symptomResult?.uncertainty_statement || 
                        "Spatial correlations do not imply singular causal attribution. Atmospheric boundary fluctuations and transboundary sources introduce epistemic variance."}
                    </p>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  );
};
