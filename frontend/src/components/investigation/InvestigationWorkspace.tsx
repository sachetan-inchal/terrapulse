import React, { useState, useEffect, useRef } from 'react';
import { 
  Radio, MapPin, Search, ChevronDown, Check, Loader2, 
  Globe2, Activity, RefreshCw, AlertTriangle, Layers,
  BarChart3, GitFork, TrendingUp, FileText, Compass, Sparkles
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
import { ChatPanel } from './ChatPanel';
import { InvestigationMap } from './InvestigationMap';
import { ActivityStreamTray } from './ActivityStreamTray';
import { EnvironmentalAnalyticsSection } from './EnvironmentalAnalyticsSection';
import { EvidenceCausalSection } from './EvidenceCausalSection';
import { ForecastingSection } from './ForecastingSection';
import { StructuredReportSection } from './StructuredReportSection';

type WorkspaceSection = 
  | 'investigation' 
  | 'map' 
  | 'analytics' 
  | 'evidence' 
  | 'forecasting' 
  | 'report';

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
  // Active Capability Section Tab
  const [activeSection, setActiveSection] = useState<WorkspaceSection>('investigation');

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
                options: data.options || ['Air Pollution (PM2.5)', 'Water Hypoxia (DO)', 'Industrial Effluents']
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

            // Update analytical report & causal findings
            if (data.investigation) {
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

  return (
    <div className="flex flex-col h-screen bg-[#030612] text-slate-100 overflow-hidden font-sans">
      
      {/* 1. Top Header with Mode Switcher & Location Intelligence */}
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

          {/* Location Selector Bar */}
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

          {/* Quick Location Pills */}
          <div className="hidden 2xl:flex items-center space-x-1.5 font-mono text-[10px]">
            <span className="text-slate-500 text-[9px] uppercase tracking-wider mr-1">Quick AOI:</span>
            {quickLocations.map((ql) => (
              <button
                key={ql.id}
                onClick={() => handleQuickSelect(ql.id)}
                className={`px-2 py-0.5 rounded transition-all ${
                  currentLocation.id.toLowerCase() === ql.id.toLowerCase()
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                    : 'bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
                }`}
              >
                {ql.name}
              </button>
            ))}
          </div>
        </div>

        {/* Center: Mode Switcher (True Bidirectional Isolation) */}
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

        {/* Right: Agent Status & Reset */}
        <div className="flex items-center space-x-3 font-mono text-[10px]">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>STRANDS AGENT ONLINE</span>
          </span>
          <button
            onClick={handleResetSession}
            className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3 h-3 text-cyan-400" />
            <span>New Session</span>
          </button>
        </div>
      </header>

      {/* 2. Capability Sections Sub-Navigation Bar */}
      <nav className="h-10 bg-[#060c1d] border-b border-cyan-500/20 px-6 flex items-center justify-between text-xs font-mono shrink-0">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setActiveSection('investigation')}
            className={`px-3 py-1 rounded-md flex items-center gap-1.5 transition-all ${
              activeSection === 'investigation'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>A. Investigation</span>
          </button>

          <button
            onClick={() => setActiveSection('map')}
            className={`px-3 py-1 rounded-md flex items-center gap-1.5 transition-all ${
              activeSection === 'map'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
            <span>B. Live Geospatial Map</span>
          </button>

          <button
            onClick={() => setActiveSection('analytics')}
            className={`px-3 py-1 rounded-md flex items-center gap-1.5 transition-all ${
              activeSection === 'analytics'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>C. Environmental Analytics</span>
          </button>

          <button
            onClick={() => setActiveSection('evidence')}
            className={`px-3 py-1 rounded-md flex items-center gap-1.5 transition-all ${
              activeSection === 'evidence'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <GitFork className="w-3.5 h-3.5 text-cyan-400" />
            <span>D. Evidence & Causal Analysis</span>
          </button>

          <button
            onClick={() => setActiveSection('forecasting')}
            className={`px-3 py-1 rounded-md flex items-center gap-1.5 transition-all ${
              activeSection === 'forecasting'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
            <span>E. Forecasting</span>
          </button>

          <button
            onClick={() => setActiveSection('report')}
            className={`px-3 py-1 rounded-md flex items-center gap-1.5 transition-all ${
              activeSection === 'report'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            <span>F. Reports</span>
          </button>
        </div>

        {/* Telemetry Snapshot Pill */}
        <div className="hidden lg:flex items-center space-x-3 text-[10px] text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
            <span>Target: <strong className="text-slate-200">{currentLocation.name}</strong></span>
          </span>
          <span>•</span>
          <span>Stations: <strong className="text-cyan-300">{stations.length}</strong></span>
          <span>•</span>
          <span>IDW Coverage: <strong className="text-emerald-400">{heatmapData?.coverage_percentage ?? 88.5}%</strong></span>
        </div>
      </nav>

      {/* 3. Section Content Display */}
      <div className="flex-1 overflow-hidden relative">

        {/* SECTION A: Investigation (Conversational Interface + Interactive Map + Activity Tray) */}
        {activeSection === 'investigation' && (
          <div className="w-full h-full flex overflow-hidden">
            {/* Left Chat Column (35%) */}
            <div className="w-[35%] min-w-[340px] max-w-[480px] h-full flex flex-col border-r border-cyan-500/20">
              <ChatPanel
                messages={messages}
                isInvestigating={isInvestigating}
                onSendMessage={handleSendMessage}
                onResetSession={handleResetSession}
                sessionId={sessionId}
              />
            </div>

            {/* Right Map Stage & Activity Stream Tray (65%) */}
            <div className="flex-1 h-full flex flex-col min-w-0">
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

              {/* Bottom Activity Stream Tray */}
              <ActivityStreamTray
                events={activityEvents}
                isInvestigating={isInvestigating}
              />
            </div>
          </div>
        )}

        {/* SECTION B: Live Geospatial Map (Full Interactive View) */}
        {activeSection === 'map' && (
          <div className="w-full h-full relative">
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
        )}

        {/* SECTION C: Environmental Analytics */}
        {activeSection === 'analytics' && (
          <div className="w-full h-full overflow-hidden">
            <EnvironmentalAnalyticsSection
              currentLocation={currentLocation}
              stations={stations}
              symptomResult={symptomResult}
            />
          </div>
        )}

        {/* SECTION D: Evidence & Causal Analysis */}
        {activeSection === 'evidence' && (
          <div className="w-full h-full overflow-hidden">
            <EvidenceCausalSection
              currentLocation={currentLocation}
              symptomResult={symptomResult}
            />
          </div>
        )}

        {/* SECTION E: Forecasting */}
        {activeSection === 'forecasting' && (
          <div className="w-full h-full overflow-hidden">
            <ForecastingSection
              currentLocation={currentLocation}
              forecastData={forecastData}
            />
          </div>
        )}

        {/* SECTION F: Reports */}
        {activeSection === 'report' && (
          <div className="w-full h-full overflow-hidden">
            <StructuredReportSection
              currentLocation={currentLocation}
              symptomResult={symptomResult}
              forecastData={forecastData}
              stations={stations}
              heatmapData={heatmapData}
              userQuery={lastUserQuery}
            />
          </div>
        )}

      </div>
    </div>
  );
};
