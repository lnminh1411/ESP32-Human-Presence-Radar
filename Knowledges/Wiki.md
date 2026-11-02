# Knowledge wiki

Max 2 sentences per entry, with file path.

- **VL53L1X aim**: its field of view is a 27° cone, so a level or downward-facing board misses a seated person 45-60° below. Tilt the board to point at the chest or head (`docs\design.md#mounting`).
- **LD2410 and fans**: the radar reads spinning fans as motion, which is why the board sits on the shelf front away from the PC tower. Cap the maximum distance gate just past the chair (`docs\design.md#mounting`).
- **RST button dead**: the SuperMini's RST (EN) button broke while the headers were soldered on. Reset by replugging USB, and enter download mode by holding BOOT while plugging in or through esptool's USB-Serial-JTAG reset (`docs\design.md#hardware`).
- **USB identity**: radar board is VID `0x303A` PID `0x8F52`, unregistered, picked above Espressif's allocated range (ended at `0x83E8` on 2026-11-02). Both boards read `0x303A:0x1001` in ROM download mode, so tell them apart by serial (`README.md#usb-identity`).
- **LD2410C pin order**: TX RX OUT GND VCC; the plain LD2410 (no C) puts OUT first. Radar IO is 3.3 V even on a 5 V supply (`pcb\README.md#parts`).
- **No diode on 5V**: the SuperMini's USB-C is the only source, so the 100 uF radar cap has nothing to backfeed, and a Schottky would drop the radar below 5 V. The cap breaks the USB 2.0 10 uF attach limit, which rear ports tolerate (`pcb\README.md#power`).
- **Radar supply jumper**: jp1 feeds the radar from the SuperMini 5V pin (1-2) or the 0.9-5V boost (2-3). The boost only helps when the 5V pin reads under 5.0 V; at 5 V in it passes through minus the SS14 drop (about 4.7 V) (`pcb\README.md#power`).
- **SuperMini identity**: ESP32-S3FH4R2 (rev v0.2, 4 MB embedded flash, 2 MB embedded PSRAM), MAC and USB serial `98:C3:77:64:72:24`. The main board is also `303A:1001` but has serial `288485895F14` and HID + Bulk interfaces, so pick ports by serial (`docs\bringup.md#esp32-s3-supermini-2026-11-02`).
- **IDF from Git Bash**: `export.ps1` fails with "MSys/Mingw is not supported" because Git Bash passes `MSYSTEM` down. Clear `MSYSTEM` and set `IDF_TOOLS_PATH=C:\Espressif` before dot-sourcing it (`docs\bringup.md#building-esp-idf-apps-from-git-bash`).
- **SuperMini orientation**: face up with USB-C to the right, the 5V/GND/3V3 row is the near row (user-checked 2026-11-02). Rev 1.1 mounts it USB-C west so that row faces the sensors and the ToF tracks run straight (`pcb\README.md#board`).
- **Space under the SuperMini**: on 8.5 mm sockets plus its 2.5 mm header plastic, its underside sits 11 mm up. The boost on a soldered header (~7.5 mm) and a jumper cap (~8.8 mm) fit under it; a socketed module does not (`Scripts\layout_board.py`).
- **No resistors on the presence board**: the ToF breakout has its own I2C and XSHUT pull-ups, and the radar's UART and OUT are 3.3 V push-pull (`pcb\README.md#parts`).
