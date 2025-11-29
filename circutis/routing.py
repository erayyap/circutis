"""
Wire routing for automatic connection generation.
Uses Manhattan routing (horizontal/vertical segments only).
"""

from typing import List, Tuple, Set, Optional, TYPE_CHECKING
from dataclasses import dataclass
from .constants import GRID_SPACING

if TYPE_CHECKING:
    from .pin import Pin


@dataclass
class Wire:
    """
    Represents a wire segment between two points.
    
    Attributes:
        start: (x, y) starting coordinates
        end: (x, y) ending coordinates
    """
    start: Tuple[int, int]
    end: Tuple[int, int]
    
    def to_asc(self) -> str:
        """Generate ASC wire command."""
        return f"WIRE {self.start[0]} {self.start[1]} {self.end[0]} {self.end[1]}"
    
    @property
    def endpoints(self) -> Set[Tuple[int, int]]:
        """Get both endpoints as a set."""
        return {self.start, self.end}
    
    def __repr__(self):
        return f"Wire({self.start} -> {self.end})"


@dataclass
class Connection:
    """
    Represents a logical connection between two pins.

    A connection may consist of multiple Wire segments due to routing.
    This class maintains the association between pins and their wires
    for validation and error reporting.

    Attributes:
        pin_a: First pin in the connection
        pin_b: Second pin in the connection
        wires: List of Wire segments that form this connection
        label: Optional net label for this connection
    """
    pin_a: "Pin"
    pin_b: "Pin"
    wires: List[Wire]
    label: Optional[str] = None

    @property
    def description(self) -> str:
        """Human-readable description for error messages."""
        comp_a = self.pin_a.component.ref
        pin_a_name = self.pin_a.name
        comp_b = self.pin_b.component.ref
        pin_b_name = self.pin_b.name
        return f"{comp_a}.{pin_a_name} to {comp_b}.{pin_b_name}"

    def __repr__(self):
        return f"Connection({self.description}, {len(self.wires)} wires)"


class Router:
    """
    Handles wire routing between pins.
    Currently implements simple L-routing (one bend maximum).
    """
    
    def __init__(self):
        self.wires: List[Wire] = []
        self._occupied_points: Set[Tuple[int, int]] = set()

    def _segment_hits_blocker(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        blocked_points: Set[Tuple[int, int]],
    ) -> bool:
        """Check if a straight segment would pass through any blocked pin."""
        if not blocked_points:
            return False

        x1, y1 = start
        x2, y2 = end

        if x1 == x2:
            ymin, ymax = sorted((y1, y2))
            for bx, by in blocked_points:
                if bx == x1 and ymin < by < ymax:
                    return True
        elif y1 == y2:
            xmin, xmax = sorted((x1, x2))
            for bx, by in blocked_points:
                if by == y1 and xmin < bx < xmax:
                    return True
        return False

    def _add_path(self, points: List[Tuple[int, int]]) -> List[Wire]:
        """Register a multi-segment path as wires and return them."""
        segments: List[Wire] = []
        for a, b in zip(points, points[1:]):
            wire = Wire(a, b)
            segments.append(wire)
            self.wires.append(wire)
            self._occupied_points.add(a)
            self._occupied_points.add(b)
        return segments

    def _path_is_clear(
        self,
        points: List[Tuple[int, int]],
        blocked_points: Set[Tuple[int, int]],
    ) -> bool:
        """Check all segments between points for collisions."""
        return all(
            not self._segment_hits_blocker(a, b, blocked_points)
            for a, b in zip(points, points[1:])
        )
    
    def route(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        blocked_points: Optional[Set[Tuple[int, int]]] = None,
        grid_unit: int = GRID_SPACING,
    ) -> List[Wire]:
        """
        Generate wire segments to connect two points.
        Uses Manhattan routing with minimal bends and avoids running
        wires directly through other pins (blocked_points).
        
        Args:
            x1, y1: Starting point coordinates
            x2, y2: Ending point coordinates
            blocked_points: Coordinates that should not be used along a segment
            grid_unit: Grid spacing used for offset jogs when needed
        
        Returns:
            List of Wire segments connecting the points
        """
        blocked_points = blocked_points or set()

        start = (x1, y1)
        end = (x2, y2)

        # No routing needed if start and end coincide
        if start == end:
            self._occupied_points.add(start)
            return []

        # Direct connection if aligned and unobstructed
        if x1 == x2 or y1 == y2:
            if not self._segment_hits_blocker(start, end, blocked_points):
                return self._add_path([start, end])

            # If blocked, create a small dogleg to dodge the obstacle
            offsets = [grid_unit, -grid_unit, 2 * grid_unit, -2 * grid_unit]

            if x1 == x2:
                for dx in offsets:
                    mid1 = (x1 + dx, y1)
                    mid2 = (x2 + dx, y2)
                    # Skip if our jog lands exactly on a blocked pin
                    if mid1 in blocked_points or mid2 in blocked_points:
                        continue
                    path = [start, mid1, (x1 + dx, y2), end]
                    if self._path_is_clear(path, blocked_points):
                        return self._add_path(path)
            else:  # Horizontal alignment
                for dy in offsets:
                    mid1 = (x1, y1 + dy)
                    mid2 = (x2, y2 + dy)
                    if mid1 in blocked_points or mid2 in blocked_points:
                        continue
                    path = [start, mid1, (x2, y1 + dy), end]
                    if self._path_is_clear(path, blocked_points):
                        return self._add_path(path)

            # Fallback: still draw direct wire to avoid routing failure
            return self._add_path([start, end])
        
        # L-routing: consider both midpoint options and avoid landing on pins
        mid1 = (x2, y1)  # Horizontal first
        mid2 = (x1, y2)  # Vertical first

        candidates = [
            [start, mid1, end],
            [start, mid2, end],
        ]

        for path in candidates:
            midpoint = path[1]
            if midpoint in blocked_points:
                continue
            if self._path_is_clear(path, blocked_points):
                return self._add_path(path)

        # Both options blocked: still use horizontal-first to avoid routing failure
        return self._add_path([start, mid1, end])
    
    def route_to_label(self, x: int, y: int, label: str) -> Tuple[List[Wire], str]:
        """
        Route from a point to a net label.
        Returns wires and the flag command.
        
        Args:
            x, y: Pin coordinates
            label: Net label name
        
        Returns:
            Tuple of (wire list, flag ASC command)
        """
        # Flag goes at the pin location
        flag_cmd = f"FLAG {x} {y} {label}"
        self._occupied_points.add((x, y))
        return ([], flag_cmd)
    
    def get_all_endpoints(self) -> Set[Tuple[int, int]]:
        """Get all wire endpoints for validation."""
        endpoints = set()
        for wire in self.wires:
            endpoints.update(wire.endpoints)
        return endpoints

    def remove_wires(self, wires_to_remove: List[Wire]):
        """
        Remove specific wire segments from the router.

        Used by layout post-processing (beautify) to re-route only a subset
        of connections without disturbing the rest of the wiring.
        """
        if not wires_to_remove:
            return

        self.wires = [w for w in self.wires if w not in wires_to_remove]

        # Recompute occupied points from remaining wires
        self._occupied_points = set()
        for wire in self.wires:
            self._occupied_points.update(wire.endpoints)
    
    def clear(self):
        """Clear all routing data."""
        self.wires = []
        self._occupied_points = set()
