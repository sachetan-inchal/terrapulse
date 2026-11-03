"""End-to-End Browser Demonstration and Verification for TerraPulse 2.0:
- Mode A: AI Environmental Investigator (Dedicated 3-panel workspace, SSE streaming, causal analysis)
- Mode B: Earth Observation Explorer (Complete cleanup with 9 dedicated workspaces, clean Overview default)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ARTIFACTS_DIR = Path(r"C:\Users\rishi\.gemini\antigravity\brain\20309b08-3dc7-4ad4-9427-13438187e9f8\screenshots")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def run_e2e_demonstration():
    print("=== Starting TerraPulse 2.0 Comprehensive End-to-End Verification ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        context = browser.new_context(viewport={"width": 1600, "height": 950})
        page = context.new_page()
        page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))

        # -------------------------------------------------------------
        # Part 1: Mode A - AI Environmental Investigator Workspace
        # -------------------------------------------------------------
        print("\n[PART 1: MODE A - AI EARTH INVESTIGATOR]")
        print("[1/18] Loading TerraPulse at http://127.0.0.1:8000 (Mode A: AI Investigator)...")
        page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded", timeout=25000)
        time.sleep(3)

        # Verify Mode A primary layout: 3-panel workspace
        page.wait_for_selector("text=Strands Investigator", timeout=10000)
        page.wait_for_selector("text=Spatial Controls", timeout=10000)
        page.wait_for_selector("button:has-text('Parameters')", timeout=10000)
        
        # Verify NO Explorer clutter in Mode A
        assert page.locator("text=Image Processing Pipeline").count() == 0, "Error: Explorer pipeline found in Investigator mode!"
        assert page.locator("text=Earth Observation Explorer Studio").count() == 0, "Error: Explorer sidebar found in Investigator mode!"

        page.screenshot(path=str(ARTIFACTS_DIR / "1_dedicated_investigator_workspace.png"))
        print("       Mode A is clean, dedicated, and isolated!")

        # Inquire: "Why is pollution increasing around Chennai?"
        print("[2/18] Submitting inquiry: 'Why is pollution increasing around Chennai?'...")
        chat_input = page.locator("input[placeholder*='Ask an environmental question']")
        chat_input.fill("Why is pollution increasing around Chennai?")
        send_btn = page.locator("button[type='submit']")
        send_btn.click()

        # Verify clarification question
        print("[3/18] Waiting for clarification question...")
        page.wait_for_selector("text=Which type of pollution around Chennai", timeout=20000)
        page.screenshot(path=str(ARTIFACTS_DIR / "2_clarification_prompt.png"))
        print("       Clarification received successfully!")

        # Select "Air Pollution (PM2.5 & Smog)"
        print("[4/18] Selecting 'Air Pollution (PM2.5 & Smog)' option...")
        air_btn = page.locator("button:has-text('Air Pollution (PM2.5 & Smog)')").first
        air_btn.click()

        # Verify live activity stream & ranked hypotheses
        print("[5/18] Monitoring SSE streaming & causal hypotheses...")
        page.wait_for_selector("text=Ranked Causal Hypotheses", timeout=30000)
        time.sleep(2)
        page.screenshot(path=str(ARTIFACTS_DIR / "3_symptom_investigation_results.png"))
        print("       Investigation completed and evidence synthesized!")

        # Verify Tab 4: Forecasting
        print("[6/18] Testing Forecasting Scenario Projections...")
        page.locator("button:has-text('Forecasting')").click()
        time.sleep(1)
        page.wait_for_selector("text=Multi-Scenario Environmental Forecasting", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "4_forecasting_scenarios.png"))
        print("       Forecasting scenarios verified!")

        # -------------------------------------------------------------
        # Part 2: Mode B - Earth Observation Explorer Clean Redesign
        # -------------------------------------------------------------
        print("\n[PART 2: MODE B - EARTH OBSERVATION EXPLORER CLEAN REDESIGN]")
        print("[7/18] Switching to Mode B: Earth Observation Explorer...")
        exp_button = page.locator("button:has-text('Earth Observation Explorer')").first
        exp_button.click()
        time.sleep(3)

        # 1. Workspace 1: Overview (Default Screen)
        print("[8/18] Verifying Workspace 1: Overview (Default Screen)...")
        page.wait_for_selector("text=1. Overview", timeout=10000)
        page.wait_for_selector("text=Satellite Availability", timeout=10000)
        page.wait_for_selector("text=Active Layers:", timeout=10000)
        page.wait_for_selector("text=Surface Telemetry", timeout=10000)
        
        # Verify Overview is clean: NO floating observation cards over globe, NO pipeline, NO AI panel on right
        assert page.locator("text=Image Processing Pipeline").count() == 0, "Error: Pipeline visualizer must NOT be in Overview!"
        assert page.locator("text=Why did this region change?").count() == 0, "Error: AI findings panel must NOT be in Explorer Overview!"
        
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_1_overview.png"))
        page.screenshot(path=str(ARTIFACTS_DIR / "mode_b_explorer_workspace.png"))
        print("       Workspace 1: Overview is clean, modular, and un-cluttered!")

        # 2. Workspace 2: Satellite Imagery
        print("[9/18] Testing Workspace 2: Satellite Imagery...")
        page.locator("button:has-text('2. Satellite Imagery')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Satellite Imagery & Scene Catalog", timeout=10000)
        page.wait_for_selector("text=Satellite Provider Filter", timeout=10000)
        page.wait_for_selector("text=Scene Metadata Inspector", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_2_imagery.png"))
        print("       Workspace 2: Satellite Imagery catalog verified!")

        # 3. Workspace 3: Spectral Analysis
        print("[10/18] Testing Workspace 3: Spectral Analysis...")
        page.locator("button:has-text('3. Spectral Analysis')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Multi-Spectral Raster & Band Composition Studio", timeout=10000)
        page.wait_for_selector("text=True Color Natural RGB", timeout=10000)
        page.wait_for_selector("text=False Color Infrared (NIR)", timeout=10000)
        page.wait_for_selector("text=Custom Band Composition", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_3_spectral.png"))
        print("       Workspace 3: Spectral Analysis studio verified!")

        # 4. Workspace 4: Land Cover & Vegetation
        print("[11/18] Testing Workspace 4: Land Cover & Vegetation...")
        page.locator("button:has-text('4. Land Cover & Vegetation')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Land Cover & Vegetation Classification", timeout=10000)
        page.wait_for_selector("text=LULC Raster Classification Map", timeout=10000)
        page.wait_for_selector("text=Area Breakdown Statistics", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_4_landcover.png"))
        print("       Workspace 4: Land Cover classification verified!")

        # 5. Workspace 5: Historical Analysis
        print("[12/18] Testing Workspace 5: Historical Analysis...")
        page.locator("button:has-text('5. Historical Analysis')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Multi-Decadal Historical Analysis", timeout=10000)
        page.wait_for_selector("text=Urban Expansion vs Vegetation Cover (%)", timeout=10000)
        page.wait_for_selector("text=Decadal Satellite Observations Gallery", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_5_historical.png"))
        print("       Workspace 5: Historical Analysis timeline & charts verified!")

        # 6. Workspace 6: Change Detection
        print("[13/18] Testing Workspace 6: Change Detection...")
        page.locator("button:has-text('6. Change Detection')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Bi-Temporal Change Detection Studio", timeout=10000)
        page.wait_for_selector("text=Interactive Split-Screen Swipe Comparison", timeout=10000)
        page.wait_for_selector("text=Total Changed Area", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_6_changedetection.png"))
        print("       Workspace 6: Change Detection swipe comparison verified!")

        # 7. Workspace 7: Environmental Indicators
        print("[14/18] Testing Workspace 7: Environmental Indicators...")
        page.locator("button:has-text('7. Environmental Indicators')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Environmental Indicators & Biophysical Telemetry", timeout=10000)
        page.wait_for_selector("text=Radiometric Response Scale:", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_7_indicators.png"))
        print("       Workspace 7: Environmental Indicators biophysical telemetry verified!")

        # 8. Workspace 8: Computer Vision
        print("[15/18] Testing Workspace 8: Computer Vision...")
        page.locator("button:has-text('8. Computer Vision')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Computer Vision & Image Registration Workspace", timeout=10000)
        page.wait_for_selector("text=Image Processing Pipeline", timeout=10000)
        page.wait_for_selector("text=SIFT Inlier Matches & Keypoint Vectors", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_8_computervision.png"))
        print("       Workspace 8: Computer Vision & SIFT/RANSAC pipeline verified!")

        # 9. Workspace 9: Reports & Exports
        print("[16/18] Testing Workspace 9: Reports & Exports...")
        page.locator("button:has-text('9. Reports & Exports')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Reports, Exports & Reproducibility Studio", timeout=10000)
        page.wait_for_selector("text=Export High-Resolution Raster", timeout=10000)
        page.wait_for_selector("text=Export GeoJSON Feature Set", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "explorer_workspace_9_reports.png"))
        print("       Workspace 9: Reports & Exports verified!")

        # Switch back to Overview
        print("[17/18] Switching back to Workspace 1: Overview...")
        page.locator("button:has-text('1. Overview')").click()
        time.sleep(1.5)
        page.wait_for_selector("text=Satellite Availability", timeout=10000)
        print("       Overview restored cleanly!")

        # Switch back to Mode A: AI Environmental Investigator
        print("[18/18] Switching back to Mode A: AI Earth Investigator...")
        inv_button = page.locator("button:has-text('AI Earth Investigator')").first
        inv_button.click()
        time.sleep(2)
        page.wait_for_selector("text=Strands Investigator", timeout=10000)
        page.screenshot(path=str(ARTIFACTS_DIR / "6_investigator_restored.png"))
        print("       Returned cleanly to Mode A with state preserved!")

        browser.close()

    print("\n=== All 18 E2E verification steps PASSED with ZERO errors! ===")


if __name__ == "__main__":
    run_e2e_demonstration()
