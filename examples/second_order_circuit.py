"""
Build a second-order Type D network by cascading an RL stage with an RC high-pass.

The RL stage uses low impedances (tens of ohms), and the RC stage uses a much
higher resistance (10 kΩ), so loading is negligible and H_tot ≈ H_HP · H_D.
"""

from pathlib import Path
from typing import Dict, Any

import circutis as circ


def build_second_order_asc(
    circutis_mod: object,
    values: Dict[str, Any],
    out_dir: Path,
    beautify: bool = True,
    filename: str = "second_order_circuit.asc",
) -> Path:
    """
    Generate the second-order Type D circuit (.asc) by cascading an RC high-pass
    stage (R_hp, C_hp) AFTER the RL Type D network.

    In this configuration the RL Type D stage presents a relatively low
    output impedance (tens of ohms), while the RC stage uses a much larger
    resistance (10 kΩ). Therefore, loading of the RL stage by the RC
    high-pass is negligible and the approximation H_tot ≈ H_HP · H_D is
    justified.

    Use the `filename` parameter to emit multiple variants (e.g., beautified
    and raw) side by side in the same folder.
    """
    Circuit = circutis_mod.Circuit
    R = circutis_mod.R
    L = circutis_mod.L
    C = circutis_mod.C
    V = circutis_mod.V
    GND = circutis_mod.GND

    c = Circuit(grid_size=14)

    # Input source and ground
    vin = c.place(V("AC 1"), row=6, col=0)
    gnd = c.place(GND(), row=8, col=0)

    # RL Type D stage (same topology as first-order circuit)
    r7 = c.place(R(f"{values['R7']:.0f}"), row=6, col=2, rotation=90)
    l2 = c.place(L(f"{values['L']:.2e}"), row=4, col=2, rotation=0)
    r8 = c.place(R(f"{values['R8']:.0f}"), row=8, col=2, rotation=0)

    # High-pass RC stage placed AFTER the RL stage:
    # VMID -> series C_hp -> VOUT -> R_hp -> GND
    chp = c.place(C(f"{values['C_hp']:.2e}"), row=6, col=4, rotation=90)
    rhp = c.place(R(f"{values['R_hp']:.0f}"), row=8, col=4, rotation=0)

    # Wiring
    c.connect(vin.negative, gnd)

    # RL stage wiring
    c.connect(vin.positive, r7.p1)
    c.connect(vin.positive, l2.p1)
    c.connect(l2.p2, r7.p2)
    c.connect(r7.p2, r8.p1)
    c.connect(r8.p2, gnd)

    # RC high-pass from VMID node
    c.connect(r7.p2, chp.p1)   # VMID -> capacitor
    c.connect(chp.p2, rhp.p1)  # after C -> top of R_hp
    c.connect(rhp.p2, gnd)     # bottom of R_hp to ground

    # Labels for probing
    c.label(vin.positive, "VIN")
    c.label(r7.p2, "VMID")
    c.label(rhp.p1, "VOUT")

    # Validate and optionally beautify just this circuit; keep changes local
    c.validate()
    if beautify:
        c.beautify()

    out_dir.mkdir(parents=True, exist_ok=True)
    asc_path = out_dir / filename
    c.save(str(asc_path), validate=False)
    return asc_path


if __name__ == "__main__":
    defaults = {
        "R7": 47.0,       # ohms
        "L": 1.0e-3,      # henry
        "R8": 22.0,       # ohms
        "C_hp": 4.7e-9,   # farad
        "R_hp": 10_000.0  # ohms
    }
    output_dir = Path(__file__).resolve().parent
    beautified_path = build_second_order_asc(
        circ,
        defaults,
        output_dir,
        beautify=True,
        filename="second_order_circuit.asc",
    )
    raw_path = build_second_order_asc(
        circ,
        defaults,
        output_dir,
        beautify=False,
        filename="second_order_circuit_unbeautified.asc",
    )
    print(f"✓ Wrote beautified {beautified_path}")
    print(f"✓ Wrote un-beautified {raw_path}")
