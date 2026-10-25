import libusb_package, usb.core, usb.backend.libusb1
print('libusb_package attrs:', [x for x in dir(libusb_package) if not x.startswith('_')])
b=None
for attr in ['get_libusb1_backend','get_backend']:
    if hasattr(libusb_package, attr):
        try:
            b=getattr(libusb_package, attr)(); print(attr,'->',b); break
        except Exception as e: print(attr,'ERR',e)
if b is None:
    for cand in ['libusb-1.0.dll','libusb-1.0.so','libusb-1.0.dylib']:
        try:
            lib=libusb_package.find_library(cand); print('lib',cand,lib)
            b=usb.backend.libusb1.get_backend(find_library=lambda x: lib); break
        except Exception as e: print('find',cand,'ERR',e)
print('backend',b)
try:
    devs=list(usb.core.find(find_all=True, backend=b))
    print('count',len(devs))
    for d in devs:
        print(f'{d.idVendor:04x}:{d.idProduct:04x} bus={d.bus} addr={d.address} {d.manufacturer} {d.product}')
except Exception as e:
    print('ENUM ERR',type(e).__name__,e)
