"""Streamlit interface for the stiffened plate calculator."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import streamlit as st

from stiffened_plate import (
    CcccAnalysisInput,
    InputValidationError,
    StiffenerOrientation,
    analyze_cccc,
)
from stiffened_plate.presentation import (
    check_rows,
    format_number,
    implemented_checks_pass,
    intermediate_groups,
)
from stiffened_plate.sections import (
    AngleSection,
    ChannelAttachment,
    ChannelSection,
    FlatBarSection,
    Handedness,
    RectangularHollowSection,
    RhsAttachment,
    TeeAttachment,
    TeeSection,
)
from stiffened_plate.visualization import front_view_figure, side_view_figure


st.set_page_config(
    page_title="Stiffened Plate Calculator",
    page_icon="▦",
    layout="wide",
)


def _apply_interface_style() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        .stApp,
        .stApp p,
        .stApp label,
        .stApp input,
        .stApp textarea,
        .stApp button,
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp h5,
        .stApp h6,
        .stApp [data-testid="stMetricValue"],
        .stApp [data-testid="stMetricLabel"],
        .stApp [data-baseweb="select"],
        .stApp [data-testid="stDataFrame"] {
            font-family: "JetBrains Mono", "Cascadia Mono", Consolas,
                "Liberation Mono", monospace !important;
        }

        .stApp p,
        .stApp label,
        .stApp input,
        .stApp textarea,
        .stApp button,
        .stApp [data-baseweb="select"] {
            font-size: 14px !important;
        }

        .stApp [data-testid="stDataFrame"] {
            font-size: 13px !important;
        }

        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stCaptionContainer"] p,
        .stApp small {
            font-size: 12px !important;
        }

        .stApp h1 {
            font-size: 2rem !important;
        }

        .stApp h2 {
            font-size: 1.4rem !important;
        }

        .stApp h3 {
            font-size: 1.15rem !important;
        }

        .stApp [data-testid="stMetricLabel"] {
            font-size: 13px !important;
        }

        .stApp [data-testid="stMetricValue"] {
            font-size: 1.65rem !important;
        }

        /* Square geometry throughout the application. */
        .stApp * {
            border-radius: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _positive_dimension(label: str, default: float, key: str) -> float:
    return float(
        st.number_input(
            label,
            min_value=0.001,
            value=default,
            step=0.0625,
            format="%.4f",
            key=key,
        )
    )


def _section_inputs(stiffener_count: int):
    if stiffener_count == 0:
        st.info("No stiffener section is required when the stiffener count is zero.")
        return None

    family = st.selectbox(
        "Section family",
        ("Flat bar", "Angle", "T-section", "RHS / SHS", "Channel / U-section"),
    )

    if family == "Flat bar":
        height = _positive_dimension("Projecting height, h (in)", 2.0, "fb_height")
        thickness = _positive_dimension("Bar thickness, t (in)", 0.25, "fb_thickness")
        return FlatBarSection(height=height, thickness=thickness)

    if family == "Angle":
        attached_leg = _positive_dimension(
            "Attached leg length (in)", 2.0, "angle_attached"
        )
        outstanding_leg = _positive_dimension(
            "Outstanding leg length (in)", 2.5, "angle_outstanding"
        )
        thickness = _positive_dimension("Angle thickness (in)", 0.25, "angle_t")
        handedness = Handedness(
            st.selectbox(
                "Projection side",
                (Handedness.RIGHT.value, Handedness.LEFT.value),
                format_func=lambda value: value.replace("_", " ").title(),
            )
        )
        return AngleSection(attached_leg, outstanding_leg, thickness, handedness)

    if family == "T-section":
        overall_depth = _positive_dimension("Overall depth (in)", 3.0, "tee_depth")
        web_thickness = _positive_dimension("Web thickness (in)", 0.25, "tee_tw")
        flange_width = _positive_dimension("Flange width (in)", 2.0, "tee_bf")
        flange_thickness = _positive_dimension(
            "Flange thickness (in)", 0.25, "tee_tf"
        )
        attachment = TeeAttachment(
            st.selectbox(
                "Face attached to plate",
                (TeeAttachment.WEB_END.value, TeeAttachment.FLANGE_FACE.value),
                format_func=lambda value: value.replace("_", " ").title(),
            )
        )
        return TeeSection(
            overall_depth,
            web_thickness,
            flange_width,
            flange_thickness,
            attachment,
        )

    if family == "RHS / SHS":
        side_a = _positive_dimension("Outside side A (in)", 2.0, "rhs_a")
        side_b = _positive_dimension("Outside side B (in)", 3.0, "rhs_b")
        wall = _positive_dimension("Wall thickness (in)", 0.25, "rhs_t")
        attachment = RhsAttachment(
            st.selectbox(
                "Side attached to plate",
                (RhsAttachment.SIDE_A.value, RhsAttachment.SIDE_B.value),
                format_func=lambda value: value.replace("_", " ").title(),
            )
        )
        return RectangularHollowSection(side_a, side_b, wall, attachment)

    overall_depth = _positive_dimension("Overall depth (in)", 3.0, "channel_d")
    flange_width = _positive_dimension("Flange width (in)", 2.0, "channel_bf")
    web_thickness = _positive_dimension("Web thickness (in)", 0.25, "channel_tw")
    flange_thickness = _positive_dimension(
        "Flange thickness (in)", 0.25, "channel_tf"
    )
    attachment = ChannelAttachment(
        st.selectbox(
            "Channel attachment",
            (
                ChannelAttachment.FLANGE_FACE.value,
                ChannelAttachment.WEB_FACE.value,
            ),
            format_func=lambda value: {
                ChannelAttachment.FLANGE_FACE.value: "Both flange end faces",
                ChannelAttachment.WEB_FACE.value: "Back of web",
            }[value],
        )
    )
    return ChannelSection(
        overall_depth,
        flange_width,
        web_thickness,
        flange_thickness,
        attachment,
    )


def _collect_inputs() -> CcccAnalysisInput:
    st.sidebar.header("Analysis inputs")
    st.sidebar.caption("Boundary condition: CCCC — all four plate edges clamped")

    with st.sidebar.expander("Plate geometry", expanded=True):
        long_span = float(
            st.number_input(
                "Long span, a (in)",
                min_value=0.001,
                value=72.0,
                step=1.0,
                format="%.4f",
            )
        )
        short_span = float(
            st.number_input(
                "Short span, b (in)",
                min_value=0.001,
                value=40.0,
                step=1.0,
                format="%.4f",
            )
        )
        plate_thickness = float(
            st.number_input(
                "Plate thickness, t (in)",
                min_value=0.001,
                value=0.1345,
                step=0.015625,
                format="%.4f",
            )
        )

    with st.sidebar.expander("Stiffeners", expanded=True):
        orientation = StiffenerOrientation(
            st.selectbox(
                "Stiffener direction",
                (
                    StiffenerOrientation.LONG_SPAN.value,
                    StiffenerOrientation.SHORT_SPAN.value,
                ),
                format_func=lambda value: value.replace("_", " ").title(),
            )
        )
        stiffener_count = int(
            st.number_input(
                "Number of equally spaced stiffeners",
                min_value=0,
                value=2,
                step=1,
            )
        )
        stiffener = _section_inputs(stiffener_count)

    with st.sidebar.expander("Material, loading, and criterion", expanded=True):
        elastic_modulus = float(
            st.number_input(
                "Elastic modulus, E (ksi)",
                min_value=0.001,
                value=29_000.0,
                step=100.0,
                format="%.1f",
            )
        )
        poisson_ratio = float(
            st.number_input(
                "Poisson's ratio, ν",
                min_value=-0.999,
                max_value=0.499,
                value=0.3,
                step=0.01,
                format="%.3f",
            )
        )
        yield_strength = float(
            st.number_input(
                "Yield strength, Fy (ksi)",
                min_value=0.001,
                value=36.0,
                step=1.0,
                format="%.3f",
            )
        )
        pressure = float(
            st.number_input(
                "Uniform pressure, q (psf)",
                min_value=0.0,
                value=100.0,
                step=10.0,
                format="%.3f",
            )
        )
        deflection_denominator = float(
            st.number_input(
                "Deflection limit denominator, L /",
                min_value=0.001,
                value=240.0,
                step=10.0,
                format="%.1f",
            )
        )

    st.sidebar.caption(
        "Inputs use imperial units. Results update automatically when a value changes."
    )
    return CcccAnalysisInput(
        long_span_in=long_span,
        short_span_in=short_span,
        plate_thickness_in=plate_thickness,
        stiffener_count=stiffener_count,
        elastic_modulus_ksi=elastic_modulus,
        poisson_ratio=poisson_ratio,
        yield_strength_ksi=yield_strength,
        pressure_psf=pressure,
        deflection_limit_denominator=deflection_denominator,
        stiffener_orientation=orientation,
        stiffener=stiffener,
    )


def _render_summary(result) -> None:
    if implemented_checks_pass(result):
        st.success(
            "All implemented elastic checks pass for the current inputs. "
            "This is not an overall code-compliance result."
        )
    else:
        st.error("One or more implemented checks fail for the current inputs.")

    response = result.response
    metric_columns = st.columns(4)
    metric_columns[0].metric(
        "Governing deflection",
        f"{format_number(response.maximum_deflection_in)} in",
        help="Maximum of the panel and stiffener deflections in the parity model.",
    )
    metric_columns[1].metric(
        "Allowable deflection",
        f"{format_number(response.allowable_deflection_in)} in",
    )
    metric_columns[2].metric(
        "Plate stress",
        f"{format_number(response.plate_stress_ksi)} ksi",
    )
    metric_columns[3].metric(
        "Stiffener stress",
        (
            f"{format_number(response.stiffener_stress_ksi)} ksi"
            if result.inputs.stiffener_count > 0
            else "N/A"
        ),
    )

    st.subheader("Geometry views")
    chart_config = {
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ("select2d", "lasso2d"),
    }
    front_column, side_column = st.columns(2, gap="large")
    with front_column:
        st.markdown("**Front view**")
        st.caption(
            "Plate plan shown to scale; stiffeners are represented by centerlines."
        )
        st.plotly_chart(
            front_view_figure(
                result.inputs.long_span_in,
                result.inputs.short_span_in,
                result.inputs.stiffener_count,
                result.inputs.stiffener_orientation,
            ),
            width="stretch",
            config=chart_config,
        )
    with side_column:
        st.markdown("**Side view**")
        st.caption(
            "One representative cross-section using the calculated attachment geometry."
        )
        st.plotly_chart(
            side_view_figure(
                result.panel.spacing_in,
                result.inputs.plate_thickness_in,
                result.inputs.stiffener if result.inputs.stiffener_count > 0 else None,
            ),
            width="stretch",
            config=chart_config,
        )

    st.subheader("Design checks")
    st.dataframe(check_rows(result), width="stretch", hide_index=True)

    failed = [row for row in check_rows(result) if row["Status"] == "FAIL"]
    for row in failed:
        st.error(
            f"{row['Check']}: demand {row['Demand']} {row['Unit']} exceeds "
            f"limit {row['Limit']} {row['Unit']}."
        )


def _render_details(result) -> None:
    st.caption(
        "Displayed values are rounded for readability; checks use full-precision values."
    )
    for title, rows in intermediate_groups(result).items():
        with st.expander(title, expanded=title == "Response"):
            st.dataframe(rows, width="stretch", hide_index=True)


def _render_assumptions(result) -> None:
    if result.warnings:
        st.subheader("Case-specific warnings")
        for warning in result.warnings:
            st.warning(warning)

    st.subheader("Calculation assumptions")
    for assumption in result.assumptions:
        st.markdown(f"- {assumption}")

    st.subheader("Checks outside the current model")
    st.warning(
        "Plate and stiffener stability, effective width, combined stress, weld and "
        "connection strength, fatigue, corrosion, plasticity, and design-code "
        "resistance factors are not implemented."
    )
    st.markdown(
        "The current calculation reproduces the source spreadsheets under the "
        "versioned `spreadsheet_parity_v1` model. It requires engineering review "
        "before use for final structural design."
    )


def main() -> None:
    _apply_interface_style()
    st.title("Stiffened Plate Calculator")
    st.caption(
        "CCCC rectangular steel plates with one set of equally spaced stiffeners "
        "under uniform pressure"
    )
    st.warning(
        "Preliminary elastic calculation only — this tool does not yet perform a "
        "complete structural-code or stability assessment."
    )

    try:
        inputs = _collect_inputs()
        result = analyze_cccc(inputs)
    except (InputValidationError, ValueError) as exc:
        st.error(f"Input error: {exc}")
        st.info("Adjust the highlighted geometry or analysis inputs in the sidebar.")
        return

    summary_tab, details_tab, assumptions_tab = st.tabs(
        ("Summary", "Calculation details", "Assumptions and limitations")
    )
    with summary_tab:
        _render_summary(result)
    with details_tab:
        _render_details(result)
    with assumptions_tab:
        _render_assumptions(result)

    st.caption(
        f"Calculation model: {result.inputs.calculation_model.value} · "
        f"Boundary condition: {result.inputs.boundary_condition.value}"
    )


if __name__ == "__main__":
    main()
