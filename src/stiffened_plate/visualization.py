"""Interactive engineering diagrams derived from analysis inputs."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .models import StiffenerOrientation
from .sections import CompositeSection, Rectangle, StiffenerSection


CENTROID_LINE_COLOR = "#f2c94c"


@dataclass(frozen=True, slots=True)
class LineSegment:
    x0: float
    y0: float
    x1: float
    y1: float
    label: str
    position_in: float


@dataclass(frozen=True, slots=True)
class FrontViewGeometry:
    long_span_in: float
    short_span_in: float
    orientation: StiffenerOrientation
    spacing_in: float
    stiffeners: tuple[LineSegment, ...]


@dataclass(frozen=True, slots=True)
class SideViewGeometry:
    plate_width_in: float
    plate_thickness_in: float
    shape: str | None
    attachment: str | None
    rectangles: tuple[Rectangle, ...]
    stiffener_width_in: float
    stiffener_depth_in: float
    stiffener_x_min_in: float
    stiffener_x_max_in: float
    stiffener_centroid_x_in: float
    stiffener_centroid_y_in: float


def side_view_plate_strip_width(
    stiffener: StiffenerSection | None,
    extra_width_in: float = 4.0,
) -> float:
    """Return the illustrative plate width used in the side-view diagram."""

    if (
        isinstance(extra_width_in, bool)
        or not isfinite(extra_width_in)
        or extra_width_in <= 0
    ):
        raise ValueError(
            "side-view extra plate width must be finite and greater than zero"
        )
    section_width = (
        0.0 if stiffener is None else stiffener.geometry().properties.width
    )
    return section_width + extra_width_in


def front_view_geometry(
    long_span_in: float,
    short_span_in: float,
    stiffener_count: int,
    orientation: StiffenerOrientation,
) -> FrontViewGeometry:
    """Return plate-plan geometry with equally spaced stiffener centerlines."""

    for name, value in (
        ("long span", long_span_in),
        ("short span", short_span_in),
    ):
        if isinstance(value, bool) or not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite value greater than zero")
    if isinstance(stiffener_count, bool) or not isinstance(stiffener_count, int):
        raise ValueError("stiffener count must be an integer")
    if stiffener_count < 0:
        raise ValueError("stiffener count must not be negative")
    if not isinstance(orientation, StiffenerOrientation):
        raise ValueError("stiffener orientation is not supported")

    if orientation is StiffenerOrientation.LONG_SPAN:
        spacing = short_span_in / (stiffener_count + 1)
        stiffeners = tuple(
            LineSegment(
                x0=0.0,
                y0=index * spacing,
                x1=long_span_in,
                y1=index * spacing,
                label=f"Stiffener {index}",
                position_in=index * spacing,
            )
            for index in range(1, stiffener_count + 1)
        )
    else:
        spacing = long_span_in / (stiffener_count + 1)
        stiffeners = tuple(
            LineSegment(
                x0=index * spacing,
                y0=0.0,
                x1=index * spacing,
                y1=short_span_in,
                label=f"Stiffener {index}",
                position_in=index * spacing,
            )
            for index in range(1, stiffener_count + 1)
        )

    return FrontViewGeometry(
        long_span_in=long_span_in,
        short_span_in=short_span_in,
        orientation=orientation,
        spacing_in=spacing,
        stiffeners=stiffeners,
    )


def front_view_figure(
    long_span_in: float,
    short_span_in: float,
    stiffener_count: int,
    orientation: StiffenerOrientation,
):
    """Build a responsive Plotly plan view of the plate and stiffeners."""

    import plotly.graph_objects as go

    geometry = front_view_geometry(
        long_span_in,
        short_span_in,
        stiffener_count,
        orientation,
    )
    length = geometry.long_span_in
    width = geometry.short_span_in

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=(0.0, length, length, 0.0, 0.0),
            y=(0.0, 0.0, width, width, 0.0),
            mode="lines",
            fill="toself",
            fillcolor="rgba(124, 135, 152, 0.10)",
            line={"color": "#7c8798", "width": 2.5},
            hovertemplate=(
                f"Plate<br>Long span: {length:.4g} in"
                f"<br>Short span: {width:.4g} in<extra></extra>"
            ),
            name="Plate boundary",
        )
    )

    if geometry.stiffeners:
        x_values: list[float | None] = []
        y_values: list[float | None] = []
        hover_values: list[str | None] = []
        direction_label = (
            "from lower plate edge"
            if orientation is StiffenerOrientation.LONG_SPAN
            else "from left plate edge"
        )
        for stiffener in geometry.stiffeners:
            hover = (
                f"{stiffener.label}<br>Position {direction_label}: "
                f"{stiffener.position_in:.4g} in"
            )
            x_values.extend((stiffener.x0, stiffener.x1, None))
            y_values.extend((stiffener.y0, stiffener.y1, None))
            hover_values.extend((hover, hover, None))
        figure.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                text=hover_values,
                mode="lines",
                line={"color": CENTROID_LINE_COLOR, "width": 2.5, "dash": "dashdot"},
                hovertemplate="%{text}<extra></extra>",
                name="Stiffener centroid lines",
            )
        )

    horizontal_dimension_y = -0.12 * width
    vertical_dimension_x = -0.08 * length
    dimension_color = "#7c8798"

    figure.add_shape(
        type="line",
        x0=0.0,
        y0=horizontal_dimension_y,
        x1=length,
        y1=horizontal_dimension_y,
        line={"color": dimension_color, "width": 1},
    )
    for x_position in (0.0, length):
        figure.add_shape(
            type="line",
            x0=x_position,
            y0=horizontal_dimension_y - 0.025 * width,
            x1=x_position,
            y1=horizontal_dimension_y + 0.025 * width,
            line={"color": dimension_color, "width": 1},
        )
    figure.add_annotation(
        x=length / 2.0,
        y=horizontal_dimension_y,
        text=f"Long span a = {length:.4g} in",
        showarrow=False,
        yshift=-16,
        font={"family": "JetBrains Mono, monospace", "size": 12},
    )

    figure.add_shape(
        type="line",
        x0=vertical_dimension_x,
        y0=0.0,
        x1=vertical_dimension_x,
        y1=width,
        line={"color": dimension_color, "width": 1},
    )
    for y_position in (0.0, width):
        figure.add_shape(
            type="line",
            x0=vertical_dimension_x - 0.015 * length,
            y0=y_position,
            x1=vertical_dimension_x + 0.015 * length,
            y1=y_position,
            line={"color": dimension_color, "width": 1},
        )
    figure.add_annotation(
        x=vertical_dimension_x,
        y=width / 2.0,
        text=f"Short span b = {width:.4g} in",
        showarrow=False,
        textangle=-90,
        xshift=-20,
        font={"family": "JetBrains Mono, monospace", "size": 12},
    )

    orientation_text = (
        "Stiffeners span in the long direction"
        if orientation is StiffenerOrientation.LONG_SPAN
        else "Stiffeners span in the short direction"
    )
    figure.add_annotation(
        x=length / 2.0,
        y=width,
        text=(
            f"{orientation_text} · {stiffener_count} stiffener"
            f"{'s' if stiffener_count != 1 else ''} · spacing {geometry.spacing_in:.4g} in"
        ),
        showarrow=False,
        yshift=18,
        font={"family": "JetBrains Mono, monospace", "size": 12},
    )

    figure.update_layout(
        template="plotly",
        height=460,
        margin={"l": 45, "r": 20, "t": 45, "b": 55},
        showlegend=False,
        hovermode="closest",
        dragmode="pan",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "JetBrains Mono, monospace", "size": 12},
        xaxis={
            "range": (-0.16 * length, 1.04 * length),
            "visible": False,
            "fixedrange": False,
            "constrain": "domain",
        },
        yaxis={
            "range": (-0.22 * width, 1.10 * width),
            "visible": False,
            "fixedrange": False,
            "scaleanchor": "x",
            "scaleratio": 1,
        },
    )
    return figure


def side_view_geometry(
    plate_width_in: float,
    plate_thickness_in: float,
    stiffener: StiffenerSection | None,
) -> SideViewGeometry:
    """Return display geometry with the plate below the attachment surface.

    The source section engine uses positive y from the plate top through the
    plate and into the stiffener. The side view translates that geometry so the
    plate/stiffener interface is y = 0, the plate occupies negative y, and the
    stiffener projects upward in positive y.
    """

    for name, value in (
        ("plate display width", plate_width_in),
        ("plate thickness", plate_thickness_in),
    ):
        if isinstance(value, bool) or not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite value greater than zero")

    if stiffener is None:
        plate = Rectangle(
            width=plate_width_in,
            height=plate_thickness_in,
            x=-plate_width_in / 2.0,
            y=-plate_thickness_in,
            label="effective_plate",
        )
        return SideViewGeometry(
            plate_width_in=plate_width_in,
            plate_thickness_in=plate_thickness_in,
            shape=None,
            attachment=None,
            rectangles=(plate,),
            stiffener_width_in=0.0,
            stiffener_depth_in=0.0,
            stiffener_x_min_in=0.0,
            stiffener_x_max_in=0.0,
            stiffener_centroid_x_in=0.0,
            stiffener_centroid_y_in=0.0,
        )

    bare = stiffener.geometry()
    composite = CompositeSection(
        plate_width=plate_width_in,
        plate_thickness=plate_thickness_in,
        stiffener=stiffener,
    ).geometry()
    rectangles = tuple(
        Rectangle(
            width=component.width,
            height=component.height,
            x=component.x,
            y=component.y - plate_thickness_in,
            label=component.label,
        )
        for component in composite.components
    )
    return SideViewGeometry(
        plate_width_in=plate_width_in,
        plate_thickness_in=plate_thickness_in,
        shape=bare.shape,
        attachment=bare.attachment,
        rectangles=rectangles,
        stiffener_width_in=bare.properties.width,
        stiffener_depth_in=bare.properties.depth,
        stiffener_x_min_in=bare.properties.x_min - bare.properties.centroid_x,
        stiffener_x_max_in=bare.properties.x_max - bare.properties.centroid_x,
        stiffener_centroid_x_in=0.0,
        stiffener_centroid_y_in=bare.properties.centroid_y,
    )


def _add_horizontal_dimension(
    figure,
    *,
    x0: float,
    x1: float,
    y: float,
    tick_size: float,
    text: str,
    text_shift: int,
) -> None:
    color = "#7c8798"
    figure.add_shape(
        type="line",
        x0=x0,
        y0=y,
        x1=x1,
        y1=y,
        line={"color": color, "width": 1},
    )
    for x_position in (x0, x1):
        figure.add_shape(
            type="line",
            x0=x_position,
            y0=y - tick_size,
            x1=x_position,
            y1=y + tick_size,
            line={"color": color, "width": 1},
        )
    figure.add_annotation(
        x=(x0 + x1) / 2.0,
        y=y,
        text=text,
        showarrow=False,
        yshift=text_shift,
        font={"family": "JetBrains Mono, monospace", "size": 11},
    )


def _add_vertical_dimension(
    figure,
    *,
    x: float,
    y0: float,
    y1: float,
    tick_size: float,
    text: str,
    text_shift: int,
) -> None:
    color = "#7c8798"
    figure.add_shape(
        type="line",
        x0=x,
        y0=y0,
        x1=x,
        y1=y1,
        line={"color": color, "width": 1},
    )
    for y_position in (y0, y1):
        figure.add_shape(
            type="line",
            x0=x - tick_size,
            y0=y_position,
            x1=x + tick_size,
            y1=y_position,
            line={"color": color, "width": 1},
        )
    figure.add_annotation(
        x=x,
        y=(y0 + y1) / 2.0,
        text=text,
        showarrow=False,
        textangle=-90,
        xshift=text_shift,
        font={"family": "JetBrains Mono, monospace", "size": 11},
    )


def side_view_figure(
    plate_width_in: float,
    plate_thickness_in: float,
    stiffener: StiffenerSection | None,
):
    """Build a Plotly cross-section view from the section engine rectangles."""

    import plotly.graph_objects as go

    geometry = side_view_geometry(
        plate_width_in,
        plate_thickness_in,
        stiffener,
    )
    figure = go.Figure()
    for component in geometry.rectangles:
        is_plate = component.label == "effective_plate"
        x0, x1 = component.x, component.x_max
        y0, y1 = component.y, component.y_max
        figure.add_trace(
            go.Scatter(
                x=(x0, x1, x1, x0, x0),
                y=(y0, y0, y1, y1, y0),
                mode="lines",
                fill="toself",
                fillcolor=(
                    "rgba(124, 135, 152, 0.28)"
                    if is_plate
                    else "rgba(0, 166, 166, 0.32)"
                ),
                line={
                    "color": "#7c8798" if is_plate else "#00a6a6",
                    "width": 2,
                },
                text=(
                    f"{'Plate' if is_plate else component.label.replace('_', ' ').title()}"
                    f"<br>Width: {component.width:.4g} in"
                    f"<br>Height: {component.height:.4g} in"
                ),
                hovertemplate="%{text}<extra></extra>",
                name=component.label,
            )
        )

    combined_x_min = min(component.x for component in geometry.rectangles)
    combined_x_max = max(component.x_max for component in geometry.rectangles)
    combined_y_min = min(component.y for component in geometry.rectangles)
    combined_y_max = max(component.y_max for component in geometry.rectangles)
    total_width = combined_x_max - combined_x_min
    total_height = combined_y_max - combined_y_min
    reference_size = max(total_width, total_height, 1.0)
    horizontal_padding = 0.10 * reference_size
    vertical_padding = 0.08 * reference_size

    plate_dimension_y = -geometry.plate_thickness_in - vertical_padding
    _add_horizontal_dimension(
        figure,
        x0=-geometry.plate_width_in / 2.0,
        x1=geometry.plate_width_in / 2.0,
        y=plate_dimension_y,
        tick_size=0.015 * reference_size,
        text=f"Displayed plate strip = {geometry.plate_width_in:.4g} in",
        text_shift=-15,
    )
    _add_vertical_dimension(
        figure,
        x=combined_x_min - horizontal_padding,
        y0=-geometry.plate_thickness_in,
        y1=0.0,
        tick_size=0.012 * reference_size,
        text=f"Plate t = {geometry.plate_thickness_in:.4g} in",
        text_shift=-19,
    )

    chart_title = "No stiffener"
    if geometry.shape is not None:
        chart_title = (
            f"{geometry.shape.upper()} | "
            f"{geometry.attachment.replace('_', ' ')} attachment"
        )
        section_dimension_y = geometry.stiffener_depth_in + vertical_padding
        _add_horizontal_dimension(
            figure,
            x0=geometry.stiffener_x_min_in,
            x1=geometry.stiffener_x_max_in,
            y=section_dimension_y,
            tick_size=0.015 * reference_size,
            text=f"Section width = {geometry.stiffener_width_in:.4g} in",
            text_shift=14,
        )
        _add_vertical_dimension(
            figure,
            x=geometry.stiffener_x_max_in + horizontal_padding,
            y0=0.0,
            y1=geometry.stiffener_depth_in,
            tick_size=0.012 * reference_size,
            text=f"Section depth = {geometry.stiffener_depth_in:.4g} in",
            text_shift=19,
        )
        centroid_extension = 0.06 * reference_size
        figure.add_shape(
            type="line",
            x0=geometry.stiffener_x_min_in - centroid_extension,
            y0=geometry.stiffener_centroid_y_in,
            x1=geometry.stiffener_x_max_in + centroid_extension,
            y1=geometry.stiffener_centroid_y_in,
            line={"color": CENTROID_LINE_COLOR, "width": 2, "dash": "dashdot"},
            layer="above",
        )
        figure.add_shape(
            type="line",
            x0=geometry.stiffener_centroid_x_in,
            y0=0.0,
            x1=geometry.stiffener_centroid_x_in,
            y1=geometry.stiffener_depth_in,
            line={"color": CENTROID_LINE_COLOR, "width": 2, "dash": "dashdot"},
            layer="above",
        )
        centroid_radius = 0.012 * reference_size
        figure.add_shape(
            type="circle",
            x0=geometry.stiffener_centroid_x_in - centroid_radius,
            y0=geometry.stiffener_centroid_y_in - centroid_radius,
            x1=geometry.stiffener_centroid_x_in + centroid_radius,
            y1=geometry.stiffener_centroid_y_in + centroid_radius,
            line={"color": CENTROID_LINE_COLOR, "width": 1},
            fillcolor=CENTROID_LINE_COLOR,
            layer="above",
        )
        figure.add_annotation(
            x=geometry.stiffener_centroid_x_in,
            y=geometry.stiffener_centroid_y_in,
            text="C<sub>s</sub>",
            showarrow=False,
            xshift=18,
            font={
                "family": "JetBrains Mono, monospace",
                "size": 11,
                "color": CENTROID_LINE_COLOR,
            },
        )

    figure.update_layout(
        template="plotly",
        height=460,
        margin={"l": 50, "r": 50, "t": 75, "b": 60},
        title={
            "text": chart_title,
            "x": 0.5,
            "xanchor": "center",
            "y": 0.98,
            "yanchor": "top",
            "font": {"family": "JetBrains Mono, monospace", "size": 12},
        },
        showlegend=False,
        hovermode="closest",
        dragmode="pan",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "JetBrains Mono, monospace", "size": 11},
        xaxis={
            "range": (
                combined_x_min - 2.2 * horizontal_padding,
                combined_x_max + 2.2 * horizontal_padding,
            ),
            "visible": False,
            "fixedrange": False,
            "constrain": "domain",
        },
        yaxis={
            "range": (
                plate_dimension_y - 1.2 * vertical_padding,
                max(combined_y_max, geometry.stiffener_depth_in)
                + 2.2 * vertical_padding,
            ),
            "visible": False,
            "fixedrange": False,
            "scaleanchor": "x",
            "scaleratio": 1,
        },
    )
    return figure
