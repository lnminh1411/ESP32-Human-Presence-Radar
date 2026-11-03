"""
Runs the whole PCB chain for one board, fresh from a blank board:
ato build -> make_blank_pcb -> sync_netlist_to_board -> layout_<board>
-> add_pours -> route_board -> chamfer_corners -> DRC -> render_board
(-> export_gerbers with --gerbers). Stops at the first failing step and
prints the DRC summary.

    python Scripts/build_board.py base|head [--gerbers] [--no-route]

--no-route stops after add_pours (placement checks only). Uses the
KiCad Python from board_config for pcbnew steps, this Python for the rest.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[1:]
if not args or args[0] not in ("base", "head"):
    raise SystemExit(__doc__)
os.environ["PCB_BOARD"] = args[0]

from board_config import BOARD_PATH, KICAD_CLI, KICAD_DIR, ROOT, SCRATCH_DIR  # noqa: E402

KPY = os.path.join(KICAD_DIR, "bin", "python.exe")
env = dict(os.environ, PYTHONIOENCODING="utf-8")


def run(cmd, cwd=HERE):
    print(">", " ".join(os.path.basename(c) if i < 2 else c for i, c in enumerate(cmd)), flush=True)
    r = subprocess.run(cmd, cwd=cwd, env=env)
    if r.returncode:
        raise SystemExit(f"step failed ({r.returncode}): {' '.join(cmd)}")


run(["ato", "build"], cwd=os.path.join(ROOT, "pcb"))
steps = ["make_blank_pcb.py", "sync_netlist_to_board.py", f"layout_{args[0]}.py", "add_pours.py"]
if "--no-route" not in args:
    steps += ["route_board.py", "chamfer_corners.py"]
for s in steps:
    run([KPY, s])
if "--no-route" in args:
    sys.exit(0)

report = os.path.join(SCRATCH_DIR, f"drc_{args[0]}.txt")
os.makedirs(SCRATCH_DIR, exist_ok=True)
subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-all", "-o", report, BOARD_PATH], env=env)
with open(report, encoding="utf-8") as f:
    lines = f.read().splitlines()
for line in lines:
    if line.startswith("**") or line.startswith("["):
        print("  ", line)
run([sys.executable, "render_board.py"])
if "--gerbers" in args:
    run([sys.executable, "export_gerbers.py"])
