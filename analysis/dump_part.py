import base64
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ADB = shutil.which("adb") or "adb"
OUT = str(Path(__file__).resolve().parent)


def dump(part: str, size_mb: int) -> bytes:
    cmd = (f"dd if=/dev/block/bootdevice/by-name/{part} "
           f"bs=1M count={size_mb} 2>/dev/null | base64")
    out = subprocess.check_output([ADB, "shell", cmd], timeout=120)
    return base64.b64decode(out)


for part, size in (("oeminfo", 16), ("dfx", 16)):
    data = dump(part, size)
    path = f"{OUT}\\{part}.bin"
    with open(path, "wb") as f:
        f.write(data)
    nonzero = sum(1 for b in data if b)
    print(f"=== {part}: {len(data):,} bytes, nonzero={nonzero:,}, saved={path}")
    strings = re.findall(rb"[ -~]{5,}", data)
    keys = (b"MGX5T", b"PIC-TL", b"IMEI", b"USRKEY", b"WVLOCK",
            b"unlock", b"UNLOCK", b"crypt", b"CRYPT", b"fail", b"FAIL",
            b"error", b"ERROR", b"recovery", b"RECOVERY", b"mount", b"format")
    hits = [s for s in strings if any(k.lower() in s.lower() for k in keys)]
    print(f"  strings={len(strings)} interesting={len(hits)}")
    for s in hits[:80]:
        print("   ", s[:160].decode("latin1", "replace"))
    if part == "oeminfo" and not hits:
        print("  first strings:", [s[:80].decode('latin1','replace') for s in strings[:20]])
