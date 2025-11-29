"""
Main Circuit class for building and exporting LTspice schematics.
"""

from typing import List, Optional, Tuple, Union
from .components import Component, GND
from .pin import Pin
from .routing import Connection, Router, Wire
from .validation import CircuitValidator, ValidationIssue
from .constants import GRID_SPACING, PIN_OFFSETS
from . import alignment


class Circuit:
    """
    Main class for building LTspice circuits.
    
    Provides a grid-based placement system and automatic wire routing.
    
    Example:
        >>> c = Circuit(grid_size=10)
        >>> r1 = c.place(R("1k"), row=0, col=2)
        >>> c1 = c.place(C("100n"), row=2, col=2)
        >>> c.connect(r1.p1, c1.p2)
        >>> c.save("circuit.asc")
    
    Attributes:
        grid_unit: Size of one grid cell in LTspice units (default: 64)
        components: List of all placed components
        width: Schematic width in pixels
        height: Schematic height in pixels
    """
    
    def __init__(self, grid_size: int = 10, grid_unit: int = GRID_SPACING):
        """
        Initialize a new circuit.

        Args:
            grid_size: Number of grid cells (determines schematic size)
            grid_unit: Pixels per grid cell (default: 64, which is 4x the LTspice base unit of 16)
        """
        self.grid_unit = grid_unit
        self.grid_size = grid_size
        self.width = grid_size * grid_unit + 200
        self.height = grid_size * grid_unit + 200
        
        self.components: List[Component] = []
        self.router = Router()
        self.connections: List["Connection"] = []  # Track all connections for validation
        self._labels: List[Tuple[str, Tuple[int, int]]] = []
        
        # Reset component counters for clean numbering
        Component.reset_counters()
    
    def _grid_to_pixels(self, row: int, col: int) -> Tuple[int, int]:
        """Convert grid coordinates to pixel coordinates."""
        # Add offset to keep components away from edge
        x = col * self.grid_unit + 100
        y = row * self.grid_unit + 100
        return (x, y)
    
    def place(self, component: Component, row: int, col: int,
              rotation: int = 0, mirror: bool = False, align_pins: bool = True,
              align_pin: str = "p1") -> Component:
        """
        Place a component on the grid with automatic pin alignment.

        Args:
            component: The component to place (R, C, L, V, I, OpAmp, GND)
            row: Grid row (0-indexed, top to bottom)
            col: Grid column (0-indexed, left to right)
            rotation: Rotation in degrees (0, 90, 180, 270)
            mirror: Whether to mirror horizontally
            align_pins: If True, adjust component origin so pins align to grid
            align_pin: Which pin to align to the grid point (default: "p1")

        Returns:
            The placed component (for chaining/pin access)

        Raises:
            ValueError: If rotation is not a multiple of 90
        """
        if rotation not in (0, 90, 180, 270):
            raise ValueError(f"Rotation must be 0, 90, 180, or 270. Got: {rotation}")

        # Set rotation first (needed for alignment calculation)
        component.rotation = rotation
        component.mirror = mirror

        if align_pins:
            # Calculate aligned origin so specified pin ends up at grid point
            component.position = alignment.calculate_aligned_origin(
                component._symbol_type,
                row,
                col,
                rotation,
                self.grid_unit,
                align_pin
            )
        else:
            # Place component origin directly at grid point (old behavior)
            component.position = self._grid_to_pixels(row, col)

        self.components.append(component)
        return component

    def place_horizontal(self, components: List[Component], row: int, start_col: int,
                         pin_spacing: int = 0) -> List[Component]:
        """
        Place components horizontally in series with pins touching.

        Components are placed CONTINUOUSLY so adjacent pins connect directly,
        NOT on a regular grid. This matches how LTspice actually works.

        Args:
            components: List of components to place
            row: Grid row for the Y-coordinate
            start_col: Starting column for first component
            pin_spacing: Gap between adjacent pins in pixels (default: 0 for touching)

        Returns:
            List of placed components

        Example:
            >>> c.place_horizontal([R("10"), L("1m"), C("1u")], row=2, start_col=2)
        """
        from .constants import PIN_OFFSETS

        placed = []
        current_x = None  # Will be set based on actual pin positions

        for i, comp in enumerate(components):
            # Two-terminal components get R90 for horizontal orientation
            if hasattr(comp, 'p1') and hasattr(comp, 'p2'):
                rotation = 90
                align_pin = "p1"
            else:
                # Other components (sources, etc.) use R0
                rotation = 0
                align_pin = "positive" if hasattr(comp, 'positive') else None

            # Set rotation first (needed for offset lookup)
            comp.rotation = rotation
            comp.mirror = False

            # For first component, use grid-based positioning
            if i == 0:
                comp.position = alignment.calculate_aligned_origin(
                    comp._symbol_type,
                    row,
                    start_col,
                    rotation,
                    self.grid_unit,
                    align_pin if align_pin else "p1"
                )
                # Get the p2 position of this component for next placement
                if hasattr(comp, 'p2'):
                    # Temporarily add to components list to get pin coords
                    self.components.append(comp)
                    current_x = comp.p2.coords[0] + pin_spacing
                    self.components.pop()  # Remove temporarily
            else:
                # Place so p1 is at current_x
                target_y = alignment.get_connection_point(row, 0, self.grid_unit)[1]

                # Get p1 offset for this rotation
                rot_offsets = PIN_OFFSETS[comp._symbol_type][rotation]
                p1_offset = rot_offsets.get(align_pin if align_pin else "p1", (0, 0))

                # Calculate origin: p1_position = origin + p1_offset
                # So: origin = p1_position - p1_offset
                origin_x = current_x - p1_offset[0]
                origin_y = target_y - p1_offset[1]
                comp.position = (origin_x, origin_y)

                # Update current_x for next component
                if hasattr(comp, 'p2'):
                    self.components.append(comp)
                    current_x = comp.p2.coords[0] + pin_spacing
                    self.components.pop()

            self.components.append(comp)
            placed.append(comp)

        return placed

    def place_vertical(self, components: List[Component], col: int, start_row: int,
                       spacing: int = 2) -> List[Component]:
        """
        Place components vertically in series with automatic pin alignment.

        All components will be oriented vertically (R0 for two-terminal components)
        and their pins will be aligned to the same x-coordinate.

        Args:
            components: List of components to place
            col: Grid column for the series
            start_row: Starting row
            spacing: Grid cells between component pins (default: 2)

        Returns:
            List of placed components

        Example:
            >>> c.place_vertical([R("10"), L("1m"), C("1u")], col=2, start_row=2)
        """
        placed = []
        current_row = start_row

        for comp in components:
            # All components use R0 for vertical orientation
            rotation = 0
            align_pin = "p1" if hasattr(comp, 'p1') else "positive"

            # Place with alignment
            self.place(comp, row=current_row, col=col, rotation=rotation,
                      align_pins=True, align_pin=align_pin)

            placed.append(comp)
            current_row += spacing

        return placed

    def create_node(self, name: str, row: int, col: int) -> "Component":
        """
        Create and place a labeled node (junction point) on the grid.

        Nodes are physical junction points where multiple connections can meet.
        This is useful for avoiding wire crossings by routing connections through
        explicit junction points.

        Args:
            name: Node name (e.g., "VCC", "GND", "NET1", "SIGNAL_A")
            row: Grid row position
            col: Grid column position

        Returns:
            Node object that can be used in connect() calls

        Example:
            >>> node1 = c.create_node("VCC", row=2, col=3)
            >>> c.connect(r1.p1, node1)
            >>> c.connect(r2.p1, node1)  # Both connect to same node
            >>>
            >>> # Avoid crossings by routing through nodes:
            >>> horiz_node = c.create_node("HORIZ_NET", row=2, col=4)
            >>> c.connect(r1.p2, horiz_node)
            >>> c.connect(horiz_node, r2.p1)
        """
        from .components import Node

        node = Node(name)
        self.place(node, row=row, col=col)
        return node

    def connect(self, pin_a: Union[Pin, Component],
                pin_b: Optional[Union[Pin, Component]] = None) -> List[Wire]:
        """
        Connect two pins with automatically routed wires.

        Can accept Pin objects directly, or components with single connection points
        (GND, Node).

        Args:
            pin_a: First pin, GND, or Node (e.g., r1.p1, gnd, node1)
            pin_b: Second pin, GND, or Node

        Returns:
            List of generated Wire segments

        Examples:
            >>> c.connect(r1.p1, c1.p2)           # Pin to pin
            >>> c.connect(v1.negative, gnd)       # Pin to GND component
            >>> c.connect(r1.p2, node1)           # Pin to Node
            >>> c.connect(node1, node2)           # Node to node (creates wire between nodes)
        """
        from .components import GND, Node

        # Handle component shortcuts (GND, Node)
        if isinstance(pin_a, Component):
            if isinstance(pin_a, (GND, Node)):
                pin_a = pin_a.pin
            else:
                raise ValueError(f"Cannot connect component {pin_a.ref} directly. Use a specific pin.")

        if isinstance(pin_b, Component):
            if isinstance(pin_b, (GND, Node)):
                pin_b = pin_b.pin
            else:
                raise ValueError(f"Cannot connect component {pin_b.ref} directly. Use a specific pin.")
        
        # Get coordinates
        x1, y1 = pin_a.coords
        x2, y2 = pin_b.coords
        
        # Mark pins as connected
        pin_a.mark_connected()
        pin_b.mark_connected()
        
        # Gather all other pin coordinates to avoid routing through them
        blocked_points = set()
        for comp in self.components:
            for pin in comp.pins:
                if pin is pin_a or pin is pin_b:
                    continue
                blocked_points.add(pin.coords)

        # Route wires
        wires = self.router.route(
            x1, y1, x2, y2,
            blocked_points=blocked_points,
            grid_unit=self.grid_unit,
        )

        # Track this connection for crossing detection
        from .routing import Connection
        connection = Connection(
            pin_a=pin_a,
            pin_b=pin_b,
            wires=wires
        )
        self.connections.append(connection)

        return wires
    
    def label(self, pin: Union[Pin, Component], name: str):
        """
        Add a net label to a pin.
        
        Labels create named nets that can connect distant points
        without explicit wires.
        
        Args:
            pin: The pin to label
            name: Net name (e.g., "VIN", "VOUT", "0" for ground)
        
        Example:
            >>> c.label(r1.p2, "VOUT")
            >>> c.label(opamp.out, "VOUT")  # Same net, connected
        """
        if isinstance(pin, Component):
            if isinstance(pin, GND):
                pin = pin.pin
            else:
                raise ValueError(f"Cannot label component {pin.ref} directly. Use a specific pin.")
        
        pin.label = name
        pin.mark_connected()
        self._labels.append((name, pin.coords))

    def beautify(self, print_report: bool = True) -> int:
        """
        Tidy small layout artifacts without moving unrelated components.

        Current pass focuses on the common elbow seen in grounded loads and
        simple series chains: a two-terminal part whose pin reaches its driver
        through an L-shaped connection. The part is slid so that pin lands on
        the elbow point, turning the run into a single straight segment. Only
        connections touching the moved component are re-routed; all other
        wires/components stay untouched. Components slide only along the axis
        perpendicular to their orientation (vertical parts slide horizontally;
        horizontal parts slide vertically) so orientation remains unchanged.

        Returns:
            Number of components that were repositioned.
        """

        def is_two_terminal(comp: Component) -> bool:
            return hasattr(comp, "p1") and hasattr(comp, "p2")

        def elbow_point(conn: "Connection") -> Optional[Tuple[int, int]]:
            """Return the bend point for a simple two-segment L connection."""
            if len(conn.wires) != 2:
                return None

            first, second = conn.wires
            shared = None
            if first.end == second.start:
                shared = first.end
            elif second.end == first.start:
                # Wire list reversed; normalize to keep shared as the elbow
                first, second = second, first
                shared = first.end
            else:
                return None

            def orientation(wire: Wire) -> Optional[str]:
                if wire.start[0] == wire.end[0]:
                    return "v"
                if wire.start[1] == wire.end[1]:
                    return "h"
                return None

            if orientation(first) == orientation(second) or shared is None:
                return None
            return shared

        def allowed_single_axis_slide(comp: Component, old_origin: Tuple[int, int], new_origin: Tuple[int, int]) -> bool:
            """
            Permit moves only along the axis perpendicular to the component orientation.
            Vertical parts (rotation 0/180) may slide in X only; horizontal parts
            (rotation 90/270) may slide in Y only.
            """
            dx = new_origin[0] - old_origin[0]
            dy = new_origin[1] - old_origin[1]
            if dx == 0 and dy == 0:
                return False

            is_vertical = comp.rotation % 180 == 0
            if is_vertical and dy != 0:
                return False
            if not is_vertical and dx != 0:
                return False
            return True

        def touches_symbol(comp: Component, symbol_type: str) -> bool:
            """Return True if this component connects to any component of given symbol type."""
            for conn in self.connections:
                if conn.pin_a.component is comp:
                    other_comp = conn.pin_b.component
                elif conn.pin_b.component is comp:
                    other_comp = conn.pin_a.component
                else:
                    continue
                if other_comp._symbol_type == symbol_type:
                    return True
            return False

        def count_corners_and_wires(pin_a: Pin, pin_b: Pin, blocked_points: set[Tuple[int, int]]) -> Tuple[int, int]:
            """
            Compute (corner_count, wire_count) for a connection using a temporary
            router so we don't mutate the real wiring while evaluating options.
            """
            from .routing import Router  # Local import to avoid cycle at module load

            temp_router = Router()
            wires = temp_router.route(
                pin_a.coords[0],
                pin_a.coords[1],
                pin_b.coords[0],
                pin_b.coords[1],
                blocked_points=blocked_points,
                grid_unit=self.grid_unit,
            )

            if not wires:
                return (0, 0)

            corners = 0
            for i in range(1, len(wires)):
                if wires[i - 1].end != wires[i].start:
                    # Unusual discontinuity counts as a corner
                    corners += 1
                    continue
                # Different orientation => a corner
                if (wires[i - 1].start[0] == wires[i - 1].end[0]) != (wires[i].start[0] == wires[i].end[0]):
                    corners += 1
            return (corners, len(wires))

        def find_better_slide(comp: Component, pin: Pin, elbow: Tuple[int, int]) -> Optional[Tuple[int, int]]:
            """
            Evaluate both elbows (current and mirrored across the pin) and pick the
            one that reduces corners/wires without violating axis rules.
            """
            origin_candidates = []

            def evaluate(target: Tuple[int, int]) -> None:
                new_origin = self._origin_for_pin(comp, pin.name, target)
                if not allowed_single_axis_slide(comp, comp.position, new_origin):
                    return
                if self._position_occupied(new_origin, ignore=comp):
                    return
                origin_candidates.append(new_origin)

            # Primary elbow
            evaluate(elbow)

            # Mirror across the pin coordinate to try the opposite direction
            px, py = pin.coords
            ex, ey = elbow
            mirrored = (2 * px - ex, 2 * py - ey)
            evaluate(mirrored)

            if not origin_candidates:
                return None

            def score_for_origin(origin: Tuple[int, int]) -> Tuple[int, int]:
                """Return aggregate (corners, wires) if component were at origin."""
                orig_pos = comp.position
                comp.position = origin

                component_conns = [
                    conn for conn in self.connections
                    if conn.pin_a.component is comp or conn.pin_b.component is comp
                ]
                total_corners = 0
                total_wires = 0
                for conn in component_conns:
                    pin_a = conn.pin_a
                    pin_b = conn.pin_b
                    blocked_points = set()
                    for other_comp in self.components:
                        for pin in other_comp.pins:
                            if pin is pin_a or pin is pin_b:
                                continue
                            blocked_points.add(pin.coords)

                    c, w = count_corners_and_wires(pin_a, pin_b, blocked_points)
                    total_corners += c
                    total_wires += w

                comp.position = orig_pos  # restore
                return (total_corners, total_wires)

            baseline_score = score_for_origin(comp.position)

            # Choose the candidate that yields the fewest corners, then wires
            best_origin = None
            best_score = (10**6, 10**6)  # (corners, wires)
            for candidate in origin_candidates:
                score = score_for_origin(candidate)
                if score < best_score:
                    best_score = score
                    best_origin = candidate

            # Only move if it improves over baseline
            if best_origin and best_score < baseline_score:
                return best_origin
            return None

        moved = 0
        touched_components = set()

        # Pass 1: absorb L-shaped elbows by moving the attached two-terminal part to the corner
        for conn in list(self.connections):
            elbow = elbow_point(conn)
            if not elbow:
                continue

            for pin in (conn.pin_a, conn.pin_b):
                comp = pin.component
                if comp in touched_components:
                    continue
                if not is_two_terminal(comp):
                    continue

                # Avoid moving feedback/bias parts tied into op-amps; keep analog intent intact
                if touches_symbol(comp, "opamp"):
                    continue

                other_pin = None
                if hasattr(comp, "p1") and hasattr(comp, "p2"):
                    other_pin = comp.p2 if pin.name == "p1" else comp.p1

                if other_pin is None:
                    continue

                old_pin_coords = {p.name: p.coords for p in comp.pins}
                new_origin = find_better_slide(comp, pin, elbow)
                if not new_origin:
                    continue

                comp.position = new_origin
                touched_components.add(comp)
                self._update_labels_for_component(comp, old_pin_coords)
                self._reroute_component_connections(comp)
                moved += 1
                break  # Only move one side of the connection

        if print_report:
            print(f"Beautify: moved {moved} component(s)")

        return moved
    
    def validate(self, print_report: bool = True) -> List[ValidationIssue]:
        """
        Validate circuit connectivity and configuration.
        
        Args:
            print_report: Whether to print validation results
        
        Returns:
            List of validation issues found
        """
        validator = CircuitValidator(self)
        issues = validator.validate()
        
        if print_report:
            validator.print_report()
        
        return issues
    
    def to_asc(self) -> str:
        """
        Generate complete ASC file content.
        
        Returns:
            String containing valid LTspice ASC schematic
        """
        lines = []
        
        # Header
        lines.append("Version 4")
        lines.append(f"SHEET 1 {self.width} {self.height}")
        
        # Wires first (LTspice convention)
        for wire in self.router.wires:
            lines.append(wire.to_asc())
        
        # Net labels (FLAGS)
        for label, (x, y) in self._labels:
            lines.append(f"FLAG {x} {y} {label}")
        
        # Components
        for comp in self.components:
            lines.append(comp.to_asc().rstrip())
        
        return "\n".join(lines) + "\n"
    
    def save(self, filename: str, validate: bool = True):
        """
        Save circuit to an ASC file.
        
        Args:
            filename: Output filename (should end in .asc)
            validate: Whether to run validation before saving
        
        Raises:
            ValueError: If validation fails with errors and validate=True
        """
        if validate:
            validator = CircuitValidator(self)
            issues = validator.validate()
            validator.print_report()
            
            if validator.has_errors():
                raise ValueError(
                    f"Circuit has {len([i for i in issues if i.severity.value == 'error'])} error(s). "
                    "Fix errors or use save(..., validate=False) to save anyway."
                )
        
        with open(filename, 'w') as f:
            f.write(self.to_asc())
        
        print(f"✓ Saved to {filename}")
    
    def __repr__(self):
        return f"Circuit({len(self.components)} components, {len(self.router.wires)} wires)"

    def _origin_for_pin(
        self,
        comp: Component,
        pin_name: str,
        target: Tuple[int, int],
        rotation_override: Optional[int] = None
    ) -> Tuple[int, int]:
        """Calculate a new origin so a given pin lands at target."""
        rotation = rotation_override if rotation_override is not None else comp.rotation
        offsets_for_rotation = PIN_OFFSETS.get(comp._symbol_type, {}).get(rotation, {})
        if pin_name not in offsets_for_rotation:
            return comp.position

        ox, oy = offsets_for_rotation[pin_name]
        mirror = comp.mirror
        if mirror:
            ox = -ox
        return (target[0] - ox, target[1] - oy)

    def _position_occupied(self, position: Tuple[int, int], ignore: Optional[Component] = None) -> bool:
        """Check if another component already sits at this origin."""
        for comp in self.components:
            if comp is ignore:
                continue
            if comp.position == position:
                return True
        return False

    def _reroute_component_connections(self, component: Component):
        """
        Re-route only the connections attached to the given component.
        
        This leaves unrelated wiring untouched while still ensuring pins
        on the moved component reach their peers.
        """
        # Collect connections to this component
        component_conns = [
            conn for conn in self.connections
            if conn.pin_a.component is component or conn.pin_b.component is component
        ]

        # Remove old wires for these connections
        wires_to_remove = []
        for conn in component_conns:
            wires_to_remove.extend(conn.wires)
        self.router.remove_wires(wires_to_remove)

        # Re-route each connection with updated pin coordinates
        for conn in component_conns:
            pin_a = conn.pin_a
            pin_b = conn.pin_b

            blocked_points = set()
            for comp in self.components:
                for pin in comp.pins:
                    if pin is pin_a or pin is pin_b:
                        continue
                    blocked_points.add(pin.coords)

            new_wires = self.router.route(
                pin_a.coords[0],
                pin_a.coords[1],
                pin_b.coords[0],
                pin_b.coords[1],
                blocked_points=blocked_points,
                grid_unit=self.grid_unit,
            )
            conn.wires = new_wires

    def _update_labels_for_component(self, component: Component, old_pin_coords: dict[str, Tuple[int, int]]):
        """
        Refresh label coordinates for pins belonging to the moved component.
        
        Labels are stored as coordinate tuples; when a component moves we need
        to carry the associated labels to the new pin coordinates to avoid
        leaving labels floating in space.
        """
        if not self._labels:
            return

        updated_labels = []
        for name, coords in self._labels:
            replaced = False
            for pin in component.pins:
                if pin.label == name and old_pin_coords.get(pin.name) == coords:
                    updated_labels.append((name, pin.coords))
                    replaced = True
                    break
            if not replaced:
                updated_labels.append((name, coords))

        self._labels = updated_labels
