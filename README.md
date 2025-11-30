<div align="center">
  <img src="logo.png" alt="Circutis Logo" width="300"/>

  # Circutis

  **Programmatically generate LTspice circuits with Python**
</div>

Circutis is a Python library that lets you build electronic circuits using code instead of manual drawing. Define your circuit components, connections, and layout in Python, then generate LTspice-compatible `.asc` schematic files automatically.

## Features

- **Grid-based layout system** for predictable component placement
- **Type-safe pin connections** to prevent wiring errors
- **Automatic wire routing** between components
- **Built-in circuit validation** to catch common mistakes
- **Zero external dependencies** - pure Python
- **LTspice compatible** - generates standard `.asc` files

## Quick Start

```python
from circutis import Circuit, R, C, V, GND

# Create a simple RC low-pass filter
c = Circuit(grid_size=10)

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

Open the generated `rc_lowpass.asc` file in LTspice and simulate!

## Installation

### Using uv (recommended)

```bash
git clone https://github.com/erayyap/circutis.git
cd circutis
uv pip install -e .
```

### Using pip

```bash
git clone https://github.com/erayyap/circutis.git
cd circutis
pip install -e .
```

**Requirements**: Python 3.9 or higher

## Components

Circutis supports all common circuit elements:

| Component | Usage | Pins |
|-----------|-------|------|
| Resistor | `R("1k")` | `p1`, `p2` |
| Capacitor | `C("100n")` | `p1`, `p2` |
| Inductor | `L("10m")` | `p1`, `p2` |
| Voltage Source | `V("12")` or `V("AC 1")` | `positive`, `negative` |
| Current Source | `I("1m")` | `positive`, `negative` |
| Op-Amp | `OpAmp("LT1001")` | `inv`, `noninv`, `out`, `vpos`, `vneg` |
| Ground | `GND()` | `pin` |

## Examples

Check out the `examples/` folder for complete working circuits:

- **`noninverting_amplifier.py`** - Op-amp amplifier with gain of 11
- **`dual_opamp_cascade.py`** - Two-stage cascaded amplifier (gain -55)
- **`rlc_bandpass.py`** - Two-stage coupled RLC bandpass filter
- **`rlc_circuit.py`** - Simple RLC resonant circuit

Run any example:

```bash
cd examples
python noninverting_amplifier.py
```

## Documentation

For detailed documentation, see [DOCUMENTATION.md](DOCUMENTATION.md), which includes:

- Complete component reference
- Circuit building tutorial
- Validation system guide
- Advanced routing techniques
- Troubleshooting tips
- API reference

## Why Circutis?

### Version Control Your Circuits
Store circuit designs in Git alongside your analysis scripts and documentation.

### Parametric Circuit Generation
Easily generate circuit variations by changing parameters:

```python
for gain in [10, 20, 50, 100]:
    r_feedback = gain * 1000
    # ... build amplifier with calculated values
```

### Automated Testing
Generate test circuits automatically for design validation.

### Circuit Templates
Build reusable circuit building blocks as Python functions.

## Validation

Built-in validation catches common errors:

```python
issues = c.validate()
if issues:
    for issue in issues:
        print(issue)
else:
    c.save("my_circuit.asc")
```

Checks for:
- Floating components (unconnected pins)
- Missing ground reference
- Disconnected circuit sections
- Op-amp power connections

## Project Structure

```
circutis/
├── circutis/            # Main library code
│   ├── circuit.py       # Circuit class
│   ├── components.py    # Component definitions
│   ├── routing.py       # Wire routing
│   ├── validation.py    # Circuit validation
│   └── ...
├── examples/            # Example circuits
│   ├── noninverting_amplifier.py
│   ├── dual_opamp_cascade.py
│   ├── rlc_bandpass.py
│   └── rlc_circuit.py
├── pyproject.toml       # Project configuration
├── README.md            # This file
└── DOCUMENTATION.md     # Detailed documentation
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **Repository**: https://github.com/erayyap/circutis
- **Issues**: https://github.com/erayyap/circutis/issues
- **Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md)
