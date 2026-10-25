import struct
for p in [r'tools/firmware/377/parts/RAMDISK.img', r'tools/firmware/377/parts/KERNEL.img', r'tools/firmware/377/parts/RECOVERY_RAMDISK.img', r'tools/firmware/377/parts/XLOADER.img']:
    b=open(p,'rb').read(64)
    print(p)
    print(' first16:', b[:16])
    if b[:8]==b'ANDROID!':
        v=struct.unpack_from('<8s9I', b, 0)
        print(' ANDROID! kernel_size=%d ramdisk_size=%d page=%d' % (v[1],v[3],v[8]))
    print(' hex:', b[:32].hex())
