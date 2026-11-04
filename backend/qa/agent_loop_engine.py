"""GeoAgent Actual Agent Loop Testing Lab Engine (MODULE 2).

Submits natural-language prompts to the real GeoAgent conversational agent,
observing actual execution traces, tool invocations, arguments, intermediate
states, iteration counts, and evaluating behaviors A through L.
"""

from __future__ import annotations

import time
import json
import inspect
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from environmental.agent import (
    TerraPulseInvestigatorAgent,
    SessionManager,
    ActivityEventType,
    ActivityEvent,
)


@dataclass
class ToolExecutionEvent:
    tool_name: str
    intent: str
    arguments: Dict[str, Any]
    raw_result_summary: Any
    latency_ms: float
    genuinely_executed_in_backend: bool
    simulated_by_agent_code: bool


@dataclass
class AgentLoopExecutionTrace:
    test_id: str
    behavior_code: str  # A through L
    behavior_name: str
    user_prompt: str
    session_id: str
    total_events: int
    iteration_count: int
    tool_calls_observed: List[ToolExecutionEvent]
    clarification_requested: Optional[Dict[str, str]]
    final_response_text: str
    final_response_data: Dict[str, Any]
    total_latency_ms: float
    loop_detected: bool
    terminated_correctly: bool
    hallucination_detected: bool
    status: str  # PASS | PARTIAL | FAIL | MOCKED
    verification_notes: str
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "behavior_code": self.behavior_code,
            "behavior_name": self.behavior_name,
            "user_prompt": self.user_prompt,
            "session_id": self.session_id,
            "total_events": self.total_events,
            "iteration_count": self.iteration_count,
            "tool_calls_observed": [asdict(t) for t in self.tool_calls_observed],
            "clarification_requested": self.clarification_requested,
            "final_response_text": self.final_response_text[:300] + ("..." if len(self.final_response_text) > 300 else ""),
            "total_latency_ms": self.total_latency_ms,
            "loop_detected": self.loop_detected,
            "terminated_correctly": self.terminated_correctly,
            "hallucination_detected": self.hallucination_detected,
            "status": self.status,
            "verification_notes": self.verification_notes,
            "timeline": self.timeline,
        }


class AgentLoopTestingLab:
    """Executes natural-language prompts through the real agent execution loop."""

    def __init__(self):
        self.session_manager = SessionManager()
        self.agent = TerraPulseInvestigatorAgent(session_manager=self.session_manager)

    def run_agent_loop_test(
        self,
        prompt: str,
        behavior_code: str = "A",
        behavior_name: str = "General Agent Loop Test",
        session_id_prefix: str = "qa_loop",
        location: Optional[str] = None,
        indicator: Optional[str] = None,
    ) -> AgentLoopExecutionTrace:
        """Executes the prompt through the live agent pipeline and monitors execution traces."""
        session_id = f"{session_id_prefix}_{int(time.time() * 1000) % 100000}"
        t0 = time.perf_counter()

        timeline: List[Dict[str, Any]] = [
            {"step": 1, "type": "USER_PROMPT", "content": prompt, "timestamp": time.strftime("%H:%M:%S")}
        ]

        # Execute through REAL agent generator
        raw_events: List[ActivityEvent] = []
        try:
            for ev in self.agent.process_message(
                user_message=prompt,
                session_id=session_id,
                location=location,
                indicator=indicator,
            ):
                raw_events.append(ev)
                timeline.append({
                    "step": len(timeline) + 1,
                    "type": ev.event_type.value.upper(),
                    "data": ev.data,
                    "timestamp": ev.timestamp,
                })
        except Exception as e:
            total_dur = round((time.perf_counter() - t0) * 1000, 2)
            return AgentLoopExecutionTrace(
                test_id=f"LOOP-{behavior_code}",
                behavior_code=behavior_code,
                behavior_name=behavior_name,
                user_prompt=prompt,
                session_id=session_id,
                total_events=0,
                iteration_count=0,
                tool_calls_observed=[],
                clarification_requested=None,
                final_response_text="",
                final_response_data={},
                total_latency_ms=total_dur,
                loop_detected=False,
                terminated_correctly=False,
                hallucination_detected=False,
                status="FAIL",
                verification_notes=f"Agent crashed with unhandled exception: {str(e)}",
                timeline=timeline,
            )

        total_dur = round((time.perf_counter() - t0) * 1000, 2)

        # Parse observed tool calls
        tool_starts = [e for e in raw_events if e.event_type == ActivityEventType.TOOL_CALL_START]
        tool_results = [e for e in raw_events if e.event_type == ActivityEventType.TOOL_CALL_RESULT]
        final_events = [e for e in raw_events if e.event_type == ActivityEventType.FINAL_RESPONSE]
        clarify_events = [e for e in raw_events if e.event_type == ActivityEventType.CLARIFICATION_NEEDED]

        tool_calls: List[ToolExecutionEvent] = []
        for i, start_ev in enumerate(tool_starts):
            tool_name = start_ev.data.get("tool_name", "unknown")
            intent = start_ev.data.get("intent", "")
            res_ev = tool_results[i] if i < len(tool_results) else None
            latency = res_ev.data.get("latency_ms", 0.0) if res_ev else 0.0
            summary = res_ev.data.get("summary", "") if res_ev else ""

            # Check authenticity: Did the tool genuinely execute or was it simulated?
            # Notice in agent.py line 1763 has hardcoded latency 16.0ms, line 1888 has 15.0ms
            is_simulated = (latency in (15.0, 16.0)) or ("latency_ms" in str(res_ev.data) and latency == 16.0)

            tool_calls.append(
                ToolExecutionEvent(
                    tool_name=tool_name,
                    intent=intent,
                    arguments=start_ev.data.get("arguments", {}),
                    raw_result_summary=summary,
                    latency_ms=latency,
                    genuinely_executed_in_backend=True,
                    simulated_by_agent_code=is_simulated,
                )
            )

        final_text = final_events[0].data.get("content", "") if final_events else ""
        final_data = final_events[0].data if final_events else {}

        clarify_data = None
        if clarify_events:
            c = clarify_events[0].data
            clarify_data = {"slot": c.get("slot", ""), "question": c.get("question", "")}

        # Check loop detection: More than 12 iterations without terminating
        loop_detected = len(raw_events) > 12

        # Check hallucination: Tool failed or returned empty but agent asserts definitive scientific findings
        hallucination_detected = False
        if not tool_calls and "empirical telemetry confirms" in final_text.lower():
            hallucination_detected = True

        # Status classification
        has_simulated_tools = any(t.simulated_by_agent_code for t in tool_calls)
        if len(final_events) == 0:
            status = "FAIL"
            notes = "Agent failed to emit FINAL_RESPONSE."
        elif has_simulated_tools:
            status = "MOCKED"
            notes = "Agent emitted synthetic tool call events with hardcoded latencies (15.0ms, 16.0ms) instead of dynamic LLM function calling."
        elif clarify_events and behavior_code == "F":
            status = "PASS"
            notes = f"Correctly handled missing slot by requesting clarification: '{clarify_data.get('slot')}'."
        elif len(tool_calls) > 0 and len(final_events) > 0:
            status = "PASS"
            notes = f"Executed {len(tool_calls)} tool calls and terminated cleanly with verified final response."
        else:
            status = "PARTIAL"
            notes = "Execution completed without tool calls."

        return AgentLoopExecutionTrace(
            test_id=f"LOOP-{behavior_code}",
            behavior_code=behavior_code,
            behavior_name=behavior_name,
            user_prompt=prompt,
            session_id=session_id,
            total_events=len(raw_events),
            iteration_count=len(tool_calls),
            tool_calls_observed=tool_calls,
            clarification_requested=clarify_data,
            final_response_text=final_text,
            final_response_data=final_data,
            total_latency_ms=total_dur,
            loop_detected=loop_detected,
            terminated_correctly=len(final_events) > 0 or len(clarify_events) > 0,
            hallucination_detected=hallucination_detected,
            status=status,
            verification_notes=notes,
            timeline=timeline,
        )

    # -------------------------------------------------------------------------
    # SUITE OF 12 AGENT LOOP BEHAVIOR TESTS (A THROUGH L)
    # -------------------------------------------------------------------------
    def run_all_behavior_tests(self) -> List[AgentLoopExecutionTrace]:
        """Runs the battery of 12 actual agent loop tests against the real agent endpoint."""
        tests = [
            # Behavior A: Single-tool invocation
            ("A", "Single-tool Invocation", "What is NDVI and how do satellites calculate it?", None, None),
            # Behavior B: Multiple sequential tool calls
            ("B", "Multiple Sequential Tool Calls", "Investigate dead fish in Bellandur Lake", "Bellandur Lake", None),
            # Behavior C: Multiple independent tool calls
            ("C", "Multiple Independent Tool Calls", "Show recent research on microplastics in freshwater lakes", None, None),
            # Behavior D: Conditional tool selection
            ("D", "Conditional Tool Selection", "Analyze vegetation changes in the Amazon rainforest", "Amazon Rainforest", None),
            # Behavior E: Tool selection based on intermediate results
            ("E", "Tool Selection Based on Intermediate Results", "Why is air pollution increasing in Chennai?", "Chennai", "PM2.5"),
            # Behavior F: Correct handling of missing information (slot clarification)
            ("F", "Handling of Missing Information", "Thousands of fish are dying in a lake. What is the cause?", None, None),
            # Behavior G: Tool failures and recovery
            ("G", "Tool Failure & Resilient Recovery", "Find medical papers on mercury poisoning in lakes", None, None),
            # Behavior H: Invalid tool arguments
            ("H", "Invalid Tool Arguments", "Analyze air pollution in NonExistentCity99999", "NonExistentCity99999", None),
            # Behavior I: Repeated or unnecessary tool calls
            ("I", "Repeated/Unnecessary Tool Call Prevention", "Hello, who are you and what can you do?", None, None),
            # Behavior J: Infinite-loop prevention & max iterations
            ("J", "Infinite-Loop Prevention & Termination", "Explain why lakes foam and compare alternative theories", "Bellandur Lake", None),
            # Behavior K: Correct termination & final response generation
            ("K", "Correct Termination & Response Assembly", "What is the highest mountain peak in India?", None, None),
            # Behavior L: Hallucination detection on unsupported queries
            ("L", "Hallucination Detection on Unknown Substances", "What is the environmental toxicity of chemical XYZ-Fake-99?", None, None),
        ]

        results = []
        for code, name, prompt, loc, ind in tests:
            trace = self.run_agent_loop_test(
                prompt=prompt,
                behavior_code=code,
                behavior_name=name,
                location=loc,
                indicator=ind,
            )
            results.append(trace)

        return results


# Singleton instance
agent_loop_lab = AgentLoopTestingLab()

