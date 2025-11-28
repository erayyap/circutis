"""
Validation utilities for circuit integrity checking.
"""

from typing import List, Set, Tuple, TYPE_CHECKING, Optional
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from .circuit import Circuit
    from .components import Component
    from .pin import Pin
    from .routing import Wire, Connection


def _segments_intersect(wire1: "Wire", wire2: "Wire") -> Optional[Tuple[int, int]]:
    """
    Check if two wire segments intersect at a crossing point.

    Detects:
    - X-crossings (horizontal crossing vertical)
    - Overlapping parallel wires
    - T-junctions (wire ending at another wire's midpoint)

    Returns:
        Crossing point (x, y) if wires cross, None otherwise

    Note: Wires that share an endpoint are NOT considered crossing
    (they're intentionally connected at that point).
    """
    x1_start, y1_start = wire1.start
    x1_end, y1_end = wire1.end
    x2_start, y2_start = wire2.start
    x2_end, y2_end = wire2.end

    # Check if wires share an endpoint (intentional connection)
    shared_points = wire1.endpoints & wire2.endpoints
    if shared_points:
        return None  # Not a crossing, just a connection point

    # Determine wire orientations
    wire1_horizontal = (y1_start == y1_end)
    wire1_vertical = (x1_start == x1_end)
    wire2_horizontal = (y2_start == y2_end)
    wire2_vertical = (x2_start == x2_end)

    # Case 1: One horizontal, one vertical (X-crossing or T-junction)
    if wire1_horizontal and wire2_vertical:
        y1 = y1_start
        x2 = x2_start

        # Check if crossing point is within both segments (including endpoints for T-junctions)
        if (min(x1_start, x1_end) <= x2 <= max(x1_start, x1_end) and
            min(y2_start, y2_end) <= y1 <= max(y2_start, y2_end)):
            # Exclude exact endpoint matches (already handled above)
            if (x2, y1) not in wire1.endpoints and (x2, y1) not in wire2.endpoints:
                return (x2, y1)

    elif wire1_vertical and wire2_horizontal:
        x1 = x1_start
        y2 = y2_start

        if (min(x2_start, x2_end) <= x1 <= max(x2_start, x2_end) and
            min(y1_start, y1_end) <= y2 <= max(y1_start, y1_end)):
            if (x1, y2) not in wire1.endpoints and (x1, y2) not in wire2.endpoints:
                return (x1, y2)

    # Case 2: Both horizontal (check for overlap)
    elif wire1_horizontal and wire2_horizontal:
        if y1_start == y2_start:  # Same Y coordinate
            # Check for X overlap
            x1_min, x1_max = sorted([x1_start, x1_end])
            x2_min, x2_max = sorted([x2_start, x2_end])

            # If they overlap (not just touch at endpoints)
            overlap_start = max(x1_min, x2_min)
            overlap_end = min(x1_max, x2_max)

            if overlap_start < overlap_end:
                # Return midpoint of overlap
                return ((overlap_start + overlap_end) // 2, y1_start)

    # Case 3: Both vertical (check for overlap)
    elif wire1_vertical and wire2_vertical:
        if x1_start == x2_start:  # Same X coordinate
            # Check for Y overlap
            y1_min, y1_max = sorted([y1_start, y1_end])
            y2_min, y2_max = sorted([y2_start, y2_end])

            overlap_start = max(y1_min, y2_min)
            overlap_end = min(y1_max, y2_max)

            if overlap_start < overlap_end:
                # Return midpoint of overlap
                return (x1_start, (overlap_start + overlap_end) // 2)

    return None  # No intersection


class ValidationSeverity(Enum):
    """Severity level for validation issues."""
    ERROR = "error"      # Will cause simulation failure
    WARNING = "warning"  # Might cause issues
    INFO = "info"        # Informational


@dataclass
class ValidationIssue:
    """Represents a validation problem found in the circuit."""
    severity: ValidationSeverity
    message: str
    component: str = ""  # Reference designator
    pin: str = ""        # Pin name
    
    def __str__(self):
        loc = ""
        if self.component:
            loc = f" [{self.component}"
            if self.pin:
                loc += f".{self.pin}"
            loc += "]"
        return f"{self.severity.value.upper()}{loc}: {self.message}"


class CircuitValidator:
    """
    Validates circuit connectivity and configuration.
    
    Checks performed:
    - Unconnected pins (at least one end should be labeled or connected)
    - Floating nodes
    - Missing ground reference
    - Component placement issues
    """
    
    def __init__(self, circuit: "Circuit"):
        self.circuit = circuit
        self.issues: List[ValidationIssue] = []
    
    def validate(self) -> List[ValidationIssue]:
        """
        Run all validation checks.

        Returns:
            List of validation issues found
        """
        self.issues = []

        self._check_unconnected_pins()
        self._check_ground_reference()
        self._check_wire_endpoints()
        self._check_overlapping_components()
        self._check_wire_crossings()  # NEW: Check for wire crossings

        return self.issues
    
    def _check_unconnected_pins(self):
        """Check for pins that are not connected to anything."""
        for comp in self.circuit.components:
            # Skip ground - it's a terminal, not a component with pins
            if comp.ref == "0" or comp._symbol_type == "gnd":
                continue
            
            for pin in comp.pins:
                if not pin.is_connected:
                    # For op-amps, vpos/vneg are optional
                    if comp._symbol_type == "opamp" and pin.name in ("vpos", "vneg"):
                        self.issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Power pin not connected (may be intentional for ideal op-amp)",
                            component=comp.ref,
                            pin=pin.name
                        ))
                    else:
                        self.issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Pin not connected - wire endpoint has no destination",
                            component=comp.ref,
                            pin=pin.name
                        ))
    
    def _check_ground_reference(self):
        """Check that circuit has at least one ground reference."""
        has_ground = False
        has_ground_label = False
        
        for comp in self.circuit.components:
            if comp._symbol_type == "gnd":
                has_ground = True
                break
        
        for label, _ in self.circuit._labels:
            if label == "0" or label.lower() == "gnd":
                has_ground_label = True
                break
        
        if not has_ground and not has_ground_label:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="No ground reference found. Add a GND component or label a net '0'."
            ))
    
    def _check_wire_endpoints(self):
        """Verify all wire endpoints connect to pins or other wires."""
        # Collect all pin coordinates
        pin_coords: Set[Tuple[int, int]] = set()
        pin_to_component: dict[Tuple[int, int], Tuple[str, str]] = {}
        for comp in self.circuit.components:
            for pin in comp.pins:
                coords = pin.coords
                pin_coords.add(coords)
                pin_to_component[coords] = (comp.ref, pin.name)

        # Collect all labeled coordinates
        label_coords: Set[Tuple[int, int]] = set()
        for _, coord in self.circuit._labels:
            label_coords.add(coord)

        # Collect all wire endpoints
        wire_endpoints: Set[Tuple[int, int]] = set()
        for wire in self.circuit.router.wires:
            wire_endpoints.add(wire.start)
            wire_endpoints.add(wire.end)

        # CRITICAL CHECK: Verify wire endpoints actually align with pins
        tolerance = 1  # Allow 1 pixel tolerance for floating point errors

        for wire in self.circuit.router.wires:
            for endpoint in (wire.start, wire.end):
                # Check if endpoint is close to any pin
                found_pin = False
                for pin_coord in pin_coords:
                    dx = abs(endpoint[0] - pin_coord[0])
                    dy = abs(endpoint[1] - pin_coord[1])
                    if dx <= tolerance and dy <= tolerance:
                        found_pin = True
                        break

                # Check if endpoint is at a label
                found_label = endpoint in label_coords

                # Check if endpoint connects to other wires (junction)
                connections_at_point = sum(1 for w in self.circuit.router.wires
                                          if endpoint in (w.start, w.end))

                # If not at pin/label and not a junction, it's floating
                if not found_pin and not found_label and connections_at_point < 2:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Wire endpoint at {endpoint} is DISCONNECTED - not at any pin location"
                    ))
                elif not found_pin and not found_label and connections_at_point >= 2:
                    # It's a junction point (multiple wires meet)
                    pass
                elif not found_pin and found_label:
                    # It's at a label, which is okay
                    pass

        # NEW CHECK: Verify marked-connected pins actually have wires nearby
        for comp in self.circuit.components:
            if comp._symbol_type == "gnd":
                continue

            for pin in comp.pins:
                if pin.is_connected:
                    pin_coord = pin.coords
                    # Check if any wire endpoint is near this pin
                    found_wire = False
                    for wire_endpoint in wire_endpoints:
                        dx = abs(pin_coord[0] - wire_endpoint[0])
                        dy = abs(pin_coord[1] - wire_endpoint[1])
                        if dx <= tolerance and dy <= tolerance:
                            found_wire = True
                            break

                    # Also check if pin has a label (labels count as connections)
                    has_label = pin.label is not None

                    if not found_wire and not has_label:
                        self.issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Pin marked as connected but no wire found at pin location {pin_coord}",
                            component=comp.ref,
                            pin=pin.name
                        ))
    
    def _check_overlapping_components(self):
        """Check for components placed at the same position."""
        positions = {}
        for comp in self.circuit.components:
            pos = comp.position
            if pos in positions:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Components overlap at position {pos}",
                    component=f"{positions[pos]}, {comp.ref}"
                ))
            else:
                positions[pos] = comp.ref

    def _check_wire_crossings(self):
        """Check for unintended wire crossings between connections."""
        # Check all pairs of connections
        for i, conn1 in enumerate(self.circuit.connections):
            for conn2 in self.circuit.connections[i+1:]:
                # Check each pair of wire segments
                for wire1 in conn1.wires:
                    for wire2 in conn2.wires:
                        crossing_point = _segments_intersect(wire1, wire2)

                        if crossing_point:
                            self.issues.append(ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                message=self._format_crossing_error_with_node_suggestion(
                                    conn1, conn2, crossing_point
                                )
                            ))

    def _format_crossing_error_with_node_suggestion(
        self,
        conn1: "Connection",
        conn2: "Connection",
        point: Tuple[int, int]
    ) -> str:
        """Generate detailed error message suggesting node-based fix."""

        # Convert crossing point to grid coordinates
        grid_row = (point[1] - 100) // self.circuit.grid_unit
        grid_col = (point[0] - 100) // self.circuit.grid_unit

        msg = f"Wire crossing detected at position {point} (grid: row={grid_row}, col={grid_col})!\n"
        msg += f"  Connection 1: {conn1.description}\n"
        msg += f"  Connection 2: {conn2.description}\n"
        msg += f"\n"
        msg += f"  To fix this crossing:\n"
        msg += f"\n"
        msg += f"  Option 1 (RECOMMENDED): Create nodes and route through them\n"
        msg += f"    This creates explicit junction points to avoid the crossing.\n"
        msg += f"\n"

        # Get component and pin references
        comp_a1 = conn1.pin_a.component.ref
        pin_a1 = conn1.pin_a.name
        comp_b1 = conn1.pin_b.component.ref
        pin_b1 = conn1.pin_b.name

        comp_a2 = conn2.pin_a.component.ref
        pin_a2 = conn2.pin_a.name
        comp_b2 = conn2.pin_b.component.ref
        pin_b2 = conn2.pin_b.name

        msg += f"    # Step 1: Create nodes near crossing point (adjust position as needed)\n"
        msg += f"    node1 = c.create_node('NET1', row={grid_row}, col={grid_col})\n"
        msg += f"    node2 = c.create_node('NET2', row={grid_row}, col={grid_col + 1})  # Offset to avoid overlap\n"
        msg += f"\n"
        msg += f"    # Step 2: Replace direct connections with node-based routing\n"
        msg += f"    # Remove: c.connect({comp_a1}.{pin_a1}, {comp_b1}.{pin_b1})\n"
        msg += f"    c.connect({comp_a1}.{pin_a1}, node1)\n"
        msg += f"    c.connect(node1, {comp_b1}.{pin_b1})\n"
        msg += f"\n"
        msg += f"    # Remove: c.connect({comp_a2}.{pin_a2}, {comp_b2}.{pin_b2})\n"
        msg += f"    c.connect({comp_a2}.{pin_a2}, node2)\n"
        msg += f"    c.connect(node2, {comp_b2}.{pin_b2})\n"
        msg += f"\n"
        msg += f"  Option 2: Use labels for wireless connection (eliminates one wire path)\n"
        msg += f"    This creates a named net connection without physical wires.\n"
        msg += f"\n"
        msg += f"    # Remove one of the connections and use labels instead\n"
        msg += f"    # For example, to eliminate Connection 2's wires:\n"
        msg += f"    # Remove: c.connect({comp_a2}.{pin_a2}, {comp_b2}.{pin_b2})\n"
        msg += f"    c.label({comp_a2}.{pin_a2}, 'NET_NAME')\n"
        msg += f"    c.label({comp_b2}.{pin_b2}, 'NET_NAME')\n"
        msg += f"\n"
        msg += f"  Option 3: Reposition components to avoid crossing\n"
        msg += f"    - Move components on the grid so wires don't intersect\n"
        msg += f"    - Adjust row/col values when placing components"

        return msg

    def has_errors(self) -> bool:
        """Check if any errors (not warnings) were found."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    def print_report(self):
        """Print a formatted validation report."""
        if not self.issues:
            print("✓ Circuit validation passed - no issues found")
            return
        
        errors = [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
        infos = [i for i in self.issues if i.severity == ValidationSeverity.INFO]
        
        print(f"Circuit validation: {len(errors)} error(s), {len(warnings)} warning(s)\n")
        
        for issue in errors:
            print(f"  ✗ {issue}")
        for issue in warnings:
            print(f"  ⚠ {issue}")
        for issue in infos:
            print(f"  ℹ {issue}")
