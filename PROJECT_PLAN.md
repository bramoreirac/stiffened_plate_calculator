# Stiffened Plate Calculator — Project Plan

## 1. Project purpose

Develop an interactive Python application for evaluating rectangular stiffened plates under uniform pressure. The application will reproduce the engineering calculations currently implemented in the Excel workbooks while providing a single, consistent interface for selecting plate geometry, stiffener arrangement, material properties, loading, and support conditions.

The first working version will support plates with all four edges clamped (`CCCC`). The design must allow additional support conditions, including `SSSS` and `CSCS`, to be added without rebuilding the application or duplicating the common calculation logic.

## 2. Initial scope

### Included in the first version

- Four-edge clamped plates (`CCCC`).
- Stiffeners running along the plate's long span.
- Stiffeners running along the plate's short span.
- Initial stiffener-section library:
  - Flat bar.
  - Angle, including equal-leg and unequal-leg configurations.
  - T-section.
  - Rectangular hollow section (RHS), with square hollow section (SHS) treated as the equal-sided case.
  - Channel/U-section.
- Imperial-unit inputs matching the source workbooks.
- Interactive selection or entry of:
  - Long and short plate spans.
  - Plate thickness.
  - Number of stiffeners.
  - Stiffener shape and the dimensions required to define that shape.
  - Elastic modulus.
  - Poisson's ratio.
  - Yield strength.
  - Uniform pressure.
- Automatic calculation of:
  - Panel dimensions and aspect ratios.
  - Plate rigidity.
  - Plate coefficients and interpolation.
  - Composite plate-stiffener section properties.
  - Plate and stiffener spring stiffnesses.
  - Load-sharing fractions.
  - Plate and stiffener deflections.
  - Plate and stiffener bending stresses.
  - Serviceability and yield checks.
- Clear display of inputs, intermediate calculations, results, and pass/fail checks.
- Automated tests against the two existing `CCCC` Excel workbooks.

### Deferred from the first version

- `SSSS`, `CSCS`, and other boundary-condition scenarios.
- The separate grillage model.
- Bulb-flat stiffeners used in marine and offshore structures.
- Hat sections and open or closed trapezoidal ribs used in orthotropic decks and lightweight panels.
- Arbitrary user-defined or built-up stiffener sections.
- Metric-unit inputs and output conversion.
- Formal calculation-report generation.
- Optimization of plate thickness or stiffener size.
- Multiple-load combinations.
- Local buckling, lateral-torsional buckling, fatigue, connection design, and other limit states not included in the source spreadsheets.

These items may be added after the CCCC calculations have been reproduced and validated.

## 3. Source workbooks

The initial implementation will use these workbooks as calculation references and validation cases:

- `CCCC_stiffened_plate_along_long_span.xlsx`
- `CCCC_stiffened_plate_along_short_span.xlsx`

The remaining workbooks will inform later extensions:

- `SSSS_stiffened_plate_along_long_span.xlsx`
- `SSSS_stiffened_plate_along_short_span.xlsx`
- `CSCS_stiffened_plate_along_long_span.xlsx`
- `CSCS_stiffened_plate_along_short_span.xlsx`
- `SSSS_grillage_ss_plate.xlsx`

The Excel files remain the initial reference implementations until the Python results have been independently reviewed and accepted.

## 4. Proposed application structure

```text
stiffened_plate_calculator/
├── app.py
├── README.md
├── requirements.txt
├── src/
│   └── stiffened_plate/
│       ├── __init__.py
│       ├── models.py
│       ├── calculations.py
│       ├── coefficients.py
│       ├── boundary_conditions.py
│       ├── validation.py
│       └── units.py
├── tests/
│   ├── test_cccc_long_span.py
│   ├── test_cccc_short_span.py
│   ├── test_coefficients.py
│   └── test_validation.py
└── PROJECT_PLAN.md
```

The exact structure may be adjusted during implementation, but the user interface, calculation engine, coefficient data, validation rules, and tests should remain separated.

## 5. Architecture principles

### Separate the interface from the engineering calculations

The user interface must collect inputs and present results, but it must not contain the main engineering equations. The calculation engine should be usable independently from the interface and directly callable by automated tests.

### Represent scenarios explicitly

The following must be explicit calculation inputs:

- Boundary condition, initially `CCCC`.
- Stiffener orientation, either long-span or short-span.

This avoids embedding a single scenario throughout the code and prepares the application for `SSSS`, `CSCS`, and future cases.

### Share common calculations

Geometry, material conversions, plate rigidity, composite-section properties, load sharing, and result formatting should be implemented once wherever the underlying equations are common.

Scenario-specific behavior should be isolated in small, well-defined components, such as:

- Coefficient selection and interpolation.
- Definition of the stiffener span.
- Definition of panel dimensions and tributary width.
- Boundary-condition-specific response equations.

### Represent stiffener geometry independently

Each stiffener shape should supply its own geometric properties through a common section interface. The plate-response calculations should consume those properties without containing shape-specific dimension formulas.

The section model should provide, as applicable:

- Gross area.
- Centroid relative to the plate surface and weld line.
- Second moment of area about the plate-bending axis.
- Extreme-fibre distances and elastic section moduli.
- Torsional constant and other stability properties when the relevant checks are implemented.
- A clear definition of which face, leg, web, or wall is attached to the plate.

Square hollow sections should not require a separate calculation engine; they are rectangular hollow sections with equal outside dimensions. Angle orientation and channel orientation must be explicit because mirroring or rotating an unsymmetrical section can change eccentricity and stability behavior.

### Preserve intermediate results

The calculation engine should return named intermediate values as well as final results. This makes the Python output auditable and allows direct comparison with individual spreadsheet cells.

### Avoid hidden assumptions

Units, formulas, coefficient limits, applicability conditions, and pass/fail criteria must be visible in the code and interface. Invalid inputs should produce a clear validation message rather than a plausible-looking result.

## 6. Proposed data model

### Calculation inputs

A structured input object should contain:

- Boundary condition.
- Stiffener orientation.
- Long span and short span.
- Plate thickness.
- Number of stiffeners.
- Stiffener shape identifier.
- Shape-specific dimensions, including the appropriate combination of height, width, web thickness, flange thickness, leg sizes, or tube wall thickness.
- Section orientation and attached face where applicable.
- Elastic modulus.
- Poisson's ratio.
- Yield strength.
- Uniform pressure.
- Deflection-limit denominator, initially 240.

### Calculation results

A structured result object should contain:

- Normalized input values and units.
- Panel geometry.
- Plate coefficients.
- Composite-section properties.
- Bare-stiffener section properties.
- Spring stiffnesses and load fractions.
- Plate and stiffener deflections.
- Governing deflection and allowable deflection.
- Plate and stiffener stresses.
- Utilization ratios.
- Individual pass/fail checks.
- Warnings and applicability notes.
- Status of each relevant limit-state check, including whether it is implemented, not applicable, or outside the current model scope.

## 7. Stiffener-section scope

### Initial section families

The first section library will include the following five families:

1. **Flat bar** — defined by projecting height and thickness.
2. **Angle** — defined by two leg lengths and thickness, with equal-leg and unequal-leg cases supported.
3. **T-section** — defined by web height and thickness plus flange width and thickness.
4. **Rectangular hollow section** — defined by outside height, outside width, and wall thickness. A square hollow section is the special case in which outside height equals outside width.
5. **Channel/U-section** — defined by web and flange dimensions, together with its orientation relative to the plate.

Section-property calculations should be formula-driven from dimensions in the first implementation. A later enhancement may add catalogs of standard rolled or manufactured sections.

### Future section families

- Bulb flats for marine and offshore work.
- Hat sections.
- Open or closed trapezoidal ribs.
- Custom welded and built-up sections.

These shapes must be addable through the common section interface without changing the plate-calculation workflow.

### Engineering limitations

Adding a new cross-section requires more than substituting a different second moment of area. Depending on the shape and loading, relevant behavior can include:

- Local buckling of webs, legs, flanges, and tube walls.
- Torsional or flexural-torsional buckling.
- Stiffener tripping about the connection to the plate.
- Lateral or global stiffener buckling.
- Eccentricity between the centroid, shear center, weld line, and applied load.
- Effective-width changes caused by plate buckling.
- Weld strength, weld continuity, and load transfer.
- Corrosion deductions and fabrication tolerances.

The initial CCCC implementation will reproduce the source spreadsheets' elastic load-sharing, deflection, bending-stress, and yield checks. It must not describe a section as fully code-compliant when the applicable local or global stability checks have not been implemented. The interface should identify each check as `PASS`, `FAIL`, `NOT IMPLEMENTED`, or `NOT APPLICABLE` as appropriate.

## 8. Coefficient strategy

The Timoshenko plate coefficients should be stored as data associated with a boundary condition rather than repeated inside long nested formulas.

For the CCCC case, the application will initially reproduce the coefficient table and linear interpolation behavior used by the spreadsheets. The implementation should:

- Accept an aspect ratio greater than or equal to 1.0.
- Interpolate between tabulated values.
- Apply the same limiting behavior as the source workbooks beyond the final tabulated aspect ratio.
- Return both the deflection and moment coefficients.
- Be covered by tests at table points, between table points, and at the limits.

Additional coefficient sets can later be registered for `SSSS`, `CSCS`, or other edge conditions.

## 9. User-interface plan

The initial interface will be a local Streamlit application opened in a web browser.

Suggested sections:

1. **Analysis scenario**
   - Boundary condition.
   - Stiffener orientation.
2. **Plate geometry**
   - Long span, short span, and thickness.
3. **Stiffener geometry**
   - Quantity and section family.
   - Shape-specific dimensions.
   - Section orientation and attached face where required.
4. **Material and loading**
   - Elastic modulus, Poisson's ratio, yield strength, and pressure.
5. **Results**
   - Governing deflection.
   - Plate stress.
   - Stiffener stress.
   - Utilization ratios and pass/fail checks.
   - A separate indication of checks that are not yet implemented.
6. **Calculation details**
   - Expandable table of intermediate values, formulas or descriptions, values, and units.
7. **Warnings and assumptions**
   - Applicability limits and invalid-input messages.

For plate thickness and stiffener dimensions, the interface may offer standard-size selections plus a custom-value option. The first implementation should prioritize accurate section-property calculations over an extensive section database.

## 10. Validation strategy

Validation will be performed at several levels.

### Spreadsheet parity

The default input cases from both CCCC workbooks will become automated regression tests. The Python results should match the workbook results for all important intermediate and final values within defined numerical tolerances.

### Formula-level tests

Tests will separately verify:

- Unit conversions.
- Panel geometry for each orientation.
- Coefficient interpolation.
- Plate rigidity.
- Composite centroid and moment of inertia.
- Section properties for every supported stiffener family.
- Spring stiffness and load sharing.
- Deflection and stress calculations.
- Pass/fail boundaries.

### Input-validation tests

Tests will reject or flag cases such as:

- Non-positive dimensions or material properties.
- Poisson's ratios outside the accepted range.
- Negative or non-integer stiffener counts.
- Invalid orientation or boundary-condition identifiers.
- Geometries that produce undefined calculations.
- Impossible hollow-section dimensions or non-positive clear dimensions.
- Slender section elements that fall outside the implemented calculation scope.
- Missing or invalid attached-face and orientation selections.

### Engineering review

Matching the spreadsheets confirms faithful translation, but it does not independently prove that the underlying engineering model is correct or applicable to every plate. Before production design use, the formulas, assumptions, coefficient sources, boundary conditions, and limit states should receive an engineering review.

## 11. Implementation phases

### Phase 1 — Extract and document CCCC logic — Complete

- Map every input, formula, output, unit, and check in both CCCC workbooks.
- Identify calculations common to both orientations.
- Identify orientation-specific geometry and equations.
- Establish expected results and numerical tolerances.
- Document which additional limit states are required for each stiffener family.

Deliverables:

- `docs/PHASE_1_CCCC_CALCULATION_SPEC.md`
- `reference/cccc_golden_cases.json`

### Phase 2 — Build the section-property engine — Complete

- Define the common stiffener-section interface.
- Implement flat-bar properties and confirm parity with the spreadsheets.
- Implement angle, T-section, RHS/SHS, and channel properties.
- Test centroids, moments of inertia, extreme-fibre distances, and section moduli against independent hand calculations or trusted section data.
- Represent section attachment and orientation explicitly.

Deliverables:

- `src/stiffened_plate/sections.py`
- `tests/test_sections.py`
- `docs/PHASE_2_SECTION_ENGINE.md`

### Phase 3 — Build the plate calculation engine — Complete

- Create typed input and result models.
- Implement CCCC coefficient interpolation.
- Implement common calculations.
- Implement long-span and short-span orientation logic.
- Add validation and clear calculation exceptions.

Deliverables:

- `src/stiffened_plate/models.py`
- `src/stiffened_plate/coefficients.py`
- `src/stiffened_plate/calculations.py`
- `tests/test_coefficients.py`
- `tests/test_cccc_calculations.py`
- `tests/test_validation.py`
- `docs/PHASE_3_CALCULATION_ENGINE.md`

### Phase 4 — Add automated verification — Complete

- Encode the two workbook cases as regression tests.
- Add coefficient, formula, validation, and boundary tests.
- Resolve every unexplained difference from the spreadsheets.
- Add independent section-property test cases for all five initial section families.

Deliverables:

- `tests/test_cccc_calculations.py`
- `tests/test_coefficients.py`
- `tests/test_formula_verification.py`
- `tests/test_check_boundaries.py`
- `tests/test_validation.py`
- `tests/test_sections.py`
- `docs/PHASE_4_VERIFICATION.md`

### Phase 5 — Build the interactive interface — Complete

- Create the Streamlit input form.
- Add results, utilization ratios, and pass/fail presentation.
- Add intermediate-calculation and assumption views.
- Test realistic input changes and invalid entries.
- Show which limit-state checks are implemented for the selected section.

Deliverables:

- `app.py`
- `src/stiffened_plate/presentation.py`
- `src/stiffened_plate/visualization.py`
- `tests/test_presentation.py`
- `tests/test_streamlit_app.py`
- `tests/test_visualization.py`
- `docs/PHASE_5_INTERFACE.md`
- Streamlit and Plotly dependency declarations in `pyproject.toml`

### Phase 6 — Review the CCCC prototype

- Compare the application and workbooks side by side.
- Review usability, terminology, units, precision, and warnings.
- Record any agreed corrections to the spreadsheet methodology.
- Establish the CCCC version as the baseline for expansion.
- Confirm that results cannot be mistaken for a complete code-compliance assessment when stability or connection checks remain outside scope.

### Phase 7 — Expand to other scenarios

- Map and implement `SSSS` calculations.
- Map and implement `CSCS` calculations.
- Decide whether the grillage workbook belongs in the same calculation engine or a separate analysis mode.
- Add scenario-specific tests and interface options.

### Phase 8 — Optional enhancements

- Metric units.
- Standard plate and stiffener catalogs.
- Bulb-flat, hat, trapezoidal-rib, and custom-section support.
- Case saving and loading.
- Side-by-side alternatives.
- PDF or Excel calculation reports.
- Design optimization.
- Packaging or deployment for other users.

## 12. Initial completion criteria

The CCCC prototype will be considered complete when:

- Both stiffener orientations are available in one application.
- Flat bars, angles, T-sections, RHS/SHS, and channels are supported through a common section model.
- All required inputs can be changed interactively.
- Intermediate and final calculations update correctly.
- The two source-workbook cases pass automated comparison tests.
- No unexplained differences remain between Python and Excel results.
- Invalid inputs receive useful messages.
- Assumptions and units are clearly displayed.
- Unimplemented stability and connection checks are clearly distinguished from passing checks.
- The calculation engine can accept additional boundary-condition implementations without major restructuring.
- The section engine can accept additional stiffener families without changes to the common plate-response calculations.

## 13. Key decisions to confirm during development

- Whether plate and stiffener dimensions should initially be free-entry values, standard-size selections, or both.
- Which orientations and attachment configurations should be available for angles and channels in the first release.
- Required display precision and numerical comparison tolerances.
- Whether the workbook's deflection limit of `b/240` should be fixed or user-selectable.
- Whether zero stiffeners should be supported as an unstiffened-plate case.
- Whether calculation reports are needed before adding SSSS and CSCS scenarios.
- Which engineering standard or internal design criteria should govern future checks beyond those already present in the workbooks.
- Which local-buckling, torsional-buckling, tripping, weld, and effective-width checks belong in the first design-level release.

## 14. Technical references for the expanded section scope

- Federal Highway Administration, *Optimization of Rib-to-Deck Welds for Steel Orthotropic Bridge Decks*: https://www.fhwa.dot.gov/publications/research/infrastructure/structures/bridge/17020/001.cfm
- National Steel Bridge Alliance/AISC, *Steel Bridge Design Handbook — Structural Behavior of Steel*: https://www.aisc.org/media/hf4jbmik/b904_sbdh_chapter4.pdf
- American Bureau of Shipping, *Rules for Building and Classing Offshore Support Vessels, Part 3*: https://ww2.eagle.org/content/dam/eagle/rules-and-guides/archives/conventional_ocean_service/180-offshoresupportvessels/osv-part-3-july-19.pdf
