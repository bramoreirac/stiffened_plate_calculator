# Stiffened Plate Calculator

An interactive Python application for evaluating rectangular steel plates with one-way stiffeners under uniform pressure.

The first release will reproduce and consolidate the two existing `CCCC` spreadsheets for plates with all four edges clamped. The architecture will allow `SSSS`, `CSCS`, and other analysis scenarios to be added later without duplicating the common calculation logic.

## Initial analysis scope

- Boundary condition: `CCCC`.
- Stiffener direction: long span or short span.
- Loading: uniform pressure.
- Units: imperial initially.
- Outputs: intermediate values, elastic deflections, bending stresses, utilization ratios, and clearly identified design checks.

## Initial stiffener library

- Flat bar.
- Equal-leg or unequal-leg angle.
- T-section.
- Rectangular hollow section (RHS), including square hollow sections (SHS).
- Channel/U-section.

Planned future additions include bulb flats, hat sections, trapezoidal ribs, and custom built-up sections.

Square and rectangular tubes share one calculation model. Angles and channels require explicit orientation and attachment definitions because they are not generally symmetric relative to the plate connection.

## Engineering scope and limitations

The initial version will reproduce the spreadsheets' elastic load-sharing, deflection, bending-stress, and yield checks. New section shapes also introduce possible local buckling, torsional or flexural-torsional buckling, stiffener tripping, lateral buckling, effective-width, connection, and weld limit states.

The application must never report overall code compliance based only on the spreadsheet checks. Each relevant check will be identified as `PASS`, `FAIL`, `NOT IMPLEMENTED`, or `NOT APPLICABLE`. Engineering review remains necessary before the program is used for final structural design.

## Design approach

The application will separate:

- The interactive user interface.
- Plate and load-sharing calculations.
- Boundary-condition coefficient data.
- Stiffener-section geometry and properties.
- Validation and applicability rules.
- Automated comparison tests.

This separation will allow new boundary conditions and stiffener shapes to be added without rewriting the complete calculator.

## Validation

The two `CCCC` workbooks will provide the initial regression cases. The Python implementation must reproduce their important intermediate and final results within defined tolerances. Every added stiffener shape will also receive independent section-property tests.

The spreadsheets establish calculation parity; they do not constitute independent verification of the engineering methodology.

## Project plan

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the detailed scope, architecture, implementation phases, validation strategy, limitations, and future roadmap.

## Current phase

Phase 1 extraction of the two CCCC spreadsheets is documented in [docs/PHASE_1_CCCC_CALCULATION_SPEC.md](docs/PHASE_1_CCCC_CALCULATION_SPEC.md). Machine-readable regression values are stored in [reference/cccc_golden_cases.json](reference/cccc_golden_cases.json).

Phase 2 produced the reusable section-property engine described in [docs/PHASE_2_SECTION_ENGINE.md](docs/PHASE_2_SECTION_ENGINE.md). It supports flat bars, angles, T-sections, RHS/SHS, channels, attachment orientation, and composite action with a tributary plate strip.

Phase 3 produced the typed CCCC plate calculation engine described in [docs/PHASE_3_CALCULATION_ENGINE.md](docs/PHASE_3_CALCULATION_ENGINE.md). It supports both stiffener orientations, consumes every Phase 2 section family, validates inputs, preserves auditable intermediate values, and reproduces both CCCC workbook reference cases. Stability, connection, and combined-stress checks remain explicitly marked as not implemented.
