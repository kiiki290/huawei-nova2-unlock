import libusb_package, usb.core
b = libusb_package.get_libusb1_backend()
devs = list(usb.core.find(find_all=True, backend=b))
print('count', len(devs))
for d in devs:
    try:
        print(f'{d.idVendor:04x}:{d.idProduct:04x} bus={d.bus} addr={d.address} class={d.bDeviceClass} cfg={d.bNumConfigurations}')
    except Exception as e:
        print('ERR on device', type(e).__name__, e)
print('--- looking for 12d1:3609 ---')
for d in devs:
    if d.idVendor == 0x12d1:
        print('HUAWEI', f'{d.idVendor:04x}:{d.idProduct:04x}', 'bus', d.bus, 'addr', d.address)
