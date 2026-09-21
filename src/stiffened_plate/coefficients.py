"""Boundary-condition coefficient data and interpolation."""

from __future__ import annotations

from math import isfinite

from .models import PlateCoefficients


# All-edges-clamped plate under uniform pressure. The data and limiting
# behavior reproduce the two source CCCC spreadsheets.
CCCC_COEFFICIENT_TABLE: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0138, 0.0513),
    (1.1, 0.0163, 0.0538),
    (1.2, 0.0188, 0.0554),
    (1.5, 0.0249, 0.0573),
    (2.0, 0.0284, 0.0568),
    (3.0, 0.0290, 0.0551),
    (4.0, 0.0291, 0.0547),
)


def cccc_coefficients(aspect_ratio: float) -> PlateCoefficients:
    """Return linearly interpolated CCCC deflection and moment coefficients.

    Values at or below the first tabulated ratio and at or above the last
    ratio are clamped, matching the spreadsheets.
    """

    if not isfinite(aspect_ratio) or aspect_ratio <= 0:
        raise ValueError("aspect ratio must be a finite value greater than zero")

    first = CCCC_COEFFICIENT_TABLE[0]
    last = CCCC_COEFFICIENT_TABLE[-1]
    if aspect_ratio <= first[0]:
        return PlateCoefficients(aspect_ratio, first[1], first[2])
    if aspect_ratio >= last[0]:
        return PlateCoefficients(aspect_ratio, last[1], last[2])

    for lower, upper in zip(CCCC_COEFFICIENT_TABLE, CCCC_COEFFICIENT_TABLE[1:]):
        if aspect_ratio <= upper[0]:
            fraction = (aspect_ratio - lower[0]) / (upper[0] - lower[0])
            beta_w = lower[1] + fraction * (upper[1] - lower[1])
            beta_m = lower[2] + fraction * (upper[2] - lower[2])
            return PlateCoefficients(aspect_ratio, beta_w, beta_m)

    raise RuntimeError("unreachable CCCC coefficient interpolation state")

