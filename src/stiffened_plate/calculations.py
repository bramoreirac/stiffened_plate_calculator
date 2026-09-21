"""CCCC stiffened-plate calculation engine."""

from __future__ import annotations

from math import isfinite

from .coefficients import cccc_coefficients
from .models import (
    AnalysisChecks,
    BoundaryCondition,
    CalculationModel,
    CheckResult,
    CheckStatus,
    CcccAnalysisInput,
    CcccAnalysisResult,
    CompositeSectionResult,
    LoadSharingResult,
    PanelGeometry,
    ResponseResult,
    StiffenerOrientation,
)
from .sections import CompositeSection


class InputValidationError(ValueError):
    """Raised when an analysis input is outside the supported model domain."""


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return isfinite(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


def _require_finite_positive(name: str, value: float) -> None:
    if not _is_finite_number(value) or value <= 0:
        raise InputValidationError(f"{name} must be a finite value greater than zero")


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not _is_finite_number(value) or value < 0:
        raise InputValidationError(f"{name} must be a finite value not less than zero")


def validate_cccc_input(data: CcccAnalysisInput) -> None:
    """Validate inputs before any engineering calculations are performed."""

    if data.boundary_condition is not BoundaryCondition.CCCC:
        raise InputValidationError("only the CCCC boundary condition is implemented")
    if data.calculation_model is not CalculationModel.SPREADSHEET_PARITY_V1:
        raise InputValidationError("only spreadsheet_parity_v1 is implemented")
    if not isinstance(data.stiffener_orientation, StiffenerOrientation):
        raise InputValidationError("stiffener orientation is not supported")

    _require_finite_positive("long span", data.long_span_in)
    _require_finite_positive("short span", data.short_span_in)
    if data.long_span_in < data.short_span_in:
        raise InputValidationError("long span must be greater than or equal to short span")
    _require_finite_positive("plate thickness", data.plate_thickness_in)

    if isinstance(data.stiffener_count, bool) or not isinstance(data.stiffener_count, int):
        raise InputValidationError("stiffener count must be an integer")
    if data.stiffener_count < 0:
        raise InputValidationError("stiffener count must not be negative")
    if data.stiffener_count > 0 and data.stiffener is None:
        raise InputValidationError("a stiffener section is required when count is positive")

    _require_finite_positive("elastic modulus", data.elastic_modulus_ksi)
    if (
        not _is_finite_number(data.poisson_ratio)
        or not -1.0 < data.poisson_ratio < 0.5
    ):
        raise InputValidationError("Poisson's ratio must be finite and between -1 and 0.5")
    _require_finite_positive("yield strength", data.yield_strength_ksi)
    _require_finite_nonnegative("pressure", data.pressure_psf)
    _require_finite_positive(
        "deflection-limit denominator", data.deflection_limit_denominator
    )

    if data.stiffener is not None:
        try:
            data.stiffener.geometry()
        except (AttributeError, TypeError, ValueError) as exc:
            raise InputValidationError(f"invalid stiffener section: {exc}") from exc


def _panel_geometry(data: CcccAnalysisInput) -> PanelGeometry:
    if data.stiffener_orientation is StiffenerOrientation.LONG_SPAN:
        stiffener_span = data.long_span_in
        spacing = data.short_span_in / (data.stiffener_count + 1)
        if data.stiffener_count > 0:
            long_side = data.long_span_in
            short_side = spacing
        else:
            long_side = data.long_span_in
            short_side = data.short_span_in
    else:
        stiffener_span = data.short_span_in
        spacing = data.long_span_in / (data.stiffener_count + 1)
        long_side = max(data.short_span_in, spacing)
        short_side = min(data.short_span_in, spacing)

    return PanelGeometry(
        stiffener_span_in=stiffener_span,
        spacing_in=spacing,
        long_side_in=long_side,
        short_side_in=short_side,
        aspect_ratio=max(long_side / short_side, 1.0),
    )


def _evaluated_check(
    name: str, demand: float, limit: float, unit: str, note: str = ""
) -> CheckResult:
    return CheckResult(
        name=name,
        status=CheckStatus.PASS if demand <= limit else CheckStatus.FAIL,
        demand=demand,
        limit=limit,
        utilization=demand / limit,
        unit=unit,
        note=note,
    )


def _pending_check(name: str, *, applicable: bool, note: str) -> CheckResult:
    return CheckResult(
        name=name,
        status=(CheckStatus.NOT_IMPLEMENTED if applicable else CheckStatus.NOT_APPLICABLE),
        note=note,
    )


def analyze_cccc(data: CcccAnalysisInput) -> CcccAnalysisResult:
    """Analyze a CCCC plate using the versioned spreadsheet-parity model.

    This deliberately retains the source workbooks' load-sharing and response
    assumptions. See the returned assumptions and the Phase 1 specification.
    """

    validate_cccc_input(data)

    elastic_modulus_psi = data.elastic_modulus_ksi * 1000.0
    pressure_psi = data.pressure_psf / 144.0
    plate_rigidity = (
        elastic_modulus_psi
        * data.plate_thickness_in**3
        / (12.0 * (1.0 - data.poisson_ratio**2))
    )
    overall = cccc_coefficients(data.long_span_in / data.short_span_in)
    panel = _panel_geometry(data)
    panel_coefficients = cccc_coefficients(panel.aspect_ratio)

    composite_result: CompositeSectionResult | None = None
    composite_inertia = 0.0
    composite_ei = 0.0
    bottom_fibre_distance = 0.0
    warnings: list[str] = []

    if data.stiffener_count > 0:
        assert data.stiffener is not None
        bare = data.stiffener.geometry()
        composite = CompositeSection(
            plate_width=panel.spacing_in,
            plate_thickness=data.plate_thickness_in,
            stiffener=data.stiffener,
        ).geometry()
        props = composite.properties
        bare_props = bare.properties
        plate_area = panel.spacing_in * data.plate_thickness_in
        plate_centroid = data.plate_thickness_in / 2.0
        stiffener_centroid = data.plate_thickness_in + bare_props.centroid_y
        plate_inertia = (
            panel.spacing_in * data.plate_thickness_in**3 / 12.0
            + plate_area * (props.centroid_y - plate_centroid) ** 2
        )
        stiffener_inertia = (
            bare_props.ix
            + bare_props.area * (stiffener_centroid - props.centroid_y) ** 2
        )
        composite_inertia = props.ix
        composite_ei = elastic_modulus_psi * composite_inertia
        bottom_fibre_distance = props.c_bottom
        composite_result = CompositeSectionResult(
            shape=bare.shape,
            attachment=bare.attachment,
            plate_area_in2=plate_area,
            stiffener_area_in2=bare_props.area,
            plate_centroid_in=plate_centroid,
            stiffener_centroid_in=stiffener_centroid,
            centroid_x_in=props.centroid_x,
            centroid_y_in=props.centroid_y,
            plate_inertia_in4=plate_inertia,
            stiffener_inertia_in4=stiffener_inertia,
            inertia_x_in4=composite_inertia,
            inertia_y_in4=props.iy,
            product_inertia_in4=props.ixy,
            bottom_fibre_distance_in=bottom_fibre_distance,
            elastic_section_modulus_bottom_in3=(
                composite_inertia / bottom_fibre_distance
            ),
            flexural_rigidity_lbf_in2=composite_ei,
        )
        if abs(props.ixy) > max(1e-12, 1e-10 * composite_inertia):
            warnings.append(
                "The composite section has nonzero product inertia; the parity model "
                "uses Ix only and does not evaluate unsymmetrical-bending coupling."
            )

    stiffener_spring = (
        data.stiffener_count
        * 192.0
        * composite_ei
        / panel.stiffener_span_in**3
        if data.stiffener_count > 0
        else 0.0
    )
    plate_spring = (
        384.0
        * plate_rigidity
        * panel.stiffener_span_in
        / (5.0 * panel.spacing_in**4)
    )
    if data.stiffener_count > 0:
        stiffener_fraction = stiffener_spring / (stiffener_spring + plate_spring)
    else:
        stiffener_fraction = 0.0
    plate_fraction = 1.0 - stiffener_fraction
    effective_plate_pressure = plate_fraction * pressure_psi
    tributary_load = pressure_psi * panel.spacing_in * panel.stiffener_span_in

    plate_deflection = (
        panel_coefficients.beta_w
        * effective_plate_pressure
        * panel.short_side_in**4
        / plate_rigidity
    )
    plate_moment = (
        panel_coefficients.beta_m
        * effective_plate_pressure
        * panel.short_side_in**2
    )
    plate_stress = 6.0 * plate_moment / data.plate_thickness_in**2 / 1000.0

    if data.stiffener_count > 0:
        stiffener_deflection = (
            tributary_load * panel.stiffener_span_in**3 / (192.0 * composite_ei)
        )
        stiffener_moment = tributary_load * panel.stiffener_span_in / 8.0
        stiffener_stress = (
            stiffener_moment
            * bottom_fibre_distance
            / composite_inertia
            / 1000.0
        )
    else:
        stiffener_deflection = 0.0
        stiffener_moment = 0.0
        stiffener_stress = 0.0

    maximum_deflection = max(plate_deflection, stiffener_deflection)
    allowable_deflection = (
        data.short_span_in / data.deflection_limit_denominator
    )
    response = ResponseResult(
        plate_deflection_in=plate_deflection,
        stiffener_deflection_in=stiffener_deflection,
        maximum_deflection_in=maximum_deflection,
        allowable_deflection_in=allowable_deflection,
        plate_moment_lbf_in_per_in=plate_moment,
        plate_stress_ksi=plate_stress,
        stiffener_moment_lbf_in=stiffener_moment,
        stiffener_stress_ksi=stiffener_stress,
    )

    stiffener_exists = data.stiffener_count > 0
    checks = AnalysisChecks(
        deflection=_evaluated_check(
            "Deflection", maximum_deflection, allowable_deflection, "in"
        ),
        plate_yield=_evaluated_check(
            "Plate elastic bending yield",
            plate_stress,
            data.yield_strength_ksi,
            "ksi",
        ),
        stiffener_yield=(
            _evaluated_check(
                "Stiffener elastic bending yield",
                stiffener_stress,
                data.yield_strength_ksi,
                "ksi",
            )
            if stiffener_exists
            else _pending_check(
                "Stiffener elastic bending yield",
                applicable=False,
                note="No stiffeners are present.",
            )
        ),
        plate_stability=_pending_check(
            "Plate stability",
            applicable=True,
            note="Effective-width and plate-buckling checks are not implemented.",
        ),
        stiffener_stability=_pending_check(
            "Stiffener section stability",
            applicable=stiffener_exists,
            note=(
                "Local, torsional, flexural-torsional, lateral, and tripping "
                "checks are not implemented."
                if stiffener_exists
                else "No stiffeners are present."
            ),
        ),
        connection=_pending_check(
            "Plate-to-stiffener connection",
            applicable=stiffener_exists,
            note=(
                "Weld and load-transfer checks are not implemented."
                if stiffener_exists
                else "No stiffeners are present."
            ),
        ),
        combined_stress=_pending_check(
            "Combined plate and stiffener stress",
            applicable=stiffener_exists,
            note=(
                "The parity model checks local plate and composite stiffener "
                "stresses separately."
                if stiffener_exists
                else "No composite stiffener stress exists to combine."
            ),
        ),
    )

    return CcccAnalysisResult(
        inputs=data,
        elastic_modulus_psi=elastic_modulus_psi,
        pressure_psi=pressure_psi,
        plate_rigidity_lbf_in=plate_rigidity,
        overall_coefficients=overall,
        panel=panel,
        panel_coefficients=panel_coefficients,
        composite_section=composite_result,
        load_sharing=LoadSharingResult(
            stiffener_spring_stiffness_lbf_per_in=stiffener_spring,
            plate_spring_stiffness_lbf_per_in=plate_spring,
            stiffener_load_fraction=stiffener_fraction,
            plate_load_fraction=plate_fraction,
            effective_plate_pressure_psi=effective_plate_pressure,
            tributary_stiffener_load_lbf=tributary_load,
        ),
        response=response,
        checks=checks,
        assumptions=(
            "All four plate edges and all calculated subpanel edges are clamped.",
            "The effective plate width equals the full stiffener spacing.",
            "The plate pressure is reduced by spring load sharing; the stiffener "
            "response uses the full tributary pressure.",
            "The tributary pressure resultant is treated as a fixed-fixed "
            "center point load using the spreadsheet constants 192 and 8.",
            "Governing deflection is the larger, not the sum, of plate-panel and "
            "stiffener deflections.",
            "Material and response behavior are elastic.",
        ),
        warnings=tuple(warnings),
    )
