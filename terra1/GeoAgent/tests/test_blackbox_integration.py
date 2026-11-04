"""Black-Box tests for GeoAgent Integration Lab (MODULE 1)."""

import pytest
from backend.qa.integration_engine import integration_engine


class TestIntegrationLabWorkflows:
    """Verifies that multi-component integration workflows execute, capture data lineage,
    and report genuine statuses without silently fabricating passes."""

    def test_workflow_1_pollutant_to_impact(self):
        """Workflow 1: Pollutant classification -> Environmental impact analysis."""
        result = integration_engine.test_pollutant_to_impact_workflow("mercury")
        assert result.workflow_id == "INT-01"
        assert len(result.stages) == 2
        assert result.stages[0].status == "SUCCESS"
        assert result.stages[1].status == "SUCCESS"
        assert result.data_lineage_verified is True
        assert result.status in ("PASS", "PARTIAL")

    def test_workflow_2_research_to_synthesis(self):
        """Workflow 2: Research retrieval -> Research verification -> LLM synthesis."""
        result = integration_engine.test_research_to_synthesis_workflow("cyanobacteria eutrophication")
        assert result.workflow_id == "INT-02"
        assert len(result.stages) == 3
        assert result.stages[0].status == "SUCCESS"
        # At least one scholarly source must be queried
        assert result.data_lineage_verified is True

    def test_workflow_3_symptom_to_cause_and_research(self):
        """Workflow 3: Symptom extraction -> Cause analysis -> Research retrieval."""
        result = integration_engine.test_symptom_to_cause_and_research_workflow(
            "Thousands of dead fish floating on the lake surface with oily sheen"
        )
        assert result.workflow_id == "INT-03"
        assert len(result.stages) == 3
        assert result.stages[0].status == "SUCCESS"
        assert result.stages[1].status == "SUCCESS"
        assert result.data_lineage_verified is True

    def test_workflow_4_geocoding_spatial_map(self):
        """Workflow 4: Geocoding -> Spatial processing -> Map rendering."""
        result = integration_engine.test_geocoding_spatial_map_workflow("Bengaluru")
        assert result.workflow_id == "INT-04"
        assert len(result.stages) == 4
        assert result.stages[0].status == "SUCCESS"
        assert result.final_output.get("geojson_features") is not None

    def test_workflow_5_pollution_to_hotspot_visualization(self):
        """Workflow 5: Pollution API -> Environmental analysis -> Geographical visualization."""
        result = integration_engine.test_pollution_to_hotspot_visualization_workflow("Bengaluru", "PM2.5")
        assert result.workflow_id == "INT-05"
        assert len(result.stages) == 3
        assert result.stages[0].status == "SUCCESS"
        assert result.stages[1].status == "SUCCESS"
        assert result.stages[2].status == "SUCCESS"
        assert result.final_output.get("hotspots_detected") is not None

    def test_workflow_6_full_investigation_synthesis(self):
        """Workflow 6: Research + pollution data + LLM -> Final environmental report."""
        result = integration_engine.test_full_investigation_synthesis_workflow("Bengaluru", "particulate matter")
        assert result.workflow_id == "INT-06"
        assert len(result.stages) == 3
        assert result.stages[0].status == "SUCCESS"
        assert result.data_lineage_verified is True

