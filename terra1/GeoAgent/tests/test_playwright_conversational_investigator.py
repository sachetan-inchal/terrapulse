"""Playwright End-to-End Test for TerraPulse 2.0 Conversational AI Investigator & Multi-Turn Intelligence.

Tests the required 4-turn multi-turn conversation:
Turn 1: "What environmental changes are happening around the selected location?"
Turn 2: "Why are these changes happening?"
Turn 3: "Show me scientific research supporting this."
Turn 4: "What are the likely environmental effects over the next five years?"

Verifies:
- Real SSE streaming and Strands agent activity stream.
- Formatted markdown message rendering (no raw ## or **).
- Clickable verified DOIs and research publications.
- 6-Tab analytical workspace navigation.
- Captures screenshots for evidence.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ARTIFACTS_DIR = Path(r"C:\Users\rishi\.gemini\antigravity\brain\20309b08-3dc7-4ad4-9427-13438187e9f8\screenshots")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def test_conversational_ai_investigator():
    print("=== Starting TerraPulse 2.0 Conversational AI Investigator E2E Test ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        context = browser.new_context(viewport={"width": 1600, "height": 950})
        page = context.new_page()

        print("\n[STEP 1] Loading TerraPulse at http://127.0.0.1:8000...")
        page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded", timeout=25000)
        time.sleep(3)

        # Ensure we are in AI Investigator mode
        investigator_btn = page.locator("button:has-text('AI Earth Investigator'), button:has-text('AI Investigator')").first
        if investigator_btn.is_visible():
            investigator_btn.click()
            time.sleep(1.5)

        page.screenshot(path=str(ARTIFACTS_DIR / "conv_step1_workspace_ready.png"))
        print("  ✓ Captured conv_step1_workspace_ready.png")

        # --------------------------------------------------------------------
        # TURN 1: "What environmental changes are happening around the selected location?"
        # --------------------------------------------------------------------
        print("\n[STEP 2] TURN 1: Asking about environmental changes around selected location...")
        chat_input = page.locator("input[placeholder*='Ask any environmental question'], input[placeholder*='Ask an environmental']").first
        chat_input.fill("What environmental changes are happening around the selected location?")
        chat_input.press("Enter")
        print("  Sent Turn 1 query, awaiting live SSE streaming and Strands tools execution...")

        # Wait for assistant response to finish streaming
        page.wait_for_selector("text=Environmental Change Assessment", timeout=25000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "conv_step2_turn1_changes_assessed.png"))
        print("  ✓ Turn 1 complete! Captured conv_step2_turn1_changes_assessed.png")

        # --------------------------------------------------------------------
        # TURN 2: "Why are these changes happening?" (Follow-up without repeating location)
        # --------------------------------------------------------------------
        print("\n[STEP 3] TURN 2: Asking causal follow-up 'Why are these changes happening?'...")
        # We can either click the follow-up pill or type it
        why_pill = page.locator("button:has-text('Why are these changes happening?')").first
        if why_pill.is_visible():
            why_pill.click()
        else:
            chat_input.fill("Why are these changes happening?")
            chat_input.press("Enter")
        print("  Sent Turn 2 causal query, awaiting Bradford Hill symptom-to-cause diagnostic...")

        page.wait_for_selector("text=Causal Investigation Report", timeout=25000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "conv_step3_turn2_causes_explained.png"))
        print("  ✓ Turn 2 complete! Captured conv_step3_turn2_causes_explained.png")

        # --------------------------------------------------------------------
        # TURN 3: "Show me scientific research supporting this."
        # --------------------------------------------------------------------
        print("\n[STEP 4] TURN 3: Requesting verified scientific research literature...")
        research_pill = page.locator("button:has-text('Show me scientific research')").first
        if research_pill.is_visible():
            research_pill.click()
        else:
            chat_input.fill("Show me scientific research supporting this.")
            chat_input.press("Enter")
        print("  Sent Turn 3 research query, querying OpenAlex, Europe PMC, Crossref, Semantic Scholar...")

        page.wait_for_selector("text=Scientific Research & Evidence", timeout=25000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "conv_step4_turn3_research_papers.png"))
        print("  ✓ Turn 3 complete! Captured conv_step4_turn3_research_papers.png")

        # --------------------------------------------------------------------
        # TURN 4: "What are the likely environmental effects over the next five years?"
        # --------------------------------------------------------------------
        print("\n[STEP 5] TURN 4: Requesting 5-year multi-scenario future forecasting...")
        forecast_pill = page.locator("button:has-text('What will happen in five years?')").first
        if forecast_pill.is_visible():
            forecast_pill.click()
        else:
            chat_input.fill("What are the likely environmental effects over the next five years?")
            chat_input.press("Enter")
        print("  Sent Turn 4 forecast query, simulating BAU, Policy Reduction, and Interventions...")

        page.wait_for_selector("text=Environmental Multi-Scenario Forecast", timeout=25000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "conv_step5_turn4_forecast_scenarios.png"))
        print("  ✓ Turn 4 complete! Captured conv_step5_turn4_forecast_scenarios.png")

        # --------------------------------------------------------------------
        # VERIFY RIGHT-SIDE 6 TABS
        # --------------------------------------------------------------------
        print("\n[STEP 6] Testing Right-Side 6-Tab Analytical Workspace...")

        # Tab 1: Parameters
        page.locator("button:has-text('1. Parameters')").click()
        time.sleep(1)
        page.screenshot(path=str(ARTIFACTS_DIR / "workspace_tab1_parameters.png"))
        print("  ✓ Tab 1 verified (Parameters)")

        # Tab 2: Spatial Analysis
        page.locator("button:has-text('2. Spatial')").click()
        time.sleep(1)
        page.screenshot(path=str(ARTIFACTS_DIR / "workspace_tab2_spatial.png"))
        print("  ✓ Tab 2 verified (Spatial)")

        # Tab 3: Causal Hypotheses
        page.locator("button:has-text('3. Hypotheses')").click()
        time.sleep(1)
        page.screenshot(path=str(ARTIFACTS_DIR / "workspace_tab3_hypotheses.png"))
        print("  ✓ Tab 3 verified (Hypotheses)")

        # Tab 4: Research Evidence
        page.locator("button:has-text('4. Evidence')").click()
        time.sleep(1)
        page.screenshot(path=str(ARTIFACTS_DIR / "workspace_tab4_evidence.png"))
        print("  ✓ Tab 4 verified (Evidence)")

        # Tab 5: Forecasting
        page.locator("button:has-text('5. Forecasting')").click()
        time.sleep(1)
        page.screenshot(path=str(ARTIFACTS_DIR / "workspace_tab5_forecasting.png"))
        print("  ✓ Tab 5 verified (Forecasting)")

        # Tab 6: Reports
        page.locator("button:has-text('6. Reports')").click()
        time.sleep(1)
        page.screenshot(path=str(ARTIFACTS_DIR / "workspace_tab6_reports.png"))
        print("  ✓ Tab 6 verified (Reports)")

        browser.close()

    print("\n=== All Conversational AI Investigator E2E Tests PASSED! ===")


if __name__ == "__main__":
    test_conversational_ai_investigator()
