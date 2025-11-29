#!/usr/bin/env python3
"""
Dual Op-Amp Cascaded Amplifier
Stage 1: Non-inverting amplifier (gain = 11)
Stage 2: Inverting amplifier (gain = -5)
Overall gain: 11 × -5 = -55 (inverting)
"""

from pathlib import Path

from circutis import Circuit, R, V, OpAmp, GND


def build_dual_opamp_cascade(out_dir: Path, beautify: bool = True, filename: str = "dual_opamp_cascade.asc") -> Path:
    """Build the dual op-amp cascade and optionally beautify."""
    circuit = Circuit(grid_size=16)

    # Input voltage source
    vin = circuit.place(V("AC 0.1"), row=6, col=0)
    gnd_in = circuit.place(GND(), row=8, col=0)

    # STAGE 1: Non-inverting amplifier (gain = 11)
    u1 = circuit.place(OpAmp(), row=6, col=4)

    # Stage 1 feedback network
    r1_feedback = circuit.place(R("10k"), row=4, col=5, rotation=0)
    r1_ground = circuit.place(R("1k"), row=8, col=4, rotation=0)
    gnd_u1 = circuit.place(GND(), row=10, col=4)

    # STAGE 2: Inverting amplifier (gain = -5)
    u2 = circuit.place(OpAmp(), row=6, col=9)

    # Stage 2 input and feedback resistors
    r2_input = circuit.place(R("10k"), row=6, col=7, rotation=90)
    r2_feedback = circuit.place(R("50k"), row=4, col=9, rotation=0)

    # Output load (optional - for measurement)
    r_load = circuit.place(R("10k"), row=8, col=11, rotation=0)
    gnd_out = circuit.place(GND(), row=10, col=11)

    # Power supplies (shared by both op-amps)
    vpos = circuit.place(V("DC 15"), row=2, col=2)
    gnd_vpos = circuit.place(GND(), row=4, col=2)

    vneg = circuit.place(V("DC -15"), row=10, col=2)
    gnd_vneg = circuit.place(GND(), row=12, col=2)

    # ============ STAGE 1 CONNECTIONS ============
    circuit.connect(vin.positive, u1.noninv)
    circuit.connect(vin.negative, gnd_in)

    circuit.connect(u1.out, r1_feedback.p1)
    circuit.connect(r1_feedback.p2, u1.inv)
    circuit.connect(u1.inv, r1_ground.p1)
    circuit.connect(r1_ground.p2, gnd_u1)

    # ============ STAGE 2 CONNECTIONS ============
    circuit.connect(u1.out, r2_input.p1)
    circuit.connect(r2_input.p2, u2.inv)

    circuit.connect(u2.out, r2_feedback.p1)
    circuit.connect(r2_feedback.p2, u2.inv)

    # Ground the non-inverting input of U2 (inverting config) - use label to avoid crossing
    circuit.label(u2.noninv, "0")

    # Output load
    circuit.connect(u2.out, r_load.p1)
    circuit.connect(r_load.p2, gnd_out)

    # ============ POWER SUPPLY CONNECTIONS (using labels) ============
    circuit.label(u1.vpos, "VCC")
    circuit.label(u2.vpos, "VCC")
    circuit.label(vpos.positive, "VCC")
    circuit.connect(vpos.negative, gnd_vpos)

    circuit.label(u1.vneg, "VEE")
    circuit.label(u2.vneg, "VEE")
    circuit.label(vneg.negative, "VEE")
    circuit.connect(vneg.positive, gnd_vneg)

    # ============ NET LABELS ============
    circuit.label(vin.positive, "VIN")
    circuit.label(u1.out, "STAGE1_OUT")
    circuit.label(u2.out, "VOUT")

    # Validate and optionally beautify
    circuit.validate()
    if beautify:
        circuit.beautify()

    out_dir.mkdir(parents=True, exist_ok=True)
    asc_path = out_dir / filename
    circuit.save(str(asc_path), validate=False)
    return asc_path


if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parent
    beautified = build_dual_opamp_cascade(output_dir, beautify=True, filename="dual_opamp_cascade.asc")
    raw = build_dual_opamp_cascade(output_dir, beautify=False, filename="dual_opamp_cascade_unbeautified.asc")

    print(f"✓ Created beautified {beautified}")
    print(f"✓ Created un-beautified {raw}")
    print("\n  Two-stage cascaded amplifier:")
    print("  - Stage 1 (U1): Non-inverting, Gain = 1 + (10k/1k) = 11")
    print("  - Stage 2 (U2): Inverting, Gain = -(50k/10k) = -5")
    print("  - Overall gain: 11 × (-5) = -55")
    print("  - Input: 0.1V AC")
