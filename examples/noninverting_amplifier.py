#!/usr/bin/env python3
"""
Non-Inverting Amplifier Circuit
Gain = 1 + (R2/R1) = 1 + (10k/1k) = 11
Output voltage = Input voltage × 11
"""

from asclib import Circuit, R, V, OpAmp, GND

# Create circuit with larger grid for better spacing
c = Circuit(grid_size=14)

# Place input voltage source (left side)
vin = c.place(V("AC 1"), row=5, col=0)
gnd_in = c.place(GND(), row=7, col=0)

# Place op-amp in center
u1 = c.place(OpAmp(), row=5, col=5)

# Place feedback resistor R2 (10k) - from output back to inverting input
# Position it above the op-amp
r2 = c.place(R("10k"), row=3, col=6, rotation=0)

# Place ground resistor R1 (1k) - from inverting input to ground
# Position it below and to the left
r1 = c.place(R("1k"), row=7, col=4, rotation=0)
gnd_r1 = c.place(GND(), row=9, col=4)

# Place power supplies on the left side
vpos = c.place(V("DC 15"), row=2, col=2)
gnd_vpos = c.place(GND(), row=4, col=2)

vneg = c.place(V("DC -15"), row=8, col=2)
gnd_vneg = c.place(GND(), row=10, col=2)

# Connect input signal to non-inverting input
c.connect(vin.positive, u1.noninv)
c.connect(vin.negative, gnd_in)

# Connect feedback network
# Output to one end of R2
c.connect(u1.out, r2.p1)
# Other end of R2 to inverting input
c.connect(r2.p2, u1.inv)
# Inverting input also connects to R1
c.connect(u1.inv, r1.p1)
# R1 to ground
c.connect(r1.p2, gnd_r1)

# Connect op-amp power supplies using labels (wireless connections)
# This avoids wire crossings with the feedback network
c.label(u1.vpos, "VCC")
c.label(vpos.positive, "VCC")
c.connect(vpos.negative, gnd_vpos)

c.label(u1.vneg, "VEE")
c.label(vneg.negative, "VEE")
c.connect(vneg.positive, gnd_vneg)

# Add net labels
c.label(vin.positive, "VIN")
c.label(u1.out, "VOUT")

# Validate and save
issues = c.validate()
if not issues:
    c.save("noninverting_amplifier.asc")
    print("✓ Non-inverting amplifier circuit created successfully!")
    print("  - Gain: 11 (1 + 10k/1k)")
    print("  - Input: 1V AC")
    print("  - Expected output: 11V AC")
    print("  - File: noninverting_amplifier.asc")
else:
    print("✗ Circuit validation failed!")
