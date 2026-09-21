import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.coefficients import (  # noqa: E402
    CCCC_COEFFICIENT_TABLE,
    cccc_coefficients,
)


class CcccCoefficientTests(unittest.TestCase):
    def assertClose(self, actual, expected):
        self.assertAlmostEqual(actual, expected, delta=1e-14)

    def test_every_table_knot(self):
        for ratio, expected_w, expected_m in CCCC_COEFFICIENT_TABLE:
            with self.subTest(ratio=ratio):
                result = cccc_coefficients(ratio)
                self.assertEqual(result.aspect_ratio, ratio)
                self.assertClose(result.beta_w, expected_w)
                self.assertClose(result.beta_m, expected_m)

    def test_midpoint_in_every_interval(self):
        for lower, upper in zip(CCCC_COEFFICIENT_TABLE, CCCC_COEFFICIENT_TABLE[1:]):
            ratio = (lower[0] + upper[0]) / 2
            with self.subTest(ratio=ratio):
                result = cccc_coefficients(ratio)
                self.assertClose(result.beta_w, (lower[1] + upper[1]) / 2)
                self.assertClose(result.beta_m, (lower[2] + upper[2]) / 2)

    def test_lower_and_upper_clamps(self):
        lower = cccc_coefficients(0.5)
        upper = cccc_coefficients(10.0)
        self.assertEqual((lower.beta_w, lower.beta_m), (0.0138, 0.0513))
        self.assertEqual((upper.beta_w, upper.beta_m), (0.0291, 0.0547))

    def test_invalid_ratio(self):
        for value in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cccc_coefficients(value)


if __name__ == "__main__":
    unittest.main()

