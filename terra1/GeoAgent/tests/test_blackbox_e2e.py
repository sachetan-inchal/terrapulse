"""Independent Black-Box Verification Suite: End-to-End Investigation Flow.

Verifies end-to-end multi-turn conversation and evidence synthesis.
"""

import pytest
from environmental.agent import TerraPulseInvestigatorAgent, SessionManager, ActivityEventType


class TestEndToEndInvestigationBlackBox:

    def test_full_investigation_turn_chennai(self):
        """A. Complete end-to-end conversation flow."""
        session_mgr = SessionManager()
        agent = TerraPulseInvestigatorAgent(session_manager=session_mgr)

        events = list(agent.process_message(
            "Why is air pollution increasing in Chennai?",
            session_id="e2e_blackbox_test"
        ))
        assert len(events) >= 2

        final_events = [e for e in events if e.event_type == ActivityEventType.FINAL_RESPONSE]
        assert len(final_events) == 1

        final_data = final_events[0].data
        content = final_data.get("content", "")
        assert "Chennai" in content or "chennai" in content.lower()
        assert "suggestions" in final_data
        assert len(final_data["suggestions"]) > 0

    def test_session_isolation_across_users(self):
        """G. Session isolation across simultaneous distinct queries."""
        session_mgr = SessionManager()
        agent = TerraPulseInvestigatorAgent(session_manager=session_mgr)

        # User A investigates Bengaluru
        list(agent.process_message("Investigate Bellandur Lake, Bengaluru", session_id="user_a"))
        # User B investigates Amazon
        list(agent.process_message("Analyze vegetation in Amazon Rainforest", session_id="user_b"))

        sess_a = session_mgr.get_session("user_a")
        sess_b = session_mgr.get_session("user_b")

        assert sess_a.location_name != sess_b.location_name

