import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.models import StiffenerOrientation  # noqa: E402
from stiffened_plate.visualization import (  # noqa: E402
    front_view_figure,
    front_view_geometry,
)


class FrontViewGeometryTests(unittest.TestCase):
    def test_long_span_stiffeners_are_horizontal_and_equally_spaced(self):
        geometry = front_view_geometry(
            72.0, 40.0, 2, StiffenerOrientation.LONG_SPAN
        )
        self.assertAlmostEqual(geometry.spacing_in, 40.0 / 3.0)
        self.assertEqual(len(geometry.stiffeners), 2)
        for index, line in enumerate(geometry.stiffeners, start=1):
            self.assertEqual((line.x0, line.x1), (0.0, 72.0))
            self.assertEqual(line.y0, line.y1)
            self.assertAlmostEqual(line.y0, index * 40.0 / 3.0)

    def test_short_span_stiffeners_are_vertical_and_equally_spaced(self):
        geometry = front_view_geometry(
            72.0, 40.0, 2, StiffenerOrientation.SHORT_SPAN
        )
        self.assertEqual(geometry.spacing_in, 24.0)
        self.assertEqual(len(geometry.stiffeners), 2)
        for index, line in enumerate(geometry.stiffeners, start=1):
            self.assertEqual((line.y0, line.y1), (0.0, 40.0))
            self.assertEqual(line.x0, line.x1)
            self.assertEqual(line.x0, index * 24.0)

    def test_zero_stiffeners_retains_full_plate_geometry(self):
        geometry = front_view_geometry(
            60.0, 30.0, 0, StiffenerOrientation.LONG_SPAN
        )
        self.assertEqual(geometry.spacing_in, 30.0)
        self.assertEqual(geometry.stiffeners, ())

    def test_invalid_geometry_is_rejected(self):
        invalid_cases = (
            (0.0, 40.0, 2, StiffenerOrientation.LONG_SPAN),
            (72.0, -1.0, 2, StiffenerOrientation.LONG_SPAN),
            (72.0, 40.0, -1, StiffenerOrientation.LONG_SPAN),
            (72.0, 40.0, 1.5, StiffenerOrientation.LONG_SPAN),
            (72.0, 40.0, 2, "diagonal"),
        )
        for case in invalid_cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                front_view_geometry(*case)


@unittest.skipUnless(importlib.util.find_spec("plotly"), "Plotly is not installed")
class FrontViewFigureTests(unittest.TestCase):
    def test_figure_contains_plate_stiffeners_dimensions_and_equal_axes(self):
        figure = front_view_figure(
            72.0, 40.0, 2, StiffenerOrientation.LONG_SPAN
        )
        self.assertEqual(len(figure.data), 2)
        self.assertEqual(figure.data[0].name, "Plate boundary")
        self.assertEqual(figure.data[1].name, "Stiffener centerlines")
        annotations = " ".join(annotation.text for annotation in figure.layout.annotations)
        self.assertIn("Long span a = 72 in", annotations)
        self.assertIn("Short span b = 40 in", annotations)
        self.assertIn("2 stiffeners", annotations)
        self.assertEqual(figure.layout.yaxis.scaleanchor, "x")
        self.assertEqual(figure.layout.yaxis.scaleratio, 1)


if __name__ == "__main__":
    unittest.main()

