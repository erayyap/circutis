"""
Main Circuit class for building and exporting LTspice schematics.
"""

from typing import List, Optional, Tuple, Union
from .components import Component, GND
from .pin import Pin
from .routing import Router, Wire
from .validation import CircuitValidator, ValidationIssue
from .constants import DEFAULT_GRID_UNIT, GRID_SPACING, ASC_HEADER
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
        lines.append(f"Version 4")
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
