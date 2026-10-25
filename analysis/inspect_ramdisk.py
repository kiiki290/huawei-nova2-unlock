import struct, gzip, re
for p in [r'tools/firmware/377/parts/RAMDISK.img', r'tools/firmware/377/parts/RECOVERY_RAMDISK.img']:
    b=open(p,'rb').read()
    magic,ks,ka,rs,ra,ss,sa,ta,ps,hv=struct.unpack_from('<8s9I',b,0)
    print(p, 'magic',magic,'kernel',ks,'ramdisk',rs,'page',ps,'hdrver',hv)
    off=ps+((ks+ps-1)//ps)*ps
    ram=b[off:off+rs]
    print(' ramdisk magic',ram[:4].hex())
    try:
        d=gzip.decompress(ram)
        print(' decompressed',len(d),d[:6])
        s=d.decode('latin1',errors='ignore')
        hits=set()
        for m in re.finditer(r'(ro\.crypto\.state=[^\x00\n]{0,40}|/dev/block/bootdevice/by-name/[a-z_]+|forceencrypt|fileencryption|dm-verity|encryptable=[^\s]+)', s):
            hits.add(m.group(0)[:120])
        for h in sorted(hits)[:30]: print('  HIT', h)
    except Exception as e:
        print(' gzip err',e)
