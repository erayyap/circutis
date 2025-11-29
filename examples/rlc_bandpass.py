#!/usr/bin/env python3
"""
RLC Bandpass Filter - Dual resonator with coupling
Two-stage RLC circuit with series input coupling and parallel resonant tanks
"""

from circutis import Circuit, R, L, C, V, GND
import math

# Create circuit
circuit = Circuit(grid_size=14)

# Input voltage source and source resistance
vin = circuit.place(V("AC 1"), row=5, col=0)
gnd_in = circuit.place(GND(), row=7, col=0)
r_source = circuit.place(R("50"), row=5, col=1, rotation=90)

# Stage 1: First parallel LC tank
cap1 = circuit.place(C("100n"), row=3, col=3, rotation=0)
ind1 = circuit.place(L("10m"), row=5, col=3, rotation=0)
res1 = circuit.place(R("1k"), row=7, col=3, rotation=0)  # Q damping
gnd1 = circuit.place(GND(), row=9, col=3)

# Coupling capacitor between stages
c_couple = circuit.place(C("47n"), row=3, col=5, rotation=90)

# Stage 2: Second parallel LC tank
cap2 = circuit.place(C("100n"), row=3, col=7, rotation=0)
ind2 = circuit.place(L("10m"), row=5, col=7, rotation=0)
res2 = circuit.place(R("1k"), row=7, col=7, rotation=0)  # Q damping
gnd2 = circuit.place(GND(), row=9, col=7)

# Output load
r_load = circuit.place(R("1k"), row=5, col=9, rotation=0)
gnd_out = circuit.place(GND(), row=7, col=9)

# Connect input to first tank
circuit.connect(vin.positive, r_source.p1)
circuit.connect(r_source.p2, cap1.p1)
circuit.connect(vin.negative, gnd_in)

# First tank connections (C1, L1, R1 in parallel)
circuit.connect(cap1.p2, ind1.p1)
circuit.connect(ind1.p2, res1.p1)
circuit.connect(res1.p2, gnd1)

# Coupling between tanks
circuit.connect(cap1.p1, c_couple.p1)
circuit.connect(c_couple.p2, cap2.p1)

# Second tank connections (C2, L2, R2 in parallel)
circuit.connect(cap2.p2, ind2.p1)
circuit.connect(ind2.p2, res2.p1)
circuit.connect(res2.p2, gnd2)

# Output load
circuit.connect(cap2.p1, r_load.p1)
circuit.connect(r_load.p2, gnd_out)

# Add net labels
circuit.label(vin.positive, "VIN")
circuit.label(cap1.p1, "TANK1")
circuit.label(cap2.p1, "TANK2")
circuit.label(cap2.p1, "VOUT")

# Validate and save
issues = circuit.validate()
if not issues:
    circuit.save("rlc_bandpass.asc")

    # Calculate resonant frequency
    L_val = 10e-3  # 10mH
    C_val = 100e-9  # 100nF
    f0 = 1 / (2 * math.pi * math.sqrt(L_val * C_val))

    print("✓ Created rlc_bandpass.asc")
    print("\n  Two-stage coupled RLC bandpass filter")
    print("  - Stage 1: Parallel LC tank (L1=10mH, C1=100nF, R1=1kΩ)")
    print("  - Stage 2: Parallel LC tank (L2=10mH, C2=100nF, R2=1kΩ)")
    print("  - Coupling: C_couple=47nF")
    print(f"  - Center frequency: ~{f0:.1f} Hz")
    print("  - Source impedance: 50Ω")
    print("  - Load impedance: 1kΩ")
else:
    print("✗ Circuit validation failed!")
