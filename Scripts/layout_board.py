"""
Places every footprint on pcb/layouts/default/default.kicad_pcb, draws the
rectangular board outline and mounting holes, adds the silkscreen and the
fit-check 3D models of the plugged-in modules.

Run on a fresh board, after make_blank_pcb.py and sync_netlist_to_board.py:

    <kicad-python> Scripts/layout_board.py

Not idempotent: re-running it on its own output corrupts live pcbnew SWIG
references. Rebuild from make_blank_pcb.py after any change here. Never
fp.Remove() footprint graphics; move them to another layer instead.

Layout, rev 1.3 (board coordinates, mm, origin = top-left, north = top):
  - North edge: ToF (J4) in the north-west corner and radar (J3) in the
    north-east corner, on right-angle sockets whose openings sit 1 mm past
    the edge, so each module stands at 90 degrees to the board and faces
    north. The SR602 PIR (J5) stands between them on the same kind of
    socket, lens facing north.
  - SuperMini turned sideways: rows run east-west, USB-C at the west edge,
    chip/antenna end east. Face up with the USB-C pointing west, its 5V row
    (side A: 5V GND 3V3 13..8) is the north row (user-checked 2026-11-02),
    so GPIO13..10 reach the ToF's XSHUT..SCL pins in order.
  - Under the SuperMini, between its rows: JP1 (radar supply jumper), C2 and
    the boost (PS1), soldered on a male header about 7.5 mm tall; the
    module's underside is 11 mm up. The antenna end stays clear.
  - East strip (needed anyway: the three sensors set the board width):
    C1 lying flat, the radar supply and signal tracks, one mounting hole.
  - South strip below the SuperMini: the second mounting hole, south-west,
    diagonal to the first.
  - Pin labels on both sides: the top ones read while assembling, the
    bottom ones once the modules cover the top.
"""
import os

import pcbnew

from board_config import BOARD_PATH, KICAD_FOOTPRINTS, REVISION, DATE, ROOT

MM = pcbnew.FromMM
OX, OY = 100.0, 100.0          # board top-left in KiCad page coordinates
W, H = 46.6, 36.5              # board size

SENSOR_PIN_Y = 9.6             # sensor socket pin row; opening 1 mm past the north edge
ROW_N, ROW_S = 13.3, 13.3 + 15.24   # SuperMini rows (15.24 mm measured)
MCU_USB_X = 0.5                # module's USB-C end
MCU_PIN1_X = MCU_USB_X + 1.6   # pin 1 (5V / TX); pins run east at 2.54
MCU_LEN, MCU_WIDTH = 23.5, 18.0
TOF_XSHUT_X = 1.9              # ToF XSHUT pad: socket courtyard 0.1 mm in from the west edge
RADAR_VCC_X = 34.2             # radar VCC pad (west end of J3)
PIR_OUT_X = 21.46              # SR602 OUT pad (west end of J5), over GPIO8; GND at the east end
PIR_DIA, PIR_LENS = 13.5, 10.0 # module board diameter, lens dome
ANT_X0 = 19.2                  # antenna keepout starts here (module chip end at 24.0)

JP1_X, JP1_PIN1_Y = 2.4, 17.4         # supply jumper under the module, pins run south
C2_PAD1 = (6.5, 17.7)                  # 100n, pads run south
PS1_PIN1 = (16.14, 17.4)               # boost header, pin 1 (VIN) east, pins run west
C1_PAD1 = (35.1, 29.6)                 # lying 100u, pads east-west, body north, under the radar VCC
HOLES = [(3.0, 33.4), (43.6, 15.0)]    # M2.5: south-west corner, east edge under the radar

BOOST_W, BOOST_D = 11.0, 10.4          # module, along the pins / away from them
BOOST_PIN_EDGE = 1.3                   # pin row centre to the module's pin edge

board = pcbnew.LoadBoard(BOARD_PATH)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}


def bx(x):
    return MM(OX + x)


def by(y):
    return MM(OY + y)


def pad(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            return p
    raise KeyError(f"{fp.GetReference()}.{num}")


def pad_mm(ref, num):
    p = pad(fps[ref], num).GetPosition()
    return p.x / 1e6 - OX, p.y / 1e6 - OY


def place_pad1(ref, x, y, deg):
    """rotate, then move so pad 1 lands on board point (x, y)"""
    fp = fps[ref]
    fp.SetOrientation(pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T))
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    p1 = pad(fp, 1).GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(bx(x) - p1.x, by(y) - p1.y))
    return fp


def place_run(ref, x, y, dx, dy):
    """pad 1 at (x, y), pad 2 in direction (dx, dy) from it"""
    for deg in (0, 90, 180, 270):
        place_pad1(ref, x, y, deg)
        x2, y2 = pad_mm(ref, 2)
        if (x2 - x) * dx + (y2 - y) * dy > 1.0:
            return
    raise SystemExit(f"{ref}: no rotation runs its pads along ({dx},{dy})")


def courtyard(fp):
    """placed courtyard box in board mm: (x0, y0, x1, y1)"""
    b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return (b.GetLeft() / 1e6 - OX, b.GetTop() / 1e6 - OY,
            b.GetRight() / 1e6 - OX, b.GetBottom() / 1e6 - OY)


def place_edge_socket(ref, num, x):
    """right-angle socket: pin row along X at SENSOR_PIN_Y, opening north,
    pad `num` at board x"""
    for deg in (90, -90):
        fp = place_pad1(ref, 0, SENSOR_PIN_Y, deg)
        if courtyard(fp)[1] < SENSOR_PIN_Y - 9:     # body runs north of the pins
            break
    else:
        raise SystemExit(f"{ref}: no rotation puts the socket opening north")
    px, _ = pad_mm(ref, num)
    place_pad1(ref, x - px, SENSOR_PIN_Y, deg)


# ---- placement ----------------------------------------------------------------
place_run("J1", MCU_PIN1_X, ROW_N, 1, 0)     # side A: 5V GND 3V3 13..8
place_run("J2", MCU_PIN1_X, ROW_S, 1, 0)     # side B: TX RX 1..7
place_edge_socket("J4", 6, TOF_XSHUT_X)      # ToF pad 6 = XSHUT
place_edge_socket("J3", 5, RADAR_VCC_X)      # radar pad 5 = VCC
place_edge_socket("J5", 3, PIR_OUT_X)        # PIR pad 3 = OUT
place_run("JP1", JP1_X, JP1_PIN1_Y, 0, 1)
place_run("C2", *C2_PAD1, 0, 1)
place_run("PS1", *PS1_PIN1, -1, 0)
place_run("C1", *C1_PAD1, 1, 0)
_, c1y = pad_mm("C1", 1)
if courtyard(fps["C1"])[1] > c1y - 5:        # lying body must point north
    raise SystemExit("C1: body does not lie north of its pads")

# ---- outline ------------------------------------------------------------------
corners = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
for (x0, y0), (x1, y1) in zip(corners, corners[1:]):
    seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(bx(x0), by(y0)))
    seg.SetEnd(pcbnew.VECTOR2I(bx(x1), by(y1)))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(MM(0.15))
    board.Add(seg)

# ---- mounting holes -------------------------------------------------------------
mh_lib = os.path.join(KICAD_FOOTPRINTS, "MountingHole.pretty")
for i, (x, y) in enumerate(HOLES, start=1):
    mh = pcbnew.FootprintLoad(mh_lib, "MountingHole_2.7mm_M2.5")
    mh.SetReference(f"MH{i}")
    mh.Reference().SetVisible(False)
    mh.SetPosition(pcbnew.VECTOR2I(bx(x), by(y)))
    board.Add(mh)
    fps[f"MH{i}"] = mh

# ---- overlap check (courtyards; sensor sockets may overhang north) -------------
boxes = {r: courtyard(fp) for r, fp in fps.items()}
for r, (x0, y0, x1, y1) in boxes.items():
    if x0 < 0 or x1 > W or y1 > H or (y0 < 0 and r not in ("J3", "J4", "J5")):
        print(f"  ! {r} courtyard leaves the board: ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f})")
refs = sorted(boxes)
for i, r in enumerate(refs):
    for s in refs[i + 1:]:
        a, b = boxes[r], boxes[s]
        if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
            print(f"  ! courtyards overlap: {r} and {s}")
# boost module body: between the socket rows, west of the antenna keepout
bx0, bx1 = PS1_PIN1[0] - 2.54 - BOOST_W / 2, PS1_PIN1[0] - 2.54 + BOOST_W / 2
by0 = PS1_PIN1[1] - BOOST_PIN_EDGE
by1 = by0 + BOOST_D
if bx1 > ANT_X0 or by0 < ROW_N + 1.27 or by1 > ROW_S - 1.27 or bx0 < boxes["C2"][2]:
    print(f"  ! boost body ({bx0:.2f},{by0:.2f})-({bx1:.2f},{by1:.2f}) hits a row, C2 or the antenna zone")

# ---- silkscreen -------------------------------------------------------------------
LEFT, RIGHT, CENTER = (pcbnew.GR_TEXT_H_ALIGN_LEFT, pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                       pcbnew.GR_TEXT_H_ALIGN_CENTER)


def text(s, x, y, hjust=CENTER, size=0.8, angle=0, bottom=False):
    """x, y in board mm; bottom=True prints mirrored on B.SilkS"""
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetLayer(pcbnew.B_SilkS if bottom else pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(0.15 * size))
    t.SetHorizJustify(hjust)
    t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    t.SetMirrored(bottom)
    t.SetPosition(pcbnew.VECTOR2I(bx(x), by(y)))
    board.Add(t)


def labels(ref, names, dy, bottom):
    for num, name in enumerate(names, start=1):
        x, y = pad_mm(ref, num)
        text(name, x, y + dy, bottom=bottom)


J1_NAMES = ["5V", "GND", "3V3", "13", "12", "11", "10", "9", "8"]
J2_NAMES = ["TX", "RX", "1", "2", "3", "4", "5", "6", "7"]
J4_NAMES = ["VIN", "GND", "SCL", "SDA", "INT", "XSH"]
J3_NAMES = ["TX", "RX", "OUT", "GND", "VCC"]
J5_NAMES = ["GND", "5V", "OUT"]
PS1_NAMES = ["VIN", "GND", "VO"]

# top: one label per pad. SuperMini rows label on their inside, the boost
# below its pins; the sensor labels sit in the 2 mm band between the sensor
# pins and the north row.
labels("J1", J1_NAMES, 2.05, False)
labels("J2", J2_NAMES, -2.05, False)
labels("J4", J4_NAMES, 1.85, False)
labels("J3", J3_NAMES, 1.85, False)
labels("J5", J5_NAMES, 1.85, False)
labels("PS1", PS1_NAMES, 2.1, False)
for num in (1, 2, 3):
    x, y = pad_mm("JP1", num)
    text(str(num), x + 1.6, y, LEFT)
text("BOOST", PS1_PIN1[0] - 2.54, 23.0)
text("C2", C2_PAD1[0], C2_PAD1[1] + 7.0)

# bottom: the same labels, sensors on the open north side of their pins
labels("J1", J1_NAMES, 1.7, True)
labels("J2", J2_NAMES, -1.7, True)
labels("J4", J4_NAMES, -1.7, True)
labels("J3", J3_NAMES, -1.7, True)
labels("J5", J5_NAMES, -1.7, True)
labels("PS1", PS1_NAMES, 1.7, True)
for num in (1, 2, 3):
    x, y = pad_mm("JP1", num)
    text(str(num), x + 1.6, y, RIGHT, bottom=True)   # mirrored: RIGHT reads east of the pad
text("ESP32 PRESENCE RADAR", 13.0, 24.4, bottom=True)
text("USB-C", 1.0, 21.0, angle=90, bottom=True)
text(f"REV {REVISION}  {DATE}", W - 5.6, 26.0, angle=90, bottom=True)
text("JP1 1-2 5V  2-3 BOOST", W - 4.0, 26.0, angle=90, bottom=True)
# top: only what stays visible with the modules plugged in
text("JP1 1-2 5V  2-3 BOOST", W - 1.2, 27.0, angle=90)

for ref in ("J1", "J2", "J3", "J4", "J5", "PS1", "JP1", "C2"):
    fps[ref].Reference().SetVisible(False)

# sensor socket bodies overhang the north edge: keep the stock silk (body
# outline, one line per pin, pin-1 hatch) and clip it at the board edge, as
# on the carrier's display sockets. Lines wholly past the edge go to F.Fab;
# lines crossing it are cut back to it.
SILK_IN = 0.2                  # silk stays this far inside the edge
cut = by(SILK_IN)
for ref in ("J3", "J4", "J5"):
    for item in fps[ref].GraphicalItems():
        if item.GetLayer() != pcbnew.F_SilkS or item.GetClass() != "PCB_SHAPE":
            continue
        s, e = item.GetStart(), item.GetEnd()
        if s.y >= cut and e.y >= cut:
            continue
        if s.y < cut and e.y < cut:
            item.SetLayer(pcbnew.F_Fab)
            continue
        inside, outside = (s, e) if s.y >= cut else (e, s)
        k = (cut - inside.y) / (outside.y - inside.y)
        clipped = pcbnew.VECTOR2I(int(inside.x + (outside.x - inside.x) * k), cut)
        if s.y < cut:
            item.SetStart(clipped)
        else:
            item.SetEnd(clipped)

# ---- fit-check 3D models (renders only) --------------------------------------------
# One pad-less footprint at the board origin carries VRML boxes for the
# plugged-in modules, in board coordinates. KiCad scales VRML by 2.54
# (1 unit = 0.1") and its 3D Y points up, so Y is flipped.
SHAPES = os.path.join(ROOT, "pcb", "footprints", "PresenceRadar.3dshapes")
U = 2.54
SOCKET_H, SPACER = 8.5, 2.5          # vertical socket body, module's male header plastic
SENSOR_PIN_Z = 1.5                    # right-angle socket pin height (approx.)


def box(x0, y0, z0, x1, y1, z1, rgb, transp=0.0):
    cx, cy, cz = (x0 + x1) / 2, -(y0 + y1) / 2, (z0 + z1) / 2
    r, g, b = rgb
    return (f"Transform {{ translation {cx/U:.4f} {cy/U:.4f} {cz/U:.4f} children [ "
            f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {r} {g} {b} "
            f"transparency {transp} }} }} geometry Box {{ size {abs(x1-x0)/U:.4f} "
            f"{abs(y1-y0)/U:.4f} {abs(z1-z0)/U:.4f} }} }} ] }}\n")


v = ""
mz = SOCKET_H + SPACER                                    # SuperMini underside
mx0, my0 = MCU_USB_X, (ROW_N + ROW_S) / 2 - MCU_WIDTH / 2
for ry in (ROW_N, ROW_S):
    v += box(MCU_PIN1_X - 1.27, ry - 1.25, SOCKET_H, MCU_PIN1_X + 8 * 2.54 + 1.27, ry + 1.25, mz, (0.1, 0.1, 0.1))
v += box(mx0, my0, mz, mx0 + MCU_LEN, my0 + MCU_WIDTH, mz + 1.0, (0.1, 0.2, 0.45), 0.35)
v += box(mx0 - 0.4, (ROW_N + ROW_S) / 2 - 4.5, mz + 1.0, mx0 + 7.0, (ROW_N + ROW_S) / 2 + 4.5,
         mz + 4.2, (0.75, 0.75, 0.78))                    # USB-C receptacle
v += box(mx0 + 10.0, (ROW_N + ROW_S) / 2 - 3.5, mz + 1.0, mx0 + 17.0, (ROW_N + ROW_S) / 2 + 3.5,
         mz + 1.9, (0.2, 0.2, 0.2))                       # ESP32-S3 package
# boost on its header: PCB on the 2.5 mm plastic, coil and diode on top
v += box(bx0, by0, SPACER, bx1, by1, SPACER + 1.0, (0.05, 0.45, 0.2))
ccx, ccy = (bx0 + bx1) / 2 + 1.0, (by0 + by1) / 2 - 1.0
v += box(ccx - 3.5, ccy - 3.5, SPACER + 1.0, ccx + 3.5, ccy + 3.5, SPACER + 5.0, (0.15, 0.15, 0.15))
v += box(bx0 + 2.0, by1 - 2.6, SPACER + 1.0, bx0 + 7.0, by1 - 0.4, SPACER + 3.2, (0.1, 0.1, 0.1))
# sensors standing off the north edge, approximate outlines (measure the
# real modules): male header plastic in the socket opening, PCB beyond it
for ref, n_pins, w, h, rgb in (("J3", 5, 16.0, 22.0, (0.1, 0.35, 0.15)), ("J4", 6, 17.0, 11.0, (0.4, 0.1, 0.5)),
                               ("J5", 3, PIR_DIA, PIR_DIA, (0.05, 0.05, 0.05))):
    xs = [pad_mm(ref, n)[0] for n in range(1, n_pins + 1)]
    cx = (min(xs) + max(xs)) / 2
    v += box(min(xs) - 1.27, -1.0 - SPACER, 0.3, max(xs) + 1.27, -1.0, 2.8, (0.1, 0.1, 0.1))
    v += box(cx - w / 2, -1.0 - SPACER - 1.0, SENSOR_PIN_Z - 1.5, cx + w / 2, -1.0 - SPACER,
             SENSOR_PIN_Z - 1.5 + h, rgb, 0.15)
# PIR lens dome in front of its round board
pcx, py0 = pad_mm("J5", 2)[0], -1.0 - SPACER - 1.0
v += box(pcx - PIR_LENS / 2, py0 - PIR_LENS, PIR_DIA / 2 - PIR_LENS / 2, pcx + PIR_LENS / 2, py0,
         PIR_DIA / 2 + PIR_LENS / 2, (0.95, 0.95, 0.92), 0.1)
os.makedirs(SHAPES, exist_ok=True)
with open(os.path.join(SHAPES, "fit_modules.wrl"), "w", encoding="utf-8") as f:
    f.write("#VRML V2.0 utf8\n" + v)

fit = pcbnew.FOOTPRINT(board)
fit.SetReference("FIT1")
fit.Reference().SetVisible(False)
fit.Value().SetVisible(False)
fit.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
fit.SetPosition(pcbnew.VECTOR2I(bx(0), by(0)))
m = pcbnew.FP_3DMODEL()
m.m_Filename = "${KIPRJMOD}/../../footprints/PresenceRadar.3dshapes/fit_modules.wrl"
fit.Models().push_back(m)
board.Add(fit)

board.Save(BOARD_PATH)
print(f"board outline {W:.1f} x {H:.1f} mm, {len(HOLES)} M2.5 holes, saved {BOARD_PATH}")
