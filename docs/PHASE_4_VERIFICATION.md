# Phase 4 Automated Verification Report

## Status

Phase 4 is complete. The calculation, section, and validation suite contains
46 passing tests and no
known unexplained differences from the two source CCCC spreadsheets.

This phase verifies the software translation and its internal numerical
behavior. It does not independently establish that the spreadsheet method is
suitable for every structural design case.

## Verification layers

| Layer | Verification performed | Result |
|---|---|---|
| Spreadsheet regression | Every stored numeric intermediate and final value from both CCCC golden cases | Pass |
| Spreadsheet checks | Deflection, plate yield, and stiffener yield Boolean results | Pass |
| Coefficients | Every table knot, every interval midpoint, lower and upper clamps, invalid ratios | Pass |
| Units and rigidity | Modulus conversion; full plate area; force-to-pressure conversion; plate-flexural-rigidity equation | Pass |
| Orientation geometry | Long-span, short-span, dimension-swapping, and zero-stiffener cases | Pass |
| Composite properties | Independent area, centroid, parallel-axis inertia, extreme fibre, and section modulus | Pass |
| Load sharing | Plate and stiffener spring constants, load fractions, effective pressure, tributary load | Pass |
| Response | Plate and stiffener deflections, moments, stresses, governing deflection, allowable deflection | Pass |
| Scaling | Linear response under doubled total force | Pass |
| Check boundaries | Zero demand, equality acceptance, just-over-limit failure, utilization, and units | Pass |
| Incomplete limit states | Stability, connection, and combined stress cannot report a false pass | Pass |
| Input validation | Scalar domains, nonnumeric values, count rules, invalid sections, and unsupported identifiers | Pass |
| Section families | Flat bar, angle, T, RHS/SHS, and channel properties and analysis integration | Pass |
| Unsymmetrical sections | Nonzero product inertia produces an explicit coupled-bending warning | Pass |
| Centroid placement | Angle handedness mirrors the profile while the bare centroid remains aligned with the plate-strip reference | Pass |

## Workbook regression acceptance

The cases in `reference/cccc_golden_cases.json` represent:

- Flat-bar stiffeners spanning the long plate direction.
- Flat-bar stiffeners spanning the short plate direction.

The tests compare every value stored in each case using relative tolerance
`1e-10` and absolute tolerance `1e-12`. Pass/fail states and identifiers are
compared exactly. Calculations use unrounded values.

The workbook pressure inputs are converted to equivalent total forces so the
pressure and all downstream workbook results remain unchanged. The engine
identifies this revised input method as `total_force_v2`.

## Formula-level independence

Formula tests construct expected results directly from the Phase 1 equations,
rather than reading the engine's internal variables. These checks separately
recalculate:

- Full plate area and total-force-to-pressure conversion.
- Plate rigidity.
- Orientation-specific panel dimensions.
- Composite centroid and inertia by the parallel-axis theorem.
- Plate and stiffener spring stiffnesses.
- Load fractions and pressure allocation.
- Plate deflection, moment, and elastic bending stress.
- Stiffener deflection, moment, and elastic bending stress.
- Governing and allowable deflections.

This isolates translation errors that could be hidden if only final workbook
outputs were compared.

## Check-boundary verification

The implemented checks use unrounded values and the inclusive rule
`demand <= limit`. Tests establish that:

- Equality is `PASS`.
- A demand just above the limit is `FAIL`.
- Zero force produces zero utilization and `PASS` for implemented checks.
- Demand, limit, utilization, and units correspond to the returned response.
- Unimplemented checks have no fabricated demand, limit, or utilization.

## Validation improvement found during Phase 4

Malformed runtime values such as numeric strings, `None`, and arbitrary
objects now raise `InputValidationError` with a field-specific message instead
of leaking a lower-level Python `TypeError`. This does not alter results for any
valid engineering input.

## How to run verification

From the project directory:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s tests -v
```

No third-party test dependency is required.

## Remaining engineering review

The following items remain outside the verified calculation scope:

- Whether the spreadsheet spring/load-sharing idealization is physically
  appropriate for a particular plate.
- Whether the equivalent fixed-fixed point-load beam model should be replaced
  by a distributed-load formulation.
- Whether panel and stiffener deflections should be combined.
- Effective plate width and shear-lag effects.
- Local plate and stiffener-element buckling.
- Stiffener lateral, torsional, flexural-torsional, and tripping behavior.
- Unsymmetrical-bending coupling for sections with nonzero product inertia.
- Weld strength, connection load transfer, fatigue, corrosion, plasticity, and
  design-code resistance factors.
- Independent validation of the CCCC coefficient source beyond faithful table
  transcription and interpolation.

These limitations remain explicit in results and should be addressed through
engineering review or later versioned calculation models. Spreadsheet parity
alone must not be interpreted as full design-code verification.

## Phase conclusion

The CCCC computational core is sufficiently regression-tested for the Phase 5
interactive interface. The interface should call this engine directly and
must not duplicate its equations or suppress its assumptions, warnings, or
unimplemented-check states.
