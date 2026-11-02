# Design decisions

Decisions made with the user on 2026-11-02, before any code or PCB. Each section says what was decided and what it rules out.

## Hardware

- MCU: spare ESP32-S3 SuperMini, native USB on GPIO19/20. Its RST (EN) button broke while the headers were soldered on (2026-11-02). To reset, unplug and replug USB. For download mode, hold BOOT (GPIO0) while plugging in, or let esptool reset it over USB-Serial-JTAG. Once the firmware moves USB to TinyUSB, it needs the main board's software path to the ROM downloader (DTR/RTS or 1200 baud), because no button can do it.
- Radar: HLK LD2410C-P, 24 GHz FMCW. Reports moving and stationary targets with per-gate energy. The beam is about ±60° wide.
- ToF: VL53L1X, up to 4 m in long mode in the dark. Its field of view is a 27° cone, so it must point straight at the target.
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

### Dedicated presence camera

Decided 2026-11-02. PcHwCtl's presence check opens the PC webcam, which blocks other apps from using it. A second camera on this board takes over the presence check and leaves the webcam free.
- Camera: a 2 MP USB (UVC) module, GC2154 sensor, 72° view, manual focus, IR-sensitive (no IR light included). Its stock cable is a 40 cm lead from a 4-pin 2.0 mm connector to USB-A. Windows sees it as a second camera; PcHwCtl picks it with `presence.camera` (DirectShow index). The ESP32 never reads it.
- Not an SPI or DVP camera: a DVP camera needs 12 or more GPIOs and the SuperMini has 8 free; an SPI camera fits, but this module needs no GPIO at all.
- Two cables from the PC, each on its own backpanel USB 2.0 port: the camera on its stock USB-A cable, the board on its USB-C as before. Cheapest option; no PCB change, rev 1.2 stands. Each device gets the port's full 500 mA (board about 200 mA, camera 120 to 200 mA).
- Ruled out: a passive Y-splitter cable (USB data is point-to-point, so one device never enumerates); a hub, on the PCB or as a module (extra cost; on the PCB the SuperMini would still need a USB-C pigtail, since its GPIO19/20, USB D-/D+, reach only its USB-C); a USB-to-UART chip on GPIO43/44 (PcHwCtl would switch from WinUSB to a COM port, and flashing would need EN, which isn't on the headers).
- PcHwCtl picks the camera by DirectShow index, which can change when cameras are replugged, and then the check would open the main webcam again. Picking it by name is a follow-up in that repo.

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
- Camera mounting on the shelf next to the board, and its cable run (stock lead is 40 cm; may need a USB extension).
- Doc folder and slug rename for a fourth repo in `E:\System Architecture Documentation\`, plus step 6 of the user's global CLAUDE.md.
