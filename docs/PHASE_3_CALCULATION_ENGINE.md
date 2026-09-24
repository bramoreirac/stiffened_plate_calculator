# Phase 3 CCCC Calculation Engine

## Status

Phase 3 is complete. The Python engine implements the versioned
`total_force_v2` calculation for plates with all four edges clamped (`CCCC`)
and stiffeners running along either the long or short plate span.

The engine retains the documented spreadsheet response method after converting
the entered total uniformly distributed force to pressure over the full plate
area. Numerical parity does not independently validate that method for design
use.

## Implementation

The phase introduced three modules:

- `models.py` contains typed inputs, intermediate results, final results,
  calculation-model identifiers, and check statuses.
- `coefficients.py` contains the CCCC coefficient table and shared linear
  interpolation routine.
- `calculations.py` contains validation, orientation-specific panel geometry,
  the common calculation flow, and check evaluation.

The calculation engine uses the common section interface from Phase 2, so the
same analysis flow accepts flat bars, angles, T-sections, RHS/SHS, and channels.

## Public API

```python
from stiffened_plate import (
    CcccAnalysisInput,
    StiffenerOrientation,
    analyze_cccc,
)
from stiffened_plate.sections import FlatBarSection

result = analyze_cccc(
    CcccAnalysisInput(
        long_span_in=72.0,
        short_span_in=40.0,
        plate_thickness_in=0.1345,
        stiffener_count=2,
        elastic_modulus_ksi=29_000.0,
        poisson_ratio=0.3,
        yield_strength_ksi=36.0,
        uniform_force_lbf=2_000.0,
        stiffener_orientation=StiffenerOrientation.LONG_SPAN,
        stiffener=FlatBarSection(height=2.0, thickness=0.25),
    )
)

print(result.response.maximum_deflection_in)
print(result.checks.deflection.status)
```

All input dimensions use inches, material stresses use ksi, and the total
uniformly distributed force uses lbf. The engine calculates pressure in psi:

```text
plate_area_in2 = long_span_in * short_span_in
pressure_psi = uniform_force_lbf / plate_area_in2
```

Returned property and response field names include units.

## Result organization

`CcccAnalysisResult` retains:

- Converted modulus, full plate area, total force, and calculated pressure.
- Overall and panel CCCC coefficients.
- Stiffener span, spacing, and panel dimensions.
- Plate rigidity.
- Bare-stiffener and composite-section properties.
- Spring stiffnesses, load fractions, and tributary stiffener load.
- Plate and stiffener deflections, moments, and stresses.
- Demand, limit, utilization, and status for implemented checks.
- Explicit assumptions and warnings.

This intermediate result set supports direct spreadsheet-cell auditing and a
later detailed-calculation view in the interactive interface.

## Check states

Every check has one of four states: `PASS`, `FAIL`, `NOT_IMPLEMENTED`, or
`NOT_APPLICABLE`.

Deflection, plate elastic bending yield, and stiffener elastic bending yield
are evaluated. Plate stability, stiffener stability, plate-to-stiffener
connection, and combined-stress checks are explicitly `NOT_IMPLEMENTED` when
applicable. They are never inferred to pass.

With zero stiffeners, the composite section is absent and stiffener-related
checks are marked `NOT_APPLICABLE`.

## Validation

The engine rejects:

- Non-finite or non-positive spans, thickness, material properties, or
  deflection-limit denominator.
- A nominal long span shorter than the nominal short span.
- Negative, fractional, or Boolean stiffener counts.
- A positive stiffener count without a valid section.
- Poisson's ratios outside `-1 < nu < 0.5`.
- Negative total force.
- Unsupported boundary conditions, orientations, or calculation models.
- Invalid section geometry reported by the Phase 2 section engine.

## Spreadsheet parity and tests

Both Phase 1 golden cases are automated tests. Each workbook pressure input is
first converted to an equivalent total force by multiplying it by the full
plate area. Every stored numeric intermediate and final result, plus all three
spreadsheet Boolean checks, is then compared using the tolerance in
`reference/cccc_golden_cases.json`.

Tests also cover every coefficient knot, every interpolation interval, both
coefficient clamps, invalid ratios, the unstiffened case, input failures, and
all Phase 2 section properties.

Run the complete suite from the project directory:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

## Deliberately preserved spreadsheet assumptions

The engine retains the Phase 1 review items, including:

- Load sharing reduces plate pressure, while stiffener response uses the full
  tributary pressure.
- The tributary pressure resultant is treated as a fixed-fixed center point
  load with the spreadsheet constants `192` and `8`.
- Governing deflection is the maximum of panel and stiffener deflections, not
  their sum.
- Full stiffener spacing is used as effective plate width.
- Internal panel edges use CCCC coefficients.
- Plate and stiffener stresses are checked separately.
- Only the bottom composite extreme fibre is used for stiffener bending stress.

The total-force input is implemented as `total_force_v2`, rather than silently
changing the meaning of the former `spreadsheet_parity_v1` pressure input.

## Current limitations

- Imperial units and nonnegative total uniformly distributed force only.
- CCCC plates with one equally spaced set of parallel stiffeners only.
- Elastic response and gross sharp-corner section properties.
- No stability, effective-width, weld, connection, plasticity, fatigue,
  corrosion, or code-resistance checks.
- Unsymmetrical sections use composite `Ix`; a nonzero product inertia produces
  a warning because coupled unsymmetrical bending is not evaluated.
