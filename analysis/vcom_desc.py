import sys
import usb.core
import usb.util
import libusb_package

sys.stdout.reconfigure(encoding="utf-8")

backend = libusb_package.get_libusb1_backend()
dev = usb.core.find(idVendor=0x12D1, idProduct=0x3609, backend=backend)
if dev is None:
    print("12d1:3609 not found")
    sys.exit(1)

print(f"device: {dev.idVendor:04x}:{dev.idProduct:04x} bus={dev.bus} addr={dev.address}")
print(f"bcdUSB={dev.bcdUSB:04x} bDeviceClass={dev.bDeviceClass} "
      f"bDeviceSubClass={dev.bDeviceSubClass} bDeviceProtocol={dev.bDeviceProtocol} "
      f"bMaxPacketSize0={dev.bMaxPacketSize0}")
try:
    print(f"manufacturer={dev.manufacturer!r}")
    print(f"product={dev.product!r}")
    print(f"serial={dev.serial_number!r}")
except Exception as e:
    print(f"string descriptors unavailable: {e}")

for cfg in dev:
    print(f"\nconfig {cfg.bConfigurationValue}: bmAttributes=0x{cfg.bmAttributes:02x} "
          f"bMaxPower={cfg.bMaxPower * 2}mA nbInterfaces={cfg.bNumInterfaces}")
    for intf in cfg:
        print(f"  interface {intf.bInterfaceNumber}.{intf.bAlternateSetting}: "
              f"class=0x{intf.bInterfaceClass:02x} sub=0x{intf.bInterfaceSubClass:02x} "
              f"proto=0x{intf.bInterfaceProtocol:02x} endpoints={intf.bNumEndpoints}")
        if intf.extra_descriptors:
            print(f"    extra: {bytes(intf.extra_descriptors).hex(' ')}")
        for ep in intf:
            print(f"    EP 0x{ep.bEndpointAddress:02x}: "
                  f"type={usb.util.endpoint_type(ep.bmAttributes)} "
                  f"maxPacket={ep.wMaxPacketSize} interval={ep.bInterval}")
