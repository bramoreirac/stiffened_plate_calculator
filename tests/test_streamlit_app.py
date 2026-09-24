import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_AVAILABLE = importlib.util.find_spec("streamlit") is not None

if STREAMLIT_AVAILABLE:
    from streamlit.testing.v1 import AppTest


@unittest.skipUnless(STREAMLIT_AVAILABLE, "Streamlit is not installed")
class StreamlitAppTests(unittest.TestCase):
    def run_app(self):
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=15)
        self.assertEqual(list(app.exception), [])
        return app

    @staticmethod
    def widget_by_label(widgets, label):
        return next(widget for widget in widgets if widget.label == label)

    def test_default_app_renders_summary_details_and_limit_states(self):
        app = self.run_app()
        self.assertEqual(app.title[0].value, "Stiffened Plate Calculator")
        self.assertTrue(
            any(
                "total uniformly distributed force" in caption.value
                and "force divided by full plate area" in caption.value
                for caption in app.caption
            )
        )
        self.assertEqual(len(app.tabs), 3)
        self.assertGreaterEqual(len(app.dataframe), 1)
        self.assertGreaterEqual(len(app.get("plotly_chart")), 2)
        self.assertTrue(any("implemented elastic checks pass" in box.value for box in app.success))
        self.assertIn(
            "NOT IMPLEMENTED", app.dataframe[0].value["Status"].tolist()
        )

    def test_force_change_produces_a_visible_failure(self):
        app = self.run_app()
        uniform_force = self.widget_by_label(
            app.number_input, "Uniformly distributed force, F (lbf)"
        )
        uniform_force.set_value(1_000_000.0)
        app.run(timeout=15)
        self.assertEqual(list(app.exception), [])
        self.assertTrue(any("implemented checks fail" in box.value for box in app.error))

    def test_zero_stiffeners_renders_without_section_inputs(self):
        app = self.run_app()
        count = self.widget_by_label(
            app.number_input, "Number of equally spaced stiffeners"
        )
        count.set_value(0)
        app.run(timeout=15)
        self.assertEqual(list(app.exception), [])
        self.assertTrue(
            any("No stiffener section is required" in box.value for box in app.info)
        )

    def test_front_view_updates_for_short_span_stiffeners(self):
        app = self.run_app()
        orientation = self.widget_by_label(app.selectbox, "Stiffener direction")
        count = self.widget_by_label(
            app.number_input, "Number of equally spaced stiffeners"
        )
        orientation.set_value("short_span")
        count.set_value(3)
        app.run(timeout=15)
        self.assertEqual(list(app.exception), [])
        self.assertGreaterEqual(len(app.get("plotly_chart")), 2)

    def test_each_section_family_renders(self):
        families = ("Flat bar", "Angle", "T-section", "RHS / SHS", "Channel / U-section")
        for family in families:
            with self.subTest(family=family):
                app = self.run_app()
                section_family = self.widget_by_label(app.selectbox, "Section family")
                section_family.set_value(family)
                app.run(timeout=15)
                self.assertEqual(list(app.exception), [])


if __name__ == "__main__":
    unittest.main()
