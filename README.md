# ESP32 Human Presence Radar

## Companion projects

This board is an add-on to the ESP32 PC Control System, the main project.

| Project | Role for this board |
|---|---|
| [ESP32 PC Control System](https://github.com/lnminh1411/ESP32-PC-Control-System) (main project) | Main desk board. Receives radar and ToF readings over ESP-NOW and runs the presence rules (AFK, away, intruder lock, night) |
| [PC Hardware Control Service](https://github.com/lnminh1411/PC-Hardware-Control-Service) (PcHwCtl) | Windows service. Reads the board over USB and combines it with its webcam presence check |

## About

A small desk presence board: ESP32-S3 SuperMini, HLK LD2410C-P mmWave radar and VL53L1X time-of-flight sensor on one PCB.

The webcam presence check in PcHwCtl fails in the dark (luma 0.1 in low-power mode reads `unknown/dark`) and its depth model can't tell 1.75 m from 2.0 m. Radar and ToF work without light and give a measured distance.

Status: PCB rev 1.3 laid out and routed (46.6 x 36.5 mm, radar + ToF + PIR, DRC 0/0, Gerbers built, not ordered). No firmware yet.

## Links

| Link | Peer | Why |
|---|---|---|
| ESP-NOW | ESP32 PC Controller main board | The desk rules (`presence.cpp`, `night.cpp`) run there and must keep working while the PC sleeps or is off |
| USB (24/7, also power) | PcHwCtl service | PcHwCtl combines radar and ToF readings with its camera `presence` check |

## USB identity

Both boards use Espressif's VID, so the PID, product string and WinUSB GUID are how the PC tools tell them apart.

| Field | Radar board | Main board (for comparison) |
|---|---|---|
| VID | `0x303A` | `0x303A` |
| PID | `0x8F52` | `0x1001` |
| Product string | `ESP32 Presence Radar` | `ESP32 PC Controller` |
| Serial | eFuse MAC | eFuse MAC |
| WinUSB interface GUID | `{3195A967-946A-4344-A4CD-F95D1D1FA31E}` | `{39531AD1-55E5-4933-869D-123B4E7D172C}` |

`0x8F52` is not registered with Espressif. On 2026-11-02 their allocated list ended at `0x83E8` and grows upward from there, so this value stays clear for a long time. Register a real PID at github.com/espressif/usb-pids before publishing the hardware.

Details, mounting and open items: [docs/design.md](docs/design.md).
