#!/usr/bin/env python3
"""Upload PotatoNV Kirin 65x bootloaders to a Huawei VCOM (12d1:3609) device.

The device exposes a vendor-specific bulk interface (EP 0x01 OUT / 0x81 IN),
not a CDC-ACM serial port.  This is a direct pyusb port of PotatoNV's
ImageFlasher protocol, so no COM driver / testsigning / Secure Boot change is
needed.

Protocol (from Potato.ImageFlasher + PotatoNV-crossplatform):
  head: FE 00 FF 01 | length BE32 | address BE32 | crc BE16
  data: DA | seq | ~seq | payload(<=0x400) | crc BE16
  tail: ED | seq | ~seq | crc BE16
Every head/data frame is ACKed with one byte 0xAA.  The tail ACK is optional.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import sys
import time
from pathlib import Path

import usb.core
import usb.util
import libusb_package

sys.stdout.reconfigure(encoding="utf-8")

VID, PID = 0x12D1, 0x3609
EP_OUT, EP_IN = 0x01, 0x81
MAX_DATA_LEN = 0x400
ACK = 0xAA
DEFAULT_DIR = (
    Path(__file__).resolve().parent.parent
    / "tools"
    / "PotatoNV-next-v2.2.1-2022.03-x86"
    / "bootloaders"
    / "hisi65x_a"
)

IMAGES = [
    # role, path, RAM address, SHA1 from manifest.xml
    ("xloader", "xloader.img", 0x00020000, "8a35f16db94dafde47aa718c673958f108805480"),
    ("fastboot", "fastboot.img", 0x10000000, "c77c7524e79aabfa5b979053dd2186dc2bae53e1"),
]


def crc16(data: bytes, crc: int = 0) -> int:
    """CRC used by PotatoNV: CCITT/XMODEM table, initial 0, two zero bytes."""
    for char in data:
        crc = ((crc << 8) | char) ^ binascii.crc_hqx(bytes([(crc >> 8) & 0xFF]), 0)
    for _ in range(2):
        crc = ((crc << 8) | 0) ^ binascii.crc_hqx(bytes([(crc >> 8) & 0xFF]), 0)
    return crc & 0xFFFF


def framed(payload: bytes) -> bytes:
    return payload + crc16(payload).to_bytes(2, "big")


class Vcom:
    def __init__(self) -> None:
        backend = libusb_package.get_libusb1_backend()
        self.dev = usb.core.find(idVendor=VID, idProduct=PID, backend=backend)
        if self.dev is None:
            raise RuntimeError("12d1:3609 not found - phone is not in VCOM mode")
        self.dev.set_configuration()
        usb.util.claim_interface(self.dev, 0)
        print(f"opened {self.dev.idVendor:04x}:{self.dev.idProduct:04x} "
              f"bus={self.dev.bus} addr={self.dev.address}")

    def close(self) -> None:
        try:
            usb.util.release_interface(self.dev, 0)
        except Exception:
            pass
        usb.util.dispose_resources(self.dev)

    def drain_in(self) -> None:
        """Discard stale bytes (a tail ACK or an old error byte)."""
        while True:
            try:
                self.dev.read(EP_IN, 64, timeout=1)
            except usb.core.USBTimeoutError:
                return
            except usb.core.USBError:
                return

    def send_frame(self, payload: bytes, *, expect_ack: bool = True,
                   ack_timeout: int = 2000) -> None:
        frame = framed(payload)
        self.drain_in()
        written = self.dev.write(EP_OUT, frame, timeout=5000)
        if written != len(frame):
            raise RuntimeError(f"short USB write: {written}/{len(frame)}")
        if not expect_ack:
            return
        try:
            ack = bytes(self.dev.read(EP_IN, 1, timeout=ack_timeout))
        except usb.core.USBTimeoutError as exc:
            raise RuntimeError(
                f"ACK timeout after {payload[0]:#04x} frame "
                f"(seq={payload[1] if len(payload) > 1 else '-'})"
            ) from exc
        if ack != bytes([ACK]):
            raise RuntimeError(f"bad ACK: {ack.hex()} (expected aa)")

    def head(self, length: int, address: int) -> None:
        payload = (b"\xFE\x00\xFF\x01"
                   + length.to_bytes(4, "big")
                   + address.to_bytes(4, "big"))
        self.send_frame(payload)

    def data(self, seq: int, chunk: bytes) -> None:
        payload = bytes([0xDA, seq & 0xFF, (~seq) & 0xFF]) + chunk
        self.send_frame(payload, ack_timeout=3000)

    def tail(self, seq: int) -> None:
        payload = bytes([0xED, seq & 0xFF, (~seq) & 0xFF])
        # The device may reset/reboot immediately after the tail; ACK optional.
        try:
            self.send_frame(payload, expect_ack=True, ack_timeout=100)
        except RuntimeError:
            pass

    def upload(self, name: str, data: bytes, address: int) -> None:
        total_frames = (len(data) + MAX_DATA_LEN - 1) // MAX_DATA_LEN
        print(f"\n[{name}] {len(data):,} bytes -> 0x{address:08X}, "
              f"{total_frames} data frames")
        self.head(len(data), address)
        seq = 0
        offset = 0
        started = time.time()
        last_print = 0.0
        while offset < len(data):
            chunk = data[offset:offset + MAX_DATA_LEN]
            seq += 1
            self.data(seq, chunk)
            offset += len(chunk)
            now = time.time()
            if now - last_print >= 0.5 or offset == len(data):
                pct = 100.0 * offset / len(data)
                rate = offset / max(now - started, 1e-6) / 1024
                print(f"\r  {offset:,}/{len(data):,} ({pct:5.1f}%) "
                      f"{rate:6.1f} KiB/s", end="", flush=True)
                last_print = now
        self.tail(seq + 1)
        print(f"\n[{name}] done in {time.time() - started:.1f}s")
        time.sleep(0.5)


def load_images(directory: Path) -> list[tuple[str, bytes, int]]:
    out = []
    for role, filename, address, expected_sha1 in IMAGES:
        path = directory / filename
        if not path.is_file():
            raise RuntimeError(f"missing image: {path}")
        data = path.read_bytes()
        sha1 = hashlib.sha1(data).hexdigest()
        ok = sha1 == expected_sha1
        print(f"{role:8s} {path.name:14s} {len(data):>10,} bytes  "
              f"SHA1 {sha1} {'OK' if ok else 'MISMATCH'}")
        if not ok:
            raise RuntimeError(f"SHA1 mismatch for {path}")
        out.append((role, data, address))
    return out


def find_fastboot(timeout: float = 20.0) -> str | None:
    """Poll `fastboot devices`; return the device line or None."""
    import shutil
    import subprocess

    exe = shutil.which("fastboot") or "fastboot"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            res = subprocess.run([exe, "devices"], capture_output=True,
                                 text=True, timeout=5)
            lines = [x.strip() for x in res.stdout.splitlines() if x.strip()]
            if lines:
                print(f"fastboot: {lines}")
                return lines[0]
        except Exception:
            pass
        time.sleep(1)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--check", action="store_true",
                        help="verify images and print protocol info only")
    parser.add_argument("--no-wait-fastboot", action="store_true")
    args = parser.parse_args()

    try:
        images = load_images(args.dir)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"\nprotocol CRC check (PotatoNV frame): {crc16(bytes([0xFE, 0x00, 0xFF, 0x01])):#06x}")
    if args.check:
        return 0

    vcom = None
    try:
        vcom = Vcom()
        for role, data, address in images:
            vcom.upload(role, data, address)
        vcom.close()
        vcom = None
        print("\nall images uploaded; releasing USB and waiting for fastboot...")
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130
    except Exception as exc:
        print(f"\nERROR: {exc}")
        return 1
    finally:
        if vcom is not None:
            vcom.close()

    if args.no_wait_fastboot:
        return 0

    device = find_fastboot()
    if device is None:
        print("fastboot device did not appear (device may still be in VCOM)")
        return 3
    print("device is in fastboot; ready for NVME unlock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
