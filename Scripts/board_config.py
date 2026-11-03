"""
Board-wide build settings and tool paths shared by the PCB scripts in this
folder. Not run directly.

Two boards, picked by the PCB_BOARD environment variable (default
"base"): the base board (SuperMini, servos, beeper; atopile build and
layout "default") and the sensor head (radar, ToF, PIR; build and layout
"head"). They are joined by a 12-pin 0.5 mm FFC.

Both are 2-layer: F.Cu carries the routing, B.Cu is a GND pour that
signals may only cross with short jumpers, power nets are routed as
net-class tracks.

Tool and scratch paths default to the original Windows setup; override them
with the environment variables named below on any other machine.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (worktree-safe)
BOARD = os.environ.get("PCB_BOARD", "base")               # base | head
BOARD_NAMES = {"base": "default", "head": "head"}           # atopile build = layout folder = file stem
if BOARD not in BOARD_NAMES:
    raise SystemExit(f"PCB_BOARD={BOARD!r}: use one of {sorted(BOARD_NAMES)}")
BOARD_NAME = BOARD_NAMES[BOARD]
BOARD_DIR = os.path.join(ROOT, "pcb", "layouts", BOARD_NAME)
BOARD_PATH = os.path.join(BOARD_DIR, BOARD_NAME + ".kicad_pcb")
NET_PATH = os.path.join(ROOT, "pcb", "build", BOARD_NAME + ".net")
RENDER_DIR = os.path.join(ROOT, "pcb", "build", "renders", BOARD)

REVISION = "2.1"
DATE = "2026-11-03"
TITLE = "ESP32 Human Presence Radar"
BOARD_TITLE = {"base": TITLE + " - base", "head": TITLE + " - sensor head"}[BOARD]

# Net classes routed wider than Default (0.2 mm): name -> (track, via
# diameter, via drill, nets), in mm. Keep equal to both .kicad_pro files.
# Power 0.3 mm fits between 2.54 mm header pads and onto the FFC's 0.3 mm
# pads at 0.5 mm pitch; servo_5v carries both SG90s (over 1 A at stall) and
# at 0.4 mm still passes between two SuperMini socket pins (0.84 mm gap).
# v3v3 only feeds the ToF: Default class.
NET_CLASSES = {
    "Power": (0.3, 0.8, 0.4, ("v5",)),
    "Servo": (0.4, 0.8, 0.4, ("servo_5v",)),
}

# ---- external tools / work folders ----
KICAD_DIR = os.environ.get("KICAD_DIR", r"C:\Program Files\KiCad\10.0")
KICAD_CLI = os.path.join(KICAD_DIR, "bin", "kicad-cli.exe" if os.name == "nt" else "kicad-cli")
KICAD_FOOTPRINTS = os.environ.get("KICAD_FOOTPRINTS", os.path.join(KICAD_DIR, "share", "kicad", "footprints"))
FREEROUTING_JAR = os.environ.get("FREEROUTING_JAR", r"K:\cache\freerouting\freerouting-2.4.1.jar")
SCRATCH_DIR = os.environ.get("PCB_SCRATCH", r"K:\scratch")       # render intermediates
ARTIFACTS_DIR = os.environ.get("PCB_ARTIFACTS", r"K:\artifacts")  # fab packages
