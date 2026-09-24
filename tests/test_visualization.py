import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.models import StiffenerOrientation  # noqa: E402
from stiffened_plate.visualization import (  # noqa: E402
    CENTROID_LINE_COLOR,
    front_view_figure,
    front_view_geometry,
    side_view_figure,
    side_view_geometry,
    side_view_plate_strip_width,
)
from stiffened_plate.sections import (  # noqa: E402
    AngleSection,
    ChannelAttachment,
    ChannelSection,
    FlatBarSection,
    Handedness,
    RectangularHollowSection,
    RhsAttachment,
    TeeAttachment,
    TeeSection,
    calculate_properties,
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


class SideViewGeometryTests(unittest.TestCase):
    def test_displayed_plate_strip_is_section_width_plus_four_inches(self):
        section = RectangularHollowSection(2.0, 3.0, 0.25)
        self.assertEqual(side_view_plate_strip_width(section), 6.0)
        self.assertEqual(side_view_plate_strip_width(None), 4.0)

    def test_flat_bar_uses_plate_interface_as_zero_elevation(self):
        geometry = side_view_geometry(12.0, 0.25, FlatBarSection(2.0, 0.5))
        components = {component.label: component for component in geometry.rectangles}
        self.assertEqual(components["effective_plate"].y, -0.25)
        self.assertEqual(components["effective_plate"].y_max, 0.0)
        self.assertEqual(components["flat_bar"].y, 0.0)
        self.assertEqual(components["flat_bar"].y_max, 2.0)
        self.assertEqual(geometry.stiffener_width_in, 0.5)
        self.assertEqual(geometry.stiffener_depth_in, 2.0)
        self.assertEqual(geometry.stiffener_centroid_x_in, 0.0)
        self.assertEqual(geometry.stiffener_centroid_y_in, 1.0)

    def test_angle_profile_is_centered_on_its_calculated_centroid(self):
        right_section = AngleSection(2.0, 2.5, 0.25, Handedness.RIGHT)
        left_section = AngleSection(2.0, 2.5, 0.25, Handedness.LEFT)
        right = side_view_geometry(6.0, 0.25, right_section)
        left = side_view_geometry(6.0, 0.25, left_section)

        for geometry, section in ((right, right_section), (left, left_section)):
            displayed_stiffener = tuple(
                component
                for component in geometry.rectangles
                if component.label != "effective_plate"
            )
            displayed_properties = calculate_properties(displayed_stiffener)
            bare_properties = section.geometry().properties
            self.assertAlmostEqual(displayed_properties.centroid_x, 0.0)
            self.assertAlmostEqual(
                displayed_properties.centroid_y,
                bare_properties.centroid_y,
            )
            self.assertEqual(geometry.stiffener_centroid_x_in, 0.0)
            self.assertAlmostEqual(
                geometry.stiffener_centroid_y_in,
                bare_properties.centroid_y,
            )

        right_components = {
            component.label: component
            for component in right.rectangles
            if component.label != "effective_plate"
        }
        left_components = {
            component.label: component
            for component in left.rectangles
            if component.label != "effective_plate"
        }
        for label, right_component in right_components.items():
            left_component = left_components[label]
            self.assertAlmostEqual(left_component.x, -right_component.x_max)
            self.assertEqual(left_component.y, right_component.y)

    def test_every_documented_section_scenario_projects_above_plate(self):
        sections = (
            AngleSection(2.0, 2.5, 0.25, Handedness.RIGHT),
            AngleSection(2.0, 2.5, 0.25, Handedness.LEFT),
            TeeSection(3.0, 0.25, 2.0, 0.25, TeeAttachment.WEB_END),
            TeeSection(3.0, 0.25, 2.0, 0.25, TeeAttachment.FLANGE_FACE),
            RectangularHollowSection(2.0, 3.0, 0.25, RhsAttachment.SIDE_A),
            RectangularHollowSection(2.0, 3.0, 0.25, RhsAttachment.SIDE_B),
            ChannelSection(3.0, 2.0, 0.25, 0.25, ChannelAttachment.WEB_FACE),
            ChannelSection(3.0, 2.0, 0.25, 0.25, ChannelAttachment.FLANGE_FACE),
        )
        for section in sections:
            with self.subTest(section=section):
                geometry = side_view_geometry(10.0, 0.25, section)
                stiffener_components = tuple(
                    component
                    for component in geometry.rectangles
                    if component.label != "effective_plate"
                )
                self.assertTrue(stiffener_components)
                self.assertTrue(all(component.y >= 0.0 for component in stiffener_components))
                self.assertAlmostEqual(
                    max(component.y_max for component in stiffener_components),
                    geometry.stiffener_depth_in,
                )

    def test_channel_attachment_geometry_matches_approved_samples(self):
        web_face = side_view_geometry(
            10.0,
            0.25,
            ChannelSection(4.0, 2.5, 0.5, 0.5, ChannelAttachment.WEB_FACE),
        )
        flange_face = side_view_geometry(
            10.0,
            0.25,
            ChannelSection(4.0, 2.5, 0.5, 0.5, ChannelAttachment.FLANGE_FACE),
        )
        web_components = {
            component.label: component for component in web_face.rectangles
        }
        flange_components = {
            component.label: component for component in flange_face.rectangles
        }
        self.assertEqual(web_components["attached_web"].y, 0.0)
        self.assertEqual(web_components["left_flange"].y, 0.5)
        self.assertEqual(flange_components["left_flange"].y, 0.0)
        self.assertEqual(flange_components["right_flange"].y, 0.0)
        self.assertEqual(flange_components["web"].y, 2.0)

    def test_unstiffened_side_view_contains_plate_only(self):
        geometry = side_view_geometry(12.0, 0.25, None)
        self.assertIsNone(geometry.shape)
        self.assertIsNone(geometry.attachment)
        self.assertEqual(len(geometry.rectangles), 1)
        self.assertEqual(geometry.rectangles[0].label, "effective_plate")


@unittest.skipUnless(importlib.util.find_spec("plotly"), "Plotly is not installed")
class FrontViewFigureTests(unittest.TestCase):
    def test_figure_contains_plate_stiffeners_dimensions_and_equal_axes(self):
        figure = front_view_figure(
            72.0, 40.0, 2, StiffenerOrientation.LONG_SPAN
        )
        self.assertEqual(len(figure.data), 2)
        self.assertEqual(figure.data[0].name, "Plate boundary")
        self.assertEqual(figure.data[1].name, "Stiffener centroid lines")
        self.assertEqual(figure.data[1].line.color, CENTROID_LINE_COLOR)
        annotations = " ".join(annotation.text for annotation in figure.layout.annotations)
        self.assertIn("Long span a = 72 in", annotations)
        self.assertIn("Short span b = 40 in", annotations)
        self.assertIn("2 stiffeners", annotations)
        self.assertEqual(figure.layout.yaxis.scaleanchor, "x")
        self.assertEqual(figure.layout.yaxis.scaleratio, 1)

    def test_side_figure_uses_section_components_and_equal_axes(self):
        section = RectangularHollowSection(2.0, 3.0, 0.25)
        geometry = side_view_geometry(12.0, 0.25, section)
        figure = side_view_figure(12.0, 0.25, section)
        self.assertEqual(len(figure.data), len(geometry.rectangles))
        annotations = " ".join(annotation.text for annotation in figure.layout.annotations)
        self.assertIn("Plate t = 0.25 in", annotations)
        self.assertIn("Section width = 2 in", annotations)
        self.assertIn("Section depth = 3 in", annotations)
        self.assertIn("C<sub>s</sub>", annotations)
        centroid_shapes = tuple(
            shape
            for shape in figure.layout.shapes
            if shape.line.color == CENTROID_LINE_COLOR
        )
        self.assertEqual(len(centroid_shapes), 3)
        self.assertEqual(figure.layout.title.text, "RHS | side a attachment")
        self.assertEqual(figure.layout.title.x, 0.5)
        self.assertEqual(figure.layout.title.xanchor, "center")
        self.assertEqual(figure.layout.yaxis.scaleanchor, "x")
        self.assertEqual(figure.layout.yaxis.scaleratio, 1)


if __name__ == "__main__":
    unittest.main()
