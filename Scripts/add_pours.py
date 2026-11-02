"""
Adds the copper pours to pcb/layouts/default/default.kicad_pcb:
  - B.Cu: GND pour on net "gnd" (the return plane under the F.Cu routing).
    Power nets are routed Power-class tracks, not planes.
  - Antenna keepout: a rule area on all copper layers (no tracks, vias or
    zone fill) under the SuperMini's antenna end, between its two socket
    rows at its chip end. Copper under the antenna detunes Wi-Fi/ESP-NOW. Must exist BEFORE
    routing so Freerouting (via the DSN export) routes around it.

Run AFTER layout_board.py (needs final footprint positions + board outline).
Every part is through-hole, so the pour connects every GND pad with no
explicit traces or vias.

    <kicad-python> Scripts/add_pours.py
"""
import pcbnew
from board_config import BOARD_PATH

MM = pcbnew.FromMM
ANT_LEN = 4.8      # antenna end of the module: chip end back this far toward USB-C
ANT_PAST = 1.0     # keepout also runs this far past the module end

board = pcbnew.LoadBoard(BOARD_PATH)

# board outline, read back from the Edge.Cuts lines layout_board.py drew
xs, ys = [], []
for item in board.GetDrawings():
    if item.GetLayer() == pcbnew.Edge_Cuts and isinstance(item, pcbnew.PCB_SHAPE):
        for pt in (item.GetStart(), item.GetEnd()):
            xs.append(pt.x)
            ys.append(pt.y)
INSET = MM(0.5)
x0, y0, x1, y1 = min(xs) + INSET, min(ys) + INSET, max(xs) - INSET, max(ys) - INSET


def rect(zone, xa, ya, xb, yb):
    o = zone.Outline()
    o.NewOutline()
    for x, y in [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]:
        o.Append(pcbnew.VECTOR2I(int(x), int(y)))


gnd = board.FindNet("gnd")
if gnd is None:
    raise SystemExit("net 'gnd' not found on board")
zone = pcbnew.ZONE(board)
zone.SetLayer(pcbnew.B_Cu)
zone.SetNetCode(gnd.GetNetCode())
zone.SetZoneName("GND_pour")
zone.SetLocalClearance(MM(0.3))
rect(zone, x0, y0, x1, y1)
board.Add(zone)

# ---- antenna keepout ----
# Rev 1.1: the SuperMini lies sideways, J1 (north row) and J2 (south row)
# pads run east from the USB-C end; the chip/antenna end is 1.6 mm past the
# last pad. Keepout: between the rows, the last ANT_LEN mm of the module
# plus ANT_PAST mm beyond it.
def pads_of(ref):
    return [p.GetPosition() for p in board.FindFootprintByReference(ref).Pads()]


row_n = sum(p.y for p in pads_of("J1")) / 9
row_s = sum(p.y for p in pads_of("J2")) / 9
chip_end = max(p.x for p in pads_of("J1")) + MM(1.6)
keep = pcbnew.ZONE(board)
keep.SetIsRuleArea(True)
keep.SetZoneName("ANTENNA_KEEPOUT")
lset = pcbnew.LSET()
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    lset.AddLayer(layer)
keep.SetLayerSet(lset)
keep.SetDoNotAllowTracks(True)
keep.SetDoNotAllowVias(True)
keep.SetDoNotAllowZoneFills(True)
keep.SetDoNotAllowPads(False)
keep.SetDoNotAllowFootprints(False)
rect(keep, chip_end - MM(ANT_LEN), row_n + MM(1.6), chip_end + MM(ANT_PAST), row_s - MM(1.6))
board.Add(keep)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

board.Save(BOARD_PATH)
print("added GND pour (B.Cu, net 'gnd'), antenna keepout")
print("saved", BOARD_PATH)
