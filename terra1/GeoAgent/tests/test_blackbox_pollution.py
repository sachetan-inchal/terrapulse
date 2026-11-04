"""Independent Black-Box Verification Suite: Pollution Intelligence.

Audits environmental.pollutants against real criteria pollutants, edge cases,
case sensitivity, and hardcoded dictionary bounds.
"""

import pytest
from environmental.pollutants import explain_pollutant, POLLUTANTS


class TestPollutionIntelligenceBlackBox:

    def test_normal_input_mercury(self):
        """A. Normal inputs and expected behavior."""
        res = explain_pollutant("mercury")
        assert res["found"] is True
        assert res["pollutant"] == "mercury"
        assert "heavy metal" in res["type"].lower()
        assert "water" in res["pathways"]
        assert any("bioaccumulation" in imp.lower() for imp in res["long_term_impacts"])

    def test_edge_cases_whitespace_and_casing(self):
        """B. Edge cases and boundary conditions."""
        res = explain_pollutant("  SULFUR DIOXIDE \n\t")
        assert res["found"] is True
        assert res["pollutant"] == "sulfur dioxide"
        assert res["form"] == "gas"

    def test_invalid_and_malformed_inputs(self):
        """C. Invalid inputs and malformed data."""
        # Empty string
        res_empty = explain_pollutant("")
        assert res_empty["found"] is False
        assert "message" in res_empty

        # Numbers and symbols
        res_symbols = explain_pollutant("!@#$1234")
        assert res_symbols["found"] is False

    def test_unsupported_criteria_pollutants_authenticity(self):
        """I. Authenticity Check: Expose hardcoded catalog limitation.
        
        EPA and WHO define major criteria pollutants (PM2.5, Lead, Ozone, Nitrogen Dioxide).
        None of these exist in the hardcoded 3-item dictionary.
        """
        criteria_pollutants = ["lead", "arsenic", "ozone", "pm2.5", "nitrogen dioxide", "benzene"]
        missing_from_catalog = []
        for pol in criteria_pollutants:
            res = explain_pollutant(pol)
            if not res["found"]:
                missing_from_catalog.append(pol)

        # Must document that all 6 criteria pollutants fail
        assert len(missing_from_catalog) == len(criteria_pollutants)
        # Verify that catalog size is strictly 3
        assert len(POLLUTANTS) == 3, f"Expected 3 static pollutants, found {len(POLLUTANTS)}"

    def test_factual_accuracy_microplastics(self):
        """J. Output correctness against scientific reference."""
        res = explain_pollutant("microplastics")
        assert res["found"] is True
        assert "solid" in res["type"].lower()
        assert "water" in res["pathways"]

