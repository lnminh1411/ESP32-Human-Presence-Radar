# Bench bring-up

Parts tested on the bench before the PCB, with what was measured. Throwaway test apps live outside the repo in `K:\temporary projects\radar-bringup\`.

## ESP32-S3 SuperMini (2026-11-02)

Status: working. Tested bare, USB only, with the RST button broken.

esptool `flash_id` (esptool v4.12.0, ESP-IDF 5.5.6 Python env):

| Item | Value |
|---|---|
| Chip | ESP32-S3 (QFN56), revision v0.2 |
| Features | Wi-Fi, BLE, embedded flash 4 MB (XMC), embedded PSRAM 2 MB (AP_3v3) |
| Flash | JEDEC manufacturer 0x46, device 0x4016, 4 MB, quad in eFuse |
| Crystal | 40 MHz |
| MAC | `98:c3:77:64:72:24` |

The board is the ESP32-S3FH4R2 variant: flash and PSRAM sit inside the chip package. At boot, ESP-IDF reports 2 MB quad PSRAM at 40 MHz and its memory test passes.

On Windows the board enumerates as `303A:1001`, a USB-Serial-JTAG CDC port with a JTAG interface. Its USB serial number is the MAC, `98:C3:77:64:72:24`. Pick the SuperMini by that serial, never by VID. The main board also shows up as `303A:1001`, with serial `288485895F14` and HID + CDC + "ESP32 Bulk" interfaces. COM numbers can change between plug-ins.

Test app `supermini_blink`: it logs chip, flash and PSRAM at boot, then toggles GPIO48 at 1 Hz. The console stays on USB-Serial-JTAG. Results:
- The onboard LED on GPIO48 blinks. GPIO48 drives both the red LED and the WS2812 data line, so the RGB LED may flicker.
- esptool `--before default_reset --after hard_reset` flashes and restarts the board over USB-Serial-JTAG. The broken RST button doesn't block flashing while the app leaves that peripheral alone.

An earlier input probe (`supermini_pinfind`: header pins pulled up, log on each low) saw GPIO5, 6, 7, 8 and 43 go low when the user touched them to GND. GPIO8 logged 321 low edges in bursts, which looks like a floating pin or a loose wire. The run didn't map every header label, so the header pin order in `pcb\README.md` still has to be checked against the silkscreen.

### Building ESP-IDF apps from Git Bash

`export.bat` refuses to run outside cmd.exe. `export.ps1` fails with "MSys/Mingw is not supported" because Git Bash passes `MSYSTEM` down to child processes. Clear `MSYSTEM`, set `IDF_TOOLS_PATH=C:\Espressif`, dot-source `C:\Espressif\frameworks\esp-idf-v5.5.6\export.ps1` in PowerShell, then run `idf.py`.

## HLK LD2410C-P radar

Not tested yet.

## VL53L1X ToF breakout

Not tested yet. The store listing shows a GY-style 6-pin board with silkscreen "VL53L0/1XV2" and pin order VIN, GND, SCL, SDA, GPIO1, XSHUT. That matches the order assumed in `pcb\README.md`. The listing photo is shared between the L0X and L1X variants. Read the silkscreen and check the VIN regulator on the actual part before wiring.
