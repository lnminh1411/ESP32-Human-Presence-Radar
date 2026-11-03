# Knowledge wiki

Max 2 sentences per entry, with file path.

- **VL53L1X aim**: its field of view is a 27° cone, so a level or downward-facing board misses a seated person 45-60° below. Tilt the board to point at the chest or head (`docs\design.md#mounting`).
- **LD2410 and fans**: the radar reads spinning fans as motion, which is why the board sits on the shelf front away from the PC tower. Cap the maximum distance gate just past the chair (`docs\design.md#mounting`).
- **RST button dead**: the SuperMini's RST (EN) button broke while the headers were soldered on. Reset by replugging USB, and enter download mode by holding BOOT while plugging in or through esptool's USB-Serial-JTAG reset (`docs\design.md#hardware`).
- **USB identity**: radar board is VID `0x303A` PID `0x8F52`, unregistered, picked above Espressif's allocated range (ended at `0x83E8` on 2026-11-02). Both boards read `0x303A:0x1001` in ROM download mode, so tell them apart by serial (`README.md#usb-identity`).
- **LD2410C pin order**: TX RX OUT GND VCC; the plain LD2410 (no C) puts OUT first. Radar IO is 3.3 V even on a 5 V supply (`pcb\README.md#parts`).
- **No diode on 5V**: each rail has one source (SuperMini USB for the sensors, the second USB for servos and beeper), so the 100 uF caps have nothing to backfeed, and a Schottky would drop the radar below 5 V. The head's cap breaks the USB 10 uF attach limit, which the rear USB 3.2 Gen 1 port tolerates (`pcb\README.md#power`).
- **SuperMini identity**: ESP32-S3FH4R2 (rev v0.2, 4 MB embedded flash, 2 MB embedded PSRAM), MAC and USB serial `98:C3:77:64:72:24`. The main board is also `303A:1001` but has serial `288485895F14` and HID + Bulk interfaces, so pick ports by serial (`docs\bringup.md#esp32-s3-supermini-2026-11-02`).
- **IDF from Git Bash**: `export.ps1` fails with "MSys/Mingw is not supported" because Git Bash passes `MSYSTEM` down. Clear `MSYSTEM` and set `IDF_TOOLS_PATH=C:\Espressif` before dot-sourcing it (`docs\bringup.md#building-esp-idf-apps-from-git-bash`).
- **SuperMini orientation**: face up with USB-C to the right, the 5V/GND/3V3 row is the near row (user-checked 2026-11-02). The base mounts it USB-C west so that row faces the FFC on the north edge (`pcb\README.md#base-board`).
- **Space under the SuperMini**: on 8.5 mm sockets plus its 2.5 mm header plastic, its underside sits 11 mm up. The beeper's PC817 and two standing resistors fit under it; a socketed module or a standing 6.3 x 11 mm cap does not (`Scripts\layout_base.py`).
- **No resistors on the sensor head**: the ToF breakout has its own I2C and XSHUT pull-ups, and the radar's UART and OUT are 3.3 V push-pull (`pcb\README.md#parts`).
- **PIR vetoes fan motion**: the LD2410 reads a moving fan as motion, a PIR only sees warm bodies, so radar motion near the chair counts only with the SR602 (GPIO10) fired recently (`docs\design.md#hardware`).
- **Two boards, one FFC**: the base stays fixed and only the sensor head rides the pan-tilt, so the servos never pull a USB cable. Base pin k meets head pin 13-k on a same-side cable; check base pin 2 to the radar VCC with a meter before plugging in sensors (`pcb\README.md#board-to-board-ffc`).
- **Blank sensors while aiming**: the moving head reads as motion to the radar and the PIR, and the SR602 holds its output 1-18 s, so ignore both during and after each servo move (`docs\design.md#hardware`).
- **Servo power USB-C**: a 6-pin power-only USB-C under the SuperMini's own, mouth on the same edge, needs a 5.1k pull-down on each CC or a C-to-C source never turns VBUS on. Its 5V leaves the module area between the TX and RX socket pins, so `servo_5v` is 0.4 mm (`pcb\README.md#base-board`).
- **Freerouting boxes in fan-outs**: at 0.5 mm pitch it routed the FFC's ground pads as 0.15 mm necks and trapped the I2C pair behind the INT track. Pre-draw those with `stitch_pad`/`route_path` (`Scripts\layout_common.py`).
