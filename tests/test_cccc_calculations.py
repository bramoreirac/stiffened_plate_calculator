import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.calculations import analyze_cccc  # noqa: E402
from stiffened_plate.models import (  # noqa: E402
    CheckStatus,
    CcccAnalysisInput,
    StiffenerOrientation,
)
from stiffened_plate.sections import (  # noqa: E402
    AngleSection,
    ChannelSection,
    FlatBarSection,
    RectangularHollowSection,
    TeeSection,
)


class CcccCalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        golden_path = PROJECT_ROOT / "reference" / "cccc_golden_cases.json"
        cls.golden = json.loads(golden_path.read_text(encoding="utf-8"))

    def assertClose(self, actual, expected):
        metadata = self.golden["metadata"]
        tolerance = max(
            metadata["absolute_tolerance"],
            metadata["relative_tolerance"] * max(abs(expected), 1.0),
        )
        self.assertAlmostEqual(actual, expected, delta=tolerance)

    def test_both_workbook_golden_cases(self):
        for case in self.golden["cases"]:
            with self.subTest(case=case["id"]):
                source = case["inputs"]
                section = case["section"]
                result = analyze_cccc(
                    CcccAnalysisInput(
                        long_span_in=source["long_span_in"],
                        short_span_in=source["short_span_in"],
                        plate_thickness_in=source["plate_thickness_in"],
                        stiffener_count=source["stiffener_count"],
                        elastic_modulus_ksi=source["elastic_modulus_ksi"],
                        poisson_ratio=source["poisson_ratio"],
                        yield_strength_ksi=source["yield_strength_ksi"],
                        pressure_psf=source["pressure_psf"],
                        deflection_limit_denominator=source[
                            "deflection_limit_denominator"
                        ],
                        stiffener_orientation=StiffenerOrientation(case["orientation"]),
                        stiffener=FlatBarSection(
                            height=section["height_in"],
                            thickness=section["thickness_in"],
                        ),
                    )
                )
                expected = case["expected"]
                composite = result.composite_section
                self.assertIsNotNone(composite)
                assert composite is not None

                actual_values = {
                    "elastic_modulus_psi": result.elastic_modulus_psi,
                    "pressure_psi": result.pressure_psi,
                    "overall_aspect_ratio": result.overall_coefficients.aspect_ratio,
                    "panel_spacing_in": result.panel.spacing_in,
                    "panel_long_side_in": result.panel.long_side_in,
                    "panel_short_side_in": result.panel.short_side_in,
                    "plate_rigidity_lbf_in": result.plate_rigidity_lbf_in,
                    "overall_beta_w": result.overall_coefficients.beta_w,
                    "overall_beta_m": result.overall_coefficients.beta_m,
                    "panel_aspect_ratio": result.panel.aspect_ratio,
                    "panel_beta_w": result.panel_coefficients.beta_w,
                    "panel_beta_m": result.panel_coefficients.beta_m,
                    "plate_flange_area_in2": composite.plate_area_in2,
                    "stiffener_area_in2": composite.stiffener_area_in2,
                    "plate_flange_centroid_in": composite.plate_centroid_in,
                    "stiffener_centroid_in": composite.stiffener_centroid_in,
                    "composite_centroid_in": composite.centroid_y_in,
                    "plate_flange_inertia_in4": composite.plate_inertia_in4,
                    "stiffener_inertia_in4": composite.stiffener_inertia_in4,
                    "composite_inertia_in4": composite.inertia_x_in4,
                    "composite_EI_lbf_in2": composite.flexural_rigidity_lbf_in2,
                    "bottom_fibre_distance_in": composite.bottom_fibre_distance_in,
                    "stiffener_spring_stiffness_lbf_per_in": (
                        result.load_sharing.stiffener_spring_stiffness_lbf_per_in
                    ),
                    "plate_spring_stiffness_lbf_per_in": (
                        result.load_sharing.plate_spring_stiffness_lbf_per_in
                    ),
                    "stiffener_load_fraction": (
                        result.load_sharing.stiffener_load_fraction
                    ),
                    "plate_load_fraction": result.load_sharing.plate_load_fraction,
                    "effective_plate_pressure_psi": (
                        result.load_sharing.effective_plate_pressure_psi
                    ),
                    "plate_deflection_in": result.response.plate_deflection_in,
                    "stiffener_deflection_in": result.response.stiffener_deflection_in,
                    "maximum_deflection_in": result.response.maximum_deflection_in,
                    "allowable_deflection_in": result.response.allowable_deflection_in,
                    "plate_moment_lbf_in_per_in": (
                        result.response.plate_moment_lbf_in_per_in
                    ),
                    "plate_stress_ksi": result.response.plate_stress_ksi,
                    "stiffener_moment_lbf_in": (
                        result.response.stiffener_moment_lbf_in
                    ),
                    "stiffener_stress_ksi": result.response.stiffener_stress_ksi,
                }
                boolean_keys = {
                    "deflection_pass",
                    "plate_yield_pass",
                    "stiffener_yield_pass",
                }
                self.assertTrue(set(expected).issubset(set(actual_values) | boolean_keys))
                for key, expected_value in expected.items():
                    if key in actual_values:
                        self.assertClose(actual_values[key], expected_value)

                self.assertEqual(
                    result.checks.deflection.status is CheckStatus.PASS,
                    expected["deflection_pass"],
                )
                self.assertEqual(
                    result.checks.plate_yield.status is CheckStatus.PASS,
                    expected["plate_yield_pass"],
                )
                self.assertEqual(
                    result.checks.stiffener_yield.status is CheckStatus.PASS,
                    expected["stiffener_yield_pass"],
                )
                self.assertEqual(
                    result.checks.stiffener_stability.status,
                    CheckStatus.NOT_IMPLEMENTED,
                )
                self.assertEqual(
                    result.checks.connection.status,
                    CheckStatus.NOT_IMPLEMENTED,
                )

    def test_unstiffened_plate_is_supported_explicitly(self):
        result = analyze_cccc(
            CcccAnalysisInput(
                long_span_in=60.0,
                short_span_in=40.0,
                plate_thickness_in=0.25,
                stiffener_count=0,
                elastic_modulus_ksi=29_000.0,
                poisson_ratio=0.3,
                yield_strength_ksi=36.0,
                pressure_psf=50.0,
                stiffener_orientation=StiffenerOrientation.LONG_SPAN,
            )
        )
        self.assertIsNone(result.composite_section)
        self.assertEqual(result.panel.spacing_in, 40.0)
        self.assertEqual(result.panel.short_side_in, 40.0)
        self.assertEqual(result.load_sharing.stiffener_load_fraction, 0.0)
        self.assertEqual(result.load_sharing.plate_load_fraction, 1.0)
        self.assertEqual(result.response.stiffener_deflection_in, 0.0)
        self.assertEqual(
            result.checks.stiffener_yield.status, CheckStatus.NOT_APPLICABLE
        )
        self.assertEqual(
            result.checks.stiffener_stability.status, CheckStatus.NOT_APPLICABLE
        )

    def test_engine_accepts_every_phase_2_section_family(self):
        sections = (
            FlatBarSection(2.0, 0.25),
            AngleSection(2.0, 2.5, 0.25),
            TeeSection(3.0, 0.25, 2.0, 0.25),
            RectangularHollowSection(2.0, 3.0, 0.25),
            ChannelSection(3.0, 2.0, 0.25, 0.25),
        )
        for section in sections:
            with self.subTest(section=type(section).__name__):
                result = analyze_cccc(
                    CcccAnalysisInput(
                        long_span_in=72.0,
                        short_span_in=40.0,
                        plate_thickness_in=0.25,
                        stiffener_count=2,
                        elastic_modulus_ksi=29_000.0,
                        poisson_ratio=0.3,
                        yield_strength_ksi=36.0,
                        pressure_psf=100.0,
                        stiffener_orientation=StiffenerOrientation.LONG_SPAN,
                        stiffener=section,
                    )
                )
                self.assertIsNotNone(result.composite_section)
                self.assertGreater(result.response.stiffener_deflection_in, 0.0)
                self.assertEqual(
                    result.checks.stiffener_stability.status,
                    CheckStatus.NOT_IMPLEMENTED,
                )


if __name__ == "__main__":
    unittest.main()
