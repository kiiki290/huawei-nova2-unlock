import os
import struct

SRC = r'tools/firmware/377/UPDATE.APP'
OUT = r'tools/firmware/377/parts'
os.makedirs(OUT, exist_ok=True)

# start offsets from analysis/updateapp-parts.txt
targets = {
    'CACHE': 0xcef7388,
    'SYSTEM': 0xd50609c,
    'VENDOR': 0xbcdeecf0,
    'ODM': 0xe036fd30,
    'PRODUCT': 0xe80293bc,
}

with open(SRC, 'rb') as f:
    for name, start in targets.items():
        outp = os.path.join(OUT, name + '.img')
        if os.path.exists(outp) and os.path.getsize(outp) > 0:
            print(f'{name}: already exists ({os.path.getsize(outp)} bytes), skip')
            continue
        f.seek(start)
        hdr = f.read(24)
        if len(hdr) != 24:
            raise IOError(f'EOF reading header for {name}')
        hdr_sz, unk1, hw_id, seq, size = struct.unpack('<IIQII', hdr)
        f.seek(start + 56)
        ftype = f.read(16).split(b'\x00')[0].decode(errors='replace')
        if ftype != name:
            raise ValueError(f'type mismatch at {name}: got {ftype!r}')
        data_off = start + hdr_sz - 4
        f.seek(data_off)
        print(f'{name}: hdr_sz={hdr_sz} size={size} data_off={hex(data_off)} -> {outp}')
        remaining = size
        with open(outp, 'wb') as o:
            while remaining:
                b = f.read(min(8 * 1024 * 1024, remaining))
                if not b:
                    raise IOError('EOF')
                o.write(b)
                remaining -= len(b)
        print(f'{name}: done')
