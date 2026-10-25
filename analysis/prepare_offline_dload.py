import os, shutil, struct
from crccheck.crc import CrcX25
base=r'tools/kirin-tool/dload'
bak=r'analysis/dload-backup'
os.makedirs(bak, exist_ok=True)
# backups
for n in ['XLOADER.img','XLOADER.img.header','PACKAGE_TYPE.img','list.txt']:
    src=os.path.join(base,n)
    if os.path.exists(src): shutil.copy2(src, os.path.join(bak,n))
# unlockcode = hw_id at header offset 12..20
hdr=open(os.path.join(base,'XLOADER.img.header'),'rb').read()
unlock=hdr[12:20]
open(os.path.join(base,'unlockcode'),'wb').write(unlock)
print('unlockcode',unlock.hex(),repr(unlock))
# PACKAGE_TYPE -> OFFLINE_UPDATE collision
pk=open(r'tools/usbdload/pk_cracked.bin','rb').read()
open(os.path.join(base,'PACKAGE_TYPE.img'),'wb').write(pk)
print('PACKAGE_TYPE patched len',len(pk),repr(pk[:16]))
# XLOADER CRC collision
xl=open(os.path.join(base,'XLOADER.img'),'rb').read()
ch=open(r'tools/usbdload/crc_hacked.bin','rb').read()
orig=xl[:0x8000]
assert len(ch)==0x8000 and len(orig)==0x8000
patched=bytes(ch[i]^orig[i] for i in range(0x8000))+xl[0x8000:]
print('CRC orig',hex(CrcX25.calc(orig)),'patched',hex(CrcX25.calc(patched[:0x8000])),'equal',CrcX25.calc(orig)==CrcX25.calc(patched[:0x8000]))
open(os.path.join(base,'XLOADER.img'),'wb').write(patched)
# header name -> PRELOADER
h=bytearray(hdr)
h[60:60+32]=b'\x00'*32
h[60:60+9]=b'PRELOADER'
open(os.path.join(base,'XLOADER.img.header'),'wb').write(bytes(h))
print('header name now',bytes(h[60:72]))
print('list.txt:'); print(open(os.path.join(base,'list.txt')).read())
