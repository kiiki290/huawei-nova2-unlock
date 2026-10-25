# Huawei nova 2 (PIC-TL00 / Kirin 659) Bootloader Unlock — Software Testpoint

[中文主教程](docs/UNLOCK-TUTORIAL.md) · [English summary](#english-summary)

> **Status:** tested on a Huawei nova 2 **PIC-TL00** (EMUI 8.0.0.377(C01), Android 8.0.0, Kirin 659 / hi6250, kernel 4.4.23+).  
> The bootloader was unlocked without disassembly; the phone was restored to stock 377 and boots. Root was not performed.
>
> **WARNING:** This is a last-resort, high-risk procedure. It wipes user data, voids warranty, and can brick the device. Only use it on a device you own. Do not use it on other models, SoCs, or EMUI versions. No warranty; you are responsible for your device.
>
> **Not included:** Huawei firmware, bootloader images, proprietary drivers, and third-party binaries are **not** committed to this repository. Download them from official/upstream sources and check their licenses. The device serial, IMEI, and unlock code are intentionally omitted.

## What this is

A reproducible write-up of a **software testpoint** (no disassembly) bootloader unlock for an old Huawei Kirin 659 device. The chain is:

```text
stock EMUI
  -> 5% USB Update mode + offline dload + CRC collision
  -> corrupted XLOADER -> VCOM (12D1:3609)
  -> pyusb upload of PotatoNV temporary USB bootloader
  -> temporary fastboot (FB UNLOCKED, 18D1:D00D)
  -> write WVLOCK/USRKEY in NVME
  -> restore stock XLOADER
  -> fastboot oem unlock <code>
  -> USER LockState: UNLOCKED
```

The write-up also documents the post-unlock **eRecovery boot loop** we hit and the non-obvious fix: the `/cust` partition (`mmcblk0p53`, 192 MB) had no filesystem; formatting it as ext4 made the system boot.

## What this is not

- Not a universal Huawei unlock tool.
- Not a signature bypass: the CRC collision only gets a deliberately corrupted XLOADER past the EMUI 8 update-binary's block-CRC check so the bootrom falls into VCOM.
- Not a recommendation to use the wrong TWRP. `twrp-3.4.0-0-prague.img` is for the **P8 Lite 2017**, not the nova 2 (PIC / Picasso); we used it only as a temporary ADB/dd diagnostic tool and restored stock recovery afterwards.
- Not a source of firmware, bootloaders, or unlock codes for other devices.

## Tested device

| Item | Value |
|---|---|
| Model | Huawei nova 2 PIC-TL00 |
| SoC | Kirin 659 / hi6250 |
| OS | EMUI 8.0.0.377(C01), Android 8.0.0 |
| Bootloader build | 8.0.0.386(C01) |
| USB modes | `12D1:3609` VCOM, `18D1:D00D` temporary fastboot, `12D1:107E` eRecovery |
| Result | `USER LockState: UNLOCKED`; stock 377 boots; root not performed |

## Repository layout

| Path | Purpose |
|---|---|
| `docs/UNLOCK-TUTORIAL.md` | Full method, toolchain, commands, protocol details, pitfalls, recovery |
| `PROGRESS.md` | Lab notebook / device-specific record (sanitize before publishing) |
| `analysis/vcom_upload.py` | pyusb VCOM uploader for the PotatoNV Kirin 65x bootloaders |
| `analysis/fastboot_nve.py` | Minimal raw fastboot client for binary `getvar:nve:` writes |
| `analysis/extract_more_parts.py` | Extract partitions from `UPDATE.APP` |
| `analysis/extract_parts_own.py` | Extract the critical boot partitions |
| `analysis/dump_part.py` | Dump `oeminfo`/`dfx` for diagnostics |
| `analysis/updateapp-parts.txt` | `UPDATE.APP` partition offsets/sizes |
| `.gitignore` | Keeps firmware, tools, venv, logs, dumps and third-party source out of git |

Large firmware, downloaded tools, bootloaders, Magisk/TWRP images, screenshots and device dumps are intentionally excluded.

## Toolchain (short version)

- Windows 10/11 + PowerShell 7, Python 3.14, Android platform-tools (`adb`, `fastboot`)
- Python: `pyserial`, `crccheck`, `pyusb`, `libusb-package`
- [Kirin-Tool v2.4.2](https://kirintool.cfd/) (reference only; its software-testpoint path rejects online OTA packages)
- [PotatoNV-next v2.2.1](https://github.com/mashed-potatoes/PotatoNV) + `bootloaders/hisi65x_a`
- [huawei-usbdload-tool](https://github.com/kasnria001/huawei-usbdload-tool) (5% USB-update sender; check its license before redistributing)
- Matching Huawei OTA (`UPDATE.APP`) from Firmware Finder / official sources
- Huawei DBAdapter driver (`hw_cdcacm` / `ew_usbccgpfilter`) for the 5% mode COM port
- Optional: Magisk 25.2 (root), TWRP `prague` (diagnostics only; wrong device)

Exact versions, hashes, and setup commands: see [docs/UNLOCK-TUTORIAL.md](docs/UNLOCK-TUTORIAL.md).

## Key pitfalls

1. The official Kirin-Tool software testpoint fails on `ONLINE_UPDATE` packages; the OTA has to be converted to an offline dload package.
2. Keep the XLOADER header name `XLOADER`; changing it to `PRELOADER` was rejected on this EMUI 8 build.
3. The 5% mode needs a working `DBAdapter Reserved Interface` COM port; the VCOM stage does not need a COM driver and is done with pyusb.
4. Never bind random devices (especially your keyboard) with Zadig.
5. `fastboot boot`, `oem reboot-recovery`, `erase misc`, `erase metadata`, and flashing `vendor/odm/product` are blocked by FB LOCKED in the normal bootloader; the temporary PotatoNV bootloader has FB UNLOCKED.
6. `fastboot getvar:nve:` truncates binary values at `0x00`; choose an unlock code whose SHA256 contains no NUL byte.
7. Restore the stock XLOADER **before** rebooting, or the phone goes back to VCOM.
8. `twrp-3.4.0-0-prague.img` is for the P8 Lite 2017, not the nova 2 (PIC / Picasso). Use it only temporarily for ADB/dd diagnostics.
9. The unlock factory reset can fail and leave the phone in eRecovery; a full 377 dload alone did not fix it.
10. The decisive fix was formatting the `/cust` partition (`mmcblk0p53`, 192 MB) as ext4; the OTA `UPDATE.APP` does not contain CUST.
11. eRecovery "download latest version" can fail with `获取软件包信息失败` because Huawei no longer hosts the old package.
12. Full 377 dload re-locked the bootloader; re-unlock with the same code before flashing.
13. Do not publish the device SN/IMEI/unlock code, firmware, bootloaders, or proprietary drivers.

## English summary

This repository documents a no-disassembly **software-testpoint bootloader unlock** for the Huawei nova 2 (PIC-TL00, Kirin 659, EMUI 8.0.0.377). It uses the 5% USB update mode with a CRC-collided XLOADER to enter VCOM, uploads the PotatoNV temporary bootloader over pyusb, writes `WVLOCK`/`USRKEY` in NVME, restores the stock XLOADER, and runs `fastboot oem unlock`. A post-unlock eRecovery boot loop was fixed by formatting the empty `/cust` partition as ext4. Firmware, bootloaders, and proprietary tools are not included. Use at your own risk.

## License

Original text and scripts: **MIT** — see [LICENSE](LICENSE). Third-party components keep their own licenses: PotatoNV (GPLv3), TWRP (GPLv3), Magisk (GPLv3), Kirin-Tool (read-only reference license), huawei-usbdload-tool (check upstream), Huawei firmware/bootloaders (Huawei property).

## Sources

- Firmware Finder data: <https://github.com/felpcereti/Huawei-Firmware-Finder>
- Open-source USB DLOAD: <https://github.com/kasnria001/huawei-usbdload-tool>
- PotatoNV: <https://github.com/mashed-potatoes/PotatoNV>
- PotatoNV cross-platform: <https://github.com/mashed-potatoes/PotatoNV-crossplatform>
- Kirin-Tool: <https://kirintool.cfd/>
- Linux USB update detection notes: <https://github.com/Redminote11tech/kirin-tool-linux/blob/main/docs/usb-update-linux-detection.md>
