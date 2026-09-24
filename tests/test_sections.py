import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stiffened_plate.sections import (  # noqa: E402
    AngleSection,
    ChannelAttachment,
    ChannelSection,
    CompositeSection,
    FlatBarSection,
    Handedness,
    RectangularHollowSection,
    RhsAttachment,
    TeeAttachment,
    TeeSection,
)


class SectionTestCase(unittest.TestCase):
    def assertClose(self, actual, expected, *, rel_tol=1e-10, abs_tol=1e-12):
        self.assertAlmostEqual(
            actual,
            expected,
            delta=max(abs_tol, rel_tol * max(abs(expected), 1.0)),
        )


class FlatBarTests(SectionTestCase):
    def test_bare_flat_bar(self):
        props = FlatBarSection(height=4.0, thickness=0.5).geometry().properties
        self.assertClose(props.area, 2.0)
        self.assertClose(props.centroid_x, 0.0)
        self.assertClose(props.centroid_y, 2.0)
        self.assertClose(props.ix, 0.5 * 4.0**3 / 12)
        self.assertClose(props.iy, 4.0 * 0.5**3 / 12)
        self.assertClose(props.sx_top, props.ix / 2.0)
        self.assertClose(props.sx_bottom, props.ix / 2.0)

    def test_composite_flat_bar_matches_both_workbooks(self):
        golden_path = PROJECT_ROOT / "reference" / "cccc_golden_cases.json"
        cases = json.loads(golden_path.read_text(encoding="utf-8"))["cases"]

        for case in cases:
            with self.subTest(case=case["id"]):
                section = FlatBarSection(
                    height=case["section"]["height_in"],
                    thickness=case["section"]["thickness_in"],
                )
                props = CompositeSection(
                    plate_width=case["expected"]["panel_spacing_in"],
                    plate_thickness=case["inputs"]["plate_thickness_in"],
                    stiffener=section,
                ).geometry().properties

                expected = case["expected"]
                self.assertClose(props.area, expected["plate_flange_area_in2"] + expected["stiffener_area_in2"])
                self.assertClose(props.centroid_y, expected["composite_centroid_in"])
                self.assertClose(props.ix, expected["composite_inertia_in4"])
                self.assertClose(props.c_bottom, expected["bottom_fibre_distance_in"])


class AngleTests(SectionTestCase):
    def test_angle_area_centroid_and_handedness(self):
        right = AngleSection(3.0, 4.0, 0.5, Handedness.RIGHT).geometry().properties
        left = AngleSection(3.0, 4.0, 0.5, Handedness.LEFT).geometry().properties

        expected_area = 3.0 * 0.5 + (4.0 - 0.5) * 0.5
        expected_y = (1.5 * 0.25 + 1.75 * 2.25) / expected_area
        self.assertClose(right.area, expected_area)
        self.assertClose(right.centroid_x, 0.5769230769230769)
        self.assertClose(right.centroid_y, expected_y)
        self.assertClose(right.ix, 5.048477564102564)
        self.assertClose(right.iy, 2.423477564102564)
        self.assertClose(right.ixy, -2.019230769230769)
        self.assertClose(left.centroid_y, expected_y)
        self.assertClose(left.centroid_x, -right.centroid_x)
        self.assertClose(left.ix, right.ix)
        self.assertClose(left.iy, right.iy)
        self.assertClose(left.ixy, -right.ixy)

    def test_composite_angle_is_aligned_on_bare_stiffener_centroid(self):
        right_section = AngleSection(3.0, 4.0, 0.5, Handedness.RIGHT)
        left_section = AngleSection(3.0, 4.0, 0.5, Handedness.LEFT)
        right = CompositeSection(12.0, 0.25, right_section).geometry().properties
        left = CompositeSection(12.0, 0.25, left_section).geometry().properties

        self.assertClose(right.centroid_x, 0.0)
        self.assertClose(left.centroid_x, 0.0)
        self.assertClose(right.centroid_y, left.centroid_y)
        self.assertClose(right.ix, left.ix)
        self.assertClose(right.iy, left.iy)
        self.assertClose(right.ixy, -left.ixy)


class TeeTests(SectionTestCase):
    def test_tee_properties_and_attachment_flip(self):
        web_end = TeeSection(4.0, 0.5, 3.0, 0.5, TeeAttachment.WEB_END).geometry().properties
        flange_face = TeeSection(4.0, 0.5, 3.0, 0.5, TeeAttachment.FLANGE_FACE).geometry().properties

        web_area = 0.5 * 3.5
        flange_area = 3.0 * 0.5
        expected_area = web_area + flange_area
        expected_y = (web_area * 1.75 + flange_area * 3.75) / expected_area
        self.assertClose(web_end.area, expected_area)
        self.assertClose(web_end.centroid_y, expected_y)
        self.assertClose(web_end.ix, 5.048477564102564)
        self.assertClose(web_end.iy, 1.1614583333333333)
        self.assertClose(flange_face.centroid_y, 4.0 - expected_y)
        self.assertClose(flange_face.ix, web_end.ix)
        self.assertClose(flange_face.iy, web_end.iy)
        self.assertClose(web_end.centroid_x, 0.0)
        self.assertClose(web_end.ixy, 0.0)


class RhsTests(SectionTestCase):
    def test_rhs_matches_outer_minus_inner_rectangle(self):
        props = RectangularHollowSection(3.0, 4.0, 0.25).geometry().properties
        expected_area = 3.0 * 4.0 - 2.5 * 3.5
        expected_ix = (3.0 * 4.0**3 - 2.5 * 3.5**3) / 12
        expected_iy = (4.0 * 3.0**3 - 3.5 * 2.5**3) / 12
        self.assertClose(props.area, expected_area)
        self.assertClose(props.centroid_x, 0.0)
        self.assertClose(props.centroid_y, 2.0)
        self.assertClose(props.ix, expected_ix)
        self.assertClose(props.iy, expected_iy)

    def test_rhs_attachment_rotates_section(self):
        side_a = RectangularHollowSection(3.0, 4.0, 0.25, RhsAttachment.SIDE_A).geometry().properties
        side_b = RectangularHollowSection(3.0, 4.0, 0.25, RhsAttachment.SIDE_B).geometry().properties
        self.assertClose(side_a.depth, 4.0)
        self.assertClose(side_b.depth, 3.0)
        self.assertClose(side_a.ix, side_b.iy)
        self.assertClose(side_a.iy, side_b.ix)

    def test_equal_sides_are_identified_as_shs(self):
        geometry = RectangularHollowSection(3.0, 3.0, 0.25).geometry()
        self.assertEqual(geometry.shape, "shs")


class ChannelTests(SectionTestCase):
    def test_flange_face_channel_has_both_flange_ends_at_plate(self):
        geometry = ChannelSection(
            4.0, 2.5, 0.5, 0.5, ChannelAttachment.FLANGE_FACE
        ).geometry()
        props = geometry.properties
        components = {component.label: component for component in geometry.components}

        expected_area = 4.0 * 0.5 + 2 * 0.5 * 2.0
        self.assertEqual(geometry.attachment, "flange_face")
        self.assertEqual(components["left_flange"].y, 0.0)
        self.assertEqual(components["right_flange"].y, 0.0)
        self.assertEqual(components["web"].y, 2.0)
        self.assertClose(props.area, expected_area)
        self.assertClose(props.centroid_x, 0.0)
        self.assertClose(props.centroid_y, 1.625)
        self.assertClose(props.ix, 2.270833333333333)
        self.assertClose(props.iy, 8.833333333333334)
        self.assertClose(props.ixy, 0.0)

    def test_web_face_channel_is_symmetric(self):
        props = ChannelSection(
            4.0, 2.5, 0.5, 0.5, ChannelAttachment.WEB_FACE
        ).geometry().properties
        expected_area = 4.0 * 0.5 + 2 * 0.5 * 2.0
        self.assertClose(props.area, expected_area)
        self.assertClose(props.centroid_x, 0.0)
        self.assertClose(props.centroid_y, 0.875)
        self.assertClose(props.ix, 2.270833333333333)
        self.assertClose(props.iy, 8.833333333333334)
        self.assertClose(props.ixy, 0.0)
        self.assertClose(props.width, 4.0)
        self.assertClose(props.depth, 2.5)

    def test_channel_attachment_flip_preserves_centroidal_inertias(self):
        flange_face = ChannelSection(
            4.0, 2.5, 0.5, 0.5, ChannelAttachment.FLANGE_FACE
        ).geometry().properties
        web_face = ChannelSection(
            4.0, 2.5, 0.5, 0.5, ChannelAttachment.WEB_FACE
        ).geometry().properties
        self.assertClose(flange_face.centroid_y + web_face.centroid_y, 2.5)
        self.assertClose(flange_face.ix, web_face.ix)
        self.assertClose(flange_face.iy, web_face.iy)


class ValidationTests(unittest.TestCase):
    def test_invalid_dimensions_raise_clear_errors(self):
        invalid_sections = (
            FlatBarSection(0.0, 0.25),
            AngleSection(0.5, 4.0, 0.5),
            TeeSection(0.5, 0.25, 2.0, 0.5),
            RectangularHollowSection(1.0, 1.0, 0.5),
            ChannelSection(1.0, 2.0, 0.25, 0.5),
        )
        for section in invalid_sections:
            with self.subTest(section=section), self.assertRaises(ValueError):
                section.geometry()

    def test_invalid_composite_plate_dimensions(self):
        with self.assertRaises(ValueError):
            CompositeSection(0.0, 0.25, FlatBarSection(2.0, 0.25)).geometry()


if __name__ == "__main__":
    unittest.main()
