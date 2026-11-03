"""Integration and unit tests for Phase 6 Backend API and SSE Streaming Infrastructure."""

from __future__ import annotations

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

# Ensure both backend and GeoAgent are importable
CURRENT_DIR = Path(__file__).resolve().parent
GEOAGENT_DIR = CURRENT_DIR.parent
TERRAPULSE_DIR = GEOAGENT_DIR.parent.parent

for p in [str(GEOAGENT_DIR), str(TERRAPULSE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app, global_investigator_agent
from environmental.research_apis.base import ArticleMetadata


def parse_sse_events(line_iterator) -> list[dict]:
    """Parse raw SSE line stream into list of {event: str, data: str} items."""
    events = []
    current_event = None
    current_data = []
    for raw_line in line_iterator:
        line = raw_line.strip()
        if not line:
            if current_event or current_data:
                events.append({
                    "event": current_event,
                    "data": "\n".join(current_data)
                })
                current_event = None
                current_data = []
        elif line.startswith("event:"):
            current_event = line.replace("event:", "", 1).strip()
        elif line.startswith("data:"):
            current_data.append(line.replace("data:", "", 1).strip())
    if current_event or current_data:
        events.append({
            "event": current_event,
            "data": "\n".join(current_data)
        })
    return events


class TestBackendAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Reset the test session before each test
        global_investigator_agent.session_manager.reset_session("test_session_123")
        global_investigator_agent.session_manager.reset_session("test_chat_stream")

    def test_health_check_preservation(self):
        """Verify baseline health check endpoint continues to function."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "2.0.0")

    def test_get_environmental_stations(self):
        """Verify stations endpoint returns telemetry with provenance and sample disclosure."""
        # Unfiltered
        resp = self.client.get("/api/environmental/stations?location=bengaluru")
        self.assertEqual(resp.status_code, 200)
        stations = resp.json()
        self.assertGreaterEqual(len(stations), 8)
        
        # Check provenance disclosure
        first = stations[0]
        self.assertTrue(first["is_sample_data"])
        self.assertIn("Illustrative benchmark telemetry", first["sample_data_note"])
        self.assertIn("station_id", first)
        self.assertIn("value", first)
        self.assertIn("unit", first)

        # Filtered by PM2.5
        resp_pm = self.client.get("/api/environmental/stations?indicator=PM2.5")
        self.assertEqual(resp_pm.status_code, 200)
        pm_stations = resp_pm.json()
        self.assertTrue(all(s["indicator"] == "PM2.5" for s in pm_stations))

    def test_get_environmental_heatmap(self):
        """Verify IDW heatmap endpoint returns GeoJSON and coverage metrics."""
        resp = self.client.get("/api/environmental/heatmap?indicator=PM2.5&power=2.0&search_radius_km=10.0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        self.assertEqual(data["indicator"], "PM2.5")
        self.assertIn("Inverse Distance Weighting", data["interpolation_method"])
        self.assertIn("coverage_percentage", data)
        self.assertIn("total_grid_points", data)
        self.assertIn("interpolated_points", data)
        self.assertIn("uninterpolated_points", data)
        self.assertIn("epistemic_notice", data)

        # Verify GeoJSON
        geojson = data["geojson"]
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertIn("features", geojson)
        self.assertGreater(len(geojson["features"]), 0)

        # Check that stations and interpolated surface features are present
        types = {f["properties"].get("data_type") for f in geojson["features"]}
        self.assertIn("MEASURED_POINT", types)
        self.assertIn("INTERPOLATED_MODEL", types)

    def test_post_symptom_analysis(self):
        """Verify symptom-to-cause investigation endpoint."""
        payload = {
            "symptom_query": "Thousands of fish dying with white toxic froth",
            "location": "Bellandur Lake, Bengaluru"
        }
        resp = self.client.post("/api/environmental/symptom-analysis", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["symptom_detected"], "fish_mortality")
        self.assertIn("Bellandur", data["location"])
        self.assertIn("hypotheses", data)
        self.assertGreater(len(data["hypotheses"]), 0)

        # Verify Bradford Hill structure on top hypothesis
        top_h = data["hypotheses"][0]
        self.assertIn("hypothesis_id", top_h)
        self.assertIn("biological_mechanism", top_h)
        self.assertIn("bradford_hill_score", top_h)
        self.assertIn("supporting_evidence", top_h)
        self.assertIn("conflicting_evidence", top_h)
        self.assertIn("alternative_explanations", top_h)
        self.assertIn("missing_data", top_h)
        self.assertIn("uncertainty_statement", data)

    def test_post_forecast(self):
        """Verify multi-scenario statistical forecasting endpoint."""
        payload = {
            "indicator": "PM2.5",
            "horizon": "+5 years",
            "reduction_percentage": 30.0,
            "location": "Bengaluru"
        }
        resp = self.client.post("/api/environmental/forecast", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["indicator"], "PM2.5")
        self.assertEqual(data["unit"], "µg/m³")
        self.assertIn("historical_observations", data)
        self.assertIn("scenarios", data)
        self.assertIn("BAU", data["scenarios"])
        self.assertIn("POL_RED", data["scenarios"])
        self.assertIn("INTERVENTION", data["scenarios"])

        # Check prediction intervals on BAU trajectory
        bau = data["scenarios"]["BAU"]
        self.assertGreater(len(bau["trajectory"]), 0)
        pt = bau["trajectory"][-1]
        self.assertLessEqual(pt["lower_95"], pt["lower_80"])
        self.assertLessEqual(pt["lower_80"], pt["predicted_value"])
        self.assertLessEqual(pt["predicted_value"], pt["upper_80"])
        self.assertLessEqual(pt["upper_80"], pt["upper_95"])

    @patch("backend.main.global_research_aggregator.search_all")
    def test_get_research_articles(self, mock_search):
        """Verify research query endpoint returns aggregated articles."""
        mock_search.return_value = (
            [
                ArticleMetadata(
                    title="Eutrophication Dynamics in Urban Tropical Lakes",
                    authors=["Ramachandra, T.V.", "Asulabha, K.S."],
                    publication_date="2021-04-15",
                    source_provider="Europe PMC",
                    doi="https://doi.org/10.1016/j.envres.2021.1001",
                    abstract_or_summary="Severe hypoxia and seasonal fish mortality driven by untreated sewage inflows."
                )
            ],
            {"Europe PMC": {"status": "SUCCESS"}}
        )

        resp = self.client.get("/api/environmental/research?q=lake+eutrophication&limit=2")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["query"], "lake eutrophication")
        self.assertEqual(data["total_found"], 1)
        self.assertEqual(data["articles"][0]["title"], "Eutrophication Dynamics in Urban Tropical Lakes")
        self.assertEqual(data["articles"][0]["source"], "Europe PMC")
        self.assertEqual(data["articles"][0]["publication_year"], 2021)

    def test_investigator_chat_streaming_clarification(self):
        """Verify SSE chat streaming emits clarification_needed when location is missing."""
        payload = {
            "message": "Why are thousands of fish dying?",
            "session_id": "test_clarify_sse",
        }
        with self.client.stream("POST", "/api/investigator/chat", json=payload) as resp:
            self.assertEqual(resp.status_code, 200)
            events = parse_sse_events(resp.iter_lines())
            event_types = [e["event"] for e in events]
            self.assertIn("clarification_needed", event_types)

    def test_investigator_chat_multi_turn_flow(self):
        """Verify multi-turn session persistence via SSE chat stream."""
        session_id = "test_multi_turn_session"

        # Turn 1: Symptom query without location -> Clarification requested
        with self.client.stream("POST", "/api/investigator/chat", json={
            "message": "Fish are floating dead along the shoreline",
            "session_id": session_id
        }) as resp1:
            self.assertEqual(resp1.status_code, 200)
            events1 = parse_sse_events(resp1.iter_lines())
            types1 = [e["event"] for e in events1]
            self.assertIn("clarification_needed", types1)

        # Turn 2: User supplies location -> Agent runs investigation and streams tool events & final report
        with self.client.stream("POST", "/api/investigator/chat", json={
            "message": "This happened at Bellandur Lake, Bengaluru",
            "session_id": session_id
        }) as resp2:
            self.assertEqual(resp2.status_code, 200)
            events2 = parse_sse_events(resp2.iter_lines())
            types2 = [e["event"] for e in events2]
            
            # Must stream tool execution activity
            self.assertIn("tool_call_start", types2)
            self.assertIn("tool_call_result", types2)
            self.assertIn("final_response", types2)

            # Check final response data payload
            final_evts = [e for e in events2 if e["event"] == "final_response"]
            self.assertEqual(len(final_evts), 1)
            final_data = json.loads(final_evts[0]["data"])

            self.assertIn("Bellandur Lake", final_data["text"])
            self.assertIn("geojson", final_data)
            self.assertEqual(final_data["geojson"]["type"], "FeatureCollection")

    def test_session_reset(self):
        """Verify session reset endpoint clears conversational memory."""
        session_id = "test_reset_session"
        # Seed session
        self.client.stream("POST", "/api/investigator/chat", json={
            "message": "Fish dying at Bellandur Lake",
            "session_id": session_id
        })
        
        # Reset
        resp = self.client.post(f"/api/investigator/reset?session_id={session_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")

        # Verify session state is reset
        session = global_investigator_agent.session_manager.get_session(session_id)
        self.assertIsNone(session.location_name)
        self.assertEqual(len(session.messages), 0)


if __name__ == "__main__":
    unittest.main()
