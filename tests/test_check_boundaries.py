import sys
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.calculations import analyze_cccc  # noqa: E402
from stiffened_plate.models import (  # noqa: E402
    CheckStatus,
    CcccAnalysisInput,
    StiffenerOrientation,
)
from stiffened_plate.sections import FlatBarSection  # noqa: E402


class CheckBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.inputs = CcccAnalysisInput(
            long_span_in=72.0,
            short_span_in=40.0,
            plate_thickness_in=0.1345,
            stiffener_count=2,
            elastic_modulus_ksi=29_000.0,
            poisson_ratio=0.3,
            yield_strength_ksi=36.0,
            uniform_force_lbf=2_000.0,
            deflection_limit_denominator=240.0,
            stiffener_orientation=StiffenerOrientation.LONG_SPAN,
            stiffener=FlatBarSection(2.0, 0.25),
        )

    def test_zero_demand_checks_pass_with_zero_utilization(self):
        result = analyze_cccc(replace(self.inputs, uniform_force_lbf=0.0))
        for check in (
            result.checks.deflection,
            result.checks.plate_yield,
            result.checks.stiffener_yield,
        ):
            with self.subTest(check=check.name):
                self.assertEqual(check.status, CheckStatus.PASS)
                self.assertEqual(check.demand, 0.0)
                self.assertEqual(check.utilization, 0.0)

    def test_deflection_limit_passes_at_equality_and_fails_above(self):
        baseline = analyze_cccc(self.inputs)
        exact_denominator = (
            self.inputs.short_span_in / baseline.response.maximum_deflection_in
        )
        exact = analyze_cccc(
            replace(self.inputs, deflection_limit_denominator=exact_denominator)
        )
        failed = analyze_cccc(
            replace(
                self.inputs,
                deflection_limit_denominator=exact_denominator * 1.000001,
            )
        )
        self.assertEqual(exact.checks.deflection.status, CheckStatus.PASS)
        self.assertAlmostEqual(exact.checks.deflection.utilization, 1.0, places=14)
        self.assertEqual(failed.checks.deflection.status, CheckStatus.FAIL)
        self.assertGreater(failed.checks.deflection.utilization, 1.0)

    def test_plate_yield_passes_at_equality_and_fails_above(self):
        baseline = analyze_cccc(self.inputs)
        exact_strength = baseline.response.plate_stress_ksi
        exact = analyze_cccc(replace(self.inputs, yield_strength_ksi=exact_strength))
        failed = analyze_cccc(
            replace(self.inputs, yield_strength_ksi=exact_strength * 0.999999)
        )
        self.assertEqual(exact.checks.plate_yield.status, CheckStatus.PASS)
        self.assertEqual(exact.checks.plate_yield.utilization, 1.0)
        self.assertEqual(failed.checks.plate_yield.status, CheckStatus.FAIL)

    def test_stiffener_yield_passes_at_equality_and_fails_above(self):
        baseline = analyze_cccc(self.inputs)
        exact_strength = baseline.response.stiffener_stress_ksi
        exact = analyze_cccc(replace(self.inputs, yield_strength_ksi=exact_strength))
        failed = analyze_cccc(
            replace(self.inputs, yield_strength_ksi=exact_strength * 0.999999)
        )
        self.assertEqual(exact.checks.stiffener_yield.status, CheckStatus.PASS)
        self.assertEqual(exact.checks.stiffener_yield.utilization, 1.0)
        self.assertEqual(failed.checks.stiffener_yield.status, CheckStatus.FAIL)

    def test_check_demands_limits_and_units_match_response(self):
        result = analyze_cccc(self.inputs)
        self.assertEqual(
            result.checks.deflection.demand,
            result.response.maximum_deflection_in,
        )
        self.assertEqual(
            result.checks.deflection.limit,
            result.response.allowable_deflection_in,
        )
        self.assertEqual(result.checks.deflection.unit, "in")
        self.assertEqual(
            result.checks.plate_yield.demand,
            result.response.plate_stress_ksi,
        )
        self.assertEqual(
            result.checks.stiffener_yield.demand,
            result.response.stiffener_stress_ksi,
        )
        self.assertEqual(result.checks.plate_yield.limit, 36.0)
        self.assertEqual(result.checks.stiffener_yield.limit, 36.0)
        self.assertEqual(result.checks.plate_yield.unit, "ksi")

    def test_unimplemented_checks_never_report_pass(self):
        result = analyze_cccc(self.inputs)
        for check in (
            result.checks.plate_stability,
            result.checks.stiffener_stability,
            result.checks.connection,
            result.checks.combined_stress,
        ):
            with self.subTest(check=check.name):
                self.assertEqual(check.status, CheckStatus.NOT_IMPLEMENTED)
                self.assertIsNone(check.demand)
                self.assertIsNone(check.limit)
                self.assertIsNone(check.utilization)
                self.assertTrue(check.note)


if __name__ == "__main__":
    unittest.main()
