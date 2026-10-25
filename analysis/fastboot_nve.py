#!/usr/bin/env python3
"""Minimal raw fastboot client for Huawei `getvar:nve:...` binary writes.

Windows pyusb works here; fastbootpy's connect() is avoided because it calls
is_kernel_driver_active(), which is unimplemented on Windows.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time

import usb.core
import usb.util
import libusb_package

sys.stdout.reconfigure(encoding="utf-8")

VID, PID = 0x18D1, 0xD00D       # Huawei fastboot (Fastboot2.0)
EP_OUT, EP_IN = 0x01, 0x81


class Fastboot:
    def __init__(self) -> None:
        backend = libusb_package.get_libusb1_backend()
        self.dev = usb.core.find(idVendor=VID, idProduct=PID, backend=backend)
        if self.dev is None:
            raise RuntimeError("18d1:d00d fastboot device not found")
        try:
            self.dev.set_configuration()
        except usb.core.USBError as exc:
            print(f"set_configuration: {exc} (continuing)")
        usb.util.claim_interface(self.dev, 0)
        print(f"fastboot: {self.dev.idVendor:04x}:{self.dev.idProduct:04x} "
              f"bus={self.dev.bus} addr={self.dev.address}")

    def close(self) -> None:
        try:
            usb.util.release_interface(self.dev, 0)
        except Exception:
            pass
        usb.util.dispose_resources(self.dev)

    def recv(self, timeout: int = 500) -> bytes:
        out = b""
        while True:
            try:
                chunk = self.dev.read(EP_IN, 4096, timeout=timeout)
            except usb.core.USBTimeoutError:
                break
            except usb.core.USBError as exc:
                print(f"read error: {exc}")
                break
            if not chunk:
                break
            out += bytes(chunk)
        return out

    def command(self, cmd: bytes) -> bytes:
        # Clear any stale bytes.
        self.recv(1)
        written = self.dev.write(EP_OUT, cmd, timeout=3000)
        if written != len(cmd):
            raise RuntimeError(f"short write {written}/{len(cmd)}")
        return self.recv()

    @staticmethod
    def parse(resp: bytes) -> tuple[bytes, bytes]:
        """Return (status, payload). Handles INFO lines before final status."""
        while resp.startswith(b"INFO"):
            if len(resp) < 8:
                break
            try:
                n = int(resp[4:8], 16)
            except ValueError:
                break
            resp = resp[8 + n:]
        if len(resp) < 4:
            raise RuntimeError(f"short response: {resp.hex()}")
        status = resp[:4]
        if status in (b"OKAY", b"FAIL"):
            if len(resp) < 8:
                return status, b""
            try:
                n = int(resp[4:8], 16)
            except ValueError:
                return status, resp[4:]
            return status, resp[8:8 + n]
        return status, resp[4:]

    def read_nve(self, prop: str) -> tuple[bytes, bytes]:
        resp = self.command(f"getvar:nve:{prop}".encode())
        status, payload = self.parse(resp)
        return status, payload

    def write_nve(self, prop: str, value: bytes) -> bytes:
        cmd = f"getvar:nve:{prop}@".encode() + value
        resp = self.command(cmd)
        status, payload = self.parse(resp)
        return status, payload


def show(prop: str, status: bytes, payload: bytes) -> None:
    print(f"{prop}: status={status.decode('ascii', 'replace')} "
          f"len={len(payload)} hex={payload.hex()} "
          f"ascii={payload.decode('ascii', 'replace')!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--read", action="append", default=[])
    ap.add_argument("--write", nargs=2, action="append", default=[],
                    metavar=("PROP", "HEX"))
    ap.add_argument("--write-key", metavar="CODE",
                    help="write WVLOCK=CODE and USRKEY=SHA256(CODE)")
    ap.add_argument("--verify-key", metavar="CODE",
                    help="read back and compare WVLOCK/USRKEY")
    args = ap.parse_args()

    fb = Fastboot()
    try:
        if args.write_key:
            code = args.write_key.encode("ascii")
            if len(code) != 16:
                raise SystemExit("key must be exactly 16 ASCII bytes")
            digest = hashlib.sha256(code).digest()
            for prop, val in (("WVLOCK", code), ("USRKEY", digest)):
                status, payload = fb.write_nve(prop, val)
                print(f"write {prop}: {status.decode('ascii', 'replace')} "
                      f"{payload.decode('ascii', 'replace')}")
                if status != b"OKAY" or b"set nv ok" not in payload:
                    raise SystemExit(f"failed to write {prop}")
        for prop, hexval in args.write:
            val = bytes.fromhex(hexval)
            status, payload = fb.write_nve(prop, val)
            print(f"write {prop}: {status.decode('ascii', 'replace')} "
                  f"{payload.decode('ascii', 'replace')}")
        if args.verify_key:
            code = args.verify_key.encode("ascii")
            digest = hashlib.sha256(code).digest()
            ok = True
            for prop, expected in (("WVLOCK", code), ("USRKEY", digest)):
                status, payload = fb.read_nve(prop)
                show(prop, status, payload)
                actual = payload.rstrip(b"\x00")
                if actual != expected:
                    ok = False
                    print(f"  MISMATCH expected {expected.hex()}")
            print("verify:", "OK" if ok else "MISMATCH")
        for prop in args.read:
            status, payload = fb.read_nve(prop)
            show(prop, status, payload)
    finally:
        fb.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
