import sys
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.calculations import (  # noqa: E402
    InputValidationError,
    analyze_cccc,
)
from stiffened_plate.models import CcccAnalysisInput, StiffenerOrientation  # noqa: E402
from stiffened_plate.sections import FlatBarSection  # noqa: E402


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid = CcccAnalysisInput(
            long_span_in=72.0,
            short_span_in=40.0,
            plate_thickness_in=0.25,
            stiffener_count=2,
            elastic_modulus_ksi=29_000.0,
            poisson_ratio=0.3,
            yield_strength_ksi=36.0,
            pressure_psf=100.0,
            stiffener_orientation=StiffenerOrientation.LONG_SPAN,
            stiffener=FlatBarSection(2.0, 0.25),
        )

    def test_invalid_scalar_inputs(self):
        invalid_changes = (
            {"long_span_in": 0.0},
            {"short_span_in": -1.0},
            {"plate_thickness_in": 0.0},
            {"elastic_modulus_ksi": float("nan")},
            {"yield_strength_ksi": 0.0},
            {"pressure_psf": -0.01},
            {"poisson_ratio": 0.5},
            {"poisson_ratio": -1.0},
            {"deflection_limit_denominator": 0.0},
        )
        for changes in invalid_changes:
            with self.subTest(changes=changes), self.assertRaises(InputValidationError):
                analyze_cccc(replace(self.valid, **changes))

    def test_long_span_must_not_be_shorter(self):
        with self.assertRaisesRegex(InputValidationError, "long span"):
            analyze_cccc(replace(self.valid, long_span_in=30.0, short_span_in=40.0))

    def test_stiffener_count_rules(self):
        for value in (-1, 1.5, True):
            with self.subTest(value=value), self.assertRaises(InputValidationError):
                analyze_cccc(replace(self.valid, stiffener_count=value))

        with self.assertRaisesRegex(InputValidationError, "stiffener section"):
            analyze_cccc(replace(self.valid, stiffener=None))

    def test_invalid_section_is_wrapped_as_input_error(self):
        with self.assertRaisesRegex(InputValidationError, "invalid stiffener section"):
            analyze_cccc(replace(self.valid, stiffener=FlatBarSection(0.0, 0.25)))


if __name__ == "__main__":
    unittest.main()

