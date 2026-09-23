import ast
import sys
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.calculations import analyze_cccc  # noqa: E402
from stiffened_plate.models import CcccAnalysisInput, StiffenerOrientation  # noqa: E402
from stiffened_plate.presentation import (  # noqa: E402
    check_rows,
    format_number,
    implemented_checks_pass,
    intermediate_groups,
)
from stiffened_plate.sections import FlatBarSection  # noqa: E402


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = CcccAnalysisInput(
            long_span_in=72.0,
            short_span_in=40.0,
            plate_thickness_in=0.1345,
            stiffener_count=2,
            elastic_modulus_ksi=29_000.0,
            poisson_ratio=0.3,
            yield_strength_ksi=36.0,
            pressure_psf=100.0,
            stiffener_orientation=StiffenerOrientation.LONG_SPAN,
            stiffener=FlatBarSection(2.0, 0.25),
        )

    def test_engineering_number_formatting(self):
        self.assertEqual(format_number(None), "—")
        self.assertEqual(format_number(0.0), "0")
        self.assertEqual(format_number(1.25), "1.25")
        self.assertEqual(format_number(0.000001), "1.000000e-06")
        self.assertEqual(format_number(2_000_000.0), "2.000000e+06")

    def test_check_table_contains_all_status_categories(self):
        rows = check_rows(analyze_cccc(self.inputs))
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[0]["Check"], "Deflection")
        self.assertEqual(rows[0]["Status"], "PASS")
        self.assertIn("NOT IMPLEMENTED", {row["Status"] for row in rows})
        expected_columns = {
            "Check",
            "Status",
            "Demand",
            "Limit",
            "Unit",
            "Utilization",
            "Note",
        }
        self.assertTrue(all(set(row) == expected_columns for row in rows))

    def test_intermediate_tables_include_auditable_groups(self):
        groups = intermediate_groups(analyze_cccc(self.inputs))
        self.assertEqual(
            set(groups),
            {
                "Conversions and plate properties",
                "Panel geometry and CCCC coefficients",
                "Spring stiffness and load sharing",
                "Response",
                "Composite plate–stiffener section",
            },
        )
        quantities = {row["Quantity"] for rows in groups.values() for row in rows}
        self.assertIn("Plate rigidity D", quantities)
        self.assertIn("Composite Ix", quantities)
        self.assertIn("Governing deflection", quantities)

    def test_unstiffened_result_omits_composite_table(self):
        result = analyze_cccc(replace(self.inputs, stiffener_count=0, stiffener=None))
        self.assertNotIn(
            "Composite plate–stiffener section", intermediate_groups(result)
        )

    def test_summary_predicate_detects_failed_implemented_check(self):
        self.assertTrue(implemented_checks_pass(analyze_cccc(self.inputs)))
        failed = analyze_cccc(replace(self.inputs, pressure_psf=1_000_000.0))
        self.assertFalse(implemented_checks_pass(failed))

    def test_streamlit_entrypoint_is_valid_python(self):
        source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(source, filename="app.py")
        self.assertIn("def main()", source)
        self.assertIn("analyze_cccc(inputs)", source)

    def test_streamlit_style_uses_jetbrains_mono_and_square_corners(self):
        source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('font-family: "JetBrains Mono"', source)
        self.assertIn("border-radius: 0 !important", source)
        self.assertIn("font-size: 14px !important", source)
        self.assertIn("font-size: 13px !important", source)
        self.assertIn("font-size: 12px !important", source)
        self.assertIn("_apply_interface_style()", source)


if __name__ == "__main__":
    unittest.main()
