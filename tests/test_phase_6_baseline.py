import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.calculations import analyze_cccc  # noqa: E402
from stiffened_plate.models import (  # noqa: E402
    CalculationModel,
    CheckStatus,
    CcccAnalysisInput,
    StiffenerOrientation,
)
from stiffened_plate.sections import FlatBarSection  # noqa: E402


class Phase6BaselineTests(unittest.TestCase):
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
            stiffener_orientation=StiffenerOrientation.LONG_SPAN,
            stiffener=FlatBarSection(2.0, 0.25),
        )

    def test_reviewed_baseline_uses_versioned_total_force_model(self):
        result = analyze_cccc(self.inputs)
        self.assertIs(result.inputs.calculation_model, CalculationModel.TOTAL_FORCE_V2)
        self.assertAlmostEqual(
            result.pressure_psi,
            self.inputs.uniform_force_lbf
            / (self.inputs.long_span_in * self.inputs.short_span_in),
        )

    def test_golden_cases_record_both_reviewed_workbooks(self):
        golden = json.loads(
            (PROJECT_ROOT / "reference" / "cccc_golden_cases.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(golden["metadata"]["calculation_model"], "total_force_v2")
        self.assertEqual(
            {case["source_workbook"] for case in golden["cases"]},
            {
                "CCCC_stiffened_plate_along_long_span.xlsx",
                "CCCC_stiffened_plate_along_short_span.xlsx",
            },
        )
        for case in golden["cases"]:
            inputs = case["inputs"]
            self.assertAlmostEqual(
                inputs["uniform_force_lbf"]
                / (inputs["long_span_in"] * inputs["short_span_in"]),
                case["expected"]["pressure_psi"],
            )

    def test_incomplete_limit_states_cannot_report_pass(self):
        checks = analyze_cccc(self.inputs).checks
        self.assertIs(checks.plate_stability.status, CheckStatus.NOT_IMPLEMENTED)
        self.assertIs(checks.stiffener_stability.status, CheckStatus.NOT_IMPLEMENTED)
        self.assertIs(checks.connection.status, CheckStatus.NOT_IMPLEMENTED)
        self.assertIs(checks.combined_stress.status, CheckStatus.NOT_IMPLEMENTED)

    def test_baseline_assumptions_expose_parity_idealizations(self):
        assumptions = " ".join(analyze_cccc(self.inputs).assumptions)
        for required_text in (
            "distributed uniformly over the full plate area",
            "full stiffener spacing",
            "full tributary pressure",
            "fixed-fixed center point load",
            "larger, not the sum",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, assumptions)


if __name__ == "__main__":
    unittest.main()
