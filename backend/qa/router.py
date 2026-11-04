"""FastAPI router for GeoAgent QA / Testing Workbench."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, HTTPException, Body, Response
from pydantic import BaseModel

from backend.qa.engine import qa_engine, TestResult
from backend.qa.integration_engine import integration_engine, IntegrationWorkflowResult
from backend.qa.agent_loop_engine import agent_loop_lab, AgentLoopExecutionTrace
from backend.qa.prompt_arena import prompt_arena, PROMPT_LIBRARY, ArenaPromptExecution

router = APIRouter(prefix="/api/qa", tags=["QA Testing Workbench"])


class CustomTestRequest(BaseModel):
    component: str
    custom_input: Optional[Any] = None


@router.get("/inventory")
def get_component_inventory():
    """Returns the comprehensive inventory of GeoAgent components and their implementation state."""
    return {
        "project": "TerraPulse GeoAgent",
        "version": "2.0.0",
        "components": [
            {
                "id": "pollutants",
                "name": "Pollution Intelligence",
                "module": "environmental.pollutants",
                "files": ["terra1/GeoAgent/environmental/pollutants.py"],
                "description": "Solid, liquid, and gaseous pollutant identification and environmental impact explanation.",
                "external_dependencies": [],
                "current_status": "MOCKED",
                "known_findings": "POLLUTANTS dictionary is hardcoded with only 3 substances (mercury, microplastics, sulfur dioxide). All other pollutants return stub fallback.",
            },
            {
                "id": "research",
                "name": "Research & Web Retrieval",
                "module": "environmental.research_apis",
                "files": [
                    "terra1/GeoAgent/environmental/research_apis/aggregator.py",
                    "terra1/GeoAgent/environmental/research_apis/openalex.py",
                    "terra1/GeoAgent/environmental/research_apis/crossref.py",
                    "terra1/GeoAgent/environmental/research_apis/europe_pmc.py",
                    "terra1/GeoAgent/environmental/research_apis/semantic_scholar.py",
                    "terra1/GeoAgent/environmental/research_apis/the_guardian.py",
                    "terra1/GeoAgent/environmental/research_apis/gdelt.py",
                ],
                "description": "Scholarly works search (OpenAlex, Crossref, Europe PMC, Semantic Scholar) and investigative environmental news (The Guardian, GDELT).",
                "external_dependencies": ["OpenAlex API", "Crossref API", "Europe PMC API", "Semantic Scholar API", "GDELT API", "The Guardian Open Platform"],
                "current_status": "PARTIAL / PASS",
                "known_findings": "OpenAlex and Crossref genuinely work without auth. Semantic Scholar suffers frequent HTTP 429 rate-limiting. The Guardian requires API key. Europe PMC encounters Cloudflare 403 blocks.",
            },
            {
                "id": "agent",
                "name": "LLM & Agent Tool Calling",
                "module": "environmental.agent",
                "files": [
                    "terra1/GeoAgent/environmental/agent.py",
                    "terra1/GeoAgent/geoagent/core/agent.py",
                ],
                "description": "Multi-turn conversational investigation agent with session management, clarification logic, and tool invocation stream.",
                "external_dependencies": ["Strands Agent Framework", "OpenAI / Anthropic (in geoagent.core)"],
                "current_status": "MOCKED / SIMULATED",
                "known_findings": "TerraPulseInvestigatorAgent in environmental/agent.py is a deterministic regex intent matching engine that emits synthetic tool-call events with hardcoded latencies (15.0ms).",
            },
            {
                "id": "symptom",
                "name": "Symptom-to-Cause Analysis",
                "module": "environmental.symptom_analyzer",
                "files": ["terra1/GeoAgent/environmental/symptom_analyzer.py"],
                "description": "Natural-language symptom classification, Bradford Hill causal criteria evaluation, and empirical telemetry checking.",
                "external_dependencies": [],
                "current_status": "PARTIAL",
                "known_findings": "Rigorous Bradford Hill structure implemented, but restricted to 5 hardcoded symptom categories in SYMPTOM_CATALOG. Unmatched symptoms produce empty hypotheses.",
            },
            {
                "id": "geospatial",
                "name": "Geospatial Analysis & IDW",
                "module": "environmental.spatial_analysis",
                "files": ["terra1/GeoAgent/environmental/spatial_analysis.py"],
                "description": "Inverse Distance Weighting (IDW) surface interpolation, Getis-Ord Gi* spatial hotspot analysis, and monitoring stations.",
                "external_dependencies": ["numpy", "scipy (optional)"],
                "current_status": "PARTIAL / MOCKED",
                "known_findings": "IDW math and Getis-Ord Gi* algorithms are genuinely implemented in numpy. However, monitoring station datasets are hardcoded samples for only 4 Indian cities.",
            },
            {
                "id": "satellite",
                "name": "Satellite Imagery & STAC",
                "module": "backend.services.satellite",
                "files": ["backend/services/satellite.py", "backend/main.py"],
                "description": "Microsoft Planetary Computer STAC querying for Sentinel-2 L2A and Landsat 8/9 scenes.",
                "external_dependencies": ["pystac_client", "planetary_computer", "Microsoft Planetary Computer STAC"],
                "current_status": "PARTIAL",
                "known_findings": "fetch_real_stac_scenes genuinely queries Planetary Computer. However, /api/imagery/tile color-tints static JPEG files, and /api/imagery/change_mask generates random noise masks (seed 42).",
            },
            {
                "id": "vision",
                "name": "Computer Vision & Change Detection",
                "module": "backend.services.vision & analysis",
                "files": ["backend/services/vision.py", "backend/services/analysis.py"],
                "description": "SIFT feature detection, FLANN matching, RANSAC homography estimation, and historical land-cover evolution trajectories.",
                "external_dependencies": ["OpenCV (cv2)", "numpy"],
                "current_status": "PARTIAL / MOCKED",
                "known_findings": "SIFT + RANSAC homography estimation is genuinely functional with OpenCV. However, historical land-cover trajectories are hardcoded for only 3 regions and silently default to Bengaluru for all other global cities.",
            },
            {
                "id": "geocoding",
                "name": "Worldwide Geocoding & Maps",
                "module": "backend.services.geocoding",
                "files": ["backend/services/geocoding.py", "terra1/GeoAgent/geoagent/tools/geography.py"],
                "description": "Dynamic global location search across OpenStreetMap Nominatim and Komoot Photon with direct coordinate parsing and UTM projection calculations.",
                "external_dependencies": ["OpenStreetMap Nominatim", "Komoot Photon"],
                "current_status": "PASS",
                "known_findings": "Genuinely functional global geocoding with dual API fallback and UTM zone math.",
            },
            {
                "id": "workflow",
                "name": "End-to-End Investigation Agent",
                "module": "backend.services.investigator",
                "files": ["backend/services/investigator.py", "environmental/agent.py"],
                "description": "Complete workflow from natural-language query to multi-source evidence synthesis and GeoJSON map generation.",
                "external_dependencies": [],
                "current_status": "PARTIAL / MOCKED",
                "known_findings": "Pipeline completes and returns synthesized reports, but SUB_AGENTS_MANIFEST (8 sub-agents) is a static decorative UI array.",
            },
        ],
    }


@router.get("/dependencies")
def check_dependencies():
    """Live dependency availability audit."""
    return qa_engine.check_dependencies()


@router.post("/run")
def run_component_test(request: CustomTestRequest):
    """Executes a single component test suite or custom test input."""
    try:
        results = qa_engine.run_component_suite(
            component_name=request.component,
            custom_input=request.custom_input,
        )
        return {
            "status": "COMPLETED",
            "component": request.component,
            "tests_run": len(results),
            "results": [r.to_dict() for r in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@router.post("/run-all")
def run_all_tests():
    """Runs all 9 component black-box verification suites."""
    try:
        return qa_engine.run_all_suites()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@router.get("/history")
def get_test_history():
    """Returns previous test execution results."""
    return {
        "count": len(qa_engine.test_history),
        "history": [r.to_dict() for r in qa_engine.test_history],
    }


@router.get("/export")
def export_report(format: str = Query("markdown", pattern="^(markdown|json)$")):
    """Exports test audit report as Markdown or JSON."""
    if format == "json":
        history = [r.to_dict() for r in qa_engine.test_history]
        return Response(content=json.dumps(history, indent=2), media_type="application/json")
    else:
        md = qa_engine.export_markdown_report()
        return Response(content=md, media_type="text/markdown")


# =============================================================================
# MODULE 1: Integration Testing Lab
# =============================================================================

class IntegrationRunRequest(BaseModel):
    workflow_id: Optional[str] = "INT-01"
    custom_args: Optional[Dict[str, Any]] = None


@router.get("/integration/list")
def list_integration_workflows():
    """Returns list of the 6 multi-component integration workflows."""
    return [
        {
            "id": "INT-01",
            "name": "Pollutant Classification → Environmental Impact Analysis",
            "description": "Tests classification of chemical pollutants into toxicity, transport mechanisms, and long-term environmental hazards.",
            "components": ["environmental.pollutants"],
        },
        {
            "id": "INT-02",
            "name": "Research Retrieval → DOI Verification → Synthesis",
            "description": "Executes live scholarly retrieval via OpenAlex and Crossref, checks real DOI resolution, and synthesizes citations.",
            "components": ["environmental.research_apis.aggregator", "OpenAlex", "Crossref"],
        },
        {
            "id": "INT-03",
            "name": "Symptom Extraction → Cause Analysis → Scholarly Retrieval",
            "description": "Parses environmental symptoms (e.g. fish mortality), evaluates Bradford Hill causal criteria, and triggers targeted academic retrieval.",
            "components": ["environmental.symptom_analyzer", "environmental.research_apis.aggregator"],
        },
        {
            "id": "INT-04",
            "name": "Geocoding → Spatial Processing → Map Rendering",
            "description": "Performs OSM Nominatim geocoding, computes UTM projections, extracts monitoring stations, and constructs GeoJSON layers.",
            "components": ["backend.services.geocoding", "environmental.spatial_analysis"],
        },
        {
            "id": "INT-05",
            "name": "Pollution API → Environmental Analysis → Hotspot Visualization",
            "description": "Extracts telemetry, computes Inverse Distance Weighting (IDW) interpolation surfaces, and evaluates Getis-Ord Gi* hotspot significance.",
            "components": ["environmental.spatial_analysis"],
        },
        {
            "id": "INT-06",
            "name": "Research + Pollution Telemetry → Evidence Synthesis",
            "description": "Tests convergence of empirical ground monitoring telemetry, external scholarly publications, and causal evidence graph generation.",
            "components": ["backend.services.investigator", "environmental.spatial_analysis", "environmental.research_apis"],
        },
    ]


@router.post("/integration/run")
def run_integration_workflow(request: IntegrationRunRequest):
    """Executes a single multi-component integration workflow."""
    wf_id = request.workflow_id or "INT-01"
    args = request.custom_args or {}

    try:
        if wf_id == "INT-01":
            pollutant = args.get("pollutant_name", "mercury")
            res = integration_engine.test_pollutant_to_impact_workflow(pollutant_name=pollutant)
        elif wf_id == "INT-02":
            query = args.get("query", "heavy metal water contamination")
            res = integration_engine.test_research_to_synthesis_workflow(query=query)
        elif wf_id == "INT-03":
            symptom = args.get("symptom_text", "Thousands of dead fish floating on the lake surface with oily sheen")
            res = integration_engine.test_symptom_to_cause_and_research_workflow(symptom_text=symptom)
        elif wf_id == "INT-04":
            location = args.get("location_name", "Bengaluru")
            res = integration_engine.test_geocoding_spatial_map_workflow(location_name=location)
        elif wf_id == "INT-05":
            location = args.get("location_name", "Bengaluru")
            ind = args.get("indicator", "PM2.5")
            res = integration_engine.test_pollution_to_hotspot_visualization_workflow(location_name=location, indicator=ind)
        elif wf_id == "INT-06":
            loc = args.get("location", "Bengaluru")
            topic = args.get("topic", "particulate matter spikes")
            res = integration_engine.test_full_investigation_synthesis_workflow(location=loc, topic=topic)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow ID: {wf_id}")

        return res.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration workflow error: {str(e)}")


@router.post("/integration/run-all")
def run_all_integration_workflows():
    """Runs all 6 multi-component integration workflows."""
    try:
        results = integration_engine.run_all_integration_workflows()
        return {
            "status": "COMPLETED",
            "total_workflows": len(results),
            "workflows": [r.to_dict() for r in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration run-all error: {str(e)}")


# =============================================================================
# MODULE 2: Actual Agent Loop Testing Lab
# =============================================================================

class AgentLoopRunRequest(BaseModel):
    behavior_code: Optional[str] = "A"
    prompt: Optional[str] = None
    location: Optional[str] = None
    indicator: Optional[str] = None


@router.get("/agent-loop/behaviors")
def list_agent_loop_behaviors():
    """Returns list of behaviors A through L tested on the actual agent loop."""
    return [
        {"code": "A", "name": "Single-Tool Invocation", "description": "Verify correct dispatch to a single backend tool for standard queries."},
        {"code": "B", "name": "Multiple Sequential Tool Calls", "description": "Verify multi-step chaining (e.g. Geocoding -> Spatial -> Research)."},
        {"code": "C", "name": "Multiple Independent Tool Calls", "description": "Verify independent retrieval for multi-topic questions."},
        {"code": "D", "name": "Conditional Tool Selection", "description": "Verify appropriate tool choice depending on query semantics."},
        {"code": "E", "name": "Tool Selection Based on Intermediate Results", "description": "Verify agent adapts downstream tools from intermediate outputs."},
        {"code": "F", "name": "Handling of Missing Information", "description": "Verify agent halts to ask clarification when required parameters are absent."},
        {"code": "G", "name": "Tool Failure & Resilient Recovery", "description": "Verify agent gracefully handles external API failures without crashing."},
        {"code": "H", "name": "Invalid Tool Arguments", "description": "Verify handling of invalid coordinates, non-existent locations, or malformed inputs."},
        {"code": "I", "name": "Repeated/Unnecessary Tool Call Prevention", "description": "Verify agent does not invoke tools for simple greetings or non-environmental queries."},
        {"code": "J", "name": "Infinite-Loop Prevention & Termination", "description": "Verify agent halts within safe iteration bound."},
        {"code": "K", "name": "Correct Termination & Response Assembly", "description": "Verify final synthesized answer includes required sections and data."},
        {"code": "L", "name": "Hallucination Detection on Unknown Substances", "description": "Verify agent explicitly denies or admits lack of knowledge for invented pollutants."},
    ]


@router.post("/agent-loop/run")
def run_agent_loop_test(request: AgentLoopRunRequest):
    """Executes a prompt against the live agent loop and analyzes behaviors."""
    code = request.behavior_code or "A"
    prompt = request.prompt
    location = request.location
    indicator = request.indicator

    # Default prompts per behavior if not provided
    prompts_map = {
        "A": ("Single-Tool Invocation", "What are the environmental impacts of mercury?"),
        "B": ("Multiple Sequential Tool Calls", "Investigate water pollution in Bellandur Lake, Bengaluru"),
        "C": ("Multiple Independent Tool Calls", "Compare sulfur dioxide impacts and air quality in New Delhi"),
        "D": ("Conditional Tool Selection", "Analyze vegetation changes in the Amazon rainforest"),
        "E": ("Tool Selection Based on Intermediate Results", "Why is air pollution increasing in Chennai?"),
        "F": ("Handling of Missing Information", "Thousands of fish are dying in a lake. What is the cause?"),
        "G": ("Tool Failure & Resilient Recovery", "Find medical papers on mercury poisoning in lakes"),
        "H": ("Invalid Tool Arguments", "Analyze air pollution in NonExistentCity99999"),
        "I": ("Repeated/Unnecessary Tool Call Prevention", "Hello, who are you and what can you do?"),
        "J": ("Infinite-Loop Prevention & Termination", "Explain why lakes foam and compare alternative theories"),
        "K": ("Correct Termination & Response Assembly", "What is the highest mountain peak in India?"),
        "L": ("Hallucination Detection on Unknown Substances", "What is the environmental toxicity of chemical XYZ-Fake-99?"),
    }

    name, default_prompt = prompts_map.get(code, ("Custom Behavior", prompt or "Analyze environmental data"))
    active_prompt = prompt if prompt else default_prompt

    try:
        trace = agent_loop_lab.run_agent_loop_test(
            prompt=active_prompt,
            behavior_code=code,
            behavior_name=name,
            location=location,
            indicator=indicator,
        )
        return trace.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent loop execution error: {str(e)}")


@router.post("/agent-loop/run-all")
def run_all_agent_loop_tests():
    """Runs all 12 behavior tests (A through L) against the live agent loop."""
    try:
        traces = agent_loop_lab.run_all_behavior_tests()
        return {
            "status": "COMPLETED",
            "total_behaviors": len(traces),
            "traces": [t.to_dict() for t in traces],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent loop run-all error: {str(e)}")


# =============================================================================
# MODULE 3, 4, 5: Natural-Language Prompt Arena & Evaluation Engine
# =============================================================================

class ArenaPromptRunRequest(BaseModel):
    prompt: str
    prompt_id: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    expected_outcomes: Optional[List[str]] = None


class ArenaBatchRequest(BaseModel):
    prompt_ids: Optional[List[str]] = None


@router.get("/arena/prompts")
def get_arena_prompts():
    """Returns the 14-category prompt library."""
    return prompt_arena.get_prompt_library()


@router.post("/arena/run")
def run_arena_prompt(request: ArenaPromptRunRequest):
    """Submits a single prompt to the arena and produces a 10-criteria evaluation."""
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty.")

    try:
        res = prompt_arena.execute_prompt(
            prompt=request.prompt,
            category_id=request.category_id,
            category_name=request.category_name,
            expected_outcomes=request.expected_outcomes,
            prompt_id=request.prompt_id,
        )
        return res.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt Arena execution error: {str(e)}")


@router.post("/arena/run-batch")
def run_arena_batch(request: ArenaBatchRequest):
    """Runs batch execution across the 14-category library."""
    try:
        results = prompt_arena.execute_batch(prompt_ids=request.prompt_ids)
        return {
            "status": "COMPLETED",
            "total_prompts": len(results),
            "results": [r.to_dict() for r in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt Arena batch error: {str(e)}")


@router.get("/arena/history")
def get_arena_history():
    """Returns history of prompt arena runs."""
    return {
        "count": len(prompt_arena.history),
        "history": [r.to_dict() for r in prompt_arena.history],
    }


# =============================================================================
# MODULE 6: Final Test Reports Center
# =============================================================================

@router.get("/reports/{report_type}")
def get_specialized_report(report_type: str, format: str = Query("markdown", pattern="^(markdown|json)$")):
    """Retrieves specialized test reports:
    - component: Component-wise testing report
    - integration: Multi-component integration workflow report
    - agent_loop: Actual agent loop behaviors (A-L) report
    - prompt_arena: Natural-language prompt arena evaluation report
    - authenticity: Authenticity, mocks, and hardcoded stubs report
    - readiness: Overall project production readiness assessment
    """
    valid_types = ["component", "integration", "agent_loop", "prompt_arena", "authenticity", "readiness"]
    if report_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}")

    # Check artifacts directory first for deep persisted reports
    artifact_dir = r"C:\Users\rishi\.gemini\antigravity\brain\5635aaba-6f41-4d06-b102-9ca1f2a29689"
    file_map = {
        "component": "component_test_reports.md",
        "integration": "e2e_workflow_report.md",
        "agent_loop": "component_test_reports.md",
        "prompt_arena": "e2e_workflow_report.md",
        "authenticity": "mock_implementation_report.md",
        "readiness": "project_readiness_report.md",
    }

    target_file = os.path.join(artifact_dir, file_map.get(report_type, "project_readiness_report.md"))
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = f"# GeoAgent QA Report: {report_type.upper()}\n\nReport generated dynamically from QA Engine."

    if format == "json":
        return {"report_type": report_type, "content": content}
    else:
        return Response(content=content, media_type="text/markdown")

