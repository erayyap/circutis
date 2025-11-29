"""
Component classes for circuit elements.
Each component knows its symbol, pins, and how to generate ASC output.
"""

from typing import Optional, Dict, List
from .pin import Pin
from .constants import PIN_OFFSETS, SYMBOL_NAMES, MIRROR_CODES


class Component:
    """
    Base class for all circuit components.
    
    Attributes:
        value: Component value (e.g., "1k", "100n", "LT1001")
        ref: Reference designator (e.g., "R1", "C2", "U1")
        position: (x, y) coordinates in LTspice units
        rotation: Rotation in degrees (0, 90, 180, 270)
        mirror: Whether component is horizontally mirrored
    """
    
    _counter: Dict[str, int] = {}  # Class-level counter for auto-naming
    _prefix: str = "X"  # Override in subclasses
    _symbol_type: str = ""  # Override in subclasses
    
    def __init__(self, value: str = "", ref: Optional[str] = None):
        self.value = value
        self.ref = ref or self._auto_ref()
        self.position: tuple[int, int] = (0, 0)
        self.rotation: int = 0
        self.mirror: bool = False
        self._pins: Dict[str, Pin] = {}
        self._init_pins()
    
    def _auto_ref(self) -> str:
        """Generate automatic reference designator."""
        prefix = self._prefix
        if prefix not in Component._counter:
            Component._counter[prefix] = 0
        Component._counter[prefix] += 1
        return f"{prefix}{Component._counter[prefix]}"
    
    @classmethod
    def reset_counters(cls):
        """Reset all reference designator counters."""
        cls._counter = {}
    
    def _init_pins(self):
        """Initialize pins based on component type. Override in subclasses."""
        # Get pin names from R0 rotation (all rotations have same pin names)
        pin_offsets = PIN_OFFSETS.get(self._symbol_type, {})
        if not pin_offsets:
            return

        # Get pin names from rotation 0 definition
        r0_pins = pin_offsets.get(0, {})
        for name in r0_pins.keys():
            self._pins[name] = Pin(self, name)
    
    def pin(self, name: str) -> Pin:
        """Get a pin by name."""
        if name not in self._pins:
            raise ValueError(f"Pin '{name}' not found on {self.ref}. Available: {list(self._pins.keys())}")
        return self._pins[name]
    
    @property
    def pins(self) -> List[Pin]:
        """Get all pins."""
        return list(self._pins.values())
    
    @property
    def unconnected_pins(self) -> List[Pin]:
        """Get all pins that haven't been connected."""
        return [p for p in self._pins.values() if not p.is_connected]
    
    def to_asc(self) -> str:
        """Generate ASC representation of this component."""
        x, y = self.position
        rot_code = MIRROR_CODES.get((self.rotation, self.mirror), "R0")
        symbol = SYMBOL_NAMES.get(self._symbol_type, self._symbol_type)
        
        lines = [f"SYMBOL {symbol} {x} {y} {rot_code}"]
        lines.append(f"SYMATTR InstName {self.ref}")
        if self.value:
            lines.append(f"SYMATTR Value {self.value}")
        
        return "\n".join(lines) + "\n"
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.ref}={self.value})"


class TwoTerminal(Component):
    """Base class for two-terminal components (R, L, C)."""
    
    @property
    def p1(self) -> Pin:
        return self._pins["p1"]
    
    @property
    def p2(self) -> Pin:
        return self._pins["p2"]


class R(TwoTerminal):
    """Resistor component."""
    _prefix = "R"
    _symbol_type = "res"


class L(TwoTerminal):
    """Inductor component."""
    _prefix = "L"
    _symbol_type = "ind"


class C(TwoTerminal):
    """Capacitor component."""
    _prefix = "C"
    _symbol_type = "cap"


class VoltageSource(Component):
    """Voltage source (DC, AC, PULSE, etc.)."""
    _prefix = "V"
    _symbol_type = "voltage"
    
    @property
    def positive(self) -> Pin:
        return self._pins["positive"]
    
    @property
    def negative(self) -> Pin:
        return self._pins["negative"]


class CurrentSource(Component):
    """Current source."""
    _prefix = "I"
    _symbol_type = "current"
    
    @property
    def positive(self) -> Pin:
        return self._pins["positive"]
    
    @property
    def negative(self) -> Pin:
        return self._pins["negative"]


class GND(Component):
    """
    Ground symbol.
    Note: In LTspice, ground is a special symbol that connects to net 0.
    """
    _prefix = "GND"
    _symbol_type = "gnd"

    def __init__(self):
        super().__init__(value="", ref=None)
        # GND doesn't need a unique ref in LTspice
        self.ref = "0"

    @property
    def pin(self) -> Pin:
        return self._pins["pin"]

    def _auto_ref(self) -> str:
        # Ground symbols don't have numbered refs
        return "0"

    def to_asc(self) -> str:
        x, y = self.position
        # Ground uses FLAG command in LTspice
        return f"FLAG {x} {y} 0\n"


class Node(Component):
    """
    Represents a labeled junction point (node) on the circuit.

    Nodes are connection points where multiple wires can meet.
    Unlike labels (which are "wireless" connections), nodes are physical
    junction points with coordinates that appear in the schematic.

    This is useful for:
    - Avoiding wire crossings by routing through explicit junction points
    - Creating clear connection points for complex circuits
    - Documenting important nets (VCC, GND, signal names, etc.)

    Example:
        >>> node1 = c.create_node("VCC", row=2, col=3)
        >>> c.connect(r1.p1, node1)
        >>> c.connect(r2.p1, node1)  # Multiple connections to same node
    """
    _prefix = "NODE"
    _symbol_type = "node"

    def __init__(self, name: str, ref: Optional[str] = None):
        """
        Create a named node.

        Args:
            name: Node name (e.g., "VCC", "GND", "NET1", "SIGNAL_A")
            ref: Optional reference (auto-generated if not provided)
        """
        super().__init__(value=name, ref=ref)
        self.name = name

    @property
    def pin(self) -> Pin:
        """Get the connection point for this node."""
        return self._pins["pin"]

    def to_asc(self) -> str:
        """Generate ASC representation of this node."""
        x, y = self.position
        # Nodes are represented as net labels (FLAGS) in LTspice
        return f"FLAG {x} {y} {self.name}\n"

    def __repr__(self):
        return f"Node({self.name})"


class OpAmp(Component):
    """
    Operational amplifier.
    
    Default symbol is opamp2 (generic op-amp).
    For specific models, pass the model name as value (e.g., "LT1001", "AD820").
    """
    _prefix = "U"
    _symbol_type = "opamp"
    
    def __init__(self, model: str = "opamp", ref: Optional[str] = None):
        super().__init__(value=model, ref=ref)
        self.model = model
    
    @property
    def inv(self) -> Pin:
        """Inverting input (-)"""
        return self._pins["inv"]
    
    @property
    def noninv(self) -> Pin:
        """Non-inverting input (+)"""
        return self._pins["noninv"]
    
    @property
    def out(self) -> Pin:
        """Output"""
        return self._pins["out"]
    
    @property
    def vpos(self) -> Pin:
        """Positive supply (V+)"""
        return self._pins["vpos"]
    
    @property
    def vneg(self) -> Pin:
        """Negative supply (V-)"""
        return self._pins["vneg"]
    
    def to_asc(self) -> str:
        x, y = self.position
        rot_code = MIRROR_CODES.get((self.rotation, self.mirror), "R0")
        symbol = SYMBOL_NAMES.get(self._symbol_type, self._symbol_type)
        
        lines = [f"SYMBOL {symbol} {x} {y} {rot_code}"]
        lines.append(f"SYMATTR InstName {self.ref}")
        if self.model and self.model != "opamp":
            lines.append(f"SYMATTR Value {self.model}")
        
        return "\n".join(lines) + "\n"


# Aliases for convenience
V = VoltageSource
I = CurrentSource  # noqa: E741
