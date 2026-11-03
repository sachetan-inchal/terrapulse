"""Unit and integration tests for Environmental Symptom and Cause Investigation Engine (Phase 3)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from environmental.spatial_analysis import MonitoringStation
from environmental.symptom_analyzer import (
    classify_symptom_from_text,
    evaluate_hypothesis_against_measurements,
    investigate_environmental_symptom,
    SYMPTOM_CATALOG,
    CausalHypothesis,
)
from environmental.research_apis.base import ArticleMetadata


import requests

def _can_reach_internet() -> bool:
    try:
        requests.get("https://1.1.1.1", timeout=2.0)
        return True
    except Exception:
        return False

ONLINE = _can_reach_internet()


class TestSymptomAnalyzer(unittest.TestCase):

    def setUp(self):
        # Sample monitoring stations with real chemical signatures
        self.lake_stations_hypoxic = [
            MonitoringStation(
                id="LAKE-INLET-01",
                name="North Inlet",
                latitude=12.94,
                longitude=77.67,
                pollutant="PM2.5",
                measured_value=65.0,
                unit="µg/m³",
                timestamp="2024-05-15T10:00:00Z",
                extra_attributes={
                    "dissolved_oxygen_mg_l": 1.1,  # Critical hypoxia (< 2.5 mg/L)
                    "surfactants_mg_l": 5.4,       # High surfactants (> 2.0 mg/L)
                },
            ),
            MonitoringStation(
                id="LAKE-OUTLET-02",
                name="South Outlet",
                latitude=12.93,
                longitude=77.68,
                pollutant="PM2.5",
                measured_value=70.0,
                unit="µg/m³",
                timestamp="2024-05-15T10:00:00Z",
                extra_attributes={
                    "dissolved_oxygen_mg_l": 0.9,
                    "surfactants_mg_l": 4.8,
                },
            ),
        ]

        self.lake_stations_oxygenated = [
            MonitoringStation(
                id="LAKE-CLEAN-01",
                name="Protected Lake Buffer",
                latitude=12.95,
                longitude=77.60,
                pollutant="PM2.5",
                measured_value=40.0,
                unit="µg/m³",
                timestamp="2024-05-15T10:00:00Z",
                extra_attributes={
                    "dissolved_oxygen_mg_l": 7.8,  # Healthy oxygenated water (> 6.0 mg/L)
                    "surfactants_mg_l": 0.2,       # Minimal surfactants
                },
            )
        ]

    def test_classify_symptom_from_natural_language(self):
        # Fish mortality
        sym1 = classify_symptom_from_text("Thousands of dead fish are floating in the lake")
        self.assertIsNotNone(sym1)
        self.assertEqual(sym1.symptom_key, "fish_mortality")

        # Toxic foam
        sym2 = classify_symptom_from_text("Why is thick white foam frothing on Bellandur lake?")
        self.assertIsNotNone(sym2)
        self.assertEqual(sym2.symptom_key, "toxic_foam")

        # Water discoloration
        sym3 = classify_symptom_from_text("The water turned bright green with dense algal scum")
        self.assertIsNotNone(sym3)
        self.assertEqual(sym3.symptom_key, "water_discoloration")

        # Air pollution smog
        sym4 = classify_symptom_from_text("Severe respiratory irritation and thick smog haze")
        self.assertIsNotNone(sym4)
        self.assertEqual(sym4.symptom_key, "air_pollution_smog")

        # Vegetation chlorosis
        sym5 = classify_symptom_from_text("Tree mortality, defoliation and yellowing chlorosis in the canopy")
        self.assertIsNotNone(sym5)
        self.assertEqual(sym5.symptom_key, "vegetation_damage")

        # Unrecognized symptom
        sym_none = classify_symptom_from_text("What time is it in Tokyo?")
        self.assertIsNone(sym_none)

    def test_evaluate_hypothesis_supporting_and_conflicting(self):
        fish_sym = [s for s in SYMPTOM_CATALOG if s.symptom_key == "fish_mortality"][0]
        hypoxia_tmpl = [h for h in fish_sym.candidate_hypotheses if h["id"] == "HYP-HYPOXIA"][0]

        # Case 1: Hypoxic stations (DO = 0.9 - 1.1 mg/L)
        supp, conf, bh = evaluate_hypothesis_against_measurements(
            hypoxia_tmpl, self.lake_stations_hypoxic
        )
        self.assertGreater(len(supp), 0)
        self.assertEqual(len(conf), 0)
        self.assertIn("critical low", supp[0].claim)
        self.assertIn("lethal threshold", bh.dose_response_gradient)
        self.assertIn("Acute industrial chemical toxicity", bh.alternative_explanations)

        # Case 2: Clean stations (DO = 7.8 mg/L)
        supp2, conf2, bh2 = evaluate_hypothesis_against_measurements(
            hypoxia_tmpl, self.lake_stations_oxygenated
        )
        self.assertEqual(len(supp2), 0)
        self.assertGreater(len(conf2), 0)
        self.assertIn("above the critical hypoxia threshold", conf2[0].claim)
        self.assertIn("Sub-critical", bh2.dose_response_gradient)

    @patch("environmental.symptom_analyzer.search_academic_literature")
    def test_investigate_fish_mortality_with_mocked_literature(self, mock_search_lit):
        # Mock literature returning verified studies
        mock_search_lit.return_value = (
            [
                ArticleMetadata(
                    source_provider="Europe PMC",
                    title="Hypoxia-induced fish mortality in tropical urban water bodies",
                    authors=["Ramachandra TV", "Asulabha KS"],
                    publication_name="Current Science",
                    publication_date="2020",
                    doi="10.18520/cs/v118/i9/1380-1387",
                    url="https://doi.org/10.18520/cs/v118/i9/1380-1387",
                    abstract_or_summary="Dissolved oxygen dropped below 1 mg/L following untreated sewage inflow, triggering massive mortality.",
                    citation_count=45,
                )
            ],
            {"status": "SUCCESS"},
        )

        query = "Thousands of fish are dying in Bellandur lake. What is causing it?"
        result = investigate_environmental_symptom(
            user_query=query,
            stations=self.lake_stations_hypoxic,
            fetch_live_literature=True,
            literature_limit=2,
        )

        self.assertEqual(result["symptom_key"], "fish_mortality")
        self.assertIn("Aquatic Organism & Fish Mortality", result["symptom_identified"])
        self.assertGreater(len(result["hypotheses_ranked"]), 0)

        # Hypoxia hypothesis should rank top due to empirical match (DO 0.9 mg/L) and literature
        top_hyp = result["hypotheses_ranked"][0]
        self.assertEqual(top_hyp["hypothesis_id"], "HYP-HYPOXIA")
        self.assertEqual(top_hyp["support_tier"], "HIGH_EMPIRICAL_SUPPORT")
        self.assertGreaterEqual(top_hyp["evidence_score"], 0.85)

        # Verify Bradford Hill structure
        self.assertIsNotNone(top_hyp["bradford_hill"])
        self.assertEqual(top_hyp["bradford_hill"]["biological_plausibility"], "High")
        self.assertTrue(len(top_hyp["bradford_hill"]["alternative_explanations"]) > 0)

        # Verify missing data disclosure
        self.assertIn("missing_measurements", result)
        self.assertTrue(len(result["missing_measurements"]) > 0)

        # Verify epistemic caveat & disclaimer
        self.assertIn("causal_disclaimer", result)
        self.assertIn("Correlation does not establish causation", top_hyp["epistemic_caveat"])

    def test_investigate_unrecognized_symptom(self):
        result = investigate_environmental_symptom(
            user_query="Can you explain how to bake bread?",
            stations=[],
            fetch_live_literature=False,
        )
        self.assertEqual(result["status"], "UNRECOGNIZED_SYMPTOM")
        self.assertEqual(len(result["hypotheses_ranked"]), 0)

    @patch("environmental.symptom_analyzer.search_academic_literature")
    def test_investigate_lake_foaming_ranking(self, mock_search_lit):
        mock_search_lit.return_value = (
            [
                ArticleMetadata(
                    source_provider="Crossref",
                    title="Surfactant concentrations and persistent foam formation in sewage-fed urban lakes",
                    authors=["Chanakya HN", "Sharachchandra L"],
                    publication_name="Ecological Engineering",
                    publication_date="2021",
                    doi="10.1016/j.ecoleng.2021.106200",
                    url="https://doi.org/10.1016/j.ecoleng.2021.106200",
                    abstract_or_summary="Linear alkylbenzene sulfonate surfactant concentrations exceeding 4 mg/L resulted in persistent white foam.",
                )
            ],
            {"status": "SUCCESS"},
        )

        query = "Why is toxic foam covering the lake surface?"
        result = investigate_environmental_symptom(
            user_query=query,
            stations=self.lake_stations_hypoxic,  # Has surfactants = 5.4 mg/L
            fetch_live_literature=True,
        )

        self.assertEqual(result["symptom_key"], "toxic_foam")
        self.assertGreater(len(result["hypotheses_ranked"]), 0)

        # Surfactant discharge should rank first because surfactants_mg_l was measured at 5.4 mg/L (> 2.0 mg/L)
        top_hyp = result["hypotheses_ranked"][0]
        self.assertEqual(top_hyp["hypothesis_id"], "HYP-SURFACTANT-DISCHARGE")
        self.assertEqual(top_hyp["support_tier"], "HIGH_EMPIRICAL_SUPPORT")

    @unittest.skipUnless(ONLINE, "Requires internet connectivity")
    def test_live_symptom_investigation_integration(self):
        """End-to-end integration test querying live OpenAlex/Crossref literature with telemetry."""
        from environmental.spatial_analysis import get_preset_bengaluru_monitoring_stations

        stations = get_preset_bengaluru_monitoring_stations()
        query = "Thousands of fish are dying in Bellandur lake with white toxic foam"

        result = investigate_environmental_symptom(
            user_query=query,
            stations=stations,
            fetch_live_literature=True,
            literature_limit=2,
        )

        self.assertEqual(result["symptom_key"], "fish_mortality")
        self.assertGreater(len(result["hypotheses_ranked"]), 0)

        top_hyp = result["hypotheses_ranked"][0]
        self.assertIn("hypothesis_id", top_hyp)
        self.assertIn("support_tier", top_hyp)
        self.assertIn("bradford_hill", top_hyp)
        # Should have real literature citations retrieved
        self.assertIsInstance(top_hyp["scientific_citations"], list)
        self.assertIn("causal_disclaimer", result)


if __name__ == "__main__":
    unittest.main()
