# Phase 2 Section-Property Engine

## 1. Status

Phase 2 is complete. The project now has a dependency-free Python section-property engine for:

- Flat bars.
- Equal-leg and unequal-leg angles.
- T-sections.
- Rectangular hollow sections, including square hollow sections.
- Channels/U-sections.
- A tributary plate strip acting compositely with any supported stiffener.

The implementation is in `src/stiffened_plate/sections.py`. Automated tests are in `tests/test_sections.py`.

## 2. Coordinate convention

- The plate lies parallel to the global `x` axis.
- The stiffener projects in the positive global `y` direction.
- A bare stiffener's attachment plane is `y = 0`.
- In a composite section, the plate top is `y = 0` and the plate bottom is `y = plate_thickness`.
- The stiffener geometry is translated so its attachment plane coincides with the plate bottom.
- The effective plate strip is centered on the bare-stiffener centroidal
  placement line at `x = 0`.
- Before composite assembly, stiffener components are translated horizontally
  by `-centroid_x`. This is zero for symmetric shapes and aligns an
  unsymmetrical angle's calculated centroid with the plate-strip centerline.

This convention matches the vertical datum used by the CCCC workbooks: composite centroid is measured from the plate top surface.

## 3. Calculation method

Each shape is decomposed into non-overlapping rectangles. The common property routine calculates:

- Gross area.
- Centroid coordinates.
- `Ix` and `Iy` about centroidal axes.
- Product of inertia `Ixy`.
- Overall width and depth.
- Distances to top, bottom, left, and right extreme fibres.
- Elastic section moduli for all four extreme fibres.
- Major and minor principal moments of inertia.
- Principal-axis angle.

The parallel-axis theorem is applied once in the common routine. Shape classes define geometry only; they do not duplicate centroid or inertia calculations.

## 4. Shape definitions

### Flat bar

Inputs:

- Projecting height.
- Thickness.

The narrow edge is attached to the plate. This is the shape used by the source spreadsheets.

### Angle

Inputs:

- Attached-leg length parallel to the plate.
- Outstanding-leg length normal to the plate.
- Common leg thickness.
- Left or right handedness.

The attached and outstanding dimensions may differ, so both equal-leg and unequal-leg angles are supported. Mirroring changes the sign of the horizontal centroid and `Ixy` but preserves area, `Ix`, and `Iy`.

### T-section

Inputs:

- Overall depth.
- Web thickness.
- Flange width.
- Flange thickness.
- Attachment by the web end or flange face.

Web-end attachment places the flange away from the plate. Flange-face attachment places the flange against the plate.

### RHS/SHS

Inputs:

- Side A.
- Side B.
- Wall thickness.
- Side A or side B attached to the plate.

The attached side is parallel to the plate. Selecting the other side rotates a non-square RHS by 90 degrees. Equal values for side A and side B identify an SHS automatically.

### Channel/U-section

Inputs:

- Overall channel depth.
- Flange width.
- Web thickness.
- Flange thickness.
- Attachment by both flange end faces or by the back of the web.

Flange-face attachment places both flange end faces against the plate, with the web connecting them at the far edge. Web-face attachment places the back of the web against the plate and both flanges project away from it. Both configurations are symmetric in the side view, so channel handedness is not required.

## 5. Composite section

`CompositeSection` accepts:

- Effective plate width.
- Plate thickness.
- Any object implementing the common stiffener-section interface.

The initial model assumes full composite action and uses the supplied plate width without an effective-width reduction. These are spreadsheet-parity assumptions, not general code-compliance conclusions.

Example:

```python
from stiffened_plate import CompositeSection, FlatBarSection

section = CompositeSection(
    plate_width=13.333333333333334,
    plate_thickness=0.1345,
    stiffener=FlatBarSection(height=2.0, thickness=0.25),
)

properties = section.geometry().properties
print(properties.centroid_y)
print(properties.ix)
print(properties.sx_bottom)
```

## 6. Validation

The engine rejects:

- Zero, negative, non-finite dimensions.
- Angle legs that do not exceed their thickness.
- T-sections whose depth does not exceed flange thickness.
- T flange widths smaller than web thickness.
- Hollow sections without positive internal clear dimensions.
- Channels whose depth does not accommodate two flanges.
- Channels whose flange width does not exceed web thickness.
- Composite sections with non-positive plate dimensions.

## 7. Verification completed

The automated suite verifies:

- Basic rectangular flat-bar properties.
- Composite flat-bar properties against both CCCC workbook golden cases.
- Angle area, centroid, `Ix`, `Iy`, `Ixy`, handedness mirroring, and composite
  alignment on the bare-stiffener centroid.
- T-section area, centroid, inertias, and attachment reversal.
- RHS properties using an independent outer-rectangle-minus-inner-rectangle solution.
- RHS 90-degree rotation and SHS identification.
- Channel properties for flange-face and web-face attachment.
- Invalid-geometry handling.

All tests use only the Python standard library. They run with:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

## 8. Current limitations

- Shapes use sharp corners.
- Rolled angle, T, and channel fillets are excluded.
- Manufactured RHS/SHS corner radii and thickness variation are excluded.
- Catalog section properties are not yet supported.
- Torsional constant, warping constant, shear-center location, plastic modulus, and effective properties are not yet calculated.
- Local, torsional, flexural-torsional, tripping, lateral, and global stability checks are not implemented.
- Weld geometry and connection stiffness are not modeled.

The interfaces leave room for these properties to be added without changing the plate calculation API.

## 9. Phase 3 handoff

The plate calculation engine can now consume `SectionProperties` instead of flat-bar dimensions. Phase 3 should:

- Define typed plate-analysis inputs and results.
- Implement the shared CCCC coefficient interpolator.
- Implement the orientation strategy from the Phase 1 specification.
- Assemble the selected stiffener with its tributary plate strip.
- Reproduce both CCCC golden cases through the full calculation path.
- Carry explicit `NOT IMPLEMENTED` states for stability and connection checks.
