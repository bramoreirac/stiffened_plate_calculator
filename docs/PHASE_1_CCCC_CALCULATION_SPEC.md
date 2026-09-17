# Phase 1 CCCC Calculation Specification

## 1. Status and purpose

This document records the calculation behavior extracted from:

- `CCCC_stiffened_plate_along_long_span.xlsx`
- `CCCC_stiffened_plate_along_short_span.xlsx`

It is the implementation specification for the first Python calculation engine. It describes what the spreadsheets currently do, including assumptions and apparent inconsistencies. It does not approve or independently validate the engineering method.

Phase 1 extraction is complete when this specification and the machine-readable golden cases agree with the cached Excel results. Items in the engineering-review register must be resolved deliberately during later phases. They must not be silently changed during translation.

## 2. Model scope found in the workbooks

Both workbooks analyze a rectangular plate with:

- All four plate edges clamped (`CCCC`).
- Uniform transverse pressure.
- One set of equally spaced, parallel flat-bar stiffeners.
- A plate strip acting compositely with each stiffener.
- Full shear connection between the plate and stiffener.
- Elastic plate and beam behavior.
- Load distribution based on relative spring stiffness.
- Deflection and yield-stress checks only.

The workbooks do not contain data validation, stability checks, weld checks, effective-width checks, combined-stress checks, or code-resistance factors.

## 3. Symbols and input mapping

The input cells are identical in both workbooks.

| Symbol | Description | Cell | Unit | Long-span case | Short-span case |
|---|---|---:|---|---:|---:|
| `a` | Long plate span | `C5` | in | 72.0 | 72.875 |
| `b` | Short plate span | `C6` | in | 40.0 | 13.25 |
| `t` | Plate thickness | `C7` | in | 0.1345 | 0.1875 |
| `n` | Number of stiffeners | `C10` | count | 2 | 2 |
| `h_s` | Flat-bar projecting height | `C11` | in | 2.0 | 2.0 |
| `t_w` | Flat-bar thickness | `C12` | in | 0.25 | 0.375 |
| `E_ksi` | Elastic modulus | `C15` | ksi | 29,000 | 29,000 |
| `nu` | Poisson's ratio | `C16` | dimensionless | 0.30 | 0.30 |
| `F_y` | Yield strength | `C17` | ksi | 36.0 | 36.0 |
| `q_psf` | Uniform pressure | `C18` | psf | 100.0 | 1,300.0 |

Blue font identifies user inputs. The workbooks contain no Excel validation rules, so invalid, fractional, negative, or geometrically inconsistent values are not blocked.

## 4. Common conversions and plate properties

The following equations are common to both orientations:

```text
E = 1000 E_ksi                                      [psi]
q = q_psf / 144                                     [psi]
r_overall = a / b                                   [-]
D = E t^3 / (12 (1 - nu^2))                         [lbf in]
```

`a` is assumed to be the long span and `b` the short span. The spreadsheet does not enforce `a >= b`.

## 5. CCCC coefficient interpolation

The coefficient table is identical in both workbooks.

| Aspect ratio | Deflection coefficient `beta_w` | Moment coefficient `beta_m` |
|---:|---:|---:|
| 1.0 | 0.0138 | 0.0513 |
| 1.1 | 0.0163 | 0.0538 |
| 1.2 | 0.0188 | 0.0554 |
| 1.5 | 0.0249 | 0.0573 |
| 2.0 | 0.0284 | 0.0568 |
| 3.0 | 0.0290 | 0.0551 |
| 4.0 | 0.0291 | 0.0547 |

The spreadsheets cite Timoshenko and Woinowsky-Krieger, *Theory of Plates and Shells*, Table 35, for an all-edges-clamped plate under uniform load.

Interpolation behavior:

- For `r <= 1.0`, return the 1.0 coefficients.
- Between table points, interpolate linearly.
- For `r > 4.0`, return the 4.0 coefficients.

The function should return both coefficients from one shared interpolation routine. Tests must cover every table point, at least one point in each interval, the lower clamp, and the upper clamp.

Both workbooks calculate coefficients for the overall plate aspect ratio. Those full-plate coefficients are not referenced by any downstream formula. Only the panel coefficients affect results.

## 6. Orientation-neutral calculation model

The two spreadsheet models can be expressed using these common orientation variables:

| Variable | Meaning |
|---|---|
| `L_s` | Stiffener span |
| `p` | Stiffener spacing and assumed tributary plate width |
| `l_panel` | Long dimension of a plate subpanel |
| `b_panel` | Short dimension of a plate subpanel |
| `r_panel` | `l_panel / b_panel`, not less than 1.0 |

After those variables are assigned, the composite-section, spring, load-sharing, deflection, stress, and check equations are common.

## 7. Long-span stiffener geometry

For stiffeners running along `a`:

```text
L_s = a
p = b / (n + 1)

if n > 0:
    l_panel = a
    b_panel = p
    r_panel = max(a / p, 1.0)
else:
    l_panel = a
    b_panel = b
    r_panel = max(a / b, 1.0)
```

Workbook cell crosswalk:

| Quantity | Cell |
|---|---:|
| Overall aspect ratio | `C24` |
| Spacing `p` | `C25` |
| Plate rigidity `D` | `C26` |
| Overall coefficients | `C27:C28` |
| Panel aspect ratio | `C29` |
| Panel coefficients | `C30:C31` |

The spacing remains `b / (n + 1)` when `n = 0`, which evaluates to `b`.

## 8. Short-span stiffener geometry

For stiffeners running along `b`:

```text
L_s = b
p = a / (n + 1)
l_panel = max(b, p)
b_panel = min(b, p)
r_panel = max(l_panel / b_panel, 1.0)
```

Workbook cell crosswalk:

| Quantity | Cell |
|---|---:|
| Overall aspect ratio | `C24` |
| Spacing `p` | `C25` |
| Panel long side | `C26` |
| Panel short side | `C27` |
| Panel aspect ratio | `C28` |
| Plate rigidity `D` | `C29` |
| Overall coefficients | `C30:C31` |
| Panel coefficients | `C32:C33` |

Unlike the long-span workbook, the short-span workbook does not include a separate `n = 0` branch for panel dimensions. With `n = 0`, `p = a`, so the panel becomes the full plate when `a >= b`.

## 9. Flat-bar composite section

The spreadsheets treat a plate strip of width `p` as the stiffener flange. The flat bar projects from the bottom surface of the plate. The vertical datum is the plate top surface.

```text
A_f = p t
A_w = h_s t_w

y_f = t / 2
y_w = t + h_s / 2

y_bar = (A_f y_f + A_w y_w) / (A_f + A_w)

I_f = p t^3 / 12 + A_f (y_bar - y_f)^2
I_w = t_w h_s^3 / 12 + A_w (y_bar - y_w)^2
I_comp = I_f + I_w

EI_comp = E I_comp
y_bottom = t + h_s - y_bar
```

The full spacing `p` is used as effective plate width. No reduction is applied for shear lag, plate buckling, local buckling, or code-specific effective-width rules.

Cell ranges:

- Long-span workbook: `C32:C41`.
- Short-span workbook: `C34:C44`.

## 10. Spring stiffness and load sharing

The common equations are:

```text
if n > 0:
    k_S = n 192 EI_comp / L_s^3
else:
    k_S = 0

k_P = 384 D L_s / (5 p^4)

if n > 0:
    alpha_S = k_S / (k_S + k_P)
else:
    alpha_S = 0

alpha_P = 1 - alpha_S
q_P = alpha_P q
```

`k_S` is the combined stiffness of all `n` stiffeners. `q_P` is the pressure assigned to the plate calculation.

Cell ranges:

- Long-span workbook: `C42:C46`.
- Short-span workbook: `C45:C49`.

## 11. Result equations

### Plate response

```text
delta_plate = beta_w_panel q_P b_panel^4 / D
M_plate = beta_m_panel q_P b_panel^2
sigma_plate = 6 M_plate / t^2 / 1000               [ksi]
```

`M_plate` has units of `lbf in/in`.

### Stiffener response

The tributary pressure resultant used by the spreadsheets is:

```text
W = q p L_s                                             [lbf]
```

The response equations are:

```text
if n > 0:
    delta_S = W L_s^3 / (192 EI_comp)
    M_S = W L_s / 8
    sigma_S = M_S y_bottom / I_comp / 1000             [ksi]
else:
    delta_S = 0
    M_S = 0
    sigma_S = 0
```

The formulas use the full pressure `q`, not `alpha_S q`.

### Governing values and checks

```text
delta_max = max(delta_plate, delta_S)
delta_allowable = b / 240

deflection_pass = delta_max <= delta_allowable
plate_yield_pass = sigma_plate <= F_y
stiffener_yield_pass = True if n == 0 else sigma_S <= F_y
```

The deflection limit always uses the overall short plate span `b`, regardless of stiffener orientation.

Cell ranges:

- Long-span workbook results: `C50:C57`; checks: `C60:C62`.
- Short-span workbook results: `C53:C60`; checks: `C63:C65`.

## 12. Golden reference cases

The complete machine-readable values are stored in `reference/cccc_golden_cases.json`.

### Long-span stiffeners

| Result | Expected value | Unit |
|---|---:|---|
| Panel spacing | 13.333333333333334 | in |
| Plate rigidity | 6461.631879578756 | lbf in |
| Composite inertia | 0.6147147315168766 | in^4 |
| Stiffener load fraction | 0.9419372500990527 | dimensionless |
| Plate deflection | 0.005739060873982558 | in |
| Stiffener deflection | 0.07269982787322687 | in |
| Maximum deflection | 0.07269982787322687 | in |
| Allowable deflection | 0.16666666666666666 | in |
| Plate stress | 0.13004887202209153 | ksi |
| Stiffener stress | 17.906497952690028 | ksi |
| Checks | PASS / PASS / PASS | — |

### Short-span stiffeners

| Result | Expected value | Unit |
|---|---:|---|
| Panel spacing | 24.291666666666668 | in |
| Plate rigidity | 17505.687671703297 | lbf in |
| Composite inertia | 1.033708159456548 | in^4 |
| Stiffener load fraction | 0.9999896618459293 | dimensionless |
| Plate deflection | 0.0000044751644555682535 | in |
| Stiffener deflection | 0.001174368829162476 | in |
| Maximum deflection | 0.001174368829162476 | in |
| Allowable deflection | 0.05520833333333333 | in |
| Plate stress | 0.00015930343162699512 | ksi |
| Stiffener stress | 9.027856125156152 | ksi |
| Checks | PASS / PASS / PASS | — |

An independent Python transcription of the extracted equations reproduced these key cached workbook values with relative tolerance `1e-12` and absolute tolerance `1e-14`.

## 13. Test tolerances

Recommended automated-test rules:

- Enumerations, counts, check states, and text identifiers: exact equality.
- Input echo and coefficient table knots: exact equality where values are directly stored.
- Spreadsheet-parity calculations: `relative tolerance = 1e-10`, `absolute tolerance = 1e-12`.
- Pass/fail decisions: evaluate unrounded values, then compare the Boolean result exactly.
- User-interface display rounding must not be used in engineering calculations.

The implementation tolerance is intentionally looser than the extraction comparison so it remains stable across Python versions and harmless floating-point evaluation-order differences.

## 14. Common and orientation-specific responsibilities

### Common components

- Input model and unit validation.
- Pressure and modulus conversion.
- Plate rigidity.
- CCCC coefficient interpolation.
- Stiffener section-property interface.
- Composite plate-stiffener section assembly.
- Spring stiffness and load fractions.
- Plate and stiffener response equations.
- Result and check models.

### Orientation strategy

The orientation component should return only:

- `L_s`.
- `p`.
- `l_panel`.
- `b_panel`.
- `r_panel`.

The remaining calculation flow should be shared. This prevents separate long-span and short-span calculators from diverging.

## 15. Required input validation for Python

The Python implementation should add validation that the spreadsheets lack:

- `a > 0`, `b > 0`, and `a >= b`.
- `t > 0`.
- `n` is an integer and `n >= 0`.
- Flat-bar dimensions are positive when `n > 0`.
- `E > 0` and `F_y > 0`.
- `-1 < nu < 0.5`; a narrower application-specific range may be adopted later.
- `q >= 0` for the initial pressure-only interface.
- Denominators and composite areas are nonzero.
- Boundary condition and orientation identifiers are supported.

The no-stiffener case should remain supported because the spreadsheet formulas include it, but its interpretation and output labels must be tested explicitly.

## 16. Engineering-review register

These items were found during extraction. They must be reviewed before the program is represented as a design-level tool.

### ER-01 — Load fraction applied only to the plate response

The spring model calculates `alpha_S` and `alpha_P`. Plate response uses `q_P = alpha_P q`, but stiffener response uses the full tributary load `W = q p L_s`, not `alpha_S q p L_s`.

Implementation rule: reproduce the spreadsheet for the parity baseline. Any corrected or alternative formulation must be a separately identified model version with new tests.

### ER-02 — Uniform pressure converted to an equivalent point-load beam model

The stiffener stiffness and response equations use the fixed-fixed center-point-load constants `192` and `8`. The applied `W` is the total pressure over the full tributary area. The workbooks therefore treat the uniform tributary load as an equivalent concentrated load at midspan for stiffener response.

Implementation rule: preserve this behavior for parity and label the assumption. Review whether a true uniformly distributed line-load model is required.

### ER-03 — Maximum of local and stiffener deflections

The governing displacement is `max(delta_plate, delta_S)`. The workbooks do not add local panel deformation to supporting-stiffener deformation.

Implementation rule: preserve for parity. Review whether the physical displacement at a plate point should include both components or use another compatibility model.

### ER-04 — Full tributary plate width used in the composite section

The effective flange width is always the full spacing `p`. No effective-width reduction is made for local buckling, shear lag, boundary effects, or a governing design standard.

### ER-05 — Internal stiffener lines treated using clamped panel coefficients

The subpanel calculations use the all-edges-clamped coefficient table. The rotational restraint actually supplied by the stiffener-to-plate assembly is not calculated.

### ER-06 — Separate stresses are not combined

The local plate bending stress and composite stiffener bending stress are checked separately against yield. The model does not combine local and global stress at common fibres and does not include membrane, shear, residual, or weld stresses.

### ER-07 — Only the bottom composite fibre is checked

The stiffener bending check uses `y_bottom`. It does not check the plate-side extreme fibre of the composite section.

### ER-08 — Overall coefficients are unused

The overall-plate `beta_w` and `beta_m` values are calculated and displayed but do not influence any result. They should either remain explicitly informational or be removed from the computational result model after review.

### ER-09 — Stability and connection limit states are absent

The workbooks contain no local buckling, tripping, lateral, torsional, flexural-torsional, global buckling, weld, fatigue, corrosion, or connection-strength checks.

## 17. Stability applicability by planned stiffener family

This table defines initial status categories, not completed design checks.

| Shape | Local element stability | Tripping/torsional stability | Overall flexural stability | Initial implementation status |
|---|---|---|---|---|
| Flat bar | Required when compression/slenderness is relevant | High priority | May apply | Not implemented |
| Angle | Required for outstanding legs | High priority; unsymmetrical open section | May apply | Not implemented |
| T-section | Required for flange and web | High priority | May apply | Not implemented |
| Channel/U | Required for flange and web | High priority; eccentric shear center | May apply | Not implemented |
| RHS/SHS | Required for tube walls | Lower torsional concern than open sections, but not automatically exempt | May apply | Not implemented |

Until these checks are implemented, the application must distinguish elastic/yield results from complete section adequacy.

## 18. Phase 1 conclusion

The two CCCC spreadsheets can be consolidated into one calculation path. The only required orientation-specific step is the assignment of stiffener span and panel geometry. All remaining equations can be shared.

The next implementation step is the section-property engine, beginning with the flat-bar composite section needed for exact spreadsheet parity and then extending through the common section interface to angle, T, RHS/SHS, and channel shapes.
