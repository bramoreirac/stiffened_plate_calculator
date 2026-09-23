"""Interactive engineering diagrams derived from analysis inputs."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .models import StiffenerOrientation


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
                line={"color": "#00a6a6", "width": 2.5},
                hovertemplate="%{text}<extra></extra>",
                name="Stiffener centerlines",
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
