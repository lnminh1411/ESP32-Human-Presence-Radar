# Knowledge wiki

Max 2 sentences per entry, with file path.

- **VL53L1X aim**: its field of view is a 27° cone, so a level or downward-facing board misses a seated person 45-60° below. Tilt the board to point at the chest or head (`docs\design.md#mounting`).
- **LD2410 and fans**: the radar reads spinning fans as motion, which is why the board sits on the shelf front away from the PC tower. Cap the maximum distance gate just past the chair (`docs\design.md#mounting`).
- **USB identity**: radar board is VID `0x303A` PID `0x8F52`, unregistered, picked above Espressif's allocated range (ended at `0x83E8` on 2026-11-02). Both boards read `0x303A:0x1001` in ROM download mode, so tell them apart by serial (`README.md#usb-identity`).
