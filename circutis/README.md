# circutis

A Python library for generating LTspice ASC schematic files with automatic wire routing.

## Why?

Writing LTspice `.asc` files by hand (or having an LLM generate them) often results in disconnected wires because coordinates must align exactly. **circutis** solves this by:

1. **Grid-based placement** — Place components on a logical grid, not pixel coordinates
2. **Computed pin positions** — Pin coordinates are calculated from component position + rotation
3. **Automatic wire routing** — Connect pins by reference, wires are generated with correct endpoints
4. **Validation** — Catch unconnected pins and missing grounds before saving

## Installation

```bash
# Copy the circutis folder to your project, or:
pip install -e /path/to/circutis
```

## Quick Start

```python
from circutis import Circuit, R, C, V, GND

# Create circuit with 10x10 grid
c = Circuit(grid_size=10)

# Place components on grid
v1 = c.place(V("12V"), row=0, col=0)
r1 = c.place(R("1k"), row=0, col=2)
c1 = c.place(C("100n"), row=2, col=2)
gnd = c.place(GND(), row=2, col=0)

# Connect pins — wires are auto-routed
c.connect(v1.positive, r1.p1)
c.connect(r1.p2, c1.p1)
c.connect(c1.p2, gnd)
c.connect(v1.negative, gnd)

# Validate and save
c.save("my_circuit.asc")
```

## Components

### Two-Terminal Components

| Component | Class | Pins | Example |
|-----------|-------|------|---------|
| Resistor | `R` | `p1`, `p2` | `R("1k")`, `R("10meg")` |
| Capacitor | `C` | `p1`, `p2` | `C("100n")`, `C("10u")` |
| Inductor | `L` | `p1`, `p2` | `L("10m")`, `L("100u")` |

### Sources

| Component | Class | Pins | Example |
|-----------|-------|------|---------|
| Voltage Source | `V` | `positive`, `negative` | `V("12")`, `V("AC 1")`, `V("PULSE(0 5 0 1n 1n 1u 2u)")` |
| Current Source | `I` | `positive`, `negative` | `I("1m")`, `I("AC 0.001")` |

### Op-Amp

```python
from circutis import OpAmp

u1 = c.place(OpAmp("LT1001"), row=2, col=4)

# Pins:
u1.inv      # Inverting input (-)
u1.noninv   # Non-inverting input (+)
u1.out      # Output
u1.vpos     # V+ supply
u1.vneg     # V- supply
```

### Ground

```python
from circutis import GND

gnd = c.place(GND(), row=4, col=0)
c.connect(some_pin, gnd)  # Can connect directly to GND component
```

## Placement Options

```python
# Basic placement
r1 = c.place(R("1k"), row=2, col=3)

# With rotation (0, 90, 180, 270 degrees)
r2 = c.place(R("1k"), row=2, col=5, rotation=90)

# With horizontal mirror
u1 = c.place(OpAmp("LT1001"), row=3, col=4, mirror=True)
```

## Net Labels

Use labels to create named nets (connects points without explicit wires):

```python
c.label(r1.p2, "VOUT")
c.label(opamp.out, "VOUT")  # Same net name = connected
```

## Validation

The library validates circuits before saving:

```python
# Automatic validation on save (raises error if problems found)
c.save("circuit.asc")

# Manual validation
issues = c.validate()

# Skip validation (not recommended)
c.save("circuit.asc", validate=False)
```

**Checks performed:**
- Unconnected pins (ERROR)
- Missing ground reference (ERROR)
- Floating wire endpoints (WARNING)
- Overlapping components (WARNING)
- Op-amp power pins (WARNING if not connected)

## Example: Inverting Amplifier

```python
from circutis import Circuit, R, V, OpAmp, GND

c = Circuit(grid_size=12)

# Power supplies
vpos = c.place(V("15"), row=0, col=0)
vneg = c.place(V("15"), row=6, col=0)

# Signal and components
vin = c.place(V("AC 1"), row=3, col=0)
u1 = c.place(OpAmp("LT1001"), row=3, col=4)
r_in = c.place(R("10k"), row=3, col=2, rotation=90)
r_fb = c.place(R("100k"), row=1, col=5, rotation=90)
gnd = c.place(GND(), row=8, col=0)

# Input
c.connect(vin.positive, r_in.p1)
c.connect(r_in.p2, u1.inv)
c.connect(vin.negative, gnd)

# Non-inverting to ground
c.connect(u1.noninv, gnd)

# Feedback
c.connect(u1.out, r_fb.p1)
c.connect(r_fb.p2, u1.inv)

# Power
c.connect(u1.vpos, vpos.positive)
c.connect(vpos.negative, gnd)
c.connect(vneg.negative, u1.vneg)
c.connect(vneg.positive, gnd)

# Output label
c.label(u1.out, "VOUT")

c.save("inverting_amp.asc")
```

## API Reference

### Circuit

```python
Circuit(grid_size=10, grid_unit=64)
```
- `grid_size`: Number of grid cells (default 10)
- `grid_unit`: Pixels per cell (default 64, matches LTspice grid)

**Methods:**
- `place(component, row, col, rotation=0, mirror=False)` — Place component on grid
- `connect(pin_a, pin_b)` — Connect two pins with auto-routed wire
- `label(pin, name)` — Add net label to pin
- `validate(print_report=True)` — Check circuit for issues
- `save(filename, validate=True)` — Save to .asc file
- `to_asc()` — Get ASC content as string

### Pin

Accessed via component properties:
```python
r1.p1, r1.p2           # Two-terminal
v1.positive, v1.negative  # Sources
u1.inv, u1.noninv, u1.out, u1.vpos, u1.vneg  # Op-amp
```

**Properties:**
- `coords` — Absolute (x, y) pixel coordinates
- `is_connected` — Whether pin has been connected
- `label` — Net label if assigned

## Extending

### Adding Components

Subclass `Component` or `TwoTerminal`:

```python
from circutis.components import TwoTerminal
from circutis.constants import PIN_OFFSETS, SYMBOL_NAMES

# Register pin offsets
PIN_OFFSETS["diode"] = {"anode": (0, 0), "cathode": (0, 64)}
SYMBOL_NAMES["diode"] = "diode"

class Diode(TwoTerminal):
    _prefix = "D"
    _symbol_type = "diode"
    
    @property
    def anode(self): return self._pins["anode"]
    
    @property
    def cathode(self): return self._pins["cathode"]
```

## License

MIT
