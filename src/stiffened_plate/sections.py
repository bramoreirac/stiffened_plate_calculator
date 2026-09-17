"""Geometric properties for supported stiffener cross-sections.

Coordinate convention
---------------------
The plate lies in the x direction and the stiffener projects in positive y.
Every bare stiffener has its attachment plane at y = 0. For a composite
plate-stiffener section, the plate top is y = 0, the plate bottom is y = t,
and the stiffener is translated so its attachment plane is at y = t.

Shapes are assembled from non-overlapping sharp-corner rectangles. Rolled
fillets and RHS corner radii are intentionally excluded from the first model.
They can later be represented by catalog properties or a polygon-based engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import atan2, degrees, isfinite, sqrt
from typing import Protocol


def _require_positive(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite value greater than zero")


class Handedness(str, Enum):
    """Side on which an unsymmetrical section projects from its web."""

    LEFT = "left"
    RIGHT = "right"


class TeeAttachment(str, Enum):
    """T-section face connected to the plate."""

    WEB_END = "web_end"
    FLANGE_FACE = "flange_face"


class RhsAttachment(str, Enum):
    """RHS side placed against the plate.

    ``SIDE_A`` places side A parallel to the plate and side B normal to it.
    ``SIDE_B`` rotates the section 90 degrees.
    """

    SIDE_A = "side_a"
    SIDE_B = "side_b"


class ChannelAttachment(str, Enum):
    """Channel face connected to the plate."""

    FLANGE_FACE = "flange_face"
    WEB_FACE = "web_face"


@dataclass(frozen=True, slots=True)
class Rectangle:
    """A non-overlapping rectangular component of a section."""

    width: float
    height: float
    x: float = 0.0
    y: float = 0.0
    label: str = "component"

    def __post_init__(self) -> None:
        _require_positive("rectangle width", self.width)
        _require_positive("rectangle height", self.height)
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("rectangle coordinates must be finite")

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def centroid_x(self) -> float:
        return self.x + self.width / 2

    @property
    def centroid_y(self) -> float:
        return self.y + self.height / 2

    @property
    def x_max(self) -> float:
        return self.x + self.width

    @property
    def y_max(self) -> float:
        return self.y + self.height

    def translated(self, dx: float = 0.0, dy: float = 0.0) -> "Rectangle":
        return Rectangle(
            width=self.width,
            height=self.height,
            x=self.x + dx,
            y=self.y + dy,
            label=self.label,
        )

    def mirrored_x(self) -> "Rectangle":
        """Mirror the rectangle about x = 0."""

        return Rectangle(
            width=self.width,
            height=self.height,
            x=-self.x_max,
            y=self.y,
            label=self.label,
        )


@dataclass(frozen=True, slots=True)
class SectionProperties:
    """Gross geometric properties about centroidal x and y axes."""

    area: float
    centroid_x: float
    centroid_y: float
    ix: float
    iy: float
    ixy: float
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    torsional_constant: float | None = None

    @property
    def depth(self) -> float:
        return self.y_max - self.y_min

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def c_top(self) -> float:
        return self.centroid_y - self.y_min

    @property
    def c_bottom(self) -> float:
        return self.y_max - self.centroid_y

    @property
    def c_left(self) -> float:
        return self.centroid_x - self.x_min

    @property
    def c_right(self) -> float:
        return self.x_max - self.centroid_x

    @property
    def sx_top(self) -> float:
        return self.ix / self.c_top

    @property
    def sx_bottom(self) -> float:
        return self.ix / self.c_bottom

    @property
    def sy_left(self) -> float:
        return self.iy / self.c_left

    @property
    def sy_right(self) -> float:
        return self.iy / self.c_right

    @property
    def principal_inertia_major(self) -> float:
        average = (self.ix + self.iy) / 2
        radius = sqrt(((self.ix - self.iy) / 2) ** 2 + self.ixy**2)
        return average + radius

    @property
    def principal_inertia_minor(self) -> float:
        average = (self.ix + self.iy) / 2
        radius = sqrt(((self.ix - self.iy) / 2) ** 2 + self.ixy**2)
        return average - radius

    @property
    def principal_axis_angle_degrees(self) -> float:
        """Principal-axis rotation from the x axis using the Ixy convention."""

        return 0.5 * degrees(atan2(-2 * self.ixy, self.iy - self.ix))


@dataclass(frozen=True, slots=True)
class SectionGeometry:
    """A section's explicit geometry and calculated properties."""

    shape: str
    attachment: str
    components: tuple[Rectangle, ...]
    properties: SectionProperties
    notes: tuple[str, ...] = ()


class StiffenerSection(Protocol):
    """Common interface implemented by every stiffener shape."""

    def geometry(self) -> SectionGeometry:
        """Return component geometry and gross section properties."""


def calculate_properties(
    components: tuple[Rectangle, ...] | list[Rectangle],
    *,
    torsional_constant: float | None = None,
) -> SectionProperties:
    """Calculate centroidal properties for non-overlapping rectangles."""

    if not components:
        raise ValueError("at least one section component is required")

    area = sum(component.area for component in components)
    centroid_x = sum(
        component.area * component.centroid_x for component in components
    ) / area
    centroid_y = sum(
        component.area * component.centroid_y for component in components
    ) / area

    ix = 0.0
    iy = 0.0
    ixy = 0.0
    for component in components:
        dx = component.centroid_x - centroid_x
        dy = component.centroid_y - centroid_y
        ix += component.width * component.height**3 / 12 + component.area * dy**2
        iy += component.height * component.width**3 / 12 + component.area * dx**2
        ixy += component.area * dx * dy

    return SectionProperties(
        area=area,
        centroid_x=centroid_x,
        centroid_y=centroid_y,
        ix=ix,
        iy=iy,
        ixy=ixy,
        x_min=min(component.x for component in components),
        x_max=max(component.x_max for component in components),
        y_min=min(component.y for component in components),
        y_max=max(component.y_max for component in components),
        torsional_constant=torsional_constant,
    )


@dataclass(frozen=True, slots=True)
class FlatBarSection:
    """A flat bar welded by its narrow edge to the plate."""

    height: float
    thickness: float

    def geometry(self) -> SectionGeometry:
        _require_positive("flat-bar height", self.height)
        _require_positive("flat-bar thickness", self.thickness)
        components = (
            Rectangle(
                width=self.thickness,
                height=self.height,
                x=-self.thickness / 2,
                label="flat_bar",
            ),
        )
        return SectionGeometry(
            shape="flat_bar",
            attachment="narrow_edge",
            components=components,
            properties=calculate_properties(components),
        )


@dataclass(frozen=True, slots=True)
class AngleSection:
    """An L-section with one leg against the plate.

    ``attached_leg`` is parallel to the plate. ``outstanding_leg`` projects
    normal to it. The two legs have one common thickness in this first model.
    """

    attached_leg: float
    outstanding_leg: float
    thickness: float
    handedness: Handedness = Handedness.RIGHT

    def geometry(self) -> SectionGeometry:
        _require_positive("angle attached leg", self.attached_leg)
        _require_positive("angle outstanding leg", self.outstanding_leg)
        _require_positive("angle thickness", self.thickness)
        if self.attached_leg <= self.thickness:
            raise ValueError("angle attached leg must exceed its thickness")
        if self.outstanding_leg <= self.thickness:
            raise ValueError("angle outstanding leg must exceed its thickness")

        components = (
            Rectangle(
                width=self.attached_leg,
                height=self.thickness,
                x=-self.thickness / 2,
                label="attached_leg",
            ),
            Rectangle(
                width=self.thickness,
                height=self.outstanding_leg - self.thickness,
                x=-self.thickness / 2,
                y=self.thickness,
                label="outstanding_leg",
            ),
        )
        if self.handedness is Handedness.LEFT:
            components = tuple(component.mirrored_x() for component in components)

        return SectionGeometry(
            shape="angle",
            attachment=f"attached_leg_{self.handedness.value}",
            components=components,
            properties=calculate_properties(components),
            notes=("Sharp heel and toe; rolled fillets are excluded.",),
        )


@dataclass(frozen=True, slots=True)
class TeeSection:
    """A sharp-corner T-section in either web-end or flange-face attachment."""

    overall_depth: float
    web_thickness: float
    flange_width: float
    flange_thickness: float
    attachment: TeeAttachment = TeeAttachment.WEB_END

    def geometry(self) -> SectionGeometry:
        _require_positive("T overall depth", self.overall_depth)
        _require_positive("T web thickness", self.web_thickness)
        _require_positive("T flange width", self.flange_width)
        _require_positive("T flange thickness", self.flange_thickness)
        if self.overall_depth <= self.flange_thickness:
            raise ValueError("T overall depth must exceed flange thickness")
        if self.flange_width < self.web_thickness:
            raise ValueError("T flange width must not be less than web thickness")

        clear_web_height = self.overall_depth - self.flange_thickness
        if self.attachment is TeeAttachment.WEB_END:
            components = (
                Rectangle(
                    width=self.web_thickness,
                    height=clear_web_height,
                    x=-self.web_thickness / 2,
                    label="web",
                ),
                Rectangle(
                    width=self.flange_width,
                    height=self.flange_thickness,
                    x=-self.flange_width / 2,
                    y=clear_web_height,
                    label="flange",
                ),
            )
        else:
            components = (
                Rectangle(
                    width=self.flange_width,
                    height=self.flange_thickness,
                    x=-self.flange_width / 2,
                    label="flange",
                ),
                Rectangle(
                    width=self.web_thickness,
                    height=clear_web_height,
                    x=-self.web_thickness / 2,
                    y=self.flange_thickness,
                    label="web",
                ),
            )

        return SectionGeometry(
            shape="tee",
            attachment=self.attachment.value,
            components=components,
            properties=calculate_properties(components),
            notes=("Sharp web-to-flange intersection; fillets are excluded.",),
        )


@dataclass(frozen=True, slots=True)
class RectangularHollowSection:
    """A sharp-corner RHS or SHS attached by one outside face."""

    side_a: float
    side_b: float
    wall_thickness: float
    attachment: RhsAttachment = RhsAttachment.SIDE_A

    def geometry(self) -> SectionGeometry:
        _require_positive("RHS side A", self.side_a)
        _require_positive("RHS side B", self.side_b)
        _require_positive("RHS wall thickness", self.wall_thickness)

        if self.attachment is RhsAttachment.SIDE_A:
            width, depth = self.side_a, self.side_b
        else:
            width, depth = self.side_b, self.side_a

        if width <= 2 * self.wall_thickness or depth <= 2 * self.wall_thickness:
            raise ValueError("RHS outside dimensions must exceed twice the wall thickness")

        t = self.wall_thickness
        components = (
            Rectangle(width=width, height=t, x=-width / 2, label="attached_wall"),
            Rectangle(
                width=width,
                height=t,
                x=-width / 2,
                y=depth - t,
                label="far_wall",
            ),
            Rectangle(
                width=t,
                height=depth - 2 * t,
                x=-width / 2,
                y=t,
                label="left_wall",
            ),
            Rectangle(
                width=t,
                height=depth - 2 * t,
                x=width / 2 - t,
                y=t,
                label="right_wall",
            ),
        )
        shape = "shs" if self.side_a == self.side_b else "rhs"
        return SectionGeometry(
            shape=shape,
            attachment=self.attachment.value,
            components=components,
            properties=calculate_properties(components),
            notes=(
                "Sharp-corner idealization; manufactured corner radii are excluded.",
                "The selected attachment side is parallel to the plate.",
            ),
        )


@dataclass(frozen=True, slots=True)
class ChannelSection:
    """A sharp-corner channel with flange-face or web-face attachment."""

    overall_depth: float
    flange_width: float
    web_thickness: float
    flange_thickness: float
    attachment: ChannelAttachment = ChannelAttachment.FLANGE_FACE
    handedness: Handedness = Handedness.RIGHT

    def geometry(self) -> SectionGeometry:
        _require_positive("channel overall depth", self.overall_depth)
        _require_positive("channel flange width", self.flange_width)
        _require_positive("channel web thickness", self.web_thickness)
        _require_positive("channel flange thickness", self.flange_thickness)
        if self.overall_depth <= 2 * self.flange_thickness:
            raise ValueError("channel depth must exceed twice the flange thickness")
        if self.flange_width <= self.web_thickness:
            raise ValueError("channel flange width must exceed web thickness")

        if self.attachment is ChannelAttachment.FLANGE_FACE:
            components = (
                Rectangle(
                    width=self.flange_width,
                    height=self.flange_thickness,
                    x=-self.web_thickness / 2,
                    label="attached_flange",
                ),
                Rectangle(
                    width=self.web_thickness,
                    height=self.overall_depth - 2 * self.flange_thickness,
                    x=-self.web_thickness / 2,
                    y=self.flange_thickness,
                    label="web",
                ),
                Rectangle(
                    width=self.flange_width,
                    height=self.flange_thickness,
                    x=-self.web_thickness / 2,
                    y=self.overall_depth - self.flange_thickness,
                    label="far_flange",
                ),
            )
            if self.handedness is Handedness.LEFT:
                components = tuple(component.mirrored_x() for component in components)
        else:
            # Rotated channel: the back of the web lies against the plate and
            # the two flanges project from its longitudinal edges.
            components = (
                Rectangle(
                    width=self.overall_depth,
                    height=self.web_thickness,
                    x=-self.overall_depth / 2,
                    label="attached_web",
                ),
                Rectangle(
                    width=self.flange_thickness,
                    height=self.flange_width - self.web_thickness,
                    x=-self.overall_depth / 2,
                    y=self.web_thickness,
                    label="left_flange",
                ),
                Rectangle(
                    width=self.flange_thickness,
                    height=self.flange_width - self.web_thickness,
                    x=self.overall_depth / 2 - self.flange_thickness,
                    y=self.web_thickness,
                    label="right_flange",
                ),
            )

        return SectionGeometry(
            shape="channel",
            attachment=(
                f"{self.attachment.value}_{self.handedness.value}"
                if self.attachment is ChannelAttachment.FLANGE_FACE
                else self.attachment.value
            ),
            components=components,
            properties=calculate_properties(components),
            notes=("Sharp corners; rolled fillets are excluded.",),
        )


@dataclass(frozen=True, slots=True)
class CompositeSection:
    """A stiffener acting compositely with a centered tributary plate strip."""

    plate_width: float
    plate_thickness: float
    stiffener: StiffenerSection

    def geometry(self) -> SectionGeometry:
        _require_positive("effective plate width", self.plate_width)
        _require_positive("plate thickness", self.plate_thickness)

        stiffener_geometry = self.stiffener.geometry()
        plate = Rectangle(
            width=self.plate_width,
            height=self.plate_thickness,
            x=-self.plate_width / 2,
            label="effective_plate",
        )
        shifted_stiffener = tuple(
            component.translated(dy=self.plate_thickness)
            for component in stiffener_geometry.components
        )
        components = (plate, *shifted_stiffener)
        return SectionGeometry(
            shape=f"plate_plus_{stiffener_geometry.shape}",
            attachment=stiffener_geometry.attachment,
            components=components,
            properties=calculate_properties(components),
            notes=(
                "Full composite action is assumed.",
                "The effective plate width equals the supplied tributary width.",
                *stiffener_geometry.notes,
            ),
        )
