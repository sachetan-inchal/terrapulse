import React, { useState, useEffect } from 'react';
import {
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ShieldAlert,
  Download,
  Terminal,
  Activity,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Layers,
  Database,
  Search,
  Globe2,
  Clock,
  ArrowRight,
  FileText,
  Sparkles,
  MapPin,
  Check,
  GitCommit,
  Cpu
} from 'lucide-react';
import { AppInterfaceMode } from '../../types';

// Types
interface TestResultSchema {
  test_id: string;
  component: string;
  category: string;
  description: string;
  input_data: any;
  expected: string;
  actual: any;
  status: 'PASS' | 'PARTIAL' | 'FAIL' | 'MOCKED' | 'BLOCKED' | 'UNVERIFIED';
  execution_time_ms: number;
  evidence: string;
  failure_explanation?: string;
  recommended_correction?: string;
  api_calls?: any[];
  logs?: string[];
}

interface ComponentInventoryItem {
  id: string;
  name: string;
  module: string;
  files: string[];
  description: string;
  external_dependencies: string[];
  current_status: string;
  known_findings: string;
}

interface StageExecution {
  stage_id: number;
  stage_name: string;
  component: string;
  raw_input: any;
  raw_output: any;
  status: string;
  latency_ms: number;
  schema_valid: boolean;
  data_loss_detected: boolean;
  notes: string;
  error?: string;
}

interface IntegrationWorkflowResult {
  workflow_id: string;
  workflow_name: string;
  description: string;
  initial_input: any;
  total_stages: number;
  stages: StageExecution[];
  final_output: any;
  status: string;
  execution_time_ms: number;
  data_lineage_verified: boolean;
  failure_stage?: string;
  authenticity_notes: string;
}

interface ToolExecutionEvent {
  tool_name: string;
  intent: string;
  arguments: any;
  raw_result_summary: any;
  latency_ms: number;
  genuinely_executed_in_backend: boolean;
  simulated_by_agent_code: boolean;
}

interface AgentLoopExecutionTrace {
  test_id: string;
  behavior_code: string;
  behavior_name: string;
  user_prompt: string;
  session_id: string;
  total_events: number;
  iteration_count: number;
  tool_calls_observed: ToolExecutionEvent[];
  clarification_requested?: any;
  final_response_text: string;
  final_response_data: any;
  total_latency_ms: number;
  loop_detected: boolean;
  terminated_correctly: boolean;
  hallucination_detected: boolean;
  status: string;
  verification_notes: string;
  timeline: any[];
}

interface ArenaEvaluationReport {
  understood_objective: boolean;
  understood_rationale: string;
  correct_tools_selected: boolean;
  tools_selected: string[];
  tools_genuinely_executed: boolean;
  execution_authenticity_notes: string;
  correct_arguments_supplied: boolean;
  tool_results_used_in_answer: boolean;
  final_answer_matches_evidence: boolean;
  geographical_outputs_accurate: boolean;
  geographical_details?: any;
  scientific_claims_qualified: boolean;
  causal_disclaimer_present: boolean;
  fabricated_results_detected: boolean;
  fabricated_details?: string;
  all_required_outcomes_achieved: boolean;
  overall_status: string;
}

interface TimelineStep {
  step_number: number;
  stage: string;
  label: string;
  details: any;
  timestamp: string;
}

interface ArenaPromptExecution {
  prompt_id: string;
  category_id: number;
  category_name: string;
  user_prompt: string;
  expected_outcomes: string[];
  actual_response_text: string;
  session_id: string;
  timeline: TimelineStep[];
  evaluation: ArenaEvaluationReport;
  map_output?: any;
  evidence_output?: any;
  execution_time_ms: number;
  timestamp: string;
}

interface Props {
  onSwitchMode: (mode: AppInterfaceMode) => void;
}

type WorkbenchTab = 'components' | 'integration' | 'agent_loop' | 'prompt_arena' | 'reports';

const SAMPLE_INPUTS: Record<string, string> = {
  pollutants: 'lead',
  research: 'eutrophication cyanobacteria dissolved oxygen',
  agent: 'Why are fish dying in Bellandur Lake?',
  symptom: 'Thousands of dead fish floating in lake',
  geospatial: 'Bengaluru',
  satellite: 'bengaluru',
  vision: '',
  geocoding: 'Mount Kilimanjaro',
  workflow: 'Why is air pollution increasing in Chennai?'
};

export const GeoAgentQAWorkbench: React.FC<Props> = ({ onSwitchMode }) => {
  // Navigation
  const [currentTab, setCurrentTab] = useState<WorkbenchTab>('components');

  // Tab 1: Component Tests State
  const [inventory, setInventory] = useState<ComponentInventoryItem[]>([]);
  const [activeComponentId, setActiveComponentId] = useState<string>('pollutants');
  const [customInput, setCustomInput] = useState<string>('lead');
  const [results, setResults] = useState<TestResultSchema[]>([]);
  const [dependencies, setDependencies] = useState<Record<string, any>>({});
  const [isRunningAll, setIsRunningAll] = useState<boolean>(false);
  const [isRunningActive, setIsRunningActive] = useState<boolean>(false);
  const [expandedTests, setExpandedTests] = useState<Record<string, boolean>>({});

  // Tab 2: Integration Lab State
  const [integrationWorkflows, setIntegrationWorkflows] = useState<any[]>([]);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string>('INT-01');
  const [workflowResults, setWorkflowResults] = useState<Record<string, IntegrationWorkflowResult>>({});
  const [isRunningIntegration, setIsRunningIntegration] = useState<boolean>(false);
  const [expandedStages, setExpandedStages] = useState<Record<string, boolean>>({});

  // Tab 3: Agent Loop Lab State
  const [behaviors, setBehaviors] = useState<any[]>([]);
  const [activeBehaviorCode, setActiveBehaviorCode] = useState<string>('A');
  const [agentLoopTraces, setAgentLoopTraces] = useState<Record<string, AgentLoopExecutionTrace>>({});
  const [isRunningAgentLoop, setIsRunningAgentLoop] = useState<boolean>(false);

  // Tab 4: Prompt Arena State
  const [arenaLibrary, setArenaLibrary] = useState<any[]>([]);
  const [selectedPromptId, setSelectedPromptId] = useState<string>('PRM-01');
  const [arenaPromptText, setArenaPromptText] = useState<string>('Identify all primary solid, liquid, and gaseous pollutants emitted by steel manufacturing plants and explain their environmental degradation pathways.');
  const [arenaResult, setArenaResult] = useState<ArenaPromptExecution | null>(null);
  const [isRunningArena, setIsRunningArena] = useState<boolean>(false);
  const [isRunningBatchArena, setIsRunningBatchArena] = useState<boolean>(false);
  const [arenaBatchResults, setArenaBatchResults] = useState<ArenaPromptExecution[]>([]);

  // Tab 5: Reports Center State
  const [activeReportType, setActiveReportType] = useState<string>('component');
  const [reportContent, setReportContent] = useState<string>('');
  const [isLoadingReport, setIsLoadingReport] = useState<boolean>(false);

  useEffect(() => {
    fetchInventory();
    fetchDependencies();
    fetchIntegrationList();
    fetchBehaviorsList();
    fetchArenaPrompts();
    handleRunAllSuites();
  }, []);

  // Fetch initial data
  const fetchInventory = async () => {
    try {
      const res = await fetch('/api/qa/inventory');
      if (res.ok) {
        const data = await res.json();
        setInventory(data.components || []);
      }
    } catch (e) {
      console.error('Inventory error:', e);
    }
  };

  const fetchDependencies = async () => {
    try {
      const res = await fetch('/api/qa/dependencies');
      if (res.ok) {
        const data = await res.json();
        setDependencies(data);
      }
    } catch (e) {
      console.error('Dependencies error:', e);
    }
  };

  const fetchIntegrationList = async () => {
    try {
      const res = await fetch('/api/qa/integration/list');
      if (res.ok) {
        const data = await res.json();
        setIntegrationWorkflows(data);
      }
    } catch (e) {
      console.error('Integration list error:', e);
    }
  };

  const fetchBehaviorsList = async () => {
    try {
      const res = await fetch('/api/qa/agent-loop/behaviors');
      if (res.ok) {
        const data = await res.json();
        setBehaviors(data);
      }
    } catch (e) {
      console.error('Behaviors error:', e);
    }
  };

  const fetchArenaPrompts = async () => {
    try {
      const res = await fetch('/api/qa/arena/prompts');
      if (res.ok) {
        const data = await res.json();
        setArenaLibrary(data);
        if (data.length > 0) {
          setArenaPromptText(data[0].prompt);
        }
      }
    } catch (e) {
      console.error('Arena prompts error:', e);
    }
  };

  // Tab 1 Handlers
  const handleSelectComponent = (comp: ComponentInventoryItem) => {
    setActiveComponentId(comp.id);
    setCustomInput(SAMPLE_INPUTS[comp.id] || '');
  };

  const handleRunAllSuites = async () => {
    setIsRunningAll(true);
    try {
      const res = await fetch('/api/qa/run-all', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
      }
    } catch (e) {
      console.error('Run all error:', e);
    } finally {
      setIsRunningAll(false);
    }
  };

  const handleRunActiveComponent = async () => {
    setIsRunningActive(true);
    try {
      const res = await fetch('/api/qa/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          component: activeComponentId,
          custom_input: customInput || undefined
        })
      });
      if (res.ok) {
        const data = await res.json();
        const otherResults = results.filter(r => r.component !== activeComponentId);
        setResults([...(data.results || []), ...otherResults]);
      }
    } catch (e) {
      console.error('Run active component error:', e);
    } finally {
      setIsRunningActive(false);
    }
  };

  // Tab 2 Handlers: Integration Lab
  const handleRunIntegrationWorkflow = async (workflowId: string) => {
    setIsRunningIntegration(true);
    try {
      const res = await fetch('/api/qa/integration/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow_id: workflowId })
      });
      if (res.ok) {
        const data = await res.json();
        setWorkflowResults(prev => ({ ...prev, [workflowId]: data }));
      }
    } catch (e) {
      console.error('Run integration error:', e);
    } finally {
      setIsRunningIntegration(false);
    }
  };

  const handleRunAllIntegration = async () => {
    setIsRunningIntegration(true);
    try {
      const res = await fetch('/api/qa/integration/run-all', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const resultMap: Record<string, IntegrationWorkflowResult> = {};
        for (const item of data.workflows || []) {
          resultMap[item.workflow_id] = item;
        }
        setWorkflowResults(resultMap);
      }
    } catch (e) {
      console.error('Run all integration error:', e);
    } finally {
      setIsRunningIntegration(false);
    }
  };

  // Tab 3 Handlers: Agent Loop Lab
  const handleRunAgentLoopBehavior = async (behaviorCode: string) => {
    setIsRunningAgentLoop(true);
    try {
      const res = await fetch('/api/qa/agent-loop/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ behavior_code: behaviorCode })
      });
      if (res.ok) {
        const data = await res.json();
        setAgentLoopTraces(prev => ({ ...prev, [behaviorCode]: data }));
      }
    } catch (e) {
      console.error('Run agent loop error:', e);
    } finally {
      setIsRunningAgentLoop(false);
    }
  };

  const handleRunAllAgentLoop = async () => {
    setIsRunningAgentLoop(true);
    try {
      const res = await fetch('/api/qa/agent-loop/run-all', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const traceMap: Record<string, AgentLoopExecutionTrace> = {};
        for (const item of data.traces || []) {
          traceMap[item.behavior_code] = item;
        }
        setAgentLoopTraces(traceMap);
      }
    } catch (e) {
      console.error('Run all agent loop error:', e);
    } finally {
      setIsRunningAgentLoop(false);
    }
  };

  // Tab 4 Handlers: Prompt Arena
  const handleSelectArenaPrompt = (promptItem: any) => {
    setSelectedPromptId(promptItem.id);
    setArenaPromptText(promptItem.prompt);
  };

  const handleRunArenaPrompt = async () => {
    setIsRunningArena(true);
    try {
      const targetItem = arenaLibrary.find(p => p.id === selectedPromptId);
      const res = await fetch('/api/qa/arena/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: arenaPromptText,
          prompt_id: selectedPromptId,
          category_id: targetItem?.category_id,
          category_name: targetItem?.category,
          expected_outcomes: targetItem?.expected_outcomes
        })
      });
      if (res.ok) {
        const data = await res.json();
        setArenaResult(data);
      }
    } catch (e) {
      console.error('Run arena error:', e);
    } finally {
      setIsRunningArena(false);
    }
  };

  const handleRunArenaBatch = async () => {
    setIsRunningBatchArena(true);
    try {
      const res = await fetch('/api/qa/arena/run-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (res.ok) {
        const data = await res.json();
        setArenaBatchResults(data.results || []);
        if (data.results && data.results.length > 0) {
          setArenaResult(data.results[0]);
        }
      }
    } catch (e) {
      console.error('Run arena batch error:', e);
    } finally {
      setIsRunningBatchArena(false);
    }
  };

  // Tab 5 Handlers: Reports Center
  const fetchReportContent = async (reportType: string) => {
    setActiveReportType(reportType);
    setIsLoadingReport(true);
    try {
      const res = await fetch(`/api/qa/reports/${reportType}?format=markdown`);
      if (res.ok) {
        const text = await res.text();
        setReportContent(text);
      }
    } catch (e) {
      console.error('Fetch report error:', e);
    } finally {
      setIsLoadingReport(false);
    }
  };

  useEffect(() => {
    if (currentTab === 'reports') {
      fetchReportContent(activeReportType);
    }
  }, [currentTab]);

  // Statistics
  const passCount = results.filter(r => r.status === 'PASS').length;
  const partialCount = results.filter(r => r.status === 'PARTIAL').length;
  const mockCount = results.filter(r => r.status === 'MOCKED').length;
  const failCount = results.filter(r => r.status === 'FAIL').length;
  const blockedCount = results.filter(r => r.status === 'BLOCKED').length;

  const activeComp = inventory.find(c => c.id === activeComponentId);
  const activeResults = results.filter(r => r.component === activeComponentId);

  const toggleExpand = (id: string) => {
    setExpandedTests(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleStageExpand = (id: string) => {
    setExpandedStages(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> PASS</span>;
      case 'PARTIAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> PARTIAL</span>;
      case 'MOCKED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1"><ShieldAlert className="w-3 h-3" /> MOCKED</span>;
      case 'FAIL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center gap-1"><XCircle className="w-3 h-3" /> FAIL</span>;
      case 'BLOCKED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center gap-1"><HelpCircle className="w-3 h-3" /> BLOCKED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-500/20 text-slate-400 border border-slate-500/30">UNVERIFIED</span>;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#020617] text-slate-100 font-sans overflow-hidden">
      {/* Top Header Bar */}
      <header className="h-14 bg-[#040816] border-b border-cyan-500/20 px-6 flex items-center justify-between flex-shrink-0 z-20">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center border border-purple-400/40">
              <Terminal className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <span className="text-xs font-bold tracking-wider uppercase font-mono text-white">GeoAgent QA / Testing Workbench</span>
              <span className="ml-2 text-[9px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">INDEPENDENT BLACK-BOX AUDIT</span>
            </div>
          </div>
        </div>

        {/* Center Mode Switcher Back to App */}
        <div className="flex items-center bg-[#070e24] p-1 rounded-xl border border-cyan-500/20">
          <button
            onClick={() => onSwitchMode('explorer')}
            className="px-3 py-1 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition-all flex items-center gap-1.5"
          >
            <Globe2 className="w-3.5 h-3.5" />
            <span>Explorer</span>
          </button>
          <button
            onClick={() => onSwitchMode('investigator')}
            className="px-3 py-1 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition-all flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>AI Investigator</span>
          </button>
          <button
            onClick={() => onSwitchMode('qa_workbench')}
            className="px-3 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r from-purple-600 to-cyan-600 text-white shadow-md border border-purple-400/30 flex items-center gap-1.5"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>QA Workbench</span>
          </button>
        </div>

        {/* Right Actions */}
        <div className="flex items-center space-x-3">
          <a
            href="/qa"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all"
          >
            <ExternalLink className="w-3 h-3" />
            <span>Standalone /qa Tab</span>
          </a>
          <a
            href="/api/qa/export?format=markdown"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-300 text-xs font-medium border border-cyan-500/40 transition-all"
          >
            <Download className="w-3 h-3" />
            <span>Export Report</span>
          </a>
        </div>
      </header>

      {/* 5-Tab Navigation Sub-Bar */}
      <div className="h-11 bg-[#050b1e] border-b border-slate-800 px-6 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentTab('components')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentTab === 'components'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Component Tests (A–J)</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 font-mono">{results.length}</span>
          </button>

          <button
            onClick={() => setCurrentTab('integration')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentTab === 'integration'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Integration Lab</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">6 Workflows</span>
          </button>

          <button
            onClick={() => setCurrentTab('agent_loop')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentTab === 'agent_loop'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Agent Loop Lab</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">12 Behaviors</span>
          </button>

          <button
            onClick={() => setCurrentTab('prompt_arena')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentTab === 'prompt_arena'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Prompt Arena & Execution Timeline</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">14 Categories</span>
          </button>

          <button
            onClick={() => setCurrentTab('reports')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentTab === 'reports'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Reports Center</span>
          </button>
        </div>

        {/* Global Status Counters */}
        <div className="flex items-center space-x-3 text-[11px] font-mono">
          <span className="text-emerald-400 font-bold">{passCount} PASS</span>
          <span className="text-slate-600">|</span>
          <span className="text-amber-400 font-bold">{partialCount} PARTIAL</span>
          <span className="text-slate-600">|</span>
          <span className="text-purple-400 font-bold">{mockCount} MOCKED</span>
          <span className="text-slate-600">|</span>
          <span className="text-rose-400 font-bold">{failCount} FAIL</span>
        </div>
      </div>

      {/* Main Tab Content Viewport */}
      <div className="flex flex-1 overflow-hidden">
        {/* ========================================================================= */}
        {/* TAB 1: COMPONENT TESTS (A-J) */}
        {/* ========================================================================= */}
        {currentTab === 'components' && (
          <>
            {/* Left Sidebar: Components Navigation */}
            <div className="w-80 bg-[#04091a] border-r border-slate-800 flex flex-col flex-shrink-0">
              <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">Components (9)</span>
                <button
                  onClick={handleRunAllSuites}
                  disabled={isRunningAll}
                  className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1 disabled:opacity-50 transition-all shadow-sm"
                >
                  <Play className="w-3 h-3" />
                  <span>{isRunningAll ? 'Running...' : 'Run All'}</span>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
                {inventory.map(comp => {
                  const compResults = results.filter(r => r.component === comp.id);
                  const isCurrent = comp.id === activeComponentId;
                  return (
                    <button
                      key={comp.id}
                      onClick={() => handleSelectComponent(comp)}
                      className={`w-full text-left p-3.5 transition-all flex flex-col gap-1.5 ${
                        isCurrent
                          ? 'bg-cyan-950/40 border-l-4 border-cyan-400 text-white'
                          : 'hover:bg-slate-900/50 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold truncate">{comp.name}</span>
                        {getStatusBadge(comp.current_status)}
                      </div>
                      <span className="text-[10px] font-mono text-slate-400 truncate">{comp.module}</span>
                      <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400 font-mono">
                        <span>Tests: {compResults.length}</span>
                        <span>•</span>
                        <span className="text-emerald-400 font-bold">{compResults.filter(r => r.status === 'PASS').length} P</span>
                        <span className="text-purple-400 font-bold">{compResults.filter(r => r.status === 'MOCKED').length} M</span>
                        <span className="text-rose-400 font-bold">{compResults.filter(r => r.status === 'FAIL').length} F</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right Pane: Component Execution & Inspection */}
            <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-6">
              {/* Active Component Card */}
              {activeComp && (
                <div className="p-5 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-3 shadow-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <h2 className="text-base font-bold text-white">{activeComp.name}</h2>
                        {getStatusBadge(activeComp.current_status)}
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{activeComp.description}</p>
                    </div>
                    <button
                      onClick={handleRunActiveComponent}
                      disabled={isRunningActive}
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-md"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>{isRunningActive ? 'Testing...' : 'Execute Component Suite'}</span>
                    </button>
                  </div>

                  <div className="text-xs text-purple-300 bg-purple-950/30 p-2.5 rounded-lg border border-purple-500/30 font-mono">
                    <b>Audit Finding:</b> {activeComp.known_findings}
                  </div>

                  {/* Custom Test Input Box */}
                  <div className="pt-2 flex items-center gap-3">
                    <label className="text-xs font-mono text-slate-300 font-semibold whitespace-nowrap">Custom Test Input:</label>
                    <input
                      type="text"
                      value={customInput}
                      onChange={e => setCustomInput(e.target.value)}
                      placeholder="e.g. mercury or lead or Lake Victoria"
                      className="flex-1 px-3 py-1.5 rounded-lg bg-[#020617] border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
                    />
                    <button
                      onClick={() => setCustomInput(SAMPLE_INPUTS[activeComp.id] || '')}
                      className="px-2.5 py-1.5 rounded bg-slate-800 text-[11px] font-mono text-slate-300 hover:text-white"
                    >
                      Reset
                    </button>
                  </div>
                </div>
              )}

              {/* Execution Results List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-cyan-400" />
                    <span>Independent Black-Box Execution Evidence ({activeResults.length} Tests)</span>
                  </h3>
                </div>

                <div className="space-y-3">
                  {activeResults.map(t => {
                    const isExpanded = expandedTests[t.test_id];
                    return (
                      <div
                        key={t.test_id}
                        className={`p-4 rounded-xl bg-[#070e24] border transition-all ${
                          t.status === 'PASS'
                            ? 'border-emerald-500/30'
                            : t.status === 'MOCKED'
                            ? 'border-purple-500/30'
                            : t.status === 'FAIL'
                            ? 'border-rose-500/30'
                            : 'border-slate-800'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <span className="text-xs font-mono font-bold text-white">{t.test_id}</span>
                            {getStatusBadge(t.status)}
                            <span className="text-[11px] font-mono text-slate-400">[{t.category}]</span>
                          </div>
                          <span className="text-[11px] font-mono text-cyan-400">⏱ {t.execution_time_ms} ms</span>
                        </div>

                        <div className="text-xs text-slate-300 mt-2 font-medium">
                          <span className="text-slate-400 font-semibold">{t.component}: </span>
                          {t.description}
                        </div>

                        <div className="mt-2.5 p-3 rounded-lg bg-[#030712] border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                          <div className="text-[10px] font-mono uppercase text-cyan-400 font-semibold mb-1">Empirical Evidence & Output:</div>
                          {t.evidence}
                        </div>

                        {t.failure_explanation && (
                          <div className="mt-2.5 p-3 rounded-lg bg-rose-950/20 border border-rose-500/30 text-xs text-rose-300 space-y-1">
                            <div><b>Root Cause:</b> {t.failure_explanation}</div>
                            {t.recommended_correction && (
                              <div className="text-rose-200"><b>Correction:</b> {t.recommended_correction}</div>
                            )}
                          </div>
                        )}

                        {/* Expand Raw Input/Output */}
                        <div className="mt-3 pt-2 border-t border-slate-800/80">
                          <button
                            onClick={() => toggleExpand(t.test_id)}
                            className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                          >
                            {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                            <span>{isExpanded ? 'Hide Raw Payloads' : 'Inspect Raw Input, Output & Outbound Network Requests'}</span>
                          </button>

                          {isExpanded && (
                            <div className="grid grid-cols-2 gap-3 mt-3">
                              <div>
                                <span className="text-[10px] font-mono uppercase text-slate-400">Raw Input:</span>
                                <pre className="mt-1 p-2.5 rounded bg-[#020617] border border-slate-800 text-[10px] font-mono text-slate-300 max-h-40 overflow-auto whitespace-pre-wrap">
                                  {JSON.stringify(t.input_data, null, 2)}
                                </pre>
                              </div>
                              <div>
                                <span className="text-[10px] font-mono uppercase text-slate-400">Raw Output:</span>
                                <pre className="mt-1 p-2.5 rounded bg-[#020617] border border-slate-800 text-[10px] font-mono text-slate-300 max-h-40 overflow-auto whitespace-pre-wrap">
                                  {JSON.stringify(t.actual, null, 2)}
                                </pre>
                              </div>
                              {t.api_calls && t.api_calls.length > 0 && (
                                <div className="col-span-2">
                                  <span className="text-[10px] font-mono uppercase text-slate-400">API Calls:</span>
                                  <pre className="mt-1 p-2.5 rounded bg-[#020617] border border-slate-800 text-[10px] font-mono text-slate-300 max-h-32 overflow-auto whitespace-pre-wrap">
                                    {JSON.stringify(t.api_calls, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* External Dependencies Radar */}
              <div className="p-5 rounded-xl bg-[#070e24] border border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span>External Service Availability Radar</span>
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(dependencies).map(([key, dep]: [string, any]) => (
                    <div key={key} className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-200">{dep.name}</span>
                        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold ${
                          dep.available
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        }`}>
                          {dep.available ? 'ONLINE' : 'UNAVAILABLE'}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 leading-tight">{dep.details}</div>
                      {dep.latency_ms > 0 && (
                        <div className="text-[10px] font-mono text-cyan-400">Latency: {dep.latency_ms} ms</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: INTEGRATION TESTING LAB (MODULE 1) */}
        {/* ========================================================================= */}
        {currentTab === 'integration' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Sidebar: Workflows */}
            <div className="w-80 bg-[#04091a] border-r border-slate-800 flex flex-col flex-shrink-0">
              <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">Workflows (6)</span>
                <button
                  onClick={handleRunAllIntegration}
                  disabled={isRunningIntegration}
                  className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1 disabled:opacity-50 transition-all shadow-sm"
                >
                  <Play className="w-3 h-3" />
                  <span>{isRunningIntegration ? 'Testing...' : 'Run All 6'}</span>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
                {integrationWorkflows.map(wf => {
                  const res = workflowResults[wf.id];
                  const isCurrent = wf.id === activeWorkflowId;
                  return (
                    <button
                      key={wf.id}
                      onClick={() => setActiveWorkflowId(wf.id)}
                      className={`w-full text-left p-3.5 transition-all flex flex-col gap-1.5 ${
                        isCurrent
                          ? 'bg-cyan-950/40 border-l-4 border-cyan-400 text-white'
                          : 'hover:bg-slate-900/50 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-cyan-400">{wf.id}</span>
                        {res ? getStatusBadge(res.status) : <span className="text-[9px] font-mono text-slate-500">READY</span>}
                      </div>
                      <span className="text-xs font-semibold text-slate-200">{wf.name}</span>
                      <span className="text-[10px] text-slate-400 line-clamp-2">{wf.description}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Main Stage: Integration Workflow Inspection */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {(() => {
                const activeWf = integrationWorkflows.find(w => w.id === activeWorkflowId);
                const res = workflowResults[activeWorkflowId];

                return (
                  <div className="space-y-5">
                    {/* Header Card */}
                    <div className="p-5 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2.5">
                            <span className="text-sm font-mono font-bold text-cyan-400">{activeWf?.id}</span>
                            <h2 className="text-base font-bold text-white">{activeWf?.name}</h2>
                            {res && getStatusBadge(res.status)}
                          </div>
                          <p className="text-xs text-slate-400 mt-1">{activeWf?.description}</p>
                        </div>
                        <button
                          onClick={() => handleRunIntegrationWorkflow(activeWorkflowId)}
                          disabled={isRunningIntegration}
                          className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-md"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>{isRunningIntegration ? 'Executing Pipeline...' : 'Execute Integration Pipeline'}</span>
                        </button>
                      </div>

                      {res && (
                        <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-800 text-xs font-mono">
                          <div>
                            <span className="text-slate-500">Execution Time: </span>
                            <span className="text-cyan-400 font-bold">{res.execution_time_ms} ms</span>
                          </div>
                          <div>
                            <span className="text-slate-500">Data Lineage Verified: </span>
                            <span className={res.data_lineage_verified ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                              {res.data_lineage_verified ? 'VERIFIED' : 'LINEAGE FAILED'}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">Total Stages: </span>
                            <span className="text-slate-200 font-bold">{res.total_stages} Stages</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Stage by Stage Pipeline Trace */}
                    {res ? (
                      <div className="space-y-4">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          <Layers className="w-4 h-4 text-cyan-400" />
                          <span>Pipeline Stage Execution & Data Transfer Lineage</span>
                        </h3>

                        <div className="space-y-3">
                          {res.stages.map((st, idx) => {
                            const isExp = expandedStages[`${res.workflow_id}-${st.stage_id}`];
                            return (
                              <div
                                key={st.stage_id}
                                className={`p-4 rounded-xl bg-[#070e24] border ${
                                  st.status === 'SUCCESS' ? 'border-emerald-500/30' : 'border-rose-500/30'
                                } space-y-2`}
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2.5">
                                    <span className="w-5 h-5 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 font-mono text-[10px] flex items-center justify-center font-bold">
                                      {st.stage_id}
                                    </span>
                                    <span className="text-xs font-bold text-white">{st.stage_name}</span>
                                    <span className="text-[10px] font-mono text-slate-400">({st.component})</span>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <span className="text-[10px] font-mono text-cyan-400">⏱ {st.latency_ms} ms</span>
                                    {st.schema_valid ? (
                                      <span className="text-[9px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                                        SCHEMA VALID
                                      </span>
                                    ) : (
                                      <span className="text-[9px] font-mono text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                                        SCHEMA INVALID
                                      </span>
                                    )}
                                    {st.data_loss_detected && (
                                      <span className="text-[9px] font-mono text-rose-300 bg-rose-950 px-2 py-0.5 rounded border border-rose-500/40">
                                        DATA LOSS DETECTED
                                      </span>
                                    )}
                                  </div>
                                </div>

                                <div className="text-xs text-slate-300 bg-[#030712] p-2.5 rounded-lg border border-slate-800">
                                  <span className="text-slate-500 font-mono">Stage Audit Note: </span>
                                  {st.notes}
                                </div>

                                {/* Raw Transfer Payloads */}
                                <div className="pt-1">
                                  <button
                                    onClick={() => toggleStageExpand(`${res.workflow_id}-${st.stage_id}`)}
                                    className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                                  >
                                    {isExp ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                    <span>{isExp ? 'Hide Raw Stage Data' : 'Inspect Inter-Component Input & Output Transfer'}</span>
                                  </button>

                                  {isExp && (
                                    <div className="grid grid-cols-2 gap-3 mt-3">
                                      <div>
                                        <span className="text-[10px] font-mono uppercase text-slate-400">Upstream Input:</span>
                                        <pre className="mt-1 p-2.5 rounded bg-[#020617] border border-slate-800 text-[10px] font-mono text-slate-300 max-h-40 overflow-auto whitespace-pre-wrap">
                                          {JSON.stringify(st.raw_input, null, 2)}
                                        </pre>
                                      </div>
                                      <div>
                                        <span className="text-[10px] font-mono uppercase text-slate-400">Downstream Output:</span>
                                        <pre className="mt-1 p-2.5 rounded bg-[#020617] border border-slate-800 text-[10px] font-mono text-slate-300 max-h-40 overflow-auto whitespace-pre-wrap">
                                          {JSON.stringify(st.raw_output, null, 2)}
                                        </pre>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ) : (
                      <div className="p-12 text-center text-slate-500 rounded-xl bg-[#070e24] border border-slate-800 font-mono text-xs">
                        Click "Execute Integration Pipeline" to trace data transfers across components.
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: AGENT LOOP LAB (MODULE 2) */}
        {/* ========================================================================= */}
        {currentTab === 'agent_loop' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Sidebar: Behaviors A through L */}
            <div className="w-80 bg-[#04091a] border-r border-slate-800 flex flex-col flex-shrink-0">
              <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">Behaviors (A–L)</span>
                <button
                  onClick={handleRunAllAgentLoop}
                  disabled={isRunningAgentLoop}
                  className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1 disabled:opacity-50 transition-all shadow-sm"
                >
                  <Play className="w-3 h-3" />
                  <span>{isRunningAgentLoop ? 'Testing...' : 'Run All 12'}</span>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
                {behaviors.map(b => {
                  const trace = agentLoopTraces[b.code];
                  const isCurrent = b.code === activeBehaviorCode;
                  return (
                    <button
                      key={b.code}
                      onClick={() => setActiveBehaviorCode(b.code)}
                      className={`w-full text-left p-3.5 transition-all flex flex-col gap-1 ${
                        isCurrent
                          ? 'bg-cyan-950/40 border-l-4 border-cyan-400 text-white'
                          : 'hover:bg-slate-900/50 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-cyan-400">Behavior {b.code}</span>
                        {trace ? getStatusBadge(trace.status) : <span className="text-[9px] font-mono text-slate-500">READY</span>}
                      </div>
                      <span className="text-xs font-semibold text-slate-200">{b.name}</span>
                      <span className="text-[10px] text-slate-400 line-clamp-1">{b.description}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Main Stage: Agent Loop Trace */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {(() => {
                const activeBehavior = behaviors.find(b => b.code === activeBehaviorCode);
                const trace = agentLoopTraces[activeBehaviorCode];

                return (
                  <div className="space-y-5">
                    {/* Header */}
                    <div className="p-5 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2.5">
                            <span className="text-sm font-mono font-bold text-cyan-400">Behavior {activeBehavior?.code}:</span>
                            <h2 className="text-base font-bold text-white">{activeBehavior?.name}</h2>
                            {trace && getStatusBadge(trace.status)}
                          </div>
                          <p className="text-xs text-slate-400 mt-1">{activeBehavior?.description}</p>
                        </div>
                        <button
                          onClick={() => handleRunAgentLoopBehavior(activeBehaviorCode)}
                          disabled={isRunningAgentLoop}
                          className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-md"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>{isRunningAgentLoop ? 'Running Agent Loop...' : 'Execute Agent Loop Test'}</span>
                        </button>
                      </div>

                      {trace && (
                        <div className="grid grid-cols-4 gap-3 pt-2 border-t border-slate-800 text-xs font-mono">
                          <div>
                            <span className="text-slate-500">Latency: </span>
                            <span className="text-cyan-400 font-bold">{trace.total_latency_ms} ms</span>
                          </div>
                          <div>
                            <span className="text-slate-500">Iterations: </span>
                            <span className="text-slate-200 font-bold">{trace.iteration_count}</span>
                          </div>
                          <div>
                            <span className="text-slate-500">Terminated: </span>
                            <span className={trace.terminated_correctly ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                              {trace.terminated_correctly ? 'NORMAL' : 'LOOP/TIMEOUT'}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">Hallucination: </span>
                            <span className={trace.hallucination_detected ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                              {trace.hallucination_detected ? 'DETECTED' : 'NONE'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Trace Details */}
                    {trace ? (
                      <div className="space-y-4">
                        {/* Prompt Submitted */}
                        <div className="p-3.5 rounded-lg bg-[#030712] border border-slate-800 text-xs font-mono">
                          <span className="text-cyan-400 font-bold">Natural-Language User Prompt: </span>
                          <span className="text-slate-200">"{trace.user_prompt}"</span>
                        </div>

                        {/* Observed Tool Calls */}
                        <div className="space-y-3">
                          <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Activity className="w-4 h-4 text-cyan-400" />
                            <span>Observed Tool Calls & Authenticity Verification ({trace.tool_calls_observed.length})</span>
                          </h3>

                          {trace.tool_calls_observed.length > 0 ? (
                            <div className="space-y-2">
                              {trace.tool_calls_observed.map((tc, idx) => (
                                <div key={idx} className="p-3 rounded-lg bg-[#070e24] border border-slate-800 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs font-mono font-bold text-cyan-400">{tc.tool_name}</span>
                                      <span className="text-[10px] text-slate-400">({tc.intent})</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-[10px] font-mono text-cyan-400">⏱ {tc.latency_ms} ms</span>
                                      {tc.simulated_by_agent_code ? (
                                        <span className="text-[9px] font-mono text-purple-300 bg-purple-950 px-2 py-0.5 rounded border border-purple-500/40 font-bold">
                                          SIMULATED TOOL EVENT (15-16ms Mock)
                                        </span>
                                      ) : (
                                        <span className="text-[9px] font-mono text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded border border-emerald-500/30 font-bold">
                                          GENUINE EXECUTION
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="text-xs text-slate-300 font-mono bg-[#020617] p-2 rounded border border-slate-800">
                                    <span className="text-slate-500">Result Summary: </span>{JSON.stringify(tc.raw_result_summary)}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 text-xs font-mono text-slate-400">
                              No tools were invoked for this query (e.g. conversational greeting or out-of-scope question).
                            </div>
                          )}
                        </div>

                        {/* Audit Notes */}
                        <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30 text-xs text-purple-200 font-mono space-y-1">
                          <div className="font-bold text-purple-400 uppercase text-[10px]">Independent Behavior Evaluation:</div>
                          <div>{trace.verification_notes}</div>
                        </div>

                        {/* Final Response */}
                        <div className="p-4 rounded-xl bg-[#070e24] border border-slate-800 space-y-2">
                          <span className="text-xs font-mono font-bold uppercase text-slate-400">Final Synthesized Response:</span>
                          <div className="p-3 rounded-lg bg-[#020617] border border-slate-800 text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                            {trace.final_response_text || '(No text response produced)'}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-12 text-center text-slate-500 rounded-xl bg-[#070e24] border border-slate-800 font-mono text-xs">
                        Click "Execute Agent Loop Test" to inspect live tool calls, iterations, and termination behavior.
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 4: PROMPT ARENA & TIMELINE TRACE (MODULES 3, 4, 5) */}
        {/* ========================================================================= */}
        {currentTab === 'prompt_arena' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Sidebar: 14 Categories */}
            <div className="w-80 bg-[#04091a] border-r border-slate-800 flex flex-col flex-shrink-0">
              <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">14 Categories</span>
                <button
                  onClick={handleRunArenaBatch}
                  disabled={isRunningBatchArena}
                  className="px-2 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-[11px] font-semibold flex items-center gap-1 disabled:opacity-50 transition-all shadow-sm"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>{isRunningBatchArena ? 'Batching...' : 'Run All 14'}</span>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
                {arenaLibrary.map(item => {
                  const isCurrent = item.id === selectedPromptId;
                  const batchItem = arenaBatchResults.find(r => r.prompt_id === item.id);
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleSelectArenaPrompt(item)}
                      className={`w-full text-left p-3 transition-all flex flex-col gap-1 ${
                        isCurrent
                          ? 'bg-cyan-950/40 border-l-4 border-cyan-400 text-white'
                          : 'hover:bg-slate-900/50 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono font-bold text-cyan-400">{item.id}</span>
                        {batchItem && getStatusBadge(batchItem.evaluation.overall_status)}
                      </div>
                      <span className="text-xs font-semibold text-slate-200">{item.category}</span>
                      <span className="text-[10px] text-slate-400 line-clamp-1">{item.prompt}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Main Stage: Arena Execution, Timeline & 10-Criteria Evaluation */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Prompt Input Box */}
              <div className="p-5 rounded-xl bg-[#070e24] border border-cyan-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold uppercase text-cyan-400">
                    Natural-Language Environmental Prompt (Unmodified Submission)
                  </span>
                  <button
                    onClick={handleRunArenaPrompt}
                    disabled={isRunningArena}
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-md"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>{isRunningArena ? 'Evaluating Prompt...' : 'Submit Exact Prompt to Real Agent'}</span>
                  </button>
                </div>

                <textarea
                  value={arenaPromptText}
                  onChange={e => setArenaPromptText(e.target.value)}
                  rows={3}
                  className="w-full px-3.5 py-2.5 rounded-lg bg-[#020617] border border-slate-700 text-xs text-slate-100 font-sans focus:outline-none focus:border-cyan-400 resize-none leading-relaxed"
                  placeholder="Enter custom environmental prompt without modification..."
                />
              </div>

              {/* Arena Evaluation Result */}
              {arenaResult && (
                <div className="space-y-6">
                  {/* Visual Execution Timeline Trace (MODULE 5) */}
                  <div className="p-5 rounded-xl bg-[#070e24] border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Clock className="w-4 h-4 text-cyan-400" />
                        <span>Visual Chronological Execution Timeline Trace (Module 5)</span>
                      </h3>
                      <span className="text-xs font-mono text-cyan-400">⏱ {arenaResult.execution_time_ms} ms</span>
                    </div>

                    <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                      {arenaResult.timeline.map((step, idx) => (
                        <div key={idx} className="relative">
                          <div className="absolute -left-6 top-1.5 w-3 h-3 rounded-full bg-cyan-500 border-2 border-[#070e24]" />
                          <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-mono font-bold text-cyan-300">
                                Step {step.step_number}: {step.stage}
                              </span>
                              <span className="text-[10px] font-mono text-slate-500">{step.timestamp}</span>
                            </div>
                            <div className="text-xs text-slate-200">{step.label}</div>
                            {step.details && (
                              <pre className="mt-1 p-2 rounded bg-[#020617] border border-slate-900 text-[10px] font-mono text-slate-400 max-h-28 overflow-auto whitespace-pre-wrap">
                                {JSON.stringify(step.details, null, 2)}
                              </pre>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 10-Criteria Independent Evaluation Engine (MODULE 4) */}
                  <div className="p-5 rounded-xl bg-[#070e24] border border-purple-500/20 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-purple-400" />
                        <span>Independent Evaluation Engine: 10 Deterministic Criteria (Module 4)</span>
                      </h3>
                      {getStatusBadge(arenaResult.evaluation.overall_status)}
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      {/* Criterion 1 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">1. Understood Objective:</span>
                          <span className={arenaResult.evaluation.understood_objective ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {arenaResult.evaluation.understood_objective ? 'YES' : 'NO'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">{arenaResult.evaluation.understood_rationale}</div>
                      </div>

                      {/* Criterion 2 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">2. Correct Tools Selected:</span>
                          <span className={arenaResult.evaluation.correct_tools_selected ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {arenaResult.evaluation.correct_tools_selected ? 'YES' : 'NO'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          Tools: {arenaResult.evaluation.tools_selected.join(', ') || 'None'}
                        </div>
                      </div>

                      {/* Criterion 3 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">3. Tools Genuinely Executed:</span>
                          <span className={arenaResult.evaluation.tools_genuinely_executed ? 'text-emerald-400 font-bold' : 'text-purple-400 font-bold'}>
                            {arenaResult.evaluation.tools_genuinely_executed ? 'GENUINE' : 'SIMULATED'}
                          </span>
                        </div>
                        <div className="text-[11px] text-purple-300 font-mono">{arenaResult.evaluation.execution_authenticity_notes}</div>
                      </div>

                      {/* Criterion 4 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">4. Correct Arguments Supplied:</span>
                          <span className={arenaResult.evaluation.correct_arguments_supplied ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {arenaResult.evaluation.correct_arguments_supplied ? 'YES' : 'NO'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">Validated against schemas and parameter extractors.</div>
                      </div>

                      {/* Criterion 5 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">5. Tool Results Used in Answer:</span>
                          <span className={arenaResult.evaluation.tool_results_used_in_answer ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {arenaResult.evaluation.tool_results_used_in_answer ? 'YES' : 'NO'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">Downstream LLM incorporated returned payload.</div>
                      </div>

                      {/* Criterion 6 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">6. Final Answer Matches Evidence:</span>
                          <span className={arenaResult.evaluation.final_answer_matches_evidence ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {arenaResult.evaluation.final_answer_matches_evidence ? 'YES' : 'NO'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">Deterministic keyword & findings alignment check.</div>
                      </div>

                      {/* Criterion 7 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">7. Geographical Outputs Accurate:</span>
                          <span className={arenaResult.evaluation.geographical_outputs_accurate ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
                            {arenaResult.evaluation.geographical_outputs_accurate ? 'ACCURATE' : 'N/A OR STUB'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {arenaResult.evaluation.geographical_details ? JSON.stringify(arenaResult.evaluation.geographical_details) : 'No spatial layer required.'}
                        </div>
                      </div>

                      {/* Criterion 8 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">8. Scientific Claims Qualified:</span>
                          <span className={arenaResult.evaluation.scientific_claims_qualified ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {arenaResult.evaluation.scientific_claims_qualified ? 'YES' : 'UNQUALIFIED'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {arenaResult.evaluation.causal_disclaimer_present ? 'Causal disclaimer present.' : 'No causal disclaimer found.'}
                        </div>
                      </div>

                      {/* Criterion 9 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">9. Fabricated Results Produced:</span>
                          <span className={arenaResult.evaluation.fabricated_results_detected ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                            {arenaResult.evaluation.fabricated_results_detected ? 'FABRICATED' : 'NONE'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">{arenaResult.evaluation.fabricated_details || 'Verified against ground truth.'}</div>
                      </div>

                      {/* Criterion 10 */}
                      <div className="p-3 rounded-lg bg-[#030712] border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-300">10. All Required Outcomes Achieved:</span>
                          <span className={arenaResult.evaluation.all_required_outcomes_achieved ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
                            {arenaResult.evaluation.all_required_outcomes_achieved ? 'ACHIEVED' : 'PARTIAL'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">Status evaluated against library benchmark criteria.</div>
                      </div>
                    </div>
                  </div>

                  {/* Final Response & Raw Outputs */}
                  <div className="p-5 rounded-xl bg-[#070e24] border border-slate-800 space-y-3">
                    <span className="text-xs font-mono font-bold uppercase text-slate-400">Actual Real Agent Response Text:</span>
                    <div className="p-3.5 rounded-lg bg-[#020617] border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                      {arenaResult.actual_response_text}
                    </div>

                    {arenaResult.map_output && (
                      <div className="pt-2">
                        <span className="text-xs font-mono font-bold uppercase text-cyan-400">Map / GeoJSON Output Inspection:</span>
                        <pre className="mt-1 p-2.5 rounded bg-[#020617] border border-slate-800 text-[10px] font-mono text-slate-300 max-h-36 overflow-auto whitespace-pre-wrap">
                          {JSON.stringify(arenaResult.map_output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 5: REPORTS CENTER (MODULE 6) */}
        {/* ========================================================================= */}
        {currentTab === 'reports' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Sidebar: Report Categories */}
            <div className="w-80 bg-[#04091a] border-r border-slate-800 flex flex-col flex-shrink-0">
              <div className="p-3 border-b border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">Specialized Reports (6)</span>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
                {[
                  { id: 'component', name: '1. Component Test Report', desc: 'Detailed test report for all 9 components across categories A–J.' },
                  { id: 'integration', name: '2. Integration Test Report', desc: 'Multi-component integration workflows and data transfer checks.' },
                  { id: 'agent_loop', name: '3. Agent Loop Test Report', desc: 'Natural-language behavior tests A–L on the live agent loop.' },
                  { id: 'prompt_arena', name: '4. Prompt Arena Report', desc: '14 environmental categories evaluated on 10 deterministic criteria.' },
                  { id: 'authenticity', name: '5. Authenticity & Mock Audit', desc: 'Deep inventory of hardcoded dictionaries, fake noise, and simulated tools.' },
                  { id: 'readiness', name: '6. Overall Project Readiness', desc: 'Summary verdict, risk assessment, and recommended fixes before production.' },
                ].map(rep => {
                  const isCurrent = rep.id === activeReportType;
                  return (
                    <button
                      key={rep.id}
                      onClick={() => fetchReportContent(rep.id)}
                      className={`w-full text-left p-3.5 transition-all flex flex-col gap-1 ${
                        isCurrent
                          ? 'bg-cyan-950/40 border-l-4 border-cyan-400 text-white'
                          : 'hover:bg-slate-900/50 text-slate-300'
                      }`}
                    >
                      <span className="text-xs font-bold">{rep.name}</span>
                      <span className="text-[10px] text-slate-400">{rep.desc}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Main Stage: Markdown Reader */}
            <div className="flex-1 flex flex-col overflow-hidden p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-white uppercase font-mono flex items-center gap-2">
                  <FileText className="w-4 h-4 text-cyan-400" />
                  <span>Report View: {activeReportType.toUpperCase()}</span>
                </h2>
                <a
                  href={`/api/qa/reports/${activeReportType}?format=markdown`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-lg bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 border border-cyan-500/40 transition-all"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download .md</span>
                </a>
              </div>

              <div className="flex-1 p-5 rounded-xl bg-[#070e24] border border-slate-800 overflow-y-auto font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                {isLoadingReport ? 'Loading report contents...' : reportContent}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
