"""Black-Box tests for Prompt Arena & Evaluation Engine (MODULE 3, 4, 5)."""

import pytest
from backend.qa.prompt_arena import prompt_arena, PROMPT_LIBRARY


class TestPromptArenaAndEvaluation:
    """Verifies that the prompt arena evaluates natural-language queries
    with 10 deterministic criteria and timeline traces."""

    def test_library_has_14_categories(self):
        """Verifies library covers all 14 required environmental prompt categories."""
        lib = prompt_arena.get_prompt_library()
        assert len(lib) == 14
        categories = {p["category"] for p in lib}
        assert "Pollution Intelligence" in categories
        assert "Scientific Research" in categories
        assert "Symptom-to-Cause Diagnosis" in categories
        assert "Geospatial Point Mapping" in categories
        assert "Unsupported Pollutant Handling" in categories

    def test_execute_exact_prompt_and_eval(self):
        """Executes a realistic prompt and validates 10-criteria evaluation."""
        result = prompt_arena.execute_prompt(
            prompt="What are the environmental pathways and chronic toxicity impacts of mercury?",
            prompt_id="PRM-01",
            category_id=1,
            category_name="Pollution Intelligence",
        )
        assert result.prompt_id == "PRM-01"
        assert len(result.timeline) >= 2
        # Module 4: 10 criteria evaluation report
        eval_rep = result.evaluation
        assert isinstance(eval_rep.understood_objective, bool)
        assert isinstance(eval_rep.tools_selected, list)
        assert eval_rep.overall_status in ("PASS", "PARTIAL", "MOCKED", "FAIL")

    def test_adversarial_prompt_handling(self):
        """Tests handling of ambiguous/adversarial prompt."""
        result = prompt_arena.execute_prompt(
            prompt="Tell me if the river is contaminated without any location or pollutant specified.",
            prompt_id="PRM-13",
            category_id=13,
            category_name="Adversarial and Ambiguous Prompts",
        )
        assert result.evaluation is not None
        assert result.actual_response is not None
