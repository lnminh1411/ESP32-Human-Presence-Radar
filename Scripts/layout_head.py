"""
Places every footprint on the sensor head board
(pcb/layouts/head/head.kicad_pcb), draws the outline and mounting holes,
adds the silkscreen and the fit-check 3D models of the plugged-in sensors.

Run on a fresh board, after make_blank_pcb.py and sync_netlist_to_board.py:

    PCB_BOARD=head <kicad-python> Scripts/layout_head.py

Not idempotent: rebuild from make_blank_pcb.py after any change here.

Layout, rev 2.2 (board mm, origin = top-left, north = top):
  - North edge, west to east: radar (J1), PIR (J3), ToF (J2), each on a
    right-angle socket whose opening sits 1 mm past the edge, so the
    modules stand at 90 degrees to the board and face north.
  - South edge: the FFC connector (J4), turned so the cable leaves south
    toward the base. Its pin order follows the sensors west to east, so
    every signal fans straight up to its socket pin; the radar's 5V reaches
    the PIR along the north side of the radar pins.
  - Behind the PIR: the red indicator LED (D1, anode west) and its 270R
    (R1, standing), fed from FFC pin 3 (GPIO4 on the base).
  - North edge, between the PIR and ToF sockets: the GL5528 LDR (R3),
    fitted from the bottom with its leads bent 90 degrees so it faces north
    past the edge, under the sensors; its 10k (R2) and 100nF (C3), 0805,
    on top in the same gap. The LDR line runs straight down to FFC pin 8.
  - South-west: C1 (100u) and C2 (100n, standing north-south) on the
    radar's 5V. Mounting holes in the two south corners.
"""
import pcbnew

from board_config import DATE, REVISION
from layout_common import (add_fit_models, box, check_courtyards, clip_silk, fps, holes,
                           labels, outline, pad_mm, place_edge_socket, place_pad1, place_run,
                           route_path, save, stitch_pad, text)

W, H = 46.6, 25.0
SENSOR_PIN_Y = 9.6             # sensor socket pin row; opening 1 mm past the north edge
RADAR_VCC_X = 2.57             # radar pad 5 (VCC), west end of J1
PIR_OUT_X = 20.36              # SR602 pad 3 (OUT), west end of J3
TOF_XSHUT_X = 32.0             # ToF pad 6 (XSHUT), west end of J2
RADAR_W, RADAR_H = 16.0, 22.0  # module outlines (approx., for the fit check)
TOF_W, TOF_H = 17.0, 11.0
PIR_DIA, PIR_LENS = 13.5, 10.0

FFC_CX = 29.5                  # FFC centre; pins run west 14..1 east
FFC_Y = H - 5.4                # pad row: body (5.2 deep) ends 0.2 inside the south edge
C1_PAD1 = (8.6, H - 3.6)       # 100u, + west
C2_PAD1 = (15.5, H - 6.4)      # 100n, pads run south
D1_K = (24.57, 16.0)           # LED cathode (pad 1), anode 2.54 west
R1_PAD1 = (19.0, 18.04)        # 270R, pad 1 (from the FFC) south, pad 2 north
LDR_CX, LDR_Y = 28.7, 2.6      # LDR pad 1, in the 2.9 mm between the J3 and J2 courtyards
HOLES = [(3.2, H - 3.2), (W - 3.2, H - 3.2)]

# ---- placement ----------------------------------------------------------------
place_edge_socket("J1", 5, RADAR_VCC_X, SENSOR_PIN_Y)
place_edge_socket("J3", 3, PIR_OUT_X, SENSOR_PIN_Y)
place_edge_socket("J2", 6, TOF_XSHUT_X, SENSOR_PIN_Y)
place_pad1("J4", FFC_CX + 3.25, FFC_Y, 180)
if pad_mm("J4", 14)[0] > pad_mm("J4", 1)[0]:
    raise SystemExit("J4: pin 14 must be west")
# FFC ground pads (14 west, 1 east): via just past each end of the pin row
stitch_pad("J4", 14, -0.8, 0)
stitch_pad("J4", 1, 0.8, 0)
place_run("C1", *C1_PAD1, 1, 0)
place_run("C2", *C2_PAD1, 0, 1)
place_run("D1", *D1_K, -1, 0)
place_run("R1", *R1_PAD1, 0, -1)
# LDR from the bottom, holes one behind the other (the gap is too narrow for
# them side by side): pad 1 (3V3) north, pad 2 (LDR line) south. Bend the
# south lead 2.5 mm further back. Its stock outline goes to B.Fab: the body
# sits bent out past the edge, not over the holes.
ldr = fps["R3"]
ldr.Flip(ldr.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
place_run("R3", LDR_CX, LDR_Y, 0, 1)
for g in ldr.GraphicalItems():
    if g.GetLayer() == pcbnew.B_SilkS:
        g.SetLayer(pcbnew.B_Fab)
# 10k and 100nF (0805) stacked below it: LDR-line pads at the ends, the two
# GND pads face each other over one via to the pour; the LDR line jumps C3's
# GND pad along the west side
place_run("R2", LDR_CX, 6.65, 0, 1)
place_run("C3", LDR_CX, 11.96, 0, -1)
stitch_pad("R2", 2, 0, (pad_mm("C3", 2)[1] - pad_mm("R2", 2)[1]) / 2)
route_path("R2", 1, [(LDR_CX - 1.15, 6.65), (LDR_CX - 1.15, 11.96), pad_mm("C3", 1)])

outline(W, H)
holes(HOLES)
check_courtyards(W, H, {"J1": "n", "J2": "n", "J3": "n", "J4": "s", "R3": "n"})

# ---- silkscreen -------------------------------------------------------------------
J1_NAMES = ["TX", "RX", "OUT", "GND", "VCC"]
J2_NAMES = ["VIN", "GND", "SCL", "SDA", "INT", "XSH"]
J3_NAMES = ["GND", "5V", "OUT"]
for ref, names in (("J1", J1_NAMES), ("J2", J2_NAMES), ("J3", J3_NAMES)):
    labels(ref, names, 1.85, False)       # top: between the pins and the routing
    labels(ref, names, -1.7, True)        # bottom: north of the pins
text("RADAR", 4.6, 12.9)
text("PIR", 22.9, 12.9)
text("TOF", 38.35, 12.9)
text("TO BASE", FFC_CX, FFC_Y - 2.0)
text("ESP32 PRESENCE RADAR - HEAD", 12.0, 4.0, bottom=True)
text(f"REV {REVISION}  {DATE}", 12.0, 5.6, bottom=True)
text("BASE PIN k = HEAD 15-k", FFC_CX, D1_K[1] - 2.4, bottom=True)
# part values
text("RED", 27.2, D1_K[1])                                        # D1
text("270R", 16.4, R1_PAD1[1] - 2.54)                             # R1
text("100uF 25V", C1_PAD1[0] + 1.25, C1_PAD1[1] - 4.2)            # C1
text("100nF", C2_PAD1[0] + 2.1, C2_PAD1[1] + 2.5, angle=90)       # C2
text("GL5528", LDR_CX, 1.0, width=0.6)                            # R3 (fitted from below)
text("10K", LDR_CX, 7.56, bottom=True)                            # R2, C3: no room on top
text("100nF", LDR_CX, 11.0, bottom=True)

for ref in ("J1", "J2", "J3", "J4", "C1", "C2", "C3", "D1", "R1", "R2", "R3"):
    fps[ref].Reference().SetVisible(False)
clip_silk(("J1", "J2", "J3"), 0.2, keep_south=True)
clip_silk(("J4",), H - 0.2, keep_south=False)

# ---- fit-check 3D models -------------------------------------------------------------
SPACER = 2.5                          # module's male header plastic
SENSOR_PIN_Z = 1.5                    # right-angle socket pin height (approx.)
v = ""
for ref, n_pins, w, h, rgb in (("J1", 5, RADAR_W, RADAR_H, (0.1, 0.35, 0.15)),
                               ("J2", 6, TOF_W, TOF_H, (0.4, 0.1, 0.5)),
                               ("J3", 3, PIR_DIA, PIR_DIA, (0.05, 0.05, 0.05))):
    xs = [pad_mm(ref, n)[0] for n in range(1, n_pins + 1)]
    cx = (min(xs) + max(xs)) / 2
    v += box(min(xs) - 1.27, -1.0 - SPACER, 0.3, max(xs) + 1.27, -1.0, 2.8, (0.1, 0.1, 0.1))
    v += box(cx - w / 2, -1.0 - SPACER - 1.0, SENSOR_PIN_Z - 1.5, cx + w / 2, -1.0 - SPACER,
             SENSOR_PIN_Z - 1.5 + h, rgb, 0.15)
pcx, py0 = pad_mm("J3", 2)[0], -1.0 - SPACER - 1.0
v += box(pcx - PIR_LENS / 2, py0 - PIR_LENS, PIR_DIA / 2 - PIR_LENS / 2, pcx + PIR_LENS / 2, py0,
         PIR_DIA / 2 + PIR_LENS / 2, (0.95, 0.95, 0.92), 0.1)
# FFC cable stub leaving south
v += box(FFC_CX - 3.0, H - 1.0, 1.0, FFC_CX + 3.0, H + 8.0, 1.1, (0.85, 0.6, 0.2))
add_fit_models("fit_head.wrl", v)

save(f"head outline {W:.1f} x {H:.1f} mm, {len(HOLES)} M2.5 holes,")
