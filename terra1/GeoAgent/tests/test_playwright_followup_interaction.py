"""Playwright Comprehensive End-to-End Verification for Conversational Language and Follow-up Interaction Fix.
Phase 8.4 Verification:
1. Natural Conversational Style with Two Levels of Explanation (Level A Simple, Level B Scientific).
2. Dynamic Suggestion Buttons that submit through unified executeSendMessage pipeline.
3. Context-aware multi-turn flow:
   - 'Analyze vegetation changes in the Amazon rainforest.'
   - Click 'Why is this happening?' (Causal drivers for Amazon, NOT fish deaths)
   - Click 'Show me scientific research.' (Amazon peer-reviewed publications + DOIs)
   - Click 'Explain in simple language.' (Analogy: air conditioner & water sponge)
   - Click 'What will happen in five years?' (Data sufficiency check + forecast)
4. Input Send button test.
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


def run_followup_interaction_verification():
    print("=== Starting TerraPulse 2.0 Conversational Language & Follow-up E2E Verification ===")

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

        # Switch to AI Earth Investigator
        investigator_btn = page.locator("button:has-text('AI Earth Investigator')").first
        if investigator_btn.is_visible():
            investigator_btn.click()
            time.sleep(2)

        chat_input = page.locator("input[placeholder*='Ask any environmental question'], input[placeholder*='Ask an environmental']").first

        # --------------------------------------------------------------------
        # TURN 1: Initial Investigation Query
        # --------------------------------------------------------------------
        print("\n[STEP 2] Submitting Turn 1: 'Analyze vegetation changes in the Amazon rainforest.'...")
        chat_input.fill("Analyze vegetation changes in the Amazon rainforest.")
        chat_input.press("Enter")

        # Wait for assistant response to finish (wait for suggestion buttons to render)
        print("  Waiting for agent response and suggestion buttons...")
        page.wait_for_selector("button:has-text('Why is this happening?')", timeout=35000)
        time.sleep(3)

        # Chat container selector
        chat_container = page.locator(".flex-1.overflow-y-auto.p-3\\.5").first

        # Verify Two Levels of Explanation in chat
        chat_text = chat_container.inner_text()
        assert "Simple Explanation" in chat_text or "What happened" in chat_text, "Missing Level A Simple Explanation"
        assert "Scientific Details" in chat_text or "Methodology" in chat_text, "Missing Level B Scientific Details"
        print("  ✓ Turn 1 response verified: Two Levels of Explanation present.")

        page.screenshot(path=str(ARTIFACTS_DIR / "followup_step1_amazon_vegetation.png"))
        print("  ✓ Captured followup_step1_amazon_vegetation.png")

        # --------------------------------------------------------------------
        # TURN 2: Click Suggestion Button: "Why is this happening?"
        # --------------------------------------------------------------------
        print("\n[STEP 3] Clicking Suggestion Button: 'Why is this happening?'...")
        why_btn = page.locator("button:has-text('Why is this happening?')").last
        assert why_btn.is_visible(), "Button 'Why is this happening?' not found!"
        why_btn.click()

        # Verify user message appears in chat transcript
        print("  Waiting for 'Why is this happening?' to be processed...")
        page.wait_for_selector("text=Why is this happening?", timeout=10000)
        
        # Wait for agent answer to complete
        page.wait_for_selector("text=Why Are These Changes Happening", timeout=40000)
        time.sleep(3)

        # Verify it discusses Amazon causes (ranching, highway, logging), NOT fish deaths
        chat_text_2 = chat_container.inner_text()
        assert "Cattle Ranching" in chat_text_2 or "Highway" in chat_text_2 or "deforestation" in chat_text_2.lower(), "Incorrect context for Why is this happening!"
        assert "fish mortality" not in chat_text_2.lower() and "hypoxia" not in chat_text_2.lower(), "Regressed to fish mortality!"
        print("  ✓ Turn 2 response verified: Context-aware causal drivers for Amazon forest loss.")

        page.screenshot(path=str(ARTIFACTS_DIR / "followup_step2_why_happening.png"))
        print("  ✓ Captured followup_step2_why_happening.png")

        # --------------------------------------------------------------------
        # TURN 3: Click Suggestion Button: "Show me scientific research."
        # --------------------------------------------------------------------
        print("\n[STEP 4] Clicking Suggestion Button: 'Show me scientific research.'...")
        research_btn = page.locator("button:has-text('Show me scientific research.')").last
        assert research_btn.is_visible(), "Button 'Show me scientific research.' not found!"
        research_btn.click()

        print("  Waiting for research papers response...")
        page.wait_for_selector("text=Scientific Research Evidence", timeout=45000)
        time.sleep(3)

        # Verify research citations & DOIs
        chat_text_3 = chat_container.inner_text()
        assert "doi.org" in chat_text_3 or "10." in chat_text_3, "Missing DOI links in research papers response"
        print("  ✓ Turn 3 response verified: Contextual peer-reviewed research citations loaded.")

        page.screenshot(path=str(ARTIFACTS_DIR / "followup_step3_scientific_research.png"))
        print("  ✓ Captured followup_step3_scientific_research.png")

        # --------------------------------------------------------------------
        # TURN 4: Click Suggestion Button: "Explain in simple language."
        # --------------------------------------------------------------------
        print("\n[STEP 5] Clicking Suggestion Button: 'Explain in simple language.'...")
        simple_btn = page.locator("button:has-text('Explain in simple language.')").last
        assert simple_btn.is_visible(), "Button 'Explain in simple language.' not found!"
        simple_btn.click()

        print("  Waiting for simple language response...")
        page.wait_for_selector("text=The forest is like a giant natural air conditioner", timeout=40000)
        time.sleep(3)

        # Verify plain English analogies
        chat_text_4 = chat_container.inner_text()
        assert "air conditioner" in chat_text_4 or "sponge" in chat_text_4, "Missing expected plain English analogies"
        print("  ✓ Turn 4 response verified: Plain language explanation with clear analogies.")

        page.screenshot(path=str(ARTIFACTS_DIR / "followup_step4_simple_language.png"))
        print("  ✓ Captured followup_step4_simple_language.png")

        # --------------------------------------------------------------------
        # TURN 5: Click Suggestion Button: "What will happen in five years?"
        # --------------------------------------------------------------------
        print("\n[STEP 6] Clicking Suggestion Button: 'What will happen in five years?'...")
        forecast_btn = page.locator("button:has-text('What will happen in five years?')").last
        assert forecast_btn.is_visible(), "Button 'What will happen in five years?' not found!"
        forecast_btn.click()

        print("  Waiting for forecasting response...")
        page.wait_for_selector("text=Environmental Forecasting Report", timeout=45000)
        time.sleep(3)

        # Verify forecast details
        chat_text_5 = chat_container.inner_text()
        assert "Data Sufficiency Check" in chat_text_5, "Missing Data Sufficiency Check in forecast"
        assert "Business-As-Usual" in chat_text_5 or "Scenario" in chat_text_5, "Missing multi-scenario projection in forecast"
        print("  ✓ Turn 5 response verified: Multi-scenario forecast with data sufficiency check.")

        page.screenshot(path=str(ARTIFACTS_DIR / "followup_step5_five_year_forecast.png"))
        print("  ✓ Captured followup_step5_five_year_forecast.png")

        # --------------------------------------------------------------------
        # TURN 6: Manual Input with Send Button (Testing the icon button click)
        # --------------------------------------------------------------------
        print("\n[STEP 7] Testing Send Button with query 'What is the highest mountain in India?'...")
        chat_input.fill("What is the highest mountain in India?")
        
        # Click the Send button icon
        send_btn = page.locator("button[type='submit']").first
        send_btn.click()

        print("  Waiting for response to manual Send button...")
        page.wait_for_selector("text=Kangchenjunga", timeout=35000)
        time.sleep(3)

        chat_text_6 = chat_container.inner_text()
        assert "Kangchenjunga" in chat_text_6, "Kangchenjunga answer missing from chat"
        print("  ✓ Turn 6 response verified: Send button successfully dispatches message.")

        page.screenshot(path=str(ARTIFACTS_DIR / "followup_step6_send_button_verified.png"))
        print("  ✓ Captured followup_step6_send_button_verified.png")

        browser.close()
        print("\n=== ALL E2E PLAYWRIGHT TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_followup_interaction_verification()
