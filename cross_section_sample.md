# Cross-section side-view samples

These sketches define the intended schematic appearance of one representative
stiffener attached to the plate. They are the visual reference for the
interactive side-view diagram.

General conventions:

- The plate is horizontal and the stiffener projects above it.
- Only one stiffener is shown, regardless of the stiffener count.
- Dimensions in the application will control the proportions of the rendered
  geometry; the ASCII samples below are not to scale.
- All initial shapes use the same sharp-corner idealization as the section
  property engine. Rolled fillets and manufactured RHS corner radii are not
  shown.
- The section is shown as physically attached to the plate surface. It does not
  penetrate the plate.

## Flat bar

The narrow edge of the flat bar is attached to the plate.

```text
                 +----+
                 |    |
                 |    |
                 |    |  <-- flat bar
                 |    |
                 |    |
-----------------+----+-----------------  plate top
========================================  plate
```

## Angle

The attached leg lies flat against the plate. The outstanding leg projects
normal to the plate. Handedness controls the side toward which the attached leg
projects.

### Right-handed angle

```text
                 +----+
                 |    |
                 |    |  <-- outstanding leg
                 |    |
                 |    +----------+
                 +---------------+  <-- attached leg projects right
-----------------+---------------+---------  plate top
==========================================  plate
```

### Left-handed angle

```text
                           +----+
                           |    |
                           |    |  <-- outstanding leg
                           |    |
                 +---------+    |
                 +--------------+  <-- attached leg projects left
-----------------+--------------+---------  plate top
=========================================  plate
```

## T-section

Two attachment configurations are supported.

### Web-end attachment

The free end of the web is attached to the plate and the flange is at the far
edge of the stiffener.

```text
             +----------------+
             |     flange     |
             +-------+--------+
                     |  |
                     |  |  <-- web
                     |  |
                     |  |
---------------------+--+---------------------  plate top
================================================  plate
```

### Flange-face attachment

The flange face lies against the plate and the web projects from the flange.

```text
                     +--+
                     |  |
                     |  |  <-- web
                     |  |
             +-------+--+-------+
             |      flange      |
-------------+------------------+-------------  plate top
================================================  plate
```

## Rectangular or square hollow section (RHS/SHS)

The selected outside face lies flat against the plate. The hollow interior is
shown explicitly. SHS uses the same view with equal outside dimensions.

### Side A attached

Side A is parallel to the plate and side B is the projecting depth.

```text
             <------ side A ------>
             +--------------------+  ^
             |  +--------------+  |  |
             |  |              |  |  | side B
             |  |    hollow    |  |  |
             |  +--------------+  |  |
-------------+--------------------+--v----------  plate top
================================================  plate
```

### Side B attached

The section is rotated 90 degrees: side B is parallel to the plate and side A
is the projecting depth.

```text
             <--- side B --->
             +--------------+  ^
             |  +--------+  |  |
             |  |        |  |  |
             |  | hollow |  |  | side A
             |  |        |  |  |
             |  +--------+  |  |
-------------+--------------+--v---------------  plate top
================================================  plate
```

## Channel / U-section

Two attachment configurations are supported. Neither configuration requires a
left- or right-handed selection.

### Web-face attachment

The back of the web lies against the plate. Both flanges project normally,
forming a U-shaped side view.

```text
             +----+              +----+
             |    |              |    |
             |    |              |    |  <-- flanges
             |    |              |    |
             +----+--------------+----+
             |       web face         |
-------------+------------------------+---------  plate top
================================================  plate
```

### Flange-face attachment

Both flange end faces join the plate. The flanges project normally from the
plate and the channel web connects them at the far edge of the stiffener.

```text
             +------------------------+
             |          web           |
             +----+--------------+----+
             |    |              |    |
             |    |              |    |  <-- flanges
             |    |              |    |
-------------+----+--------------+----+---------  plate top
                  ^              ^
                  both flange end faces attached
================================================  plate
```

## Rendering requirements derived from these samples

The interactive side view should:

- Draw the plate and section from the same rectangle components used by the
  section-property engine.
- Reflect the selected dimensions, attachment face, rotation, and handedness
  where applicable. Handedness remains applicable to angles only.
- Do not request handedness for channels. Channel web-face and flange-face
  attachment are both symmetric in the intended side view.
- For channel flange-face attachment, place both flange end faces against the
  plate; do not place one complete flange flat against the plate.
- Keep equal horizontal and vertical plotting scales so section proportions are
  meaningful.
- Center the representative stiffener relative to the displayed plate strip
  while retaining any real section eccentricity.
- Label the plate thickness and the principal section dimensions.
- Show the hollow region for RHS/SHS.
- Continue to show invalid geometry as an input error rather than drawing a
  plausible-looking section.

## Implementation alignment

The section-property engine, application controls, composite calculations, and
side-view renderer use these same attachment conventions. Channel handedness
has been removed, and channel flange-face attachment means that both flange end
faces connect to the plate.
