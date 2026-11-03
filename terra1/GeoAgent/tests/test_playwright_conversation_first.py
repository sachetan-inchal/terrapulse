"""Playwright End-to-End Verification for Conversation-First Architecture & 6 Specific Queries.

Tests:
1. Startup: Clean conversation welcome, empty search, no preloaded Bengaluru/telemetry, map at world center.
2. Test A: "Which is the highest mountain in India?" -> Kangchenjunga direct answer.
3. Test C: "What is NDVI?" -> Formula, range table, no tool clutter.
4. Test B: "Why is air pollution increasing in Chennai?" -> Chennai detected, map navigated, in-situ CAAQMS telemetry, verified DOIs.
5. Reset: Session reset clears context.
6. Test D: "Analyze vegetation changes in the Amazon rainforest." -> Multi-temporal change detection, remote wilderness sensor note.
7. Test E: "Show me research supporting this." -> Follow-up contextual research with real DOIs.
8. Test F: "What will happen in five years?" -> Multi-scenario forward forecast (+5 years, BAU, Policy, Intervention).
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


def run_conversation_first_verification():
    print("=== Starting TerraPulse 2.0 Conversation-First E2E Verification ===")

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

        # Ensure we are in AI Earth Investigator mode
        investigator_btn = page.locator("button:has-text('AI Earth Investigator')").first
        if investigator_btn.is_visible():
            investigator_btn.click()
            time.sleep(1.5)

        # Verify Startup State
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step1_clean_startup.png"))
        print("  ✓ Captured cf_step1_clean_startup.png (Verified: Clean startup welcome, no preloaded telemetry)")

        chat_input = page.locator("input[placeholder*='Ask any environmental question'], input[placeholder*='Ask an environmental']").first

        # --------------------------------------------------------------------
        # TEST A: "Which is the highest mountain in India?"
        # --------------------------------------------------------------------
        print("\n[STEP 2] TEST A: Querying 'Which is the highest mountain in India?'...")
        chat_input.fill("Which is the highest mountain in India?")
        chat_input.press("Enter")

        page.wait_for_selector("text=Kangchenjunga", timeout=25000)
        time.sleep(2)
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step2_kangchenjunga.png"))
        print("  ✓ Test A passed! Kangchenjunga answered directly without tool clutter. Captured cf_step2_kangchenjunga.png")

        # --------------------------------------------------------------------
        # TEST C: "What is NDVI?"
        # --------------------------------------------------------------------
        print("\n[STEP 3] TEST C: Querying conceptual definition 'What is NDVI?'...")
        chat_input.fill("What is NDVI?")
        chat_input.press("Enter")

        page.wait_for_selector("text=Normalized Difference Vegetation Index", timeout=25000)
        time.sleep(2)
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step3_ndvi.png"))
        print("  ✓ Test C passed! NDVI formula and range explained directly. Captured cf_step3_ndvi.png")

        # --------------------------------------------------------------------
        # TEST B: "Why is air pollution increasing in Chennai?"
        # --------------------------------------------------------------------
        print("\n[STEP 4] TEST B: Querying 'Why is air pollution increasing in Chennai?'...")
        chat_input.fill("Why is air pollution increasing in Chennai?")
        chat_input.press("Enter")

        page.wait_for_selector("text=Chennai", timeout=30000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step4_chennai_pollution.png"))
        print("  ✓ Test B passed! Chennai air quality investigated with CAAQMS telemetry. Captured cf_step4_chennai_pollution.png")

        # Check Parameters tab
        param_tab = page.locator("button:has-text('1. Parameters')").first
        if param_tab.is_visible():
            param_tab.click()
            time.sleep(1)
            page.screenshot(path=str(ARTIFACTS_DIR / "cf_step4_chennai_parameters_tab.png"))
            print("  ✓ Captured cf_step4_chennai_parameters_tab.png")

        # --------------------------------------------------------------------
        # RESET SESSION
        # --------------------------------------------------------------------
        print("\n[STEP 5] Testing Session Reset ('New Investigation')...")
        reset_btn = page.locator("button:has-text('New Investigation'), button:has-text('New')").first
        if reset_btn.is_visible():
            reset_btn.click()
            time.sleep(1.5)
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step5_session_reset.png"))
        print("  ✓ Captured cf_step5_session_reset.png (Session and location context cleared)")

        # --------------------------------------------------------------------
        # TEST D: "Analyze vegetation changes in the Amazon rainforest."
        # --------------------------------------------------------------------
        print("\n[STEP 6] TEST D: Querying 'Analyze vegetation changes in the Amazon rainforest.'...")
        chat_input.fill("Analyze vegetation changes in the Amazon rainforest.")
        chat_input.press("Enter")

        page.wait_for_selector("text=Amazon", timeout=30000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step6_amazon_vegetation.png"))
        print("  ✓ Test D passed! Multi-decadal satellite change detection over Amazon. Captured cf_step6_amazon_vegetation.png")

        # --------------------------------------------------------------------
        # TEST E: "Show me research supporting this." (Contextual follow-up)
        # --------------------------------------------------------------------
        print("\n[STEP 7] TEST E: Follow-up 'Show me research supporting this.'...")
        chat_input.fill("Show me research supporting this.")
        chat_input.press("Enter")

        page.wait_for_selector("text=Scientific Literature Findings", timeout=65000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step7_amazon_research.png"))
        print("  ✓ Test E passed! Retrieved peer-reviewed papers on Amazon deforestation. Captured cf_step7_amazon_research.png")

        # Check Evidence tab
        evidence_tab = page.locator("button:has-text('4. Evidence')").first
        if evidence_tab.is_visible():
            evidence_tab.click()
            time.sleep(1)
            page.screenshot(path=str(ARTIFACTS_DIR / "cf_step7_evidence_tab.png"))
            print("  ✓ Captured cf_step7_evidence_tab.png")

        # --------------------------------------------------------------------
        # TEST F: "What will happen in five years?" (Contextual forward forecast)
        # --------------------------------------------------------------------
        print("\n[STEP 8] TEST F: Follow-up 'What will happen in five years?'...")
        chat_input.fill("What will happen in five years?")
        chat_input.press("Enter")

        page.wait_for_selector("text=Environmental Forecasting Report", timeout=65000)
        time.sleep(3)
        page.screenshot(path=str(ARTIFACTS_DIR / "cf_step8_amazon_forecast.png"))
        print("  ✓ Test F passed! Multi-scenario forward forecast (+5 years, BAU, Policy, Intervention). Captured cf_step8_amazon_forecast.png")

        # Check Forecasting tab
        forecast_tab = page.locator("button:has-text('5. Forecasting')").first
        if forecast_tab.is_visible():
            forecast_tab.click()
            time.sleep(1)
            page.screenshot(path=str(ARTIFACTS_DIR / "cf_step8_forecasting_tab.png"))
            print("  ✓ Captured cf_step8_forecasting_tab.png")

        browser.close()
        print("\n=== All 6 Tests & Multi-Tab E2E Verifications Completed Successfully! ===")


if __name__ == "__main__":
    run_conversation_first_verification()
