# Scripts

One entry per script: what it does, usage, file path. Max 3 sentences each.

PCB chain, copied from the ESP32 PC Controller carrier and adapted, for two boards: `PCB_BOARD=base` (atopile build and layout `default`) or `PCB_BOARD=head`. `<kicad-python>` = `C:\Program Files\KiCad\10.0\bin\python.exe` (the only Python with `pcbnew`). `build_board.py` runs the whole chain for one board; by hand, from `Scripts\`, in this order:

```bash
cd pcb && PYTHONIOENCODING=utf-8 ato build && cd ../Scripts
export PCB_BOARD=head
<kicad-python> make_blank_pcb.py
<kicad-python> sync_netlist_to_board.py
<kicad-python> layout_head.py
<kicad-python> add_pours.py
<kicad-python> route_board.py
<kicad-python> chamfer_corners.py
kicad-cli pcb drc --severity-all -o drc.rpt ../pcb/layouts/head/head.kicad_pcb
python render_board.py
python export_gerbers.py
```

- **build_board.py** (`Scripts\build_board.py`): runs `ato build` and the chain above for one board from a blank board, prints the DRC summary and renders. `python Scripts/build_board.py base|head [--gerbers] [--no-route]`; `--no-route` stops after the pours (placement and courtyard checks only).
- **board_config.py** (`Scripts\board_config.py`): shared settings, not run. `PCB_BOARD` picks the board and its paths; `REVISION`, `DATE`, `TITLE`, net classes (`NET_CLASSES`: Power `v5` 0.3 mm, Servo `servo_5v` 0.4 mm, keep equal to both `.kicad_pro`), tool paths (`KICAD_DIR`, `FREEROUTING_JAR`, `PCB_SCRATCH`, `PCB_ARTIFACTS` env overrides).
- **make_blank_pcb.py** (`Scripts\make_blank_pcb.py`): writes a blank 2-layer board for `PCB_BOARD` with the title block. Overwrites unconditionally.
- **sync_netlist_to_board.py** (`Scripts\sync_netlist_to_board.py`): loads `pcb\build\<build>.net` onto the board headless (footprints + pad nets; project footprints from `pcb\footprints\PresenceRadar.pretty`). Refs come from atopile instance names per board (`REF_BY_INSTANCE`); a new instance with no entry stops the script.
- **layout_common.py** (`Scripts\layout_common.py`): helpers for the two layout scripts, not run: pad-anchored placement, edge sockets, outline, holes, courtyard check, locked pre-routes (`route_path`) and GND stitch vias (`stitch_pad`), silkscreen, fit-check VRML boxes.
- **layout_base.py** (`Scripts\layout_base.py`): places the base (SuperMini sideways, USB-C west, servo-power USB-C under it, FFC on the north edge, beeper parts under the module, servo/speaker strip south), draws the 32.0 x 42.0 mm outline, 2 M2.5 holes, silkscreen, pre-routes the tight spots (FFC fan-out, 5V, the USB-C's CC/GND/VBUS stubs and VBUS bridge), and writes `fit_base.wrl`. Not idempotent: rebuild from `make_blank_pcb.py` after any change.
- **layout_head.py** (`Scripts\layout_head.py`): places the sensor head (radar, PIR, ToF on right-angle sockets at the north edge, FFC on the south edge, C1/C2 south-west), draws the 46.6 x 21.0 mm outline, 2 M2.5 holes, silkscreen and `fit_head.wrl`. Not idempotent, same as the base.
- **add_pours.py** (`Scripts\add_pours.py`): B.Cu GND pour on both boards; on the base also the antenna keepout between the SuperMini rows (last 4.8 mm of the module plus 1 mm past it). The keepout must exist before routing.
- **route_board.py** (`Scripts\route_board.py`): Freerouting (`K:\cache\freerouting\freerouting-2.4.1.jar`) in two passes, F.Cu only then F.Cu + B.Cu, then refills zones. Run only on a fresh board; a phantom "1 unrouted" in its log is normal, trust KiCad's DRC.
- **chamfer_corners.py** (`Scripts\chamfer_corners.py`): turns 90-degree track corners into 45-degree diagonals, collision-checked.
- **render_board.py** (`Scripts\render_board.py`): F.Cu, B.Cu, top and bottom silkscreen and 3D views with board dimensions, into `pcb\build\renders\<board>\` (system Python, needs pymupdf + Pillow).
- **export_gerbers.py** (`Scripts\export_gerbers.py`): Gerbers, PTH/NPTH drills with maps and the job file into `K:\artifacts\ESP32_Human_Presence_Radar_<board>_rev<REV>_gerbers\` plus a `.zip`. Clears the folder each run.

- **bench.py** (`Scripts\bench.py`): builds, flashes, logs and sends console lines to the SuperMini, finding its COM port by USB serial (its MAC), never by VID, so it can't touch the main board. Run it with the ESP-IDF Python env: `C:/Espressif/python_env/idf5.5_py3.12_env/Scripts/python.exe Scripts/bench.py port|build <app>|flash <app>|log <s>|send "<line>"`. `build` clears `MSYSTEM` so ESP-IDF's export script works from Git Bash.
