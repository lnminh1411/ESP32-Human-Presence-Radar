# Scripts

One entry per script: what it does, usage, file path. Max 3 sentences each.

PCB chain, copied from the ESP32 PC Controller carrier and adapted. `<kicad-python>` = `C:\Program Files\KiCad\10.0\bin\python.exe` (the only Python with `pcbnew`). Full rebuild, from the repo root, in this order:

```bash
cd pcb && PYTHONIOENCODING=utf-8 ato build && cd ..
<kicad-python> Scripts/make_blank_pcb.py
<kicad-python> Scripts/sync_netlist_to_board.py
<kicad-python> Scripts/layout_board.py
<kicad-python> Scripts/add_pours.py
<kicad-python> Scripts/route_board.py
<kicad-python> Scripts/chamfer_corners.py
kicad-cli pcb drc --severity-all -o drc.rpt pcb/layouts/default/default.kicad_pcb
python Scripts/render_board.py
python Scripts/export_gerbers.py
```

- `Scripts\board_config.py`: shared settings, not run. `REVISION`, `DATE`, `TITLE` (title block, fab file names), Power net class values, tool paths (`KICAD_DIR`, `FREEROUTING_JAR`, `PCB_SCRATCH`, `PCB_ARTIFACTS` env overrides).
- `Scripts\make_blank_pcb.py`: writes a blank 2-layer `pcb\layouts\default\default.kicad_pcb` with the title block. Overwrites unconditionally.
- `Scripts\sync_netlist_to_board.py`: loads `pcb\build\default.net` onto the board headless (footprints + pad nets; project footprints from `pcb\footprints\PresenceRadar.pretty`). Refs come from atopile instance names (`REF_BY_INSTANCE`: `mcu.a` J1, `mcu.b` J2, `radar` J3, `tof` J4, `boost` PS1, `jp1` JP1, `c1`/`c2` C1/C2); a new instance with no entry stops the script.
- `Scripts\layout_board.py`: places every part (rev 1.2: SuperMini sideways, USB-C west, sensors in the north corners), draws the 38.5 x 33.5 mm outline, 2 M2.5 holes and the top and bottom silkscreen, and writes fit-check models (`pcb\footprints\PresenceRadar.3dshapes\fit_modules.wrl`, on a pad-less FIT1 footprint). Placement constants at the top; not idempotent, rebuild from `make_blank_pcb.py` after any change.
- `Scripts\add_pours.py`: B.Cu GND pour and the antenna keepout between the SuperMini rows (last 4.8 mm of the module plus 1 mm past it). The keepout must exist before routing.
- `Scripts\route_board.py`: Freerouting (`K:\cache\freerouting\freerouting-2.4.1.jar`) in two passes, F.Cu only then F.Cu + B.Cu, then refills zones. Run only on a fresh board; a phantom "1 unrouted" in its log is normal, trust KiCad's DRC.
- `Scripts\chamfer_corners.py`: turns 90-degree track corners into 45-degree diagonals, collision-checked.
- `Scripts\render_board.py`: F.Cu, B.Cu, top and bottom silkscreen, a 3D overview and a 3D view from the sensor side, with board dimensions, into `pcb\build\renders\` (system Python, needs pymupdf + Pillow).
- `Scripts\export_gerbers.py`: Gerbers, PTH/NPTH drills with maps and the job file into `K:\artifacts\ESP32_Human_Presence_Radar_rev<REV>_gerbers\` plus a `.zip`. Clears the folder each run.
