import re
p=r'tools/kirin-tool/Kirin-Tool.dll'
b=open(p,'rb').read()
# ASCII strings
asc=re.findall(rb'[\x20-\x7e]{5,}', b)
asc=[s.decode('latin1') for s in asc]
# UTF-16LE strings
uni=re.findall(rb'(?:[\x20-\x7e]\x00){5,}', b)
uni=[s.decode('utf-16le') for s in uni]
allstr=sorted(set(asc+uni))
keys=['software','testpoint','test point','unlock','dbadapter','vcom','usb com','base update','xloader','select','kirin 65','hisi65','bootloader','upgrade','fastboot','driver','partition','flash','exit']
for s in allstr:
    l=s.lower()
    if any(k in l for k in keys):
        print(s[:300])
