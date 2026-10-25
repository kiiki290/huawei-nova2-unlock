import libusb_package, usb.core
b=libusb_package.get_libusb1_backend()
d=usb.core.find(idVendor=0x12d1,idProduct=0x3609,backend=b)
print('pyusb VCOM:', 'FOUND bus=%s addr=%s' % (d.bus,d.address) if d else 'NOT FOUND')
