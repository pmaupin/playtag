#! /usr/bin/env python3
'''
A part of playtag

Copyright (c) 2022 Patrick Maupin  MIT License

ftdi_ctl allows you to find FTDI 2232 and 4232 devices on Linux
systems, and either bind them to, or unbind them from, a tty
device port.
'''


import os
from collections import defaultdict
from pathlib import Path

def FindFTDI():
    class OneDevice:
        pass
    result = []
    devices = Path('/sys/bus/usb/devices')

    @property
    def readit(self):
        class Reader:
            def __getattr__(_, name):
                my_file = self / name
                return my_file.read_text().strip() if my_file.exists() else ''
            __call__ = __getattr__
        return Reader()
    type(devices).readit = readit

    subdevices = defaultdict(set)

    for name in devices.glob('*:*'):
        subdevices[name.parent / name.name.rsplit(':', 1)[0]].add(name)


    for device in list(subdevices):
        vid, pid = device.readit.idVendor, device.readit.idProduct
        if vid == '0403' and pid in ('6010', '6011', '6014'):
            manufacturer, product, serial = device.readit.manufacturer, device.readit.product, device.readit.serial
            for index, subdevice in enumerate(sorted(subdevices[device])):
                assert subdevice.readit.interface == product
                index = 'ABCD'[index] if pid != '6014' else ''
                obj = OneDevice()
                obj.devnum = subdevice.name
                obj.tty = ' '.join(x.name for x in subdevice.glob('tty*'))
                obj.manufacturer = manufacturer
                obj.product = product + (' ' + index if index else index)
                obj.serialnum = serial + ('_' + index if index else index) if serial else ''
                obj.vid = vid
                obj.pid = pid
                result.append(obj)

    for index, obj in enumerate(result):
        obj.index = str(index)
    return result

def find_devices(key):
    return [x for x in FindFTDI() if key in vars(x).values()]

def show_help(what=''):
        raise SystemExit('''%s
    ftdi_ctl may be called without arguments to print out a list of FT4232H and FT2232H devices in the system,
    or with bind/unbind arguments to bind or unbind.  The parameter to bind and unbind can
    be the device number, the serial number or the product/index name (as a single argument in quotes).

    Permissions must be set properly in order for this program to be able to bind/unbind the serial
    driver.  Add the below to a file in /etc/udev/rules.d to allow this:

        # Allow userland programs to bind/unbind FTDI devices
        ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", MODE="666", RUN+="/bin/sh -c 'chmod 222 /sys/bus/usb/drivers/ftdi_sio/*bind'"

''' % what)

def binder(function, key):
    devices = find_devices(key)
    if len(devices) > 1:
        return show_help('\n\nERROR: Multiple devices meet this specification.\n\n')
    device, = devices
    tty = device.tty

    try:
        (Path('/sys/bus/usb/drivers/ftdi_sio') / function).write_text(device.devnum + '\n')
    except OSError as msg:
        if function == 'bind':
            if tty:
                raise SystemExit('\nERROR: %r is already bound to %s.\n' % (key, tty))
        elif not tty:
            raise SystemExit('\nERROR: %r is not bound to a tty.\n' % key)
        else:
            raise SystemExit('\nERROR: Could not complete operation.  Maybe already %s?  (%s)\n' % (function.replace('i', 'ou'), msg))

def go(argv):
    if len(argv) <= 1:
        devices = FindFTDI()
        for obj in devices:
            print("%2s %-14s %-8s %-10s %-15s '%s'" %
                  (obj.index, obj.devnum, obj.tty, obj.manufacturer, obj.serialnum, obj.product))
    elif len(argv) == 3 and argv[1] in 'bind unbind'.split():
        binder(*argv[1:])
    else:
        show_help()

if __name__ == '__main__':
    import sys
    go(sys.argv)
