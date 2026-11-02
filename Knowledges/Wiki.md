# Knowledge wiki

Max 2 sentences per entry, with file path.

- **VL53L1X aim**: its field of view is a 27° cone, so a level or downward-facing board misses a seated person 45-60° below. Tilt the board to point at the chest or head (`docs\design.md#mounting`).
- **LD2410 and fans**: the radar reads spinning fans as motion, which is why the board sits on the shelf front away from the PC tower. Cap the maximum distance gate just past the chair (`docs\design.md#mounting`).
- **RST button dead**: the SuperMini's RST (EN) button broke while the headers were soldered on. Reset by replugging USB, and enter download mode by holding BOOT while plugging in or through esptool's USB-Serial-JTAG reset (`docs\design.md#hardware`).
- **USB identity**: radar board is VID `0x303A` PID `0x8F52`, unregistered, picked above Espressif's allocated range (ended at `0x83E8` on 2026-11-02). Both boards read `0x303A:0x1001` in ROM download mode, so tell them apart by serial (`README.md#usb-identity`).
- **LD2410C pin order**: TX RX OUT GND VCC; the plain LD2410 (no C) puts OUT first. Radar IO is 3.3 V even on a 5 V supply (`pcb\README.md#parts`).
- **No diode on 5V**: the SuperMini's USB-C is the only source, so the 100 uF radar cap has nothing to backfeed, and a Schottky would drop the radar below 5 V. The cap breaks the USB 2.0 10 uF attach limit, which rear ports tolerate (`pcb\README.md#power`).
