# Phase 5 Interactive Interface

## Status

Phase 5 is complete. `app.py` provides a local Streamlit interface over the
verified CCCC calculation engine. The interface contains no engineering
equations; it builds typed inputs, calls `analyze_cccc`, and presents the
returned results.

## Installation and launch

From the project directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m streamlit run app.py
```

Streamlit opens the calculator in the default browser. Stop the local server
with `Ctrl+C` in the PowerShell window.

The project currently requires Python 3.11 or newer, Streamlit 1.64 or a
compatible later 1.x release, and Plotly 6.x, as declared in `pyproject.toml`.

## Input workflow

Inputs are arranged in expandable sidebar groups and recalculate immediately:

1. **Plate geometry**
   - Long span.
   - Short span.
   - Plate thickness.
2. **Stiffeners**
   - Long-span or short-span direction.
   - Number of equally spaced stiffeners.
   - Section family and its dimensions.
   - Attachment face and handedness where applicable.
3. **Material, loading, and criterion**
   - Elastic modulus.
   - Poisson's ratio.
   - Yield strength.
   - Uniform pressure.
   - Deflection-limit denominator.

The supported section choices are:

- Flat bar.
- Equal-leg or unequal-leg angle.
- T-section with web-end or flange-face attachment.
- RHS/SHS with either outside side attached.
- Channel/U-section with flange-face or web-face attachment and handedness
  where relevant.

When the stiffener count is zero, section inputs are removed and the engine
runs the explicitly supported unstiffened case.

## Result views

### Summary

- A qualified implemented-check result. The application never presents this
  as overall structural-code compliance.
- Governing and allowable deflections.
- Plate and stiffener elastic bending stresses.
- An interactive front view showing the plate dimensions and equally spaced
  stiffener centerlines in the selected orientation.
- A table containing every check, status, demand, limit, unit, utilization,
  and note.
- Individual visible messages for failed implemented checks.

### Calculation details

Expandable tables present:

- Unit conversions and plate rigidity.
- Overall and panel CCCC coefficients.
- Panel geometry and stiffener spacing.
- Bare and composite section properties.
- Spring stiffness and load fractions.
- Plate and stiffener response values.

Displayed values are rounded only for readability. The engine evaluates checks
using full-precision values.

### Assumptions and limitations

- Case-specific warnings, including nonzero product inertia for
  unsymmetrical sections.
- The assumptions returned by the versioned calculation model.
- A prominent list of stability, effective-width, connection, combined-stress,
  and other checks that are not implemented.

## Input errors

Relational geometry errors that cannot be prevented by a single numeric input
limit—for example, an RHS wall thickness that leaves no clear interior—are
caught by the calculation and section engines. The interface displays the
message without producing results for the invalid case.

The long span must remain greater than or equal to the short span. The names
refer to geometric ordering, not merely user labels.

## Presentation layer

`src/stiffened_plate/presentation.py` converts typed results into display-only
tables and formatting. Keeping this logic outside `app.py` makes it testable
without a browser and prevents display rounding from feeding back into the
engineering calculations.

## Interface verification

The complete installed-environment suite contains 59 passing tests. Five use
Streamlit's native application test harness to verify:

- The default calculator renders the summary, detail tabs, and incomplete
  limit states.
- A large pressure change produces a visible failed-check result.
- Zero stiffeners remove the section requirement and still render results.
- Flat bar, angle, T-section, RHS/SHS, and channel selections all render and
  execute without application exceptions.
- The front view renders and updates when the stiffener direction and count
  change.

Five visualization tests independently verify long-span and short-span line
orientation, equal spacing, the zero-stiffener case, invalid inputs, plate
dimensions, dimension annotations, and equal-axis scaling.

Six additional presentation tests verify table contents, number formatting,
the implemented-check summary predicate, the unstiffened result layout, and
the application entry point.

Run all tests after installing the project:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s tests -v
```

The native interface tests skip automatically in calculation-only environments
where Streamlit has not been installed.

## Current interface limits

- CCCC boundary conditions only.
- Imperial units only.
- No standard section or plate catalog yet; dimensions are free-entry values.
- No saved cases, comparison mode, optimization, or report export.
- The front view is implemented; the representative plate-and-stiffener side
  cross-section remains a future interface enhancement.
- No SSSS, CSCS, or grillage selector until their calculation models have been
  extracted and verified.

These are interface limitations in addition to the engineering limitations
documented in the Phase 3 and Phase 4 reports.
