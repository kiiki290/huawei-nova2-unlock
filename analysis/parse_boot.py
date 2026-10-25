import struct, gzip
p = r"tools\twrp\twrp-3.4.0-0-prague.img"
b = open(p,'rb').read()
v = struct.unpack_from('<8s9I', b, 0)
magic=v[0]; kernel_size,kernel_addr,ramdisk_size,ramdisk_addr,second_size,second_addr,tags_addr,page_size,hdr_ver=v[1:]
print('magic', magic, 'hdr_ver', hdr_ver)
print('kernel', kernel_size, 'ramdisk', ramdisk_size, 'page_size', page_size)
print('name', b[48:64].split(b'\0')[0])
print('cmdline', b[64:576].split(b'\0')[0].decode(errors='replace'))
def pad(n): return ((n+page_size-1)//page_size)*page_size
ro = page_size + pad(kernel_size)
ram = b[ro:ro+ramdisk_size]
open('analysis/twrp-ramdisk.cpio.gz','wb').write(ram)
print('ramdisk magic', ram[:4])
try:
    d = gzip.decompress(ram); open('analysis/twrp-ramdisk.cpio','wb').write(d); print('decompressed', len(d), d[:6])
except Exception as e: print('gzip error', e)
