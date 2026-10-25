import usb.core, usb.backend.libusb1, libusb_package
lib = libusb_package.find_library()
print('libusb:', lib)
b = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
print('backend:', b)
try:
    devs = list(usb.core.find(find_all=True, backend=b))
except Exception as e:
    print('ENUM ERR', type(e).__name__, e); raise SystemExit
print('count', len(devs))
for d in devs:
    print(f'{d.idVendor:04x}:{d.idProduct:04x} bus={d.bus} addr={d.address} manuf={d.manufacturer} prod={d.product}')
