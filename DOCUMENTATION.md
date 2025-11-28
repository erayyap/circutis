# Circutis - Complete Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Components Reference](#components-reference)
6. [Circuit Building](#circuit-building)
7. [Validation](#validation)
8. [Advanced Features](#advanced-features)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

**Circutis** (based on asclib) is a Python library for programmatically generating LTspice ASC schematic files. Instead of manually drawing circuits in LTspice, you can write Python code to define your circuits with precise control over component placement, connections, and routing.

### Why Circutis?

- **Programmatic Circuit Generation**: Define circuits in code for version control and automation
- **Grid-Based Layout**: Predictable component placement using a grid system
- **Automatic Wire Routing**: Smart wire routing between components
- **Circuit Validation**: Built-in validation to catch common errors
- **Type Safety**: Pin-based connections prevent wiring mistakes
- **LTspice Compatible**: Generates standard .asc files that open directly in LTspice

---

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/erayyap/circutis.git
cd circutis

# Install with uv
uv pip install -e .
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/erayyap/circutis.git
cd circutis

# Install in development mode
pip install -e .
```

### Requirements

- Python 3.9 or higher
- No external dependencies required

---

## Quick Start

Here's a simple RC low-pass filter circuit:

```python
from asclib import Circuit, R, C, V, GND

# Create a circuit with a 10x10 grid
c = Circuit(grid_size=10)

# Place components on the grid
vin = c.place(V("AC 1"), row=0, col=0)
r1 = c.place(R("1k"), row=0, col=2)
c1 = c.place(C("100n"), row=2, col=4)
gnd = c.place(GND(), row=4, col=0)

# Connect components
c.connect(vin.positive, r1.p1)
c.connect(r1.p2, c1.p1)
c.connect(c1.p2, gnd)
c.connect(vin.negative, gnd)

# Add a label for the output
c.label(r1.p2, "VOUT")

# Save the circuit
c.save("rc_lowpass.asc")
```

This generates an LTspice schematic file that you can open and simulate.

---

## Core Concepts

### Grid System

Circuits are built on a grid system where each component occupies a position defined by `(row, col)` coordinates:

- **Grid Size**: Defines the spacing between grid points (default: 16 LTspice units)
- **Row**: Vertical position (Y-axis)
- **Col**: Horizontal position (X-axis)
- **Rotation**: Component orientation (0°, 90°, 180°, 270°)

```python
# Grid position examples
c = Circuit(grid_size=16)
r1 = c.place(R("1k"), row=0, col=0)        # Top-left
r2 = c.place(R("2k"), row=0, col=2)        # Two columns right
r3 = c.place(R("3k"), row=2, col=0)        # Two rows down
r4 = c.place(R("4k"), row=1, col=1, rotation=90)  # Rotated 90°
```

### Pins

Every component has named pins that you use for connections:

```python
# Passive components (R, L, C)
r1 = c.place(R("1k"))
r1.p1  # Pin 1
r1.p2  # Pin 2

# Voltage/Current sources
v1 = c.place(V("12"))
v1.positive  # Positive terminal
v1.negative  # Negative terminal

# Op-amps
u1 = c.place(OpAmp("LT1001"))
u1.inv      # Inverting input
u1.noninv   # Non-inverting input
u1.out      # Output
u1.vpos     # Positive supply
u1.vneg     # Negative supply

# Ground
gnd = c.place(GND())
gnd.pin  # Ground connection point
```

### Connections

There are two ways to connect components:

#### 1. Direct Wire Connections

```python
# Connect pins with wires (automatic routing)
c.connect(v1.positive, r1.p1)
c.connect(r1.p2, gnd)
```

#### 2. Net Labels (Wireless)

Use labels to connect components without visible wires:

```python
# Create wireless connections via labels
c.label(u1.vpos, "VCC")
c.label(vpos.positive, "VCC")
# Both pins labeled "VCC" are now connected
```

---

## Components Reference

### Resistor - `R(value)`

```python
r1 = c.place(R("1k"), row=0, col=0)
r2 = c.place(R("10k"), row=0, col=2, rotation=90)

# Pins: p1, p2
c.connect(r1.p1, r2.p2)
```

**Supported value formats**:
- `"1k"` - 1 kΩ
- `"10M"` - 10 MΩ
- `"100"` - 100 Ω
- `"4.7k"` - 4.7 kΩ

### Capacitor - `C(value)`

```python
c1 = c.place(C("100n"), row=0, col=0)
c2 = c.place(C("10u"), row=0, col=2)

# Pins: p1, p2
c.connect(c1.p1, c2.p2)
```

**Supported value formats**:
- `"100n"` - 100 nF
- `"10u"` - 10 µF
- `"1m"` - 1 mF
- `"47p"` - 47 pF

### Inductor - `L(value)`

```python
l1 = c.place(L("10m"), row=0, col=0)
l2 = c.place(L("100u"), row=0, col=2)

# Pins: p1, p2
c.connect(l1.p1, l2.p2)
```

**Supported value formats**:
- `"10m"` - 10 mH
- `"100u"` - 100 µH
- `"1"` - 1 H

### Voltage Source - `V(value)`

```python
# DC voltage source
vdc = c.place(V("12"), row=0, col=0)

# AC voltage source
vac = c.place(V("AC 1"), row=0, col=2)

# Sine wave
vsine = c.place(V("SINE(0 1 1k)"), row=0, col=4)

# Pins: positive, negative
c.connect(vdc.positive, r1.p1)
c.connect(vdc.negative, gnd)
```

### Current Source - `I(value)`

```python
# DC current source
idc = c.place(I("1m"), row=0, col=0)

# AC current source
iac = c.place(I("AC 100u"), row=0, col=2)

# Pins: positive, negative
c.connect(idc.positive, r1.p1)
c.connect(idc.negative, gnd)
```

### Op-Amp - `OpAmp(model)`

```python
# Generic op-amp
u1 = c.place(OpAmp(), row=0, col=0)

# Specific model
u2 = c.place(OpAmp("LT1001"), row=0, col=5)

# Pins: inv, noninv, out, vpos, vneg
c.connect(u1.noninv, vin.positive)
c.connect(u1.inv, gnd)
c.connect(u1.out, r_load.p1)

# Power connections (often use labels)
c.label(u1.vpos, "VCC")
c.label(u1.vneg, "VEE")
```

### Ground - `GND()`

```python
gnd = c.place(GND(), row=4, col=0)

# Pin: pin
c.connect(v1.negative, gnd)
c.connect(r1.p2, gnd)
```

---

## Circuit Building

### Step 1: Create Circuit Instance

```python
from asclib import Circuit

# Default grid (16 units spacing)
c = Circuit()

# Custom grid size
c = Circuit(grid_size=20)
```

### Step 2: Place Components

```python
# Place with position and optional rotation
v1 = c.place(V("12"), row=0, col=0)
r1 = c.place(R("1k"), row=0, col=2, rotation=90)
c1 = c.place(C("100n"), row=2, col=2)
gnd = c.place(GND(), row=4, col=0)
```

### Step 3: Make Connections

```python
# Wire connections
c.connect(v1.positive, r1.p1)
c.connect(r1.p2, c1.p1)
c.connect(c1.p2, gnd)
c.connect(v1.negative, gnd)

# Label connections (for power rails, etc.)
c.label(v1.positive, "VCC")
c.label(gnd, "0")
```

### Step 4: Add Labels

```python
# Label important nodes
c.label(vin.positive, "VIN")
c.label(r1.p2, "VOUT")
c.label(c1.p1, "NODE_A")
```

### Step 5: Validate

```python
# Check for issues (optional but recommended)
issues = c.validate()

if issues:
    print("Circuit has issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Circuit is valid!")
```

### Step 6: Save

```python
# Save with validation (default)
c.save("my_circuit.asc")

# Save without validation (not recommended)
c.save("my_circuit.asc", validate=False)
```

---

## Validation

The validation system catches common circuit errors:

### What Gets Validated

1. **Floating Components**: Components with unconnected pins
2. **Missing Ground**: Circuits without a ground reference
3. **Disconnected Nets**: Isolated sections of the circuit
4. **Op-Amp Power**: Op-amps with missing power connections

### Using Validation

```python
# Automatic validation during save
c.save("circuit.asc")  # Raises ValueError if issues found

# Manual validation
issues = c.validate()
for issue in issues:
    print(f"{issue.severity}: {issue.message}")
    if issue.component:
        print(f"  Component: {issue.component}")
    if issue.pins:
        print(f"  Pins: {issue.pins}")

# Skip validation (use with caution)
c.save("circuit.asc", validate=False)
```

### Example: Catching Errors

```python
c = Circuit()
v1 = c.place(V("5"), row=0, col=0)
r1 = c.place(R("1k"), row=0, col=2)
r2 = c.place(R("1k"), row=2, col=2)  # Floating!

# Only partial connections
c.connect(v1.positive, r1.p1)

# This will fail validation
try:
    c.save("bad_circuit.asc")
except ValueError as e:
    print(f"Error: {e}")
    # Error: Circuit validation failed with 3 errors
```

---

## Advanced Features

### Component Rotation

```python
# Horizontal resistor (default)
r1 = c.place(R("1k"), row=0, col=0, rotation=0)

# Vertical resistor
r2 = c.place(R("1k"), row=0, col=2, rotation=90)

# Upside down
r3 = c.place(R("1k"), row=0, col=4, rotation=180)

# Vertical (other direction)
r4 = c.place(R("1k"), row=0, col=6, rotation=270)
```

### Net Labels for Complex Routing

Use labels to avoid messy wire crossings:

```python
# Power distribution
c.label(vpos.positive, "VCC")
c.label(u1.vpos, "VCC")
c.label(u2.vpos, "VCC")
# All VCC nodes are now connected

# Ground distribution
c.label(gnd, "0")
c.label(u1.noninv, "0")
c.label(c1.p2, "0")
```

### Multiple Grounds

```python
# You can place multiple ground symbols
gnd1 = c.place(GND(), row=4, col=0)
gnd2 = c.place(GND(), row=4, col=5)
gnd3 = c.place(GND(), row=8, col=3)

# They're all connected to ground
c.connect(v1.negative, gnd1)
c.connect(v2.negative, gnd2)
c.connect(r1.p2, gnd3)
```

### Inspecting Generated ASC

```python
# Print raw ASC content
print(c.to_asc())

# Save and view
c.save("circuit.asc")
with open("circuit.asc") as f:
    print(f.read())
```

---

## Examples

### Example 1: RC Low-Pass Filter

```python
from asclib import Circuit, R, C, V, GND

c = Circuit(grid_size=8)

vin = c.place(V("AC 1"), row=0, col=0)
r1 = c.place(R("1k"), row=0, col=2)
c1 = c.place(C("100n"), row=2, col=4)
gnd = c.place(GND(), row=4, col=0)

c.connect(vin.positive, r1.p1)
c.connect(r1.p2, c1.p1)
c.connect(c1.p2, gnd)
c.connect(vin.negative, gnd)

c.label(r1.p2, "VOUT")
c.save("rc_lowpass.asc")
```

### Example 2: RLC Bandpass Filter

See `examples/rlc_bandpass.py` for a complete two-stage coupled RLC bandpass filter.

### Example 3: Non-Inverting Op-Amp Amplifier

See `examples/noninverting_amplifier.py` for a gain-of-11 non-inverting amplifier.

### Example 4: Cascaded Op-Amp Stages

See `examples/dual_opamp_cascade.py` for a two-stage cascaded amplifier with overall gain of -55.

### Example 5: Simple RLC Series Circuit

See `examples/rlc_circuit.py` for a basic RLC resonant circuit.

---

## Troubleshooting

### "Circuit validation failed"

Check for:
- Floating components (unconnected pins)
- Missing ground reference
- Op-amp power connections

Use `c.validate()` to get detailed error messages.

### "Pin X not found on component Y"

You're trying to access a pin that doesn't exist. Check the component's available pins:
- Resistors, capacitors, inductors: `p1`, `p2`
- Voltage/current sources: `positive`, `negative`
- Op-amps: `inv`, `noninv`, `out`, `vpos`, `vneg`
- Ground: `pin`

### Components overlapping in LTspice

Increase the `grid_size` parameter:

```python
# Instead of
c = Circuit(grid_size=8)

# Try
c = Circuit(grid_size=16)
```

### Wires crossing incorrectly

Use net labels for cleaner routing:

```python
# Instead of long wire
c.connect(distant_component.p1, far_component.p2)

# Use labels
c.label(distant_component.p1, "NET1")
c.label(far_component.p2, "NET1")
```

### Op-amp validation errors

Make sure all five pins are connected:

```python
u1 = c.place(OpAmp())

# Input/output
c.connect(u1.noninv, vin)
c.connect(u1.inv, feedback_net)
c.connect(u1.out, r_out.p1)

# Power (can use labels)
c.label(u1.vpos, "VCC")
c.label(u1.vneg, "VEE")
```

---

## API Reference

### Circuit Class

```python
Circuit(grid_size=16)
```

**Methods**:
- `place(component, row, col, rotation=0)` - Place a component
- `connect(pin1, pin2, ...)` - Connect pins with wires
- `label(pin, name)` - Add a net label to a pin
- `validate()` - Check circuit for errors
- `save(filename, validate=True)` - Save to .asc file
- `to_asc()` - Get ASC content as string

### Component Functions

- `R(value)` - Create resistor
- `C(value)` - Create capacitor
- `L(value)` - Create inductor
- `V(value)` - Create voltage source
- `I(value)` - Create current source
- `OpAmp(model="")` - Create op-amp
- `GND()` - Create ground symbol

---

## Tips and Best Practices

1. **Start with a larger grid**: Use `grid_size=16` or `grid_size=20` to avoid cramped layouts
2. **Use labels for power rails**: Keeps schematics clean and readable
3. **Always validate**: Let the validator catch mistakes before opening in LTspice
4. **Comment your code**: Describe what each section of the circuit does
5. **Organize by stages**: Group related components together
6. **Use descriptive labels**: `"STAGE1_OUT"` is better than `"N1"`
7. **Check examples**: The `examples/` folder has complete working circuits

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## License

MIT License - see LICENSE file for details

---

## Support

- GitHub Issues: https://github.com/erayyap/circutis/issues
- Repository: https://github.com/erayyap/circutis

---

For more examples and updates, visit the [GitHub repository](https://github.com/erayyap/circutis).
