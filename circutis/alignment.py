"""
Alignment utilities for pin-aware component placement.

The key insight: Components should be placed so their PINS align to a connection grid,
not so their ORIGINS align to a grid. This module calculates the correct component
origin to achieve pin alignment.
"""

from typing import Tuple
from .constants import PIN_OFFSETS, DEFAULT_GRID_UNIT


def snap_to_grid(value: int, grid_unit: int = DEFAULT_GRID_UNIT) -> int:
    """
    Snap a coordinate value to the nearest grid point.

    Args:
        value: The coordinate to snap
        grid_unit: Grid spacing in LTspice units

    Returns:
        Snapped coordinate
    """
    return round(value / grid_unit) * grid_unit


def get_connection_point(row: int, col: int, grid_unit: int) -> Tuple[int, int]:
    """
    Get the connection grid point for a given grid cell.

    This is where pins should connect, not necessarily where component origins go.

    Args:
        row: Grid row
        col: Grid column
        grid_unit: Grid spacing

    Returns:
        (x, y) coordinate of the connection point
    """
    # Add offset to keep away from edge
    x = col * grid_unit + 100
    y = row * grid_unit + 100
    return (x, y)


def calculate_aligned_origin(
    component_type: str,
    target_row: int,
    target_col: int,
    rotation: int,
    grid_unit: int,
    align_pin: str = "p1",
) -> Tuple[int, int]:
    """
    Calculate component origin so that a specific pin aligns to the connection grid.

    This is the core of the pin alignment system. Instead of placing the component
    origin at the grid point, we calculate where the origin needs to be so that
    the desired pin ends up at the grid point.

    Args:
        component_type: Component symbol type (e.g., "res", "cap", "ind")
        target_row: Target grid row for the pin
        target_col: Target grid column for the pin
        rotation: Component rotation (0, 90, 180, 270)
        grid_unit: Grid spacing
        align_pin: Which pin to align to the grid (default: "p1")

    Returns:
        (x, y) coordinate for component origin

    Example:
        >>> # Place a resistor at R90 so its p1 pin is at grid (2, 2)
        >>> origin = calculate_aligned_origin("res", 2, 2, 90, 64, "p1")
        >>> # origin will be adjusted so that when p1's offset is applied,
        >>> # the pin ends up at the connection point for (2, 2)
    """
    # Get target connection point
    target_x, target_y = get_connection_point(target_row, target_col, grid_unit)

    # Get pin offset for this rotation
    if component_type not in PIN_OFFSETS:
        # Fallback to target point if unknown component
        return (target_x, target_y)

    rotation_offsets = PIN_OFFSETS[component_type].get(rotation)
    if not rotation_offsets:
        return (target_x, target_y)

    if align_pin not in rotation_offsets:
        # If specified pin doesn't exist, try first available pin
        align_pin = list(rotation_offsets.keys())[0]

    pin_offset_x, pin_offset_y = rotation_offsets[align_pin]

    # Calculate origin: origin + offset = target
    # Therefore: origin = target - offset
    origin_x = target_x - pin_offset_x
    origin_y = target_y - pin_offset_y

    return (origin_x, origin_y)


def get_recommended_spacing(
    comp1_type: str,
    comp2_type: str,
    orientation: str = "horizontal"
) -> int:
    """
    Get recommended spacing between two components.

    Args:
        comp1_type: First component type
        comp2_type: Second component type
        orientation: "horizontal" or "vertical"

    Returns:
        Recommended spacing in grid units (not pixels)
    """
    # Default spacing: 1 grid cell apart for horizontal, 2 for vertical
    if orientation == "horizontal":
        return 2  # 2 grid cells = 128 pixels at grid_unit=64
    else:
        return 2


def align_horizontal_series(
    components: list,
    start_row: int,
    start_col: int,
    grid_unit: int,
    spacing: int = 2
) -> list[Tuple[int, int, int]]:
    """
    Calculate positions for components in horizontal series.

    Places components so they form a horizontal chain with all pins aligned
    to the same y-coordinate.

    Args:
        components: List of Component objects
        start_row: Starting grid row
        start_col: Starting grid column
        grid_unit: Grid spacing
        spacing: Number of grid cells between components

    Returns:
        List of (x, y, rotation) tuples for each component
    """
    positions = []
    current_col = start_col

    for comp in components:
        # For horizontal series, use R90 rotation for two-terminal components
        rotation = 90 if hasattr(comp, 'p1') and hasattr(comp, 'p2') else 0

        # Calculate origin to align p1 to the current grid position
        origin = calculate_aligned_origin(
            comp._symbol_type,
            start_row,
            current_col,
            rotation,
            grid_unit,
            align_pin="p1"
        )

        positions.append((*origin, rotation))
        current_col += spacing

    return positions


def align_vertical_series(
    components: list,
    start_row: int,
    start_col: int,
    grid_unit: int,
    spacing: int = 2
) -> list[Tuple[int, int, int]]:
    """
    Calculate positions for components in vertical series.

    Places components so they form a vertical chain with all pins aligned
    to the same x-coordinate.

    Args:
        components: List of Component objects
        start_row: Starting grid row
        start_col: Starting grid column
        grid_unit: Grid spacing
        spacing: Number of grid cells between components

    Returns:
        List of (x, y, rotation) tuples for each component
    """
    positions = []
    current_row = start_row

    for comp in components:
        # For vertical series, use R0 rotation for two-terminal components
        rotation = 0 if hasattr(comp, 'p1') and hasattr(comp, 'p2') else 0

        # Calculate origin to align p1 to the current grid position
        origin = calculate_aligned_origin(
            comp._symbol_type,
            current_row,
            start_col,
            rotation,
            grid_unit,
            align_pin="p1"
        )

        positions.append((*origin, rotation))
        current_row += spacing

    return positions
