"""Independent Black-Box Verification Suite: Symptom-to-Cause Analysis.

Verifies Bradford Hill causal reasoning, multiple competing hypotheses,
unrecognized symptom handling, and scientific caveats.
"""

import pytest
from environmental.symptom_analyzer import (
    investigate_environmental_symptom,
    classify_symptom_from_text,
    SYMPTOM_CATALOG,
)


class TestSymptomAnalyzerBlackBox:

    def test_fish_kill_hypotheses_and_bradford_hill(self):
        """A & J: Fish mortality symptom with mechanistic hypotheses."""
        res = investigate_environmental_symptom(
            "Thousands of fish dying in wetland lake with low dissolved oxygen",
            fetch_live_literature=False
        )
        assert res["symptom_identified"] == "Aquatic Organism & Fish Mortality (Fish Kill)"
        hyps = res["hypotheses_ranked"]
        assert len(hyps) >= 3, "Expected at least 3 candidate causes"

        # Hypotheses must include Dissolved Oxygen Depletion
        hyp_names = [h["cause_name"].lower() for h in hyps]
        assert any("oxygen" in name or "hypoxia" in name for name in hyp_names)

        # Must include alternative rival explanations
        first_bh = hyps[0].get("bradford_hill")
        assert first_bh is not None
        assert "alternative_explanations" in first_bh
        assert len(first_bh["alternative_explanations"]) > 0

        # Epistemic caveat must be explicitly present
        assert "causal_disclaimer" in res
        assert "correlation" in res["causal_disclaimer"].lower()

    def test_toxic_foam_symptom(self):
        """A. Surfactant foam symptom extraction."""
        res = investigate_environmental_symptom(
            "White detergent froth and toxic foam covering spillway",
            fetch_live_literature=False
        )
        assert "foam" in res["symptom_identified"].lower() or "froth" in res["symptom_identified"].lower()

    def test_unrecognized_symptom_catalog_limitation(self):
        """I. Authenticity Check: Catalog limitation to 5 static profiles."""
        assert len(SYMPTOM_CATALOG) == 5, f"Expected 5 static profiles, found {len(SYMPTOM_CATALOG)}"

        res = investigate_environmental_symptom(
            "Amphibian limb deformities caused by agricultural runoff",
            fetch_live_literature=False
        )
        # Should return Unrecognized Symptom with 0 hypotheses
        assert "unrecognized" in res["symptom_identified"].lower() or "unknown" in res["symptom_identified"].lower()
        assert len(res["hypotheses_ranked"]) == 0
