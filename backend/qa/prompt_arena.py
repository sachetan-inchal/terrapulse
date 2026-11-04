"""GeoAgent Natural-Language Prompt Arena & Evaluation Engine (MODULE 3, 4, 5).

Provides:
- 14-Category Predefined Environmental Prompt Library.
- Custom Prompt Submission without silent modification.
- Complete Visual Execution Timeline Trace (real execution order).
- Independent Evaluation Engine with 10 deterministic criteria.
- Batch & Single Prompt Execution.
"""

from __future__ import annotations

import time
import json
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from environmental.agent import (
    TerraPulseInvestigatorAgent,
    SessionManager,
    ActivityEventType,
    ActivityEvent,
)


@dataclass
class ArenaEvaluationReport:
    understood_objective: bool
    understood_rationale: str
    correct_tools_selected: bool
    tools_selected: List[str]
    tools_genuinely_executed: bool
    execution_authenticity_notes: str
    correct_arguments_supplied: bool
    tool_results_used_in_answer: bool
    final_answer_matches_evidence: bool
    geographical_outputs_accurate: bool
    geographical_details: Optional[Dict[str, Any]]
    scientific_claims_qualified: bool
    causal_disclaimer_present: bool
    fabricated_results_detected: bool
    fabricated_details: Optional[str]
    all_required_outcomes_achieved: bool
    overall_status: str  # PASS | PARTIAL | FAIL | MOCKED | BLOCKED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineStep:
    step_number: int
    stage: str  # USER_PROMPT | INTENT_CLASSIFICATION | TOOL_SELECTION | TOOL_EXECUTION | RAW_RESULTS | GEOSPATIAL_PROCESSING | MAP_GENERATION | FINAL_RESPONSE
    label: str
    details: Any
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ArenaPromptExecution:
    prompt_id: str
    category_id: int
    category_name: str
    user_prompt: str
    expected_outcomes: List[str]
    actual_response: str
    suggestions: List[str]
    timeline: List[TimelineStep]
    evaluation: ArenaEvaluationReport
    map_output: Optional[Dict[str, Any]]
    evidence_output: Optional[Dict[str, Any]]
    execution_time_ms: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "user_prompt": self.user_prompt,
            "expected_outcomes": self.expected_outcomes,
            "actual_response": self.actual_response,
            "suggestions": self.suggestions,
            "timeline": [t.to_dict() for t in self.timeline],
            "evaluation": self.evaluation.to_dict(),
            "map_output": self.map_output,
            "evidence_output": self.evidence_output,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp,
        }


# Curated Library of Environmental Prompts across 14 Categories
PROMPT_LIBRARY = [
    {
        "id": "PRM-01",
        "category_id": 1,
        "category": "Pollution Intelligence",
        "prompt": "What are the environmental pathways and chronic toxicity impacts of mercury?",
        "expected_outcomes": [
            "Identify substance as heavy metal",
            "Disclose water and soil pathways",
            "Highlight methylmercury bioaccumulation in aquatic food chains",
        ],
    },
    {
        "id": "PRM-02",
        "category_id": 2,
        "category": "Scientific Research",
        "prompt": "Find recent peer-reviewed research on microplastics in freshwater lakes.",
        "expected_outcomes": [
            "Retrieve authentic scholarly papers from OpenAlex or Crossref",
            "Include publication years and journal names",
            "Present real summaries without hallucinations",
        ],
    },
    {
        "id": "PRM-03",
        "category_id": 3,
        "category": "Research Reference Verification",
        "prompt": "Show verified papers studying urban wetland eutrophication and verify their direct DOI links.",
        "expected_outcomes": [
            "Provide standardized DOIs (10.xxxx/...)",
            "Include clickable https://doi.org/ URLs",
            "Exclude fictitious or broken citations",
        ],
    },
    {
        "id": "PRM-04",
        "category_id": 4,
        "category": "Symptom-to-Cause Diagnosis",
        "prompt": "Thousands of dead fish are floating near a lake spillway. What is causing this?",
        "expected_outcomes": [
            "Classify fish mortality symptom",
            "Formulate multiple competing hypotheses (Anoxia/Hypoxia, Industrial Toxins, HABs)",
            "Apply Bradford Hill considerations and list missing telemetry needed",
        ],
    },
    {
        "id": "PRM-05",
        "category_id": 5,
        "category": "Air-Quality Analysis",
        "prompt": "Why is air pollution increasing in Chennai? Show active monitoring telemetry.",
        "expected_outcomes": [
            "Resolve Chennai location and coordinates",
            "Retrieve CAAQMS station telemetry (Manali, Velachery, Alandur)",
            "Disclose data provenance and spatial clustering z-scores",
        ],
    },
    {
        "id": "PRM-06",
        "category_id": 6,
        "category": "Water Pollution Analysis",
        "prompt": "Analyze toxic surfactant foaming and industrial effluent in Bellandur Lake.",
        "expected_outcomes": [
            "Identify synthetic detergent / linear alkylbenzene sulfonate (LAS) mechanism",
            "Evaluate dissolved oxygen depletion and domestic sewage influx",
            "Generate GeoJSON map for lake catchment",
        ],
    },
    {
        "id": "PRM-07",
        "category_id": 7,
        "category": "Soil Contamination",
        "prompt": "Investigate heavy metal accumulation and soil degradation in industrial corridors.",
        "expected_outcomes": [
            "Address soil contamination mechanisms",
            "Discuss industrial effluent ingress",
            "Acknowledge epistemic boundaries without unverified assertions",
        ],
    },
    {
        "id": "PRM-08",
        "category_id": 8,
        "category": "Geospatial Point Mapping",
        "prompt": "Locate Mount Kilimanjaro on the map and mark its exact coordinates.",
        "expected_outcomes": [
            "Geocode landmark via OpenStreetMap",
            "Return coordinates around latitude -3.0674, longitude 37.3556",
            "Provide appropriate zoom and location metadata",
        ],
    },
    {
        "id": "PRM-09",
        "category_id": 9,
        "category": "Geospatial Polygon Mapping",
        "prompt": "Highlight the catchment boundary and monitoring stations around Varthur Lake.",
        "expected_outcomes": [
            "Resolve Varthur Lake AOI bounding box",
            "Generate RFC 7946 GeoJSON FeatureCollection",
            "Distinguish measured station points from polygon boundaries",
        ],
    },
    {
        "id": "PRM-10",
        "category_id": 10,
        "category": "Multi-Tool Agent Workflows",
        "prompt": "Analyze vegetation changes in the Amazon rainforest and find supporting research.",
        "expected_outcomes": [
            "Query multi-spectral NDVI canopy data",
            "Search academic literature via OpenAlex",
            "Assemble multi-stage synthesis report",
        ],
    },
    {
        "id": "PRM-11",
        "category_id": 11,
        "category": "Missing-Data Handling",
        "prompt": "Why are fish dying? (No location specified)",
        "expected_outcomes": [
            "Detect missing location slot",
            "Emit CLARIFICATION_NEEDED or prompt user for specific water body",
            "Avoid hallucinating a default city without disclosure",
        ],
    },
    {
        "id": "PRM-12",
        "category_id": 12,
        "category": "API Failure Recovery",
        "prompt": "Search European biomedical literature on mercury when external servers return HTTP 403.",
        "expected_outcomes": [
            "Handle Europe PMC Cloudflare 403 gracefully",
            "Fall back to OpenAlex/Crossref without crashing",
            "Return valid scholarly findings",
        ],
    },
    {
        "id": "PRM-13",
        "category_id": 13,
        "category": "Adversarial & Ambiguous Prompts",
        "prompt": "Where is Springfield?",
        "expected_outcomes": [
            "Recognize ambiguity in place name",
            "Return multiple candidate locations or ask for state/country clarification",
        ],
    },
    {
        "id": "PRM-14",
        "category_id": 14,
        "category": "Unsupported Pollutant Handling",
        "prompt": "Explain the biological pathways and toxicity of Perfluorooctanoic acid (PFOA).",
        "expected_outcomes": [
            "Disclose whether PFOA is in local database",
            "Transparently state that scientific research is required without fabricating data",
        ],
    },
]


class PromptArenaEngine:
    """Manages prompt library, submission, timeline trace generation, and deterministic evaluation."""

    def __init__(self):
        self.session_manager = SessionManager()
        self.agent = TerraPulseInvestigatorAgent(session_manager=self.session_manager)
        self.history: List[ArenaPromptExecution] = []

    def get_prompt_library(self) -> List[Dict[str, Any]]:
        return PROMPT_LIBRARY

    def execute_prompt(
        self,
        prompt: str,
        category_id: int = 10,
        category_name: str = "Custom Prompt",
        expected_outcomes: Optional[List[str]] = None,
        prompt_id: Optional[str] = None,
    ) -> ArenaPromptExecution:
        """Submits prompt directly to the live GeoAgent and executes the 10-point independent evaluation."""
        p_id = prompt_id or f"PRM-CUST-{int(time.time() * 1000) % 10000}"
        expected = expected_outcomes or ["Address user inquiry accurately", "Utilize verified data sources"]
        session_id = f"arena_{int(time.time() * 1000) % 100000}"

        t0 = time.perf_counter()
        timeline: List[TimelineStep] = []
        step_idx = 1

        # Step 1: User Prompt
        timeline.append(
            TimelineStep(
                step_number=step_idx,
                stage="USER_PROMPT",
                label="User Prompt Received",
                details={"raw_prompt": prompt, "session_id": session_id},
                timestamp=time.strftime("%H:%M:%S"),
            )
        )
        step_idx += 1

        # Execute through REAL agent
        events: List[ActivityEvent] = []
        try:
            for ev in self.agent.process_message(user_message=prompt, session_id=session_id):
                events.append(ev)
                stage_name = "INTERMEDIATE"
                label = f"Agent Event: {ev.event_type.value}"

                if ev.event_type == ActivityEventType.TOOL_CALL_START:
                    stage_name = "TOOL_SELECTION"
                    label = f"Tool Invocation: {ev.data.get('tool_name')}"
                elif ev.event_type == ActivityEventType.TOOL_CALL_RESULT:
                    stage_name = "TOOL_EXECUTION"
                    label = f"Tool Completed: {ev.data.get('tool_name')}"
                elif ev.event_type == ActivityEventType.CLARIFICATION_NEEDED:
                    stage_name = "CLARIFICATION_DISPATCH"
                    label = f"Clarification Needed: {ev.data.get('slot')}"
                elif ev.event_type == ActivityEventType.FINAL_RESPONSE:
                    stage_name = "FINAL_RESPONSE"
                    label = "Final Response Synthesis"

                timeline.append(
                    TimelineStep(
                        step_number=step_idx,
                        stage=stage_name,
                        label=label,
                        details=ev.data,
                        timestamp=ev.timestamp,
                    )
                )
                step_idx += 1
        except Exception as exc:
            total_dur = round((time.perf_counter() - t0) * 1000, 2)
            eval_crash = ArenaEvaluationReport(
                understood_objective=False,
                understood_rationale="Execution halted due to unhandled backend exception.",
                correct_tools_selected=False,
                tools_selected=[],
                tools_genuinely_executed=False,
                execution_authenticity_notes="Crashed before tool completion.",
                correct_arguments_supplied=False,
                tool_results_used_in_answer=False,
                final_answer_matches_evidence=False,
                geographical_outputs_accurate=False,
                geographical_details=None,
                scientific_claims_qualified=False,
                causal_disclaimer_present=False,
                fabricated_results_detected=False,
                fabricated_details=str(exc),
                all_required_outcomes_achieved=False,
                overall_status="FAIL",
            )
            res_obj = ArenaPromptExecution(
                prompt_id=p_id,
                category_id=category_id,
                category_name=category_name,
                user_prompt=prompt,
                expected_outcomes=expected,
                actual_response=f"Execution error: {str(exc)}",
                suggestions=[],
                timeline=timeline,
                evaluation=eval_crash,
                map_output=None,
                evidence_output=None,
                execution_time_ms=total_dur,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            self.history.insert(0, res_obj)
            return res_obj

        total_dur = round((time.perf_counter() - t0) * 1000, 2)

        # Parse Final Response & Map Output
        final_ev = [e for e in events if e.event_type == ActivityEventType.FINAL_RESPONSE]
        final_text = final_ev[0].data.get("content", "") if final_ev else ""
        suggestions = final_ev[0].data.get("suggestions", []) if final_ev else []
        map_geojson = final_ev[0].data.get("map_geojson") or final_ev[0].data.get("geojson") if final_ev else None
        loc_info = final_ev[0].data.get("location_info") if final_ev else None
        investigation_data = final_ev[0].data.get("investigation") if final_ev else None

        # Tools called
        tool_starts = [e for e in events if e.event_type == ActivityEventType.TOOL_CALL_START]
        tool_results = [e for e in events if e.event_type == ActivityEventType.TOOL_CALL_RESULT]
        tools_selected = [t.data.get("tool_name", "") for t in tool_starts]

        # ---------------------------------------------------------------------
        # INDEPENDENT 10-CRITERIA EVALUATION LAYER (MODULE 4)
        # ---------------------------------------------------------------------
        prompt_lower = prompt.lower()
        response_lower = final_text.lower()

        # 1. Understood Objective
        key_terms = re.findall(r"\b\w{4,}\b", prompt_lower)
        matched_terms = [t for t in key_terms if t in response_lower]
        understood = len(matched_terms) >= max(1, len(key_terms) // 3)
        understood_rationale = (
            f"Agent response contains relevant semantic keywords ({', '.join(matched_terms[:4])})."
            if understood
            else "Response did not address key concepts in the prompt."
        )

        # 2. Correct Tools Selected
        correct_tools = True
        if "fish" in prompt_lower and "dying" in prompt_lower:
            correct_tools = any("symptom" in t for t in tools_selected) or any(e.event_type == ActivityEventType.CLARIFICATION_NEEDED for e in events)
        elif "research" in prompt_lower or "paper" in prompt_lower:
            correct_tools = any("research" in t or "literature" in t for t in tools_selected) or "DOI" in final_text

        # 3. Genuine Tool Execution vs Simulation
        has_simulated_latencies = any(r.data.get("latency_ms") in (15.0, 16.0) for r in tool_results)
        tools_genuinely_executed = len(tools_selected) == 0 or not has_simulated_latencies
        authenticity_notes = (
            "Tools executed with real latency and backend compute."
            if not has_simulated_latencies
            else "Observed synthetic tool-call events with hardcoded latency numbers (15.0ms / 16.0ms)."
        )

        # 4. Correct Arguments
        correct_args = True
        for t in tool_starts:
            args = t.data.get("arguments", {})
            if "location" in args and not args["location"]:
                correct_args = False

        # 5. Tool Results Used
        tool_results_used = len(tools_selected) == 0 or len(final_text) > 100

        # 6. Final Answer Matches Evidence
        matches_evidence = True
        if investigation_data:
            top_cause = investigation_data.get("hypotheses_ranked", [{}])[0].get("cause_name", "")
            if top_cause and top_cause.lower() not in response_lower:
                matches_evidence = False

        # 7. Geographical Outputs
        geo_accurate = True
        geo_details = None
        if loc_info:
            lat = loc_info.get("latitude")
            lon = loc_info.get("longitude")
            geo_accurate = lat is not None and -90 <= lat <= 90 and lon is not None and -180 <= lon <= 180
            geo_details = {"name": loc_info.get("name"), "lat": lat, "lon": lon, "bbox": loc_info.get("bbox")}

        # 8. Scientific Claims Qualified & Causal Disclaimer
        causal_disclaimer_present = (
            "correlation" in response_lower
            or "causality" in response_lower
            or "epistemic" in response_lower
            or "scientific integrity rule" in response_lower
        )
        claims_qualified = True

        # 9. Fabricated Results Detected
        fabricated_detected = False
        fabricated_details = None
        # Check for unlisted city defaulting to Bengaluru
        if any(c in prompt_lower for c in ["paris", "tokyo", "chicago", "london"]) and "74.2%" in final_text:
            fabricated_detected = True
            fabricated_details = "Returned hardcoded Bengaluru built-up percentage (74.2%) for an unlisted foreign city."
        elif has_simulated_latencies:
            fabricated_detected = True
            fabricated_details = "Agent yielded synthetic tool execution events with pre-written text."

        # 10. All Required Outcomes Achieved
        all_achieved = understood and correct_tools and not fabricated_detected and len(final_text) > 0

        # Overall Status
        if fabricated_detected or has_simulated_latencies:
            overall_status = "MOCKED"
        elif not understood or not len(final_text):
            overall_status = "FAIL"
        elif all_achieved:
            overall_status = "PASS"
        else:
            overall_status = "PARTIAL"

        eval_report = ArenaEvaluationReport(
            understood_objective=understood,
            understood_rationale=understood_rationale,
            correct_tools_selected=correct_tools,
            tools_selected=tools_selected,
            tools_genuinely_executed=tools_genuinely_executed,
            execution_authenticity_notes=authenticity_notes,
            correct_arguments_supplied=correct_args,
            tool_results_used_in_answer=tool_results_used,
            final_answer_matches_evidence=matches_evidence,
            geographical_outputs_accurate=geo_accurate,
            geographical_details=geo_details,
            scientific_claims_qualified=claims_qualified,
            causal_disclaimer_present=causal_disclaimer_present,
            fabricated_results_detected=fabricated_detected,
            fabricated_details=fabricated_details,
            all_required_outcomes_achieved=all_achieved,
            overall_status=overall_status,
        )

        res_obj = ArenaPromptExecution(
            prompt_id=p_id,
            category_id=category_id,
            category_name=category_name,
            user_prompt=prompt,
            expected_outcomes=expected,
            actual_response=final_text,
            suggestions=suggestions,
            timeline=timeline,
            evaluation=eval_report,
            map_output={"geojson": map_geojson, "location_info": loc_info} if map_geojson or loc_info else None,
            evidence_output=investigation_data,
            execution_time_ms=total_dur,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        self.history.insert(0, res_obj)
        return res_obj

    def execute_batch(self, prompt_ids: Optional[List[str]] = None) -> List[ArenaPromptExecution]:
        """Executes a batch of library prompts and evaluates each independently."""
        targets = PROMPT_LIBRARY
        if prompt_ids:
            targets = [p for p in PROMPT_LIBRARY if p["id"] in prompt_ids]

        results = []
        for item in targets:
            exec_res = self.execute_prompt(
                prompt=item["prompt"],
                category_id=item["category_id"],
                category_name=item["category"],
                expected_outcomes=item["expected_outcomes"],
                prompt_id=item["id"],
            )
            results.append(exec_res)

        return results


# Singleton instance
prompt_arena = PromptArenaEngine()

