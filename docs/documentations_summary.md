# Documentation summary

Each doc in `docs\` with its file path. Update in the same pass when a doc is added, removed or renamed.

Cross-repo system design (ESP32 PC Control System main board and helper, PcHwCtl, LocalAIHost, and this board as repo D): `E:\System Architecture Documentation\ESP32 PC Control System\ESP32-PC-Control-System.md`, with an agent copy `ESP32-PC-Control-System.agents.md` and a PDF in the same folder.

- `docs\design.md`: design decisions from 2026-11-02. Hardware (S3 SuperMini, LD2410C-P, VL53L1X; thermal array dropped), the two links (ESP-NOW to the main board, USB to PcHwCtl) with their constraints, why there is no dedicated camera (dropped; GPIO, USB and cabling findings kept), mounting position and tilt on the shelf front, open items.
- `pcb\README.md` (not in `docs\`): the presence PCB, rev 1.2. Build command, revision history, board layout (SuperMini sideways with USB-C west, parts under it, antenna keepout, routing rules), parts and how each mounts, why there are no resistors, the GPIO pin map, the radar supply jumper (direct or boost), and why the 5V rail has a 100 uF capacitor and no diode. Renders in `docs\images\`.
- `README.md` (repo root, not in `docs\`): project overview, links table, USB identity (VID `0x303A`, PID `0x8F52`, product string, WinUSB GUID).
- `docs\bringup.md`: bench bring-up results per part. SuperMini esptool identity (S3 rev v0.2, 4 MB flash, 2 MB PSRAM, MAC), GPIO48 blink test, how to tell it apart from the main board on USB, building ESP-IDF from Git Bash. Radar and ToF sections hold what is known so far.
