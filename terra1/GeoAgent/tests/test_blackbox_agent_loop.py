"""Black-Box tests for GeoAgent Actual Agent Loop Testing Lab (MODULE 2)."""

import pytest
from backend.qa.agent_loop_engine import agent_loop_lab


class TestAgentLoopLab:
    """Tests the real GeoAgent agent loop through natural-language prompts,
    capturing actual events and distinguishing genuine vs simulated executions."""

    def test_behavior_a_single_tool(self):
        """Behavior A: Single-tool invocation."""
        trace = agent_loop_lab.run_agent_loop_test(
            prompt="What are the environmental impacts of mercury?",
            behavior_code="A",
            behavior_name="Single-Tool Invocation",
        )
        assert trace.behavior_code == "A"
        assert trace.terminated_correctly is True
        assert trace.loop_detected is False
        assert len(trace.timeline) > 0

    def test_behavior_f_missing_information_slot_filling(self):
        """Behavior F: Handling of missing information (slot clarification)."""
        trace = agent_loop_lab.run_agent_loop_test(
            prompt="Thousands of fish are dying in a lake. What is the cause?",
            behavior_code="F",
            behavior_name="Handling of Missing Information",
        )
        assert trace.behavior_code == "F"
        assert trace.terminated_correctly is True

    def test_behavior_i_unnecessary_tool_prevention(self):
        """Behavior I: Repeated or unnecessary tool calls for casual greetings."""
        trace = agent_loop_lab.run_agent_loop_test(
            prompt="Hello, who are you and what can you do?",
            behavior_code="I",
            behavior_name="Repeated/Unnecessary Tool Call Prevention",
        )
        assert trace.behavior_code == "I"
        assert len(trace.tool_calls_observed) == 0
        assert trace.terminated_correctly is True

    def test_behavior_l_hallucination_detection(self):
        """Behavior L: Hallucination detection on unknown chemical."""
        trace = agent_loop_lab.run_agent_loop_test(
            prompt="What is the environmental toxicity of chemical XYZ-Fake-99?",
            behavior_code="L",
            behavior_name="Hallucination Detection on Unknown Substances",
        )
        assert trace.behavior_code == "L"
        assert trace.status in ("PASS", "PARTIAL", "MOCKED")

