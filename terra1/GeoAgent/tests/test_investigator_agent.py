"""Unit and conversational flow tests for TerraPulse Conversational Environmental Investigator Agent (Phase 5)."""

from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock

from environmental.agent import (
    TerraPulseInvestigatorAgent,
    SessionManager,
    ActivityEventType,
    InvestigationSession,
)


class TestInvestigatorAgent(unittest.TestCase):

    def setUp(self):
        self.session_manager = SessionManager()
        self.agent = TerraPulseInvestigatorAgent(session_manager=self.session_manager)

    def test_session_isolation(self):
        s1 = self.session_manager.get_or_create_session("session_user_A")
        s2 = self.session_manager.get_or_create_session("session_user_B")

        s1.location_name = "Bellandur Lake, Bengaluru"
        s2.location_name = "Peenya Industrial Area, Bengaluru"

        self.assertNotEqual(s1.location_name, s2.location_name)
        self.assertEqual(len(self.session_manager.list_sessions()), 2)

    def test_clarification_on_missing_location(self):
        events = list(self.agent.process_message(
            user_message="Why are fish dying in a lake?",
            session_id="test_clarify_session",
        ))

        # Must emit clarification_needed
        clarify_events = [e for e in events if e.event_type == ActivityEventType.CLARIFICATION_NEEDED]
        self.assertEqual(len(clarify_events), 1)
        self.assertEqual(clarify_events[0].data["slot"], "location")
        self.assertIn("Which lake", clarify_events[0].data["question"])

        # Check session recorded pending clarification
        session = self.session_manager.get_or_create_session("test_clarify_session")
        self.assertEqual(session.pending_clarification, "LOCATION")
        self.assertEqual(session.symptom_key, "fish_mortality")

    def test_multi_turn_investigation_flow(self):
        session_id = "test_multi_turn_flow"

        # Turn 1: Symptom query without location -> Triggers clarification
        turn1_events = list(self.agent.process_message(
            user_message="Thousands of fish are dying in a lake. What is the cause?",
            session_id=session_id,
        ))
        clarify = [e for e in turn1_events if e.event_type == ActivityEventType.CLARIFICATION_NEEDED]
        self.assertEqual(len(clarify), 1)

        # Turn 2: User provides location -> Resolves location and executes investigation tools
        turn2_events = list(self.agent.process_message(
            user_message="Bellandur Lake in Bengaluru",
            session_id=session_id,
        ))

        # Check tool execution events
        tool_starts = [e for e in turn2_events if e.event_type == ActivityEventType.TOOL_CALL_START]
        tool_results = [e for e in turn2_events if e.event_type == ActivityEventType.TOOL_CALL_RESULT]
        final_res = [e for e in turn2_events if e.event_type == ActivityEventType.FINAL_RESPONSE]

        self.assertGreaterEqual(len(tool_starts), 2)  # Ran symptom analysis and spatial hotspot analysis
        self.assertGreaterEqual(len(tool_results), 2)
        self.assertEqual(len(final_res), 1)

        final_data = final_res[0].data
        self.assertIn("Bellandur Lake", final_data["location"])
        self.assertIn("Dissolved Oxygen", final_data["content"])
        self.assertIn("Ranked Causal Hypotheses", final_data["content"])
        self.assertIsNotNone(final_data["map_geojson"])
        self.assertEqual(final_data["map_geojson"]["type"], "FeatureCollection")

        # Turn 3: Follow-up forecasting query -> Retains Bellandur context and forecasts
        turn3_events = list(self.agent.process_message(
            user_message="What will happen to pollution levels in 5 years if no action is taken?",
            session_id=session_id,
        ))

        forecast_starts = [e for e in turn3_events if e.event_type == ActivityEventType.TOOL_CALL_START]
        self.assertTrue(any(e.data["tool_name"] == "generate_environmental_forecast" for e in forecast_starts))

        turn3_final = [e for e in turn3_events if e.event_type == ActivityEventType.FINAL_RESPONSE][0]
        self.assertIn("Environmental Forecasting Report", turn3_final.data["content"])
        self.assertIn("Business-As-Usual", turn3_final.data["content"])
        self.assertIn("Bellandur Lake", turn3_final.data["content"])

    def test_direct_query_with_location_and_symptom(self):
        session_id = "test_direct_session"
        events = list(self.agent.process_message(
            user_message="Why is there thick toxic foam covering Bellandur Lake in Bengaluru?",
            session_id=session_id,
        ))

        # Location and symptom both provided, so no clarification needed
        clarify = [e for e in events if e.event_type == ActivityEventType.CLARIFICATION_NEEDED]
        self.assertEqual(len(clarify), 0)

        final_res = [e for e in events if e.event_type == ActivityEventType.FINAL_RESPONSE][0]
        self.assertIn("Surfactant", final_res.data["content"])
        self.assertIn("Bellandur Lake", final_res.data["location"])

    def test_general_literature_search_query(self):
        session_id = "test_lit_session"
        events = list(self.agent.process_message(
            user_message="What are the recent papers on microplastics in freshwater lakes?",
            session_id=session_id,
        ))

        tool_starts = [e for e in events if e.event_type == ActivityEventType.TOOL_CALL_START]
        self.assertEqual(tool_starts[0].data["tool_name"], "search_all_research")

        final_res = [e for e in events if e.event_type == ActivityEventType.FINAL_RESPONSE][0]
        self.assertIn("Scientific Literature Findings", final_res.data["content"])


if __name__ == "__main__":
    unittest.main()

