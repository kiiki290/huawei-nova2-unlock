import os, shutil
from crccheck.crc import CrcX25
base=r'tools/kirin-tool/dload'; bak=r'analysis/dload-backup'
# restore original header (name XLOADER)
shutil.copy2(os.path.join(bak,'XLOADER.img.header'), os.path.join(base,'XLOADER.img.header'))
h=open(os.path.join(base,'XLOADER.img.header'),'rb').read()
print('header name:',bytes(h[60:72]))
# re-apply CRC collision if XLOADER is original
orig=open(os.path.join(bak,'XLOADER.img'),'rb').read()
cur=open(os.path.join(base,'XLOADER.img'),'rb').read()
ch=open(r'tools/usbdload/crc_hacked.bin','rb').read()
patched=bytes(ch[i]^orig[i] for i in range(0x8000))+orig[0x8000:]
if cur!=patched:
    open(os.path.join(base,'XLOADER.img'),'wb').write(patched); print('repatched XLOADER')
else: print('XLOADER already patched')
print('CRC equal:',CrcX25.calc(orig[:0x8000])==CrcX25.calc(patched[:0x8000]))
# ensure offline package + unlockcode
pk=open(r'tools/usbdload/pk_cracked.bin','rb').read()
if open(os.path.join(base,'PACKAGE_TYPE.img'),'rb').read()!=pk:
    open(os.path.join(base,'PACKAGE_TYPE.img'),'wb').write(pk); print('PACKAGE_TYPE repatched')
if not os.path.exists(os.path.join(base,'unlockcode')):
    open(os.path.join(base,'unlockcode'),'wb').write(orig[0:0])
print('list:',open(os.path.join(base,'list.txt')).read().replace('\n',','))
