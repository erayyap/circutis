"""
asclib - Python library for generating LTspice ASC schematic files.

A grid-based circuit builder with automatic wire routing.

Example:
    from asclib import Circuit, R, C, V, GND
    
    c = Circuit(grid_size=10)
    
    v1 = c.place(V("12V"), row=0, col=0)
    r1 = c.place(R("1k"), row=0, col=2)
    c1 = c.place(C("100n"), row=2, col=2)
    gnd = c.place(GND(), row=2, col=0)
    
    c.connect(v1.positive, r1.p1)
    c.connect(r1.p2, c1.p1)
    c.connect(c1.p2, gnd)
    c.connect(v1.negative, gnd)
    
    c.save("my_circuit.asc")

Components:
    R      - Resistor (pins: p1, p2)
    L      - Inductor (pins: p1, p2)
    C      - Capacitor (pins: p1, p2)
    V      - Voltage source (pins: positive, negative)
    I      - Current source (pins: positive, negative)
    OpAmp  - Operational amplifier (pins: inv, noninv, out, vpos, vneg)
    GND    - Ground symbol (pin: pin)
"""

from .circuit import Circuit
from .components import (
    Component,
    R, L, C,
    V, I,
    VoltageSource,
    CurrentSource,
    OpAmp,
    GND,
    Node,
)
from .pin import Pin
from .routing import Wire, Router, Connection
from .validation import CircuitValidator, ValidationIssue, ValidationSeverity

__version__ = "0.1.0"
__author__ = "asclib"

__all__ = [
    # Main class
    "Circuit",

    # Components
    "Component",
    "R", "L", "C",
    "V", "I",
    "VoltageSource", "CurrentSource",
    "OpAmp",
    "GND",
    "Node",

    # Supporting classes
    "Pin",
    "Wire",
    "Router",
    "Connection",

    # Validation
    "CircuitValidator",
    "ValidationIssue",
    "ValidationSeverity",
]
