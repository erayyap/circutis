"""
Constants for ASC file generation.
Pin offsets are relative to component origin at rotation=0.
All coordinates are in LTspice units (typically 16-pixel grid).
"""

# Default grid size in LTspice units (base grid unit is 16)
DEFAULT_GRID_UNIT = 16  # LTspice base unit
GRID_SPACING = 64       # Recommended spacing between components (4x base unit)

# LTspice rotation codes
ROTATION_CODES = {
    0: "R0",
    90: "R90",
    180: "R180",
    270: "R270",
}

# Mirror codes (combined with rotation)
MIRROR_CODES = {
    (0, False): "R0",
    (90, False): "R90",
    (180, False): "R180",
    (270, False): "R270",
    (0, True): "M0",
    (90, True): "M90",
    (180, True): "M180",
    (270, True): "M270",
}

# Pin offsets for each component type, ROTATION-SPECIFIC
# Format: {rotation: {pin_name: (x_offset, y_offset)}}
# These offsets are extracted from actual LTspice symbol files and verified
# against ground truth circuits (Draft1.asc, Draft2.asc, Draft3.asc)
PIN_OFFSETS = {
    "res": {
        0: {    # Vertical orientation (pins top/bottom)
            # Standard LTspice vertical resistor body
            "p1": (16, 16),     # Top pin
            "p2": (16, 96),    # Bottom pin
        },
        90: {   # Horizontal orientation (pins left/right)
            "p1": (-96, 16),    # Left pin (verified from Draft3 R1, R2)
            "p2": (-16, 16),    # Right pin
        },
        180: {  # Vertical flipped
            "p1": (-16, -16),
            "p2": (-16, -96),
        },
        270: {  # Horizontal flipped
            "p1": (-16, -16),
            "p2": (-96, -16),
        },
    },
    "ind": {
        0: {    # Vertical orientation (pins top/bottom)
            # Standard LTspice vertical resistor body
            "p1": (16, 16),     # Top pin
            "p2": (16, 96),    # Bottom pin
        },
        90: {   # Horizontal orientation (pins left/right)
            "p1": (-96, 16),    # Left pin (verified from Draft3 R1, R2)
            "p2": (-16, 16),    # Right pin
        },
        180: {  # Vertical flipped
            "p1": (-16, 0),
            "p2": (-16, -80),
        },
        270: {  # Horizontal flipped
            "p1": (0, -16),
            "p2": (-80, -16),
        },
    },

    "current": {
        0: {    # Vertical orientation (pins top/bottom)
            # Standard LTspice vertical resistor body
            "positive": (0, 0),     # Top pin
            "negative": (0, 80),    # Bottom pin
        },
        90: {   # Horizontal orientation (pins left/right)
            "positive": (0, 0),    # Left pin (verified from Draft3 R1, R2)
            "negative": (80, 0),    # Right pin
        },
        180: {  # Vertical flipped
            "positive": (-0, 0),
            "negative": (-0, -80),
        },
        270: {  # Horizontal flipped
            "positive": (0, -0),
            "negative": (-80, -0),
        },
    },

    "voltage": {
        0: {    # Vertical orientation (pins top/bottom)
            # Standard LTspice vertical resistor body
            "positive": (0, 16),     # Top pin
            "negative": (0, 96),    # Bottom pin
        },
        90: {   # Horizontal orientation (pins left/right)
            "positive": (16, 0),    # Left pin (verified from Draft3 R1, R2)
            "negative": (96, 0),    # Right pin
        },
        180: {  # Vertical flipped
            "positive": (-0, -16),
            "negative": (-0, -96),
        },
        270: {  # Horizontal flipped
            "positive": (-16, -0),
            "negative": (-96, -0),
        },
    },
    "cap": {
        0: {    # Vertical orientation
            # Draft3 C1/C2: top lead far above origin
            "p1": (16, 0),
            "p2": (16, 64),
        },
        90: {   # Horizontal orientation
            # From reference_horizontal.asc: pins offset down by 16, 32px apart
            "p1": (-64, 16),      # Left pin
            "p2": (-0, 16),     # Right pin
        },
        180: {  # Vertical flipped
            "p1": (-16, 0),
            "p2": (-16, -64),
        },
        270: {  # Horizontal flipped
            "p1": (0, 16),
            "p2": (-64, 16),
        },
    },
    "gnd": {
        0: {
            "pin": (0, 0),
        },
        90: {
            "pin": (0, 0),
        },
        180: {
            "pin": (0, 0),
        },
        270: {
            "pin": (0, 0),
        },
    },
    "node": {
        # Nodes are junction points - single pin at origin for all rotations
        0: {
            "pin": (0, 0),
        },
        90: {
            "pin": (0, 0),
        },
        180: {
            "pin": (0, 0),
        },
        270: {
            "pin": (0, 0),
        },
    },
    # Op-amp (standard 5-pin symbol like opamp2)
    "opamp": {
        0: {
            "noninv": (-32, 48),      # + input (IN+)
            "inv": (-32, 80),          # - input (IN-)
            "out": (32, 64),        # Output
            "vpos": (0, 32),      # V+ supply (optional)
            "vneg": (0, 96),       # V- supply (optional)
        },
    },
}

# Component symbol names in LTspice
SYMBOL_NAMES = {
    "res": "res",
    "cap": "cap",
    "ind": "ind",
    "voltage": "voltage",
    "current": "current",
    "gnd": "0",
    "node": "node",  # Node junction point
    "opamp": "opamp2",  # Default op-amp symbol
}

# ASC file header template
ASC_HEADER = """Version 4
SHEET 1 {width} {height}
"""
