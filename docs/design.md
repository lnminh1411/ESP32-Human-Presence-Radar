# Design decisions

Decisions made with the user on 2026-11-02, before any code or PCB. Each section says what was decided and what it rules out.

## Hardware

- MCU: spare ESP32-S3 SuperMini, native USB on GPIO19/20. Its RST (EN) button broke while the headers were soldered on (2026-11-02). To reset, unplug and replug USB. For download mode, hold BOOT (GPIO0) while plugging in, or let esptool reset it over USB-Serial-JTAG. Once the firmware moves USB to TinyUSB, it needs the main board's software path to the ROM downloader (DTR/RTS or 1200 baud), because no button can do it.
- Radar: HLK LD2410C-P, 24 GHz FMCW. Reports moving and stationary targets with per-gate energy. The beam is about ±60° wide.
- ToF: VL53L1X, up to 4 m in long mode in the dark. Its field of view is a 27° cone, so it must point straight at the target.
- No thermal array (dropped 2026-11-02): an AMG8833 8x8 module was considered as a third presence signal, out to about 2 m. The 26k VND listing turned out to be a pricing error; the real price is about 697k VND. If it comes back, it fits on the ToF's I2C bus (0x68/0x69; ToF at 0x29), but the north edge has no room left, so the board would have to grow.
- Own small PCB.

## Links

### ESP-NOW to the main board

The ESP32 PC Controller main board runs the desk rules: day AFK, away, intruder lock with Pushover, night desk hold (`firmware/main/presence.cpp`, `night.cpp`). Those rules must run while the PC is asleep or off, so the radar board talks to the main board directly over ESP-NOW instead of through the PC.

Constraints:
- ESP-NOW frames go out on the main board's Wi-Fi STA channel. The router is 2.4 GHz on channels 1 to 11, and the radar board has to follow the channel the main board is on.
- Radar readings can trigger the intruder lock. Frames need ESP-NOW encryption (LMK) and a sequence counter, so a spoofed or replayed frame can't fake presence or absence.
- The board-side stat name next to `pc.present` is not decided yet.

### USB to PcHwCtl

The board stays on PC USB 24/7 for power, so it also carries data to the PcHwCtl service (not the ESP32 helper). PcHwCtl can then combine radar and ToF readings with its camera `presence` check.

Constraints:
- USB identity in the README. The ESP32 helper's serial fallback takes the first `USB\VID_303A` COM port, and `scripts/idf_flash.py` in the ESP32 PC Controller repo auto-detects VID `0x303A`. Both must filter on the main board's PID and interface so they never open the radar board. PcHwCtl must likewise open only PID `0x8F52`.
- In ROM download mode both boards show up as `0x303A:0x1001`. Flashing tools must tell them apart by serial number (eFuse MAC).
- With the PC off, the USB port must keep 5 V standby power. That needs BIOS ErP turned off (still pending on the user's PC). Without it the board loses power exactly when ESP-NOW matters: at night and while away.

### No dedicated camera

Considered and dropped on 2026-11-02. The idea was a second USB camera (2 MP UVC module) to take over PcHwCtl's presence check, so the check would stop opening the PC webcam and blocking other apps.
- Dropped because radar and ToF take over routine presence. The webcam and the NPU stay for face recognition (intruder protection) at login or service startup, and for normal webcam use such as Discord.
- Findings, in case it comes back: a parallel (DVP) camera needs 12 or more GPIOs and the SuperMini has 8 free. An SPI camera (4 GPIOs plus the shared I2C) fits. A USB camera needs no GPIO, but the ESP32 can't read it (one full-speed USB port, already the link to PcHwCtl), so it runs on its own PC cable. A passive Y-splitter cable can't share one port (USB data is point-to-point), and a hub on this PCB would still need a USB-C pigtail, because the SuperMini's GPIO19/20 (USB D-/D+) reach only its USB-C.
- Possible later: an IR camera for presence in the dark. That needs a sensor with no IR-cut filter plus an 850 nm IR LED.

## Mounting

Position: the front face of the shelf above the desk, centred over the 27-inch monitor, higher and further forward than the first idea (directly under the shelf edge). The user moved it there to keep the PC tower fans, at the left end of the desk, out of the radar beam. The LD2410 reads spinning fans as motion.

The board sits tilted down toward the chair. The seated user is about 45 to 60° below horizontal from the sensor.
- The ToF's 27° cone misses a seated person completely if the board faces level or straight down. The tilt must aim it at the chest or head.
- At 45 to 60° off its centre line the radar would sit at the edge of its beam and lose most of the stationary (breathing) signal. The same tilt fixes this.
- One wedge bracket for the whole board covers both sensors.

Other mounting rules:
- The seated chest must be visible from the sensor over the top of the monitor. The radar can't see through the monitor's metal back or shelf brackets.
- The ToF needs a clear view. A cover is fine only if it passes infrared and the ToF is crosstalk-calibrated through it. The radar works behind thin plastic.
- Set the LD2410 maximum distance gate just past the chair, then tune per-gate thresholds against an empty-room reading. That cuts reflections and motion from the rest of the room.

## Open items

- Bracket angle, measured on site.
- ESP-NOW frame format, stat key names on the main board.
- USB transport to PcHwCtl (WinUSB vendor bulk with the GUID above is the plan) and its verbs.
- Step 6 of the user's global CLAUDE.md still names the old architecture folder and three repos. The user chose to leave it unchanged for now (2026-11-02). The docs themselves moved to `E:\System Architecture Documentation\ESP32 PC Control System\` with this repo as repo D.
