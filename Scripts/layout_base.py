"""
Places every footprint on the base board
(pcb/layouts/default/default.kicad_pcb), draws the outline and mounting
holes, adds the silkscreen and the fit-check 3D model of the SuperMini.

Run on a fresh board, after make_blank_pcb.py and sync_netlist_to_board.py:

    PCB_BOARD=base <kicad-python> Scripts/layout_base.py

Not idempotent: rebuild from make_blank_pcb.py after any change here.

Layout, rev 2.0 (board mm, origin = top-left, north = top):
  - SuperMini turned sideways: rows run east-west, USB-C at the west edge,
    chip/antenna end east. Face up with the USB-C pointing west, its 5V row
    (side A: 5V GND 3V3 13..8) is the north row (user-checked 2026-11-02).
  - North edge: the FFC connector (J3), cable leaving north toward the
    head. Its pins 3-8 fan straight down into GPIO13..8; pins 9-10 (I2C)
    run around the module's chip end to GPIO6/7; 5V comes up between the
    3V3 and GPIO13 pins, 3V3 runs under the connector body to pin 11.
  - Under the SuperMini, between its rows: the servo power USB-C (J5),
    mouth flush with the west edge right under the SuperMini's own USB-C,
    so both cables leave the same edge; its 5.1k CC pull-downs (R4, R5,
    0805) behind it; the beeper's 270R and 33R (R1, R2) and its PC817
    (U1, turned upright). The antenna end stays clear. The two VBUS pads
    are joined by a short B.Cu bridge; servo_5v leaves between the TX and
    RX pins at 0.4 mm.
  - South strip: the servo plugs (J4, 2x3, signal pins east), the speaker
    header (J6) with the 1N4007 and the 10k lying under it as rungs across
    its pins 1 and 4, and C1 on the servo 5V.
  - Mounting holes north-east and south-west.
"""
import pcbnew

from board_config import DATE, REVISION
from layout_common import (MM, add_fit_models, board, box, bx, by, check_courtyards, clip_silk,
                           courtyard, fps, holes, labels, outline, pad, pad_mm, place_pad1,
                           place_run, route_path, save, stitch_pad, text)

W, H = 32.0, 42.0
ROW_N, ROW_S = 11.5, 11.5 + 15.24   # SuperMini rows (15.24 mm measured)
MCU_USB_X = 0.5                # module's USB-C end
MCU_PIN1_X = MCU_USB_X + 1.6   # pin 1 (5V / TX); pins run east at 2.54
MCU_LEN, MCU_WIDTH = 23.5, 18.0

FFC_CX, FFC_Y = 16.6, 5.4      # FFC centre, pad row; body (5.2 deep) ends 0.2 inside the north edge
MCY = (ROW_N + ROW_S) / 2      # module centre line
J5_AT = (3.4, MCY)             # USB-C origin: its "PCB edge" line (3.4 mm in front) on the west edge
VIA_X = 7.7                    # VBUS bridge vias, just behind J5's pads
R4_AT, R5_AT = (10.0, 18.05), (10.0, 20.2)   # 0805 CC pull-downs (north CC, south CC), pad 1 west
R2_PAD1 = (9.4, 15.5)          # 33R, pads run east; pad 1 (collector side) west
R1_PAD1 = (9.4, 22.75)          # 270R, pads run east; pad 1 (GPIO4 side) west
U1_PIN1 = (14.7, 22.82)        # PC817 upright: pin 2 east of pin 1, pin 4 north of it
J4_PIN1 = (8.6, 31.4)          # servos: pan row 1-3-5 west, tilt row 2-4-6 south of it
J6_PIN1 = (22.22, 31.4)        # speaker, + east, drive (pin 4) west
D1_K = (22.22, 34.9)           # 1N4007 lying, cathode east under J6 pin 1
R3_PAD1 = (22.22, 38.6)        # 10k lying, under D1
C1_PAD1 = (26.35, 33.4)        # 100u standing, + west
HOLES = [(28.6, 3.4), (3.0, 39.0)]

# ---- placement ----------------------------------------------------------------
place_run("J1", MCU_PIN1_X, ROW_N, 1, 0)     # side A: 5V GND 3V3 13..8
place_run("J2", MCU_PIN1_X, ROW_S, 1, 0)     # side B: TX RX 1..7
place_pad1("J3", FFC_CX - 2.75, FFC_Y, 0)
if pad_mm("J3", 12)[0] < pad_mm("J3", 1)[0] or courtyard(fps["J3"])[1] > FFC_Y - 5:
    raise SystemExit("J3: pin 1 must be west with the body north")
stitch_pad("J3", 1, -0.8, 0)                 # FFC ground pads: via past each end of the row
stitch_pad("J3", 12, 0.8, 0)
# Pre-routes Freerouting boxed in or necked to 0.15 mm. I2C (FFC 9 SDA,
# 10 SCL) leaves the fan-out first, runs east above GPIO8, down past the
# antenna keepout and back west under the south row: SCL outside, so it
# lands on GPIO6, SDA on GPIO7. INT (FFC 8) drops below the I2C pair
# before turning to GPIO8. 5V runs under the north row and up between the
# 3V3 and GPIO13 pins.
route_path("J3", 9, [(FFC_CX + 1.25, 7.0), (FFC_CX + 2.05, 7.8), (25.6, 7.8), (25.6, ROW_S),
                     pad_mm("J2", 9)])
route_path("J3", 10, [(FFC_CX + 1.75, 6.6), (FFC_CX + 2.35, 7.2), (26.2, 7.2), (26.2, ROW_S + 1.46),
                      (20.6, ROW_S + 1.46), (pad_mm("J2", 8)[0], ROW_S + 0.74), pad_mm("J2", 8)])
route_path("J3", 8, [(FFC_CX + 0.75, 8.4), (20.0, 8.4), (pad_mm("J1", 9)[0], ROW_N - 0.68),
                     pad_mm("J1", 9)])
# PIR (FFC 6) and XSHUT (FFC 7) fan out under the INT track the same way.
route_path("J3", 6, [(FFC_CX - 0.25, 9.6), (pad_mm("J1", 7)[0], 10.59), pad_mm("J1", 7)])
route_path("J3", 7, [(FFC_CX + 0.25, 9.0), (pad_mm("J1", 8)[0] - 0.3, 9.0),
                     (pad_mm("J1", 8)[0], 9.3), pad_mm("J1", 8)])
route_path("J1", 1, [(3.5, 12.9), (8.45, 12.9), (8.45, 9.6),
                     (11.05, 7.0), (FFC_CX - 2.75, 7.0), (FFC_CX - 2.25, 6.5), (FFC_CX - 2.25, FFC_Y)],
           width=0.3)
# ---- servo power USB-C under the module ----
j5 = fps["J5"]
for deg in (90, -90):                        # mouth (+Y in the footprint) west
    j5.SetOrientation(pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T))
    j5.SetPosition(pcbnew.VECTOR2I(bx(J5_AT[0]), by(J5_AT[1])))
    if pad_mm("J5", "A5")[0] > J5_AT[0] + 2:
        break
else:
    raise SystemExit("J5: no rotation puts the mouth west")
cc_n, cc_s = sorted(("A5", "B5"), key=lambda n: pad_mm("J5", n)[1])
vb_n, vb_s = sorted(("A9", "B9"), key=lambda n: pad_mm("J5", n)[1])
r_n, r_s = ("R4", "R5") if cc_n == "A5" else ("R5", "R4")
place_run(r_n, R4_AT[0] - 0.9125, R4_AT[1], 1, 0)
place_run(r_s, R5_AT[0] - 0.9125, R5_AT[1], 1, 0)
# 0.5 mm-pitch-ish pads again: Freerouting necked CC and GND to 0.15 mm,
# so they are drawn here. CC straight to its pull-down; each GND pad to the
# shell leg behind it (the legs reach the B.Cu pour).
for cc, r in ((cc_n, r_n), (cc_s, r_s)):
    x, y = pad_mm("J5", cc)
    route_path("J5", cc, [(VIA_X + 0.3, y), pad_mm(r, 1)])
legs = [(p.GetPosition().x / 1e6 - 100.0, p.GetPosition().y / 1e6 - 100.0)
        for p in j5.Pads() if p.GetNumber() == "SH"]
for g in ("A12", "B12"):
    gx, gy = pad_mm("J5", g)
    route_path("J5", g, [min(legs, key=lambda l: (l[0] - gx) ** 2 + (l[1] - gy) ** 2)], width=0.3)


def add_via(x, y, net, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(bx(x), by(y)))
    v.SetWidth(MM(d))
    v.SetDrill(MM(drill))
    v.SetNet(net)
    v.SetLocked(True)
    board.Add(v)


# VBUS: both pads to vias, joined on B.Cu behind the CC pads; the south
# pad also carries servo_5v down and west, out between TX and RX.
vbus = pad(j5, vb_s).GetNet()
yn, ys = pad_mm("J5", vb_n)[1], pad_mm("J5", vb_s)[1]
route_path("J5", vb_n, [(VIA_X, yn)], width=0.4)
add_via(VIA_X, yn, vbus)
add_via(VIA_X, ys, vbus)
bridge = pcbnew.PCB_TRACK(board)
bridge.SetStart(pcbnew.VECTOR2I(bx(VIA_X), by(yn)))
bridge.SetEnd(pcbnew.VECTOR2I(bx(VIA_X), by(ys)))
bridge.SetWidth(MM(0.5))
bridge.SetLayer(pcbnew.B_Cu)
bridge.SetNet(vbus)
bridge.SetLocked(True)
board.Add(bridge)
gap_x = (pad_mm("J2", 1)[0] + pad_mm("J2", 2)[0]) / 2
route_path("J5", vb_s, [(VIA_X, ys), (VIA_X, ROW_S - 2.14), (VIA_X - 0.6, ROW_S - 1.54),
                        (gap_x + 0.63, ROW_S - 1.54), (gap_x, ROW_S - 0.91), (gap_x, ROW_S + 1.7)],
           width=0.4)

for deg in (0, 90, 180, 270):                # upright: pin 2 east of pin 1, pin 4 north of it
    place_pad1("U1", *U1_PIN1, deg)
    if pad_mm("U1", 2)[0] > U1_PIN1[0] + 1 and pad_mm("U1", 4)[1] < U1_PIN1[1] - 5:
        break
else:
    raise SystemExit("U1: no rotation fits")
place_run("R1", *R1_PAD1, 1, 0)
place_run("R2", *R2_PAD1, 1, 0)
for deg in (0, 90, 180, 270):                # pad 3 west of pad 1, pad 2 south of it
    place_pad1("J4", *J4_PIN1, deg)
    if pad_mm("J4", 3)[0] < J4_PIN1[0] - 1 and pad_mm("J4", 2)[1] > J4_PIN1[1] + 1:
        break
else:
    raise SystemExit("J4: no rotation fits")
place_run("J6", *J6_PIN1, -1, 0)
place_run("D1", *D1_K, -1, 0)
place_run("R3", *R3_PAD1, -1, 0)
place_run("C1", *C1_PAD1, 1, 0)

outline(W, H)
holes(HOLES)
check_courtyards(W, H, {"J3": "n", "J5": "w"})

# ---- silkscreen -------------------------------------------------------------------
J1_NAMES = ["5V", "GND", "3V3", "13", "12", "11", "10", "9", "8"]
J2_NAMES = ["TX", "RX", "1", "2", "3", "4", "5", "6", "7"]
J4_NAMES = ["S", "S", "+", "+", "-", "-"]

# top: SuperMini rows label on their inside (read while assembling)
labels("J1", J1_NAMES, 2.05, False)
labels("J2", J2_NAMES, -2.05, False)
labels("J6", ["+", "", "", "DRV"], -2.3, False)
for bottom in (False, True):
    text("PAN", pad_mm("J4", 3)[0], 29.3, bottom=bottom)
    text("TILT", pad_mm("J4", 4)[0], 36.0, bottom=bottom)

# bottom: the same, readable once the module covers the top
labels("J1", J1_NAMES, 1.7, True)
labels("J2", J2_NAMES, -1.7, True)
labels("J6", ["5V", "", "", "SPK"], -2.3, True)
text("PRESENCE RADAR BASE", 14.0, 40.7, bottom=True)
text(f"REV {REVISION}  {DATE}", FFC_CX, 8.7, bottom=True)
text("R2 33R", 10.67, 16.8, bottom=True)                 # parts under the module: values below
text("R4 R5 5.1K", 10.0, MCY, size=0.8, bottom=True)
text("R1 270R", 10.67, 21.0, bottom=True)
text("PC817", (pad_mm("U1", 1)[0] + pad_mm("U1", 2)[0]) / 2, MCY, angle=90, bottom=True)
text("1N4007", 18.4, 36.75, bottom=True)
text("10K", 18.4, 38.6, bottom=True)
text("USB-C  UPPER: MCU  LOWER: SERVO 5V", 0.7, MCY, angle=90, bottom=True)
text("TO HEAD", FFC_CX, 1.6, bottom=True)

for ref in ("J1", "J2", "J3", "J4", "J5", "J6", "D1", "R3", "R1", "R2", "R4", "R5", "U1"):
    fps[ref].Reference().SetVisible(False)
clip_silk(("J3",), 0.2, keep_south=True)

# ---- fit-check 3D model -------------------------------------------------------------
SOCKET_H, SPACER = 8.5, 2.5          # vertical socket body, module's male header plastic
v = ""
mz = SOCKET_H + SPACER                                    # SuperMini underside
mx0, my0 = MCU_USB_X, (ROW_N + ROW_S) / 2 - MCU_WIDTH / 2
mcy = (ROW_N + ROW_S) / 2
for ry in (ROW_N, ROW_S):
    v += box(MCU_PIN1_X - 1.27, ry - 1.25, SOCKET_H, MCU_PIN1_X + 8 * 2.54 + 1.27, ry + 1.25, mz, (0.1, 0.1, 0.1))
v += box(mx0, my0, mz, mx0 + MCU_LEN, my0 + MCU_WIDTH, mz + 1.0, (0.1, 0.2, 0.45), 0.35)
v += box(mx0 - 0.4, mcy - 4.5, mz + 1.0, mx0 + 7.0, mcy + 4.5, mz + 4.2, (0.75, 0.75, 0.78))  # USB-C
v += box(mx0 + 10.0, mcy - 3.5, mz + 1.0, mx0 + 17.0, mcy + 3.5, mz + 1.9, (0.2, 0.2, 0.2))  # ESP32-S3
v += box(FFC_CX - 3.0, -8.0, 1.0, FFC_CX + 3.0, 1.0, 1.1, (0.85, 0.6, 0.2))                 # FFC cable
add_fit_models("fit_base.wrl", v)

save(f"base outline {W:.1f} x {H:.1f} mm, {len(HOLES)} M2.5 holes,")
