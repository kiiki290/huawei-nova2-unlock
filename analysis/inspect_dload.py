import os, re
base=r'tools/kirin-tool/dload'
for name in ['PACKAGE_TYPE','CURVER','VERLIST','unlockcode','SHA256RSA','CRC']:
    p=os.path.join(base,name+'.img')
    if os.path.exists(p):
        b=open(p,'rb').read()
        asc=''.join(chr(c) if 32<=c<127 else '.' for c in b)
        print(f'{name}.img len={len(b)} hex={b[:64].hex()}')
        print(f'  ascii={asc[:200]}')
    else: print(name,'missing')
# headers
for name in ['XLOADER','PACKAGE_TYPE','CURVER']:
    p=os.path.join(base,name+'.img.header')
    if os.path.exists(p):
        b=open(p,'rb').read()
        print(f'{name}.header len={len(b)} hex={b[:96].hex()}')
        asc=''.join(chr(c) if 32<=c<127 else '.' for c in b)
        print('  ascii=',asc)
# XLOADER strings
p=os.path.join(base,'XLOADER.img')
if os.path.exists(p):
    b=open(p,'rb').read()
    for m in re.finditer(rb'[ -~]{4,}', b[:4096]):
        print('XLOADER str:',m.group(0)[:100])
