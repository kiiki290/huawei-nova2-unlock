import re
b=open(r'tools/kirin-tool/Kirin-Tool.dll','rb').read()
asc=[s.decode('latin1') for s in re.findall(rb'[\x20-\x7e]{4,}', b)]
uni=[s.decode('utf-16le') for s in re.findall(rb'(?:[\x20-\x7e]\x00){4,}', b)]
keys=['testpoint','vcom','unlock','base update','select','cpu','65x','driver','upgrade','usb update','usb com','xloader','bootloader','fastboot state','firmware']
seen=set()
for s in asc+uni:
    l=s.lower()
    if any(k in l for k in keys) and s not in seen:
        seen.add(s); print(s[:400])
