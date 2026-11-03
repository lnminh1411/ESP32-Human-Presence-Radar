"""
Helpers shared by layout_base.py and layout_head.py: board loading,
board-mm coordinates, pad-anchored placement, outline, mounting holes,
courtyard checks, silkscreen text and the fit-check VRML boxes.

Importing this loads the board picked by PCB_BOARD (board_config).
Coordinates are board mm: origin = board top-left, north = top, y down.
"""
import os

import pcbnew

from board_config import BOARD_PATH, KICAD_FOOTPRINTS, ROOT

MM = pcbnew.FromMM
OX, OY = 100.0, 100.0          # board top-left in KiCad page coordinates

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


def place_run(ref, x, y, dx, dy, second=2):
    """pad 1 at (x, y), pad `second` in direction (dx, dy) from it"""
    for deg in (0, 90, 180, 270):
        place_pad1(ref, x, y, deg)
        x2, y2 = pad_mm(ref, second)
        if (x2 - x) * dx + (y2 - y) * dy > 1.0:
            return
    raise SystemExit(f"{ref}: no rotation runs its pads along ({dx},{dy})")


def courtyard(fp):
    """placed courtyard box in board mm: (x0, y0, x1, y1)"""
    b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return (b.GetLeft() / 1e6 - OX, b.GetTop() / 1e6 - OY,
            b.GetRight() / 1e6 - OX, b.GetBottom() / 1e6 - OY)


def place_edge_socket(ref, num, x, pin_y):
    """right-angle socket: pin row along X at pin_y, opening north, pad
    `num` at board x"""
    for deg in (90, -90):
        fp = place_pad1(ref, 0, pin_y, deg)
        if courtyard(fp)[1] < pin_y - 9:            # body runs north of the pins
            break
    else:
        raise SystemExit(f"{ref}: no rotation puts the socket opening north")
    px, _ = pad_mm(ref, num)
    place_pad1(ref, x - px, pin_y, deg)


def outline(w, h):
    corners = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
    for (x0, y0), (x1, y1) in zip(corners, corners[1:]):
        seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(bx(x0), by(y0)))
        seg.SetEnd(pcbnew.VECTOR2I(bx(x1), by(y1)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.15))
        board.Add(seg)


def holes(points):
    mh_lib = os.path.join(KICAD_FOOTPRINTS, "MountingHole.pretty")
    for i, (x, y) in enumerate(points, start=1):
        mh = pcbnew.FootprintLoad(mh_lib, "MountingHole_2.7mm_M2.5")
        mh.SetReference(f"MH{i}")
        mh.Reference().SetVisible(False)
        mh.SetPosition(pcbnew.VECTOR2I(bx(x), by(y)))
        board.Add(mh)
        fps[f"MH{i}"] = mh


def check_courtyards(w, h, overhang):
    """print courtyards that leave the board or overlap; `overhang` maps a
    ref to the edges ("n", "s", "w", "e") it may stick out past"""
    boxes = {r: courtyard(fp) for r, fp in fps.items() if r != "FIT1"}
    for r, (x0, y0, x1, y1) in boxes.items():
        ok = overhang.get(r, "")
        if ((x0 < 0 and "w" not in ok) or (x1 > w and "e" not in ok) or (y0 < 0 and "n" not in ok)
                or (y1 > h and "s" not in ok)):
            print(f"  ! {r} courtyard leaves the board: ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f})")
    refs = sorted(boxes)
    for i, r in enumerate(refs):
        for s in refs[i + 1:]:
            a, b = boxes[r], boxes[s]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                print(f"  ! courtyards overlap: {r} and {s}")
    return boxes


def stitch_pad(ref, num, dx, dy, via_d=0.6, drill=0.3, width=0.3):
    """Locked track + via from an SMD pad to the B.Cu pour, (dx, dy) mm from
    the pad centre. Left to Freerouting, the 0.5 mm-pitch FFC ground pads
    got 0.15 mm F.Cu necks instead of vias."""
    p = pad(fps[ref], num)
    start = p.GetPosition()
    end = pcbnew.VECTOR2I(start.x + MM(dx), start.y + MM(dy))
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(start)
    t.SetEnd(end)
    t.SetWidth(MM(width))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(p.GetNet())
    t.SetLocked(True)
    board.Add(t)
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(end)
    v.SetWidth(MM(via_d))
    v.SetDrill(MM(drill))
    v.SetNet(p.GetNet())
    v.SetLocked(True)
    board.Add(v)


def route_path(ref, num, points, width=0.2):
    """Locked F.Cu track from a pad's centre through board-mm points, for
    the few routes Freerouting boxes in. It finishes the rest of the net."""
    p = pad(fps[ref], num)
    prev = p.GetPosition()
    for x, y in points:
        cur = pcbnew.VECTOR2I(bx(x), by(y))
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(prev)
        t.SetEnd(cur)
        t.SetWidth(MM(width))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(p.GetNet())
        t.SetLocked(True)
        board.Add(t)
        prev = cur


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


def labels(ref, names, dy, bottom, dx=0.0):
    for num, name in enumerate(names, start=1):
        if name:
            x, y = pad_mm(ref, num)
            text(name, x + dx, y + dy, bottom=bottom)


def clip_silk(refs, edge_y, keep_south):
    """Footprint silk that overhangs a board edge: lines wholly past the
    edge go to F.Fab, lines crossing it are cut back to it. keep_south=True
    keeps the part south of edge_y (a north edge), False the part north of
    it (a south edge). Never fp.Remove() graphics: SWIG lifetime bug."""
    cut = by(edge_y)

    def inside(p):
        return p.y >= cut if keep_south else p.y <= cut

    for ref in refs:
        for item in fps[ref].GraphicalItems():
            if item.GetLayer() != pcbnew.F_SilkS or item.GetClass() != "PCB_SHAPE":
                continue
            s, e = item.GetStart(), item.GetEnd()
            if inside(s) and inside(e):
                continue
            if not inside(s) and not inside(e):
                item.SetLayer(pcbnew.F_Fab)
                continue
            a, b = (s, e) if inside(s) else (e, s)
            k = (cut - a.y) / (b.y - a.y)
            clipped = pcbnew.VECTOR2I(int(a.x + (b.x - a.x) * k), cut)
            if inside(s):
                item.SetEnd(clipped)
            else:
                item.SetStart(clipped)


# ---- fit-check 3D models (renders only) --------------------------------------------
# One pad-less footprint at the board origin carries VRML boxes for the
# plugged-in modules, in board coordinates. KiCad scales VRML by 2.54
# (1 unit = 0.1") and its 3D Y points up, so Y is flipped.
U = 2.54


def box(x0, y0, z0, x1, y1, z1, rgb, transp=0.0):
    cx, cy, cz = (x0 + x1) / 2, -(y0 + y1) / 2, (z0 + z1) / 2
    r, g, b = rgb
    return (f"Transform {{ translation {cx/U:.4f} {cy/U:.4f} {cz/U:.4f} children [ "
            f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {r} {g} {b} "
            f"transparency {transp} }} }} geometry Box {{ size {abs(x1-x0)/U:.4f} "
            f"{abs(y1-y0)/U:.4f} {abs(z1-z0)/U:.4f} }} }} ] }}\n")


def add_fit_models(name, vrml):
    shapes = os.path.join(ROOT, "pcb", "footprints", "PresenceRadar.3dshapes")
    os.makedirs(shapes, exist_ok=True)
    with open(os.path.join(shapes, name), "w", encoding="utf-8") as f:
        f.write("#VRML V2.0 utf8\n" + vrml)
    fit = pcbnew.FOOTPRINT(board)
    fit.SetReference("FIT1")
    fit.Reference().SetVisible(False)
    fit.Value().SetVisible(False)
    fit.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
    fit.SetPosition(pcbnew.VECTOR2I(bx(0), by(0)))
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = "${KIPRJMOD}/../../footprints/PresenceRadar.3dshapes/" + name
    fit.Models().push_back(m)
    board.Add(fit)


def save(msg):
    board.Save(BOARD_PATH)
    print(msg, "saved", BOARD_PATH)
