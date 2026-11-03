"""Bench helper for the SuperMini: build, flash, log and send console lines.

The port is picked by USB serial number (the SuperMini's MAC), never by VID,
because the ESP32 PC Controller main board is also VID 0x303A and its console
command `reset` hard-resets the PC.

Run with the ESP-IDF Python env:
  C:/Espressif/python_env/idf5.5_py3.12_env/Scripts/python.exe Scripts/bench.py <command> ...

Commands:
  port                      print the SuperMini's COM port
  build <app_dir>           idf.py build (clears MSYSTEM so it works from Git Bash)
  flash <app_dir>           esptool write_flash @flash_args, then hard reset
  log <seconds>             print console lines (the boot banner is gone by the time the port reopens)
  send <line> [--wait S]    send one console line, print replies for S seconds
"""
import argparse
import os
import subprocess
import sys
import time

import serial
from serial.tools import list_ports

SUPERMINI_SERIAL = "98:C3:77:64:72:24"
IDF_PATH = r"C:\Espressif\frameworks\esp-idf-v5.5.6"
IDF_TOOLS_PATH = r"C:\Espressif"


def find_port(sn):
    hits = [p.device for p in list_ports.comports()
            if p.vid == 0x303A and (p.serial_number or "").upper() == sn.upper()]
    if len(hits) != 1:
        sys.exit(f"expected one port with USB serial {sn}, found {hits or 'none'}")
    return hits[0]


def open_port(port):
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = port, 115200, 0.2
    s.dtr = False  # DTR/RTS low: opening the USB-Serial-JTAG port must not reset the chip
    s.rts = False
    s.open()
    return s


def pump(s, secs):
    end, buf = time.time() + secs, b""
    while time.time() < end:
        buf += s.read(4096)
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            print(time.strftime("%H:%M:%S ") + line.decode("utf-8", "replace").rstrip("\r"), flush=True)


def cmd_build(app_dir):
    env = {k: v for k, v in os.environ.items() if k != "MSYSTEM"}
    env["IDF_TOOLS_PATH"] = IDF_TOOLS_PATH
    ps = (f". '{IDF_PATH}\\export.ps1' *> $null; "
          f"Set-Location -LiteralPath '{os.path.abspath(app_dir)}'; idf.py build; exit $LASTEXITCODE")
    return subprocess.call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], env=env)


def cmd_flash(app_dir, port):
    return subprocess.call([sys.executable, "-m", "esptool", "--chip", "esp32s3", "--port", port,
                            "-b", "460800", "--before", "default_reset", "--after", "hard_reset",
                            "write_flash", "@flash_args"], cwd=os.path.join(app_dir, "build"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serial", default=SUPERMINI_SERIAL, help="USB serial of the target board")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("port")
    sub.add_parser("build").add_argument("app_dir")
    sub.add_parser("flash").add_argument("app_dir")
    sub.add_parser("log").add_argument("seconds", type=float)
    p = sub.add_parser("send")
    p.add_argument("line")
    p.add_argument("--wait", type=float, default=2.0)
    a = ap.parse_args()

    if a.cmd == "build":
        sys.exit(cmd_build(a.app_dir))
    port = find_port(a.serial)
    if a.cmd == "port":
        print(port)
    elif a.cmd == "flash":
        sys.exit(cmd_flash(a.app_dir, port))
    elif a.cmd == "log":
        pump(open_port(port), a.seconds)
    elif a.cmd == "send":
        s = open_port(port)
        s.write(a.line.encode() + b"\n")
        pump(s, a.wait)


if __name__ == "__main__":
    main()
