# Documentation summary

Each doc in `docs\` with its file path. Update in the same pass when a doc is added, removed or renamed.

Cross-repo system design (ESP32 PC Control System main board and helper, PcHwCtl, LocalAIHost, and this board as repo D): `E:\System Architecture Documentation\ESP32 PC Control System\ESP32-PC-Control-System.md`, with an agent copy `ESP32-PC-Control-System.agents.md` and a PDF in the same folder.

- `docs\design.md`: design decisions from 2026-11-02. Hardware (S3 SuperMini, LD2410C-P, VL53L1X, SR602 PIR; thermal array dropped; two-servo pan-tilt with a fixed base and a moving sensor head; piezo beeper), presence rules for the firmware including blanking while the servos move, the two links (ESP-NOW to the main board, USB to PcHwCtl on a rear USB 3.2 Gen 1 port) with their constraints, why there is no dedicated camera (dropped; GPIO, USB and cabling findings kept), mounting position and tilt on the shelf front, open items.
- `pcb\README.md` (not in `docs\`): the presence PCBs, rev 1.4: base (SuperMini, servos, beeper) and sensor head (radar, PIR, ToF) joined by a 12-pin FFC. Build commands, revision history, FFC pinout and cable check, both board layouts and routing rules, parts and how each mounts, the GPIO pin map, power (two USB inputs), the beeper circuit. Renders in `docs\images\`.
- `README.md` (repo root, not in `docs\`): project overview, links table, USB identity (VID `0x303A`, PID `0x8F52`, product string, WinUSB GUID).
- `docs\bringup.md`: bench bring-up results per part. SuperMini esptool identity (S3 rev v0.2, 4 MB flash, 2 MB PSRAM, MAC), GPIO48 blink test, SG90 servo on GPIO8, how to tell it apart from the main board on USB, building ESP-IDF from Git Bash. Radar and ToF sections hold what is known so far.
