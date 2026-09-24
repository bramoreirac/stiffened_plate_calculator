import sys
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.calculations import analyze_cccc  # noqa: E402
from stiffened_plate.models import CcccAnalysisInput, StiffenerOrientation  # noqa: E402
from stiffened_plate.sections import FlatBarSection  # noqa: E402


class FormulaVerificationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = CcccAnalysisInput(
            long_span_in=60.0,
            short_span_in=30.0,
            plate_thickness_in=0.5,
            stiffener_count=1,
            elastic_modulus_ksi=30_000.0,
            poisson_ratio=0.25,
            yield_strength_ksi=50.0,
            uniform_force_lbf=3_600.0,
            deflection_limit_denominator=300.0,
            stiffener_orientation=StiffenerOrientation.LONG_SPAN,
            stiffener=FlatBarSection(height=2.0, thickness=0.5),
        )

    def assertClose(self, actual, expected, rel_tol=1e-12, abs_tol=1e-14):
        self.assertAlmostEqual(
            actual,
            expected,
            delta=max(abs_tol, rel_tol * max(abs(expected), 1.0)),
        )

    def test_unit_conversions_and_plate_rigidity(self):
        result = analyze_cccc(self.inputs)
        expected_e = 30_000.0 * 1000.0
        expected_area = 60.0 * 30.0
        expected_q = 3_600.0 / expected_area
        expected_d = expected_e * 0.5**3 / (12.0 * (1.0 - 0.25**2))
        self.assertEqual(result.elastic_modulus_psi, expected_e)
        self.assertEqual(result.plate_area_in2, expected_area)
        self.assertEqual(result.pressure_psi, expected_q)
        self.assertClose(result.plate_rigidity_lbf_in, expected_d)

    def test_pressure_varies_with_total_force_and_full_plate_area(self):
        base = analyze_cccc(self.inputs)
        doubled_force = analyze_cccc(
            replace(self.inputs, uniform_force_lbf=7_200.0)
        )
        doubled_area = analyze_cccc(replace(self.inputs, long_span_in=120.0))

        self.assertClose(doubled_force.pressure_psi, 2.0 * base.pressure_psi)
        self.assertClose(doubled_area.plate_area_in2, 2.0 * base.plate_area_in2)
        self.assertClose(doubled_area.pressure_psi, 0.5 * base.pressure_psi)

    def test_long_span_panel_geometry(self):
        result = analyze_cccc(self.inputs)
        self.assertEqual(result.panel.stiffener_span_in, 60.0)
        self.assertEqual(result.panel.spacing_in, 15.0)
        self.assertEqual(result.panel.long_side_in, 60.0)
        self.assertEqual(result.panel.short_side_in, 15.0)
        self.assertEqual(result.panel.aspect_ratio, 4.0)

    def test_short_span_panel_geometry_when_spacing_is_shorter(self):
        inputs = replace(
            self.inputs,
            long_span_in=72.0,
            short_span_in=30.0,
            stiffener_count=3,
            stiffener_orientation=StiffenerOrientation.SHORT_SPAN,
        )
        result = analyze_cccc(inputs)
        self.assertEqual(result.panel.stiffener_span_in, 30.0)
        self.assertEqual(result.panel.spacing_in, 18.0)
        self.assertEqual(result.panel.long_side_in, 30.0)
        self.assertEqual(result.panel.short_side_in, 18.0)
        self.assertClose(result.panel.aspect_ratio, 30.0 / 18.0)

    def test_short_span_panel_geometry_when_spacing_is_longer(self):
        inputs = replace(
            self.inputs,
            long_span_in=72.0,
            short_span_in=20.0,
            stiffener_count=1,
            stiffener_orientation=StiffenerOrientation.SHORT_SPAN,
        )
        result = analyze_cccc(inputs)
        self.assertEqual(result.panel.spacing_in, 36.0)
        self.assertEqual(result.panel.long_side_in, 36.0)
        self.assertEqual(result.panel.short_side_in, 20.0)
        self.assertEqual(result.panel.aspect_ratio, 1.8)

    def test_composite_terms_by_independent_parallel_axis_calculation(self):
        result = analyze_cccc(self.inputs)
        composite = result.composite_section
        assert composite is not None

        plate_area = 15.0 * 0.5
        bar_area = 2.0 * 0.5
        plate_y = 0.25
        bar_y = 0.5 + 1.0
        centroid_y = (plate_area * plate_y + bar_area * bar_y) / (
            plate_area + bar_area
        )
        plate_ix = 15.0 * 0.5**3 / 12.0 + plate_area * (centroid_y - plate_y) ** 2
        bar_ix = 0.5 * 2.0**3 / 12.0 + bar_area * (bar_y - centroid_y) ** 2

        self.assertEqual(composite.plate_area_in2, plate_area)
        self.assertEqual(composite.stiffener_area_in2, bar_area)
        self.assertClose(composite.centroid_y_in, centroid_y)
        self.assertClose(composite.plate_inertia_in4, plate_ix)
        self.assertClose(composite.stiffener_inertia_in4, bar_ix)
        self.assertClose(composite.inertia_x_in4, plate_ix + bar_ix)
        self.assertClose(composite.bottom_fibre_distance_in, 2.5 - centroid_y)
        self.assertClose(
            composite.elastic_section_modulus_bottom_in3,
            composite.inertia_x_in4 / composite.bottom_fibre_distance_in,
        )

    def test_spring_stiffness_and_load_sharing_equations(self):
        result = analyze_cccc(self.inputs)
        composite = result.composite_section
        assert composite is not None

        expected_ks = (
            self.inputs.stiffener_count
            * 192.0
            * composite.flexural_rigidity_lbf_in2
            / result.panel.stiffener_span_in**3
        )
        expected_kp = (
            384.0
            * result.plate_rigidity_lbf_in
            * result.panel.stiffener_span_in
            / (5.0 * result.panel.spacing_in**4)
        )
        expected_alpha_s = expected_ks / (expected_ks + expected_kp)
        expected_alpha_p = 1.0 - expected_alpha_s

        loads = result.load_sharing
        self.assertClose(loads.stiffener_spring_stiffness_lbf_per_in, expected_ks)
        self.assertClose(loads.plate_spring_stiffness_lbf_per_in, expected_kp)
        self.assertClose(loads.stiffener_load_fraction, expected_alpha_s)
        self.assertClose(loads.plate_load_fraction, expected_alpha_p)
        self.assertClose(
            loads.effective_plate_pressure_psi,
            expected_alpha_p * result.pressure_psi,
        )
        self.assertClose(
            loads.tributary_stiffener_load_lbf,
            result.pressure_psi
            * result.panel.spacing_in
            * result.panel.stiffener_span_in,
        )

    def test_plate_and_stiffener_response_equations(self):
        result = analyze_cccc(self.inputs)
        composite = result.composite_section
        assert composite is not None
        loads = result.load_sharing
        panel = result.panel
        coefficients = result.panel_coefficients

        expected_plate_deflection = (
            coefficients.beta_w
            * loads.effective_plate_pressure_psi
            * panel.short_side_in**4
            / result.plate_rigidity_lbf_in
        )
        expected_plate_moment = (
            coefficients.beta_m
            * loads.effective_plate_pressure_psi
            * panel.short_side_in**2
        )
        expected_plate_stress = (
            6.0 * expected_plate_moment / self.inputs.plate_thickness_in**2 / 1000.0
        )
        expected_stiffener_deflection = (
            loads.tributary_stiffener_load_lbf
            * panel.stiffener_span_in**3
            / (192.0 * composite.flexural_rigidity_lbf_in2)
        )
        expected_stiffener_moment = (
            loads.tributary_stiffener_load_lbf * panel.stiffener_span_in / 8.0
        )
        expected_stiffener_stress = (
            expected_stiffener_moment
            * composite.bottom_fibre_distance_in
            / composite.inertia_x_in4
            / 1000.0
        )

        response = result.response
        self.assertClose(response.plate_deflection_in, expected_plate_deflection)
        self.assertClose(response.plate_moment_lbf_in_per_in, expected_plate_moment)
        self.assertClose(response.plate_stress_ksi, expected_plate_stress)
        self.assertClose(response.stiffener_deflection_in, expected_stiffener_deflection)
        self.assertClose(response.stiffener_moment_lbf_in, expected_stiffener_moment)
        self.assertClose(response.stiffener_stress_ksi, expected_stiffener_stress)
        self.assertEqual(
            response.maximum_deflection_in,
            max(expected_plate_deflection, expected_stiffener_deflection),
        )
        self.assertEqual(
            response.allowable_deflection_in,
            self.inputs.short_span_in / self.inputs.deflection_limit_denominator,
        )

    def test_response_is_linear_with_total_force(self):
        base = analyze_cccc(self.inputs)
        doubled = analyze_cccc(replace(self.inputs, uniform_force_lbf=7_200.0))
        for base_value, doubled_value in (
            (base.response.plate_deflection_in, doubled.response.plate_deflection_in),
            (
                base.response.stiffener_deflection_in,
                doubled.response.stiffener_deflection_in,
            ),
            (base.response.plate_stress_ksi, doubled.response.plate_stress_ksi),
            (
                base.response.stiffener_stress_ksi,
                doubled.response.stiffener_stress_ksi,
            ),
        ):
            self.assertClose(doubled_value, 2.0 * base_value)


if __name__ == "__main__":
    unittest.main()
