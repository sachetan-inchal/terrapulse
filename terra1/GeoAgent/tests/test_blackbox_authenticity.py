"""Independent Black-Box Verification Suite: Authenticity & Mock Detection.

Specifically investigates:
1. Hardcoded pollutant dictionaries (POLLUTANTS in environmental/pollutants.py).
2. Hardcoded landcover trajectories (HISTORICAL_LANDCOVER_TRAJECTORIES in backend/services/analysis.py).
3. Random-noise change masks (backend/main.py get_change_mask_tile).
4. Simulated tool delays (environmental/agent.py hardcoded 15.0ms / 16.0ms).
5. Static Sub-Agents UI array (SUB_AGENTS_MANIFEST in backend/services/investigator.py).
"""

import inspect
import pytest
from environmental.pollutants import POLLUTANTS
from backend.services.analysis import (
    HISTORICAL_LANDCOVER_TRAJECTORIES,
    get_environmental_analysis,
)
from backend.services.investigator import SUB_AGENTS_MANIFEST
import environmental.agent as agent_module


class TestAuthenticityVerificationBlackBox:

    def test_mock_pollutant_dictionary(self):
        """Authenticity: Expose that POLLUTANTS dictionary is a 3-item static mock."""
        assert len(POLLUTANTS) == 3
        assert set(POLLUTANTS.keys()) == {"mercury", "microplastics", "sulfur dioxide"}

    def test_mock_landcover_trajectories_silent_default(self):
        """Authenticity: Expose that unlisted global cities silently inherit Bengaluru numbers."""
        assert len(HISTORICAL_LANDCOVER_TRAJECTORIES) == 3
        assert set(HISTORICAL_LANDCOVER_TRAJECTORIES.keys()) == {"bengaluru", "amazon", "chennai"}

        # Query Paris and Tokyo
        paris_data = get_environmental_analysis("paris", 2024)
        tokyo_data = get_environmental_analysis("tokyo", 2024)
        bengaluru_data = get_environmental_analysis("bengaluru", 2024)

        # Both silently returned Bengaluru's numbers!
        assert paris_data.built_up_coverage_pct == bengaluru_data.built_up_coverage_pct
        assert tokyo_data.built_up_coverage_pct == bengaluru_data.built_up_coverage_pct

    def test_mock_subagents_manifest(self):
        """Authenticity: Expose that 8 sub-agents in UI are static decorative dictionaries."""
        assert len(SUB_AGENTS_MANIFEST) == 8
        for agent_entry in SUB_AGENTS_MANIFEST:
            assert "name" in agent_entry
            assert "status" in agent_entry
            # Notice they are all statically marked 'Done' or 'Verified' without executing
            assert agent_entry["status"] in ("Done", "Verified")

    def test_simulated_tool_call_latencies_in_agent(self):
        """Authenticity: Inspect TerraPulseInvestigatorAgent for hardcoded synthetic tool call latencies."""
        source = inspect.getsource(agent_module)
        # Check for hardcoded 15.0 and 16.0 ms simulated tool responses
        assert '"latency_ms": 15.0' in source or "'latency_ms': 15.0" in source
        assert '"latency_ms": 16.0' in source or "'latency_ms': 16.0" in source

