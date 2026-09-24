"""Presentation helpers shared by the interactive interface and its tests."""

from __future__ import annotations

from dataclasses import fields

from .models import CcccAnalysisResult, CheckResult, CheckStatus


STATUS_LABELS: dict[CheckStatus, str] = {
    CheckStatus.PASS: "PASS",
    CheckStatus.FAIL: "FAIL",
    CheckStatus.NOT_IMPLEMENTED: "NOT IMPLEMENTED",
    CheckStatus.NOT_APPLICABLE: "NOT APPLICABLE",
}


def format_number(value: float | None, *, significant_digits: int = 6) -> str:
    """Format an engineering result without changing the calculation value."""

    if value is None:
        return "—"
    if value == 0:
        return "0"
    magnitude = abs(value)
    if magnitude >= 1_000_000 or magnitude < 0.0001:
        return f"{value:.{significant_digits}e}"
    return f"{value:.{significant_digits}f}".rstrip("0").rstrip(".")


def _check_tuple(result: CcccAnalysisResult) -> tuple[CheckResult, ...]:
    return tuple(getattr(result.checks, field.name) for field in fields(result.checks))


def check_rows(result: CcccAnalysisResult) -> list[dict[str, str]]:
    """Return every check as a table-ready row."""

    rows: list[dict[str, str]] = []
    for check in _check_tuple(result):
        utilization = (
            "—"
            if check.utilization is None
            else f"{100.0 * check.utilization:.1f}%"
        )
        rows.append(
            {
                "Check": check.name,
                "Status": STATUS_LABELS[check.status],
                "Demand": format_number(check.demand),
                "Limit": format_number(check.limit),
                "Unit": check.unit or "—",
                "Utilization": utilization,
                "Note": check.note,
            }
        )
    return rows


def implemented_checks_pass(result: CcccAnalysisResult) -> bool:
    """Return true when no implemented check fails.

    This is intentionally not an overall code-compliance statement.
    """

    return not any(check.status is CheckStatus.FAIL for check in _check_tuple(result))


def _row(quantity: str, value: float | str, unit: str = "—") -> dict[str, str]:
    return {
        "Quantity": quantity,
        "Value": format_number(value) if isinstance(value, (int, float)) else value,
        "Unit": unit,
    }


def intermediate_groups(
    result: CcccAnalysisResult,
) -> dict[str, list[dict[str, str]]]:
    """Build auditable intermediate-calculation tables."""

    panel = result.panel
    overall = result.overall_coefficients
    panel_coefficients = result.panel_coefficients
    load = result.load_sharing
    response = result.response

    groups: dict[str, list[dict[str, str]]] = {
        "Conversions and plate properties": [
            _row("Elastic modulus", result.elastic_modulus_psi, "psi"),
            _row("Total uniform force", result.inputs.uniform_force_lbf, "lbf"),
            _row("Full plate area", result.plate_area_in2, "in^2"),
            _row("Uniform pressure", result.pressure_psi, "psi"),
            _row("Plate rigidity D", result.plate_rigidity_lbf_in, "lbf·in"),
        ],
        "Panel geometry and CCCC coefficients": [
            _row("Overall aspect ratio", overall.aspect_ratio),
            _row(
                "Overall deflection coefficient βw (informational only)",
                overall.beta_w,
            ),
            _row(
                "Overall moment coefficient βm (informational only)",
                overall.beta_m,
            ),
            _row("Stiffener span", panel.stiffener_span_in, "in"),
            _row("Stiffener spacing / tributary width", panel.spacing_in, "in"),
            _row("Panel long side", panel.long_side_in, "in"),
            _row("Panel short side", panel.short_side_in, "in"),
            _row("Panel aspect ratio", panel.aspect_ratio),
            _row("Panel deflection coefficient βw", panel_coefficients.beta_w),
            _row("Panel moment coefficient βm", panel_coefficients.beta_m),
        ],
        "Spring stiffness and load sharing": [
            _row(
                "Combined stiffener spring stiffness",
                load.stiffener_spring_stiffness_lbf_per_in,
                "lbf/in",
            ),
            _row(
                "Plate spring stiffness",
                load.plate_spring_stiffness_lbf_per_in,
                "lbf/in",
            ),
            _row("Stiffener load fraction", load.stiffener_load_fraction),
            _row("Plate load fraction", load.plate_load_fraction),
            _row(
                "Effective plate pressure",
                load.effective_plate_pressure_psi,
                "psi",
            ),
            _row(
                "Tributary stiffener load",
                load.tributary_stiffener_load_lbf,
                "lbf",
            ),
        ],
        "Response": [
            _row("Plate deflection", response.plate_deflection_in, "in"),
            _row("Stiffener deflection", response.stiffener_deflection_in, "in"),
            _row("Governing deflection", response.maximum_deflection_in, "in"),
            _row("Allowable deflection", response.allowable_deflection_in, "in"),
            _row(
                "Plate moment",
                response.plate_moment_lbf_in_per_in,
                "lbf·in/in",
            ),
            _row("Plate elastic bending stress", response.plate_stress_ksi, "ksi"),
            _row("Stiffener moment", response.stiffener_moment_lbf_in, "lbf·in"),
            _row(
                "Stiffener elastic bending stress",
                response.stiffener_stress_ksi,
                "ksi",
            ),
        ],
    }

    composite = result.composite_section
    if composite is not None:
        groups["Composite plate–stiffener section"] = [
            _row("Stiffener shape", composite.shape),
            _row("Attachment", composite.attachment),
            _row("Effective plate area", composite.plate_area_in2, "in²"),
            _row("Stiffener area", composite.stiffener_area_in2, "in²"),
            _row("Plate centroid from plate top", composite.plate_centroid_in, "in"),
            _row(
                "Stiffener centroid from plate top",
                composite.stiffener_centroid_in,
                "in",
            ),
            _row("Composite centroid x", composite.centroid_x_in, "in"),
            _row("Composite centroid y", composite.centroid_y_in, "in"),
            _row("Plate contribution to Ix", composite.plate_inertia_in4, "in⁴"),
            _row(
                "Stiffener contribution to Ix",
                composite.stiffener_inertia_in4,
                "in⁴",
            ),
            _row("Composite Ix", composite.inertia_x_in4, "in⁴"),
            _row("Composite Iy", composite.inertia_y_in4, "in⁴"),
            _row("Composite Ixy", composite.product_inertia_in4, "in⁴"),
            _row(
                "Bottom extreme-fibre distance",
                composite.bottom_fibre_distance_in,
                "in",
            ),
            _row(
                "Bottom elastic section modulus",
                composite.elastic_section_modulus_bottom_in3,
                "in³",
            ),
            _row(
                "Composite flexural rigidity EI",
                composite.flexural_rigidity_lbf_in2,
                "lbf·in²",
            ),
        ]

    return groups
