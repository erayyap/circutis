#!/usr/bin/env python3
"""
Non-Inverting Amplifier Circuit
Gain = 1 + (R2/R1) = 1 + (10k/1k) = 11
Output voltage = Input voltage × 11
"""

from pathlib import Path

from circutis import Circuit, R, V, OpAmp, GND


def build_noninverting_amplifier(out_dir: Path, beautify: bool = True, filename: str = "noninverting_amplifier.asc") -> Path:
    """Build the non-inverting amplifier and optionally beautify."""
    c = Circuit(grid_size=14)

    # Place input voltage source (left side)
    vin = c.place(V("AC 1"), row=5, col=0)
    gnd_in = c.place(GND(), row=7, col=0)

    # Place op-amp in center
    u1 = c.place(OpAmp(), row=5, col=5)

    # Feedback and bias network
    r2 = c.place(R("10k"), row=3, col=6, rotation=0)
    r1 = c.place(R("1k"), row=7, col=4, rotation=0)
    gnd_r1 = c.place(GND(), row=9, col=4)

    # Power supplies on the left side
    vpos = c.place(V("DC 15"), row=2, col=2)
    gnd_vpos = c.place(GND(), row=4, col=2)

    vneg = c.place(V("DC -15"), row=8, col=2)
    gnd_vneg = c.place(GND(), row=10, col=2)

    # Signal path
    c.connect(vin.positive, u1.noninv)
    c.connect(vin.negative, gnd_in)

    c.connect(u1.out, r2.p1)
    c.connect(r2.p2, u1.inv)
    c.connect(u1.inv, r1.p1)
    c.connect(r1.p2, gnd_r1)

    # Power labels avoid crossing wires
    c.label(u1.vpos, "VCC")
    c.label(vpos.positive, "VCC")
    c.connect(vpos.negative, gnd_vpos)

    c.label(u1.vneg, "VEE")
    c.label(vneg.negative, "VEE")
    c.connect(vneg.positive, gnd_vneg)

    # Net labels
    c.label(vin.positive, "VIN")
    c.label(u1.out, "VOUT")

    # Validate and optionally beautify
    c.validate()
    if beautify:
        c.beautify()

    out_dir.mkdir(parents=True, exist_ok=True)
    asc_path = out_dir / filename
    c.save(str(asc_path), validate=False)
    return asc_path


if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parent
    beautified = build_noninverting_amplifier(output_dir, beautify=True, filename="noninverting_amplifier.asc")
    raw = build_noninverting_amplifier(output_dir, beautify=False, filename="noninverting_amplifier_unbeautified.asc")

    print("✓ Non-inverting amplifier circuit created successfully!")
    print(f"  - Beautified: {beautified}")
    print(f"  - Un-beautified: {raw}")
    print("  - Gain: 11 (1 + 10k/1k)")
    print("  - Input: 1V AC")
