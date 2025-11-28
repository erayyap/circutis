#!/usr/bin/env python3
"""
Dual Op-Amp Cascaded Amplifier
Stage 1: Non-inverting amplifier (gain = 11)
Stage 2: Inverting amplifier (gain = -5)
Overall gain: 11 × -5 = -55 (inverting)
"""

from circutis import Circuit, R, V, OpAmp, GND

# Create circuit
circuit = Circuit(grid_size=16)

# Input voltage source
vin = circuit.place(V("AC 0.1"), row=6, col=0)
gnd_in = circuit.place(GND(), row=8, col=0)

# STAGE 1: Non-inverting amplifier (gain = 11)
# Op-amp 1
u1 = circuit.place(OpAmp(), row=6, col=4)

# Stage 1 feedback network
r1_feedback = circuit.place(R("10k"), row=4, col=5, rotation=0)  # Feedback resistor
r1_ground = circuit.place(R("1k"), row=8, col=4, rotation=0)     # Ground resistor
gnd_u1 = circuit.place(GND(), row=10, col=4)

# STAGE 2: Inverting amplifier (gain = -5)
# Op-amp 2
u2 = circuit.place(OpAmp(), row=6, col=9)

# Stage 2 input and feedback resistors
r2_input = circuit.place(R("10k"), row=6, col=7, rotation=90)      # Input resistor
r2_feedback = circuit.place(R("50k"), row=4, col=9, rotation=0)   # Feedback resistor

# Stage 2 ground for non-inverting input (using label to avoid crossing)
# We'll use a label instead of a direct connection

# Output load (optional - for measurement)
r_load = circuit.place(R("10k"), row=8, col=11, rotation=0)
gnd_out = circuit.place(GND(), row=10, col=11)

# Power supplies (shared by both op-amps)
vpos = circuit.place(V("DC 15"), row=2, col=2)
gnd_vpos = circuit.place(GND(), row=4, col=2)

vneg = circuit.place(V("DC -15"), row=10, col=2)
gnd_vneg = circuit.place(GND(), row=12, col=2)

# ============ STAGE 1 CONNECTIONS ============
# Input signal to non-inverting input of U1
circuit.connect(vin.positive, u1.noninv)
circuit.connect(vin.negative, gnd_in)

# Feedback network for stage 1
circuit.connect(u1.out, r1_feedback.p1)
circuit.connect(r1_feedback.p2, u1.inv)
circuit.connect(u1.inv, r1_ground.p1)
circuit.connect(r1_ground.p2, gnd_u1)

# ============ STAGE 2 CONNECTIONS ============
# Coupling from stage 1 output to stage 2 input resistor
circuit.connect(u1.out, r2_input.p1)
circuit.connect(r2_input.p2, u2.inv)

# Feedback for stage 2
circuit.connect(u2.out, r2_feedback.p1)
circuit.connect(r2_feedback.p2, u2.inv)

# Ground the non-inverting input of U2 (inverting config) - use label to avoid crossing
circuit.label(u2.noninv, "0")

# Output load
circuit.connect(u2.out, r_load.p1)
circuit.connect(r_load.p2, gnd_out)

# ============ POWER SUPPLY CONNECTIONS (using labels) ============
# Positive supply for both op-amps
circuit.label(u1.vpos, "VCC")
circuit.label(u2.vpos, "VCC")
circuit.label(vpos.positive, "VCC")
circuit.connect(vpos.negative, gnd_vpos)

# Negative supply for both op-amps
circuit.label(u1.vneg, "VEE")
circuit.label(u2.vneg, "VEE")
circuit.label(vneg.negative, "VEE")
circuit.connect(vneg.positive, gnd_vneg)

# ============ NET LABELS ============
circuit.label(vin.positive, "VIN")
circuit.label(u1.out, "STAGE1_OUT")
circuit.label(u2.out, "VOUT")

# Validate and save
issues = circuit.validate()
if not issues:
    circuit.save("dual_opamp_cascade.asc")
    print("✓ Created dual_opamp_cascade.asc")
    print("\n  Two-stage cascaded amplifier:")
    print("  - Stage 1 (U1): Non-inverting, Gain = 1 + (10k/1k) = 11")
    print("  - Stage 2 (U2): Inverting, Gain = -(50k/10k) = -5")
    print("  - Overall gain: 11 × (-5) = -55")
    print("  - Input: 0.1V AC")
    print("  - Stage 1 output: ~1.1V")
    print("  - Final output: ~-5.5V (inverted)")
    print("\n  Key nodes:")
    print("  - VIN: Input signal")
    print("  - STAGE1_OUT: Output of first amplifier")
    print("  - VOUT: Final output")
else:
    print("✗ Circuit validation failed!")
    for issue in issues:
        print(f"  {issue}")
