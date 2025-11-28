"""
Pin class for component terminals.
Handles coordinate calculations with rotation/mirror transformations.
"""

from typing import TYPE_CHECKING, Optional
import math

if TYPE_CHECKING:
    from .components import Component


class Pin:
    """
    Represents a connection point on a component.
    
    Attributes:
        component: The parent component this pin belongs to
        name: Pin identifier (e.g., 'p1', 'inv', 'out')
        offset: Base offset from component origin (before rotation)
        label: Optional net label for this pin
    """
    
    def __init__(self, component: "Component", name: str):
        """
        Initialize a pin.

        Note: Offset is no longer stored here - it's looked up from PIN_OFFSETS
        based on component rotation at the time coords are requested.
        """
        self.component = component
        self.name = name
        self.label: Optional[str] = None
        self._connected = False

    @property
    def coords(self) -> tuple[int, int]:
        """
        Get absolute coordinates of this pin.
        Uses rotation-specific offsets from PIN_OFFSETS table.
        """
        from .constants import PIN_OFFSETS

        base_x, base_y = self.component.position
        rotation = self.component.rotation
        symbol_type = self.component._symbol_type

        # Look up rotation-specific offset
        if symbol_type not in PIN_OFFSETS:
            raise ValueError(f"Unknown component type: {symbol_type}")

        rotation_offsets = PIN_OFFSETS[symbol_type].get(rotation)
        if rotation_offsets is None:
            raise ValueError(f"No pin offsets defined for {symbol_type} at rotation {rotation}")

        if self.name not in rotation_offsets:
            raise ValueError(f"Pin '{self.name}' not found in offsets for {symbol_type} R{rotation}")

        ox, oy = rotation_offsets[self.name]

        # Apply horizontal mirror if needed
        if self.component.mirror:
            ox = -ox

        return (base_x + ox, base_y + oy)
    
    def mark_connected(self):
        """Mark this pin as connected to a wire."""
        self._connected = True
    
    @property
    def is_connected(self) -> bool:
        """Check if this pin has been connected."""
        return self._connected or self.label is not None
    
    def __repr__(self):
        return f"Pin({self.component.ref}.{self.name} @ {self.coords})"
