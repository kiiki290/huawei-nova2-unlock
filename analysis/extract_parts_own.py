import struct, os
SRC = r'tools/firmware/377/UPDATE.APP'
OUT = r'tools/firmware/377/parts'
os.makedirs(OUT, exist_ok=True)
# header starts (offset after 4-byte magic) obtained from the partition listing
targets = {
    'XLOADER': 0x3ffe8,
    'KERNEL': 0x2edf87c,
    'RECOVERY_RAMDISK': 0x46e28e0,
    'RAMDISK': 0xbef5324,
    'VBMETA': 0x32e2b0,
    'RECOVERY_VBMETA': 0x76e89a8,
}
with open(SRC, 'rb') as f:
    for name, start in targets.items():
        f.seek(start)
        hdr_sz, unk1, hw_id, seq, size = struct.unpack('<IIQII', f.read(24))
        f.seek(start + 56)
        ftype = f.read(16).split(b'\x00')[0].decode(errors='replace')
        data_off = start + hdr_sz - 4
        assert ftype == name, (ftype, name)
        f.seek(data_off)
        outp = os.path.join(OUT, name + '.img')
        remaining = size
        with open(outp, 'wb') as o:
            while remaining:
                b = f.read(min(8*1024*1024, remaining))
                if not b: raise IOError('EOF')
                o.write(b); remaining -= len(b)
        print(f'{name}: hdr_sz={hdr_sz} size={size} data_off={hex(data_off)} -> {outp}')
