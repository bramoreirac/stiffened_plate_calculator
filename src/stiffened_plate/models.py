"""Typed inputs and results for stiffened-plate analyses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sections import StiffenerSection


class BoundaryCondition(str, Enum):
    """Supported plate-edge boundary conditions."""

    CCCC = "CCCC"


class StiffenerOrientation(str, Enum):
    """Direction in which the parallel stiffeners span."""

    LONG_SPAN = "long_span"
    SHORT_SPAN = "short_span"


class CalculationModel(str, Enum):
    """Versioned engineering calculation methods."""

    SPREADSHEET_PARITY_V1 = "spreadsheet_parity_v1"


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class CcccAnalysisInput:
    """Imperial-unit inputs for the CCCC spreadsheet-parity model.

    Lengths are inches, material stresses are ksi, and pressure is psf.
    A stiffener section is required when ``stiffener_count`` is positive.
    """

    long_span_in: float
    short_span_in: float
    plate_thickness_in: float
    stiffener_count: int
    elastic_modulus_ksi: float
    poisson_ratio: float
    yield_strength_ksi: float
    pressure_psf: float
    stiffener_orientation: StiffenerOrientation
    stiffener: StiffenerSection | None = None
    deflection_limit_denominator: float = 240.0
    boundary_condition: BoundaryCondition = BoundaryCondition.CCCC
    calculation_model: CalculationModel = CalculationModel.SPREADSHEET_PARITY_V1


@dataclass(frozen=True, slots=True)
class PlateCoefficients:
    aspect_ratio: float
    beta_w: float
    beta_m: float


@dataclass(frozen=True, slots=True)
class PanelGeometry:
    stiffener_span_in: float
    spacing_in: float
    long_side_in: float
    short_side_in: float
    aspect_ratio: float


@dataclass(frozen=True, slots=True)
class CompositeSectionResult:
    shape: str
    attachment: str
    plate_area_in2: float
    stiffener_area_in2: float
    plate_centroid_in: float
    stiffener_centroid_in: float
    centroid_x_in: float
    centroid_y_in: float
    plate_inertia_in4: float
    stiffener_inertia_in4: float
    inertia_x_in4: float
    inertia_y_in4: float
    product_inertia_in4: float
    bottom_fibre_distance_in: float
    elastic_section_modulus_bottom_in3: float
    flexural_rigidity_lbf_in2: float


@dataclass(frozen=True, slots=True)
class LoadSharingResult:
    stiffener_spring_stiffness_lbf_per_in: float
    plate_spring_stiffness_lbf_per_in: float
    stiffener_load_fraction: float
    plate_load_fraction: float
    effective_plate_pressure_psi: float
    tributary_stiffener_load_lbf: float


@dataclass(frozen=True, slots=True)
class ResponseResult:
    plate_deflection_in: float
    stiffener_deflection_in: float
    maximum_deflection_in: float
    allowable_deflection_in: float
    plate_moment_lbf_in_per_in: float
    plate_stress_ksi: float
    stiffener_moment_lbf_in: float
    stiffener_stress_ksi: float


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: CheckStatus
    demand: float | None = None
    limit: float | None = None
    utilization: float | None = None
    unit: str | None = None
    note: str = ""


@dataclass(frozen=True, slots=True)
class AnalysisChecks:
    deflection: CheckResult
    plate_yield: CheckResult
    stiffener_yield: CheckResult
    plate_stability: CheckResult
    stiffener_stability: CheckResult
    connection: CheckResult
    combined_stress: CheckResult


@dataclass(frozen=True, slots=True)
class CcccAnalysisResult:
    """Auditable output from the CCCC spreadsheet-parity calculation."""

    inputs: CcccAnalysisInput
    elastic_modulus_psi: float
    pressure_psi: float
    plate_rigidity_lbf_in: float
    overall_coefficients: PlateCoefficients
    panel: PanelGeometry
    panel_coefficients: PlateCoefficients
    composite_section: CompositeSectionResult | None
    load_sharing: LoadSharingResult
    response: ResponseResult
    checks: AnalysisChecks
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]

