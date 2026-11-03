"""Unit and integration tests for Environmental Forecasting Engine (Phase 4)."""

from __future__ import annotations

import unittest
from environmental.forecasting import (
    HistoricalObservation,
    ForecastPoint,
    ScenarioResult,
    ForecastReport,
    validate_historical_time_series,
    resolve_target_year,
    generate_environmental_forecast,
    parse_observation_timestamp,
)


class TestEnvironmentalForecasting(unittest.TestCase):

    def setUp(self):
        # 5-year historical annual PM2.5 time series
        self.pm25_history = [
            HistoricalObservation(
                timestamp="2020-01-01T00:00:00Z",
                year=2020.0,
                value=60.0,
                unit="µg/m³",
                indicator="PM2.5",
                source="Continuous CAAQMS Telemetry",
            ),
            HistoricalObservation(
                timestamp="2021-01-01T00:00:00Z",
                year=2021.0,
                value=68.0,
                unit="µg/m³",
                indicator="PM2.5",
                source="Continuous CAAQMS Telemetry",
            ),
            HistoricalObservation(
                timestamp="2022-01-01T00:00:00Z",
                year=2022.0,
                value=74.0,
                unit="µg/m³",
                indicator="PM2.5",
                source="Continuous CAAQMS Telemetry",
            ),
            HistoricalObservation(
                timestamp="2023-01-01T00:00:00Z",
                year=2023.0,
                value=82.0,
                unit="µg/m³",
                indicator="PM2.5",
                source="Continuous CAAQMS Telemetry",
            ),
            HistoricalObservation(
                timestamp="2024-01-01T00:00:00Z",
                year=2024.0,
                value=90.0,
                unit="µg/m³",
                indicator="PM2.5",
                source="Continuous CAAQMS Telemetry",
            ),
        ]

        # 5-year lake dissolved oxygen time series (degrading)
        self.do_history = [
            HistoricalObservation(
                timestamp="2020-01-01T00:00:00Z",
                year=2020.0,
                value=4.5,
                unit="mg/L",
                indicator="dissolved_oxygen_mg_l",
                source="Lake In-Situ Sensor",
            ),
            HistoricalObservation(
                timestamp="2021-01-01T00:00:00Z",
                year=2021.0,
                value=3.8,
                unit="mg/L",
                indicator="dissolved_oxygen_mg_l",
                source="Lake In-Situ Sensor",
            ),
            HistoricalObservation(
                timestamp="2022-01-01T00:00:00Z",
                year=2022.0,
                value=2.9,
                unit="mg/L",
                indicator="dissolved_oxygen_mg_l",
                source="Lake In-Situ Sensor",
            ),
            HistoricalObservation(
                timestamp="2023-01-01T00:00:00Z",
                year=2023.0,
                value=2.1,
                unit="mg/L",
                indicator="dissolved_oxygen_mg_l",
                source="Lake In-Situ Sensor",
            ),
            HistoricalObservation(
                timestamp="2024-01-01T00:00:00Z",
                year=2024.0,
                value=1.4,
                unit="mg/L",
                indicator="dissolved_oxygen_mg_l",
                source="Lake In-Situ Sensor",
            ),
        ]

    def test_parse_timestamps(self):
        dt1, yr1 = parse_observation_timestamp("2024-05-15T12:00:00Z")
        self.assertEqual(dt1.year, 2024)
        self.assertAlmostEqual(yr1, 2024.37, places=1)

        dt2, yr2 = parse_observation_timestamp("2020")
        self.assertEqual(dt2.year, 2020)
        self.assertEqual(yr2, 2020.0)

    def test_validate_historical_time_series_success(self):
        valid, err = validate_historical_time_series(self.pm25_history)
        self.assertIsNone(err)
        self.assertEqual(len(valid), 5)

    def test_validate_rejection_insufficient_records(self):
        # Only 2 points
        short_history = self.pm25_history[:2]
        valid, err = validate_historical_time_series(short_history, min_observations=4)
        self.assertIsNotNone(err)
        self.assertIn("Insufficient historical data", err)

    def test_validate_rejection_physical_bound_violation(self):
        invalid_obs = self.pm25_history.copy()
        # Negative PM2.5 violates physical reality
        invalid_obs.append(
            HistoricalObservation(
                timestamp="2025-01-01T00:00:00Z",
                year=2025.0,
                value=-15.0,
                unit="µg/m³",
                indicator="PM2.5",
            )
        )
        valid, err = validate_historical_time_series(invalid_obs)
        self.assertIsNotNone(err)
        self.assertIn("Physical bound violation", err)

    def test_validate_rejection_inconsistent_unit(self):
        invalid_obs = self.pm25_history.copy()
        invalid_obs.append(
            HistoricalObservation(
                timestamp="2025-01-01T00:00:00Z",
                year=2025.0,
                value=50.0,
                unit="ppm",  # Inconsistent unit
                indicator="PM2.5",
            )
        )
        valid, err = validate_historical_time_series(invalid_obs, expected_unit="µg/m³")
        self.assertIsNotNone(err)
        self.assertIn("Inconsistent unit", err)

    def test_resolve_target_year(self):
        self.assertEqual(resolve_target_year("+1 year", 2024), 2025)
        self.assertEqual(resolve_target_year("+3 years", 2024), 2027)
        self.assertEqual(resolve_target_year("+5 years", 2024), 2029)
        self.assertEqual(resolve_target_year("2030", 2024), 2030)
        self.assertEqual(resolve_target_year("2040", 2024), 2040)

    def test_generate_environmental_forecast_pm25_horizons(self):
        for horizon in ["+1 year", "+3 years", "+5 years", "2030"]:
            report, err = generate_environmental_forecast(
                historical_data=self.pm25_history,
                horizon=horizon,
                reduction_percentage=30.0,
            )
            self.assertIsNone(err)
            self.assertIsNotNone(report)
            self.assertEqual(report.indicator, "PM2.5")
            self.assertEqual(report.baseline_year, 2024)
            self.assertEqual(report.baseline_value, 90.0)

            # Check all 3 scenarios exist
            self.assertIn("BAU", report.scenarios)
            self.assertIn("POL_RED", report.scenarios)
            self.assertIn("INTERVENTION", report.scenarios)

            bau_traj = report.scenarios["BAU"].trajectory
            self.assertGreater(len(bau_traj), 0)

            # Check interval bounds hierarchy: lower95 <= lower80 <= val <= upper80 <= upper95
            for pt in bau_traj:
                self.assertLessEqual(pt.lower_95, pt.lower_80)
                self.assertLessEqual(pt.lower_80, pt.projected_value + 1e-6)
                self.assertLessEqual(pt.projected_value, pt.upper_80 + 1e-6)
                self.assertLessEqual(pt.upper_80, pt.upper_95)
                # Physical bounds: PM >= 0
                self.assertGreaterEqual(pt.lower_95, 0.0)

    def test_prediction_intervals_expand_with_horizon(self):
        report, _ = generate_environmental_forecast(
            historical_data=self.pm25_history,
            horizon="+5 years",
        )
        bau_pts = report.scenarios["BAU"].trajectory
        # Uncertainty margin at year 5 should be greater than year 1
        margin_yr1 = bau_pts[0].uncertainty_margin
        margin_yr5 = bau_pts[-1].uncertainty_margin
        self.assertGreater(margin_yr5, margin_yr1)

    def test_scenario_comparison_policy_reduction(self):
        report, _ = generate_environmental_forecast(
            historical_data=self.pm25_history,
            horizon="+5 years",
            reduction_percentage=30.0,
        )
        bau_final = report.scenarios["BAU"].trajectory[-1].projected_value
        red_final = report.scenarios["POL_RED"].trajectory[-1].projected_value
        int_final = report.scenarios["INTERVENTION"].trajectory[-1].projected_value

        # Under 30% reduction, pollutant concentration must be significantly lower than BAU
        self.assertLess(red_final, bau_final)
        # Under comprehensive intervention, it should also be significantly lower
        self.assertLess(int_final, bau_final)

    def test_dissolved_oxygen_recovery_scenario(self):
        report, _ = generate_environmental_forecast(
            historical_data=self.do_history,
            horizon="+5 years",
            reduction_percentage=30.0,
        )
        # Under BAU, DO continues to drop
        bau_final = report.scenarios["BAU"].trajectory[-1].projected_value
        # Under intervention, aeration & wetland buffer recovers DO
        int_final = report.scenarios["INTERVENTION"].trajectory[-1].projected_value

        self.assertGreater(int_final, bau_final)
        # Must not exceed physical saturation (approx 16 mg/L)
        self.assertLessEqual(int_final, 16.0)

    def test_rejection_when_insufficient_epochs(self):
        # 3 points only -> should fail data sufficiency check
        short_history = self.pm25_history[:3]
        report, err = generate_environmental_forecast(short_history, horizon="+5 years")
        self.assertIsNone(report)
        self.assertIsNotNone(err)
        self.assertIn("Insufficient historical data", err)


if __name__ == "__main__":
    unittest.main()

