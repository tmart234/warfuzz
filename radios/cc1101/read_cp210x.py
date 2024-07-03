# -*- coding: utf-8 -*-
import usb.core
import usb.util


devices = usb.core.find(find_all=True)
if not devices:
    print("No USB devices found!!")
else:
    for device in devices:
        print(f"Device: {device}")
        print(f"  Vendor ID: {hex(device.idVendor)}")
