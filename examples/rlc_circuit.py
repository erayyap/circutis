"""
RLC Series Circuit - Simple resonant circuit
"""
import os

from circutis import Circuit, R, L, C, V, GND

def create_rlc_series():
    """Create an RLC series resonant circuit."""
    c = Circuit(grid_size=30)

    # Input voltage source
    vin = c.place(V("AC 1"), row=2, col=0)

    # Horizontal components (R90) spaced out
    r1 = c.place(R("10"), row=2, col=3, rotation=90)
    l1 = c.place(L("1m"), row=2, col=6, rotation=90)
    c1 = c.place(C("1u"), row=2, col=9, rotation=90)

    # Vertical load resistor and ground
    r_load = c.place(R("100"), row=4, col=6)
    gnd = c.place(GND(), row=6, col=0)

    # Connect series circuit
    c.connect(vin.positive, r1.p1)
    c.connect(r1.p2, l1.p1)
    c.connect(l1.p2, c1.p1)
    c.connect(c1.p2, r_load.p1)
    c.connect(r_load.p2, gnd)
    c.connect(vin.negative, gnd)

    # Add net labels
    c.label(vin.positive, "VIN")
    c.label(c1.p2, "VOUT")

    # Validate, beautify minor elbows, then save next to this script
    c.validate()
    c.beautify()

    out_path = os.path.join(os.path.dirname(__file__), "rlc_series.asc")
    c.save(out_path, validate=False)
    print(f"✓ Created {out_path}")
    print(f"  Resonant frequency: ~{1/(2*3.14159*((1e-3*1e-6)**0.5)):.0f} Hz")
    return c

if __name__ == "__main__":
    create_rlc_series()
