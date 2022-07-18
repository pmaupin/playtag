#! /usr/bin/env python3

'''
Code to read/write FTDI parts in D2XX mode

Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''

import time
import atexit
from collections import defaultdict
from .d2xx_wrapper import FT, windows
from .mpsse_commands import Commands

test = False

try:
    unicode
except NameError:
    def convert_load(s):
        if isinstance(s, bytes):
            return s.decode('Latin-1')
        return s
else:
    def convert_load(s):
        return s


DWORD = FT.DWORD
LPDWORD = FT.LPDWORD
CHAR = FT.CHAR

class SysInfo(list):
    def __init__(self):
        if FT.loaded:
            numdevs = DWORD()
            FT.CreateDeviceInfoList(FT.byref(numdevs))
            devlist = (FT.DEVICE_LIST_INFO_NODE * (numdevs.value))()
            FT.GetDeviceInfoList(devlist, numdevs)
            self[:] = devlist
            assert len(self) == numdevs.value
        self.addstrings()

    def addstrings(self):
        strings = self.indexstrings = defaultdict(list)
        for i, what in enumerate(self):
            for name, _ in what._fields_:
                value = ''.join(str(convert_load(getattr(what, name))).split()).lower()
                strings[value].append(i)

    def __str__(self):
        result = []
        for i, what in enumerate(self):
            result.append('\n[%d]' % i)
            for name, _ in what._fields_:
                x = convert_load(getattr(what, name))
                result.append('        %s = %s' % (name, repr(str(x))))
        if not result:
            result.append("\nNo devices found" if FT.loaded else "\nCould not find FTDI DLL")
        result.append('')
        return '\n'.join(result)

    def find(self, index):
        try:
            return index + (index < 0 and len(self))
        except TypeError:
            pass
        if isinstance(index, str):
            index = [index]
        devnum = []
        try:
            for s in index:
                devnum += self.indexstrings[''.join(s.split()).lower()]
        except AttributeError:
            pass
        if len(devnum) != 1:
            if not devnum:
                message = '\n'.join(['',
                     "Error: Could not find FTDI D2xx device named '%s'" % index,
                     '',
                     'Devices available:', '',
                     str(self)])
            else:
                message = "Error:  Multiple FTDI devices found: %d devices named '%s'" % (len(devnum), index)
            raise SystemExit(message)
        return devnum[0]

info = SysInfo()

class FtdiDefaults(object):
    FTDI_USB_IN_SIZE = 65535
    FTDI_USB_OUT_SIZE = 65535
    FTDI_READ_TIMEOUT = 0
    FTDI_WRITE_TIMEOUT = 5000
    FTDI_LATENCY_TIMER = 16
    FTDI_STARTUP_SLEEP = 50
    FTDI_JTAG_FREQ = 15e6
    FTDI_GPIO_MASK = 0x1b
    FTDI_GPIO_OUT = 0x08
    FTDI_ADAPTIVE_CLOCKING = False
    FTDI_LOOPBACK_TEST = False
    FTDI_DEBUG = False

class FtdiDevice(FT):
    Commands = Commands
    isopen = False
    def __init__(self, config):
        config.add_defaults(FtdiDefaults)
        self.debug = config.FTDI_DEBUG and open(config.FTDI_DEBUG, 'wt') or test
        index = self.index = info.find(config.CABLE_NAME)
        self.Open(index, self.byref(self))
        self.init_buffers(config.FTDI_USB_IN_SIZE, config.FTDI_USB_OUT_SIZE)
        self.isopen = True
        atexit.register(self.__del__)

        # Sequence taken from app note 129.
        #self.ResetPort()   # Does this reset both channels?
        if windows:  # Broken in Linux driver libftd2xx.so.1.1.12
            self.Purge(self.PURGE_RX | self.PURGE_TX)
        self.SetUSBParameters(config.FTDI_USB_IN_SIZE, config.FTDI_USB_OUT_SIZE)
        self.SetChars(0, 0, 0, 0)
        self.SetTimeouts(config.FTDI_READ_TIMEOUT, config.FTDI_WRITE_TIMEOUT)
        self.SetLatencyTimer(config.FTDI_LATENCY_TIMER)
        self.SetBitMode(0, self.BITMODE_RESET)
        self.SetBitMode(0, self.BITMODE_MPSSE)
        time.sleep(config.FTDI_STARTUP_SLEEP/1000.0)  # From example in app note 129.  Whatever.
        self.synchronize()
        self.setspeed(config.FTDI_JTAG_FREQ, config.FTDI_ADAPTIVE_CLOCKING, config.FTDI_LOOPBACK_TEST)
        self.set_gpio_mask(config.FTDI_GPIO_MASK)
        self.write_gpio(config.FTDI_GPIO_OUT)
        if self.debug:
            print(hex(self.read_gpio()), file=self.debug)
        self.synchronize()

    def init_buffers(self, maxread, maxwrite):
        wbuffer = (maxwrite * self.UCHAR)()
        wref = self.byref(wbuffer)
        wxfer = self.DWORD()
        wxref = self.byref(wxfer)
        self.wbuffer = wbuffer
        self.wlength = 0
        self._wbufinfo = wref, wxfer, wxref
        rbuffer = (maxread * self.UCHAR)()
        rref = self.byref(rbuffer)
        rxfer = self.DWORD()
        rxref = self.byref(rxfer)
        self._rbufinfo = rbuffer, rref, rxfer, rxref

    def set_gpio_mask(self, mask=0):
        self.output_mask = mask

    def write_gpio(self, value=None, wr_gpio=Commands.wr_gpio):
        if value is not None:
            self._current_gpio = value
        else:
            value = self._current_gpio
        self.writebytes(
            wr_gpio[0], value & 0xFF, self.output_mask & 0xFF,
            wr_gpio[1], value >> 8, self.output_mask >> 8,
        )

    def read_gpio(self, rd_gpio=Commands.rd_gpio):
        self.writebytes(rd_gpio[0], rd_gpio[1])
        x = self.readbytes(2)
        return x[0] | (x[1] << 8)

    def setspeed(self, speed=6e6, adaptive=False, loopback=False):
        hispeed = bool(info[self.index].Flags & 2)
        adaptive = adaptive and Commands.enable_adaptive_clocking or Commands.disable_adaptive_clocking
        loopback = loopback and Commands.loopback_en or Commands.loopback_dis
        if hispeed:
            self.writebytes(Commands.disable_clk_div5, Commands.disable_three_phase, adaptive, loopback)
            base = 30e6
        else:
            base = 6e6
        div = min(max(int(base / speed - 1), 0), 65535)
        self.writebytes(Commands.set_divisor, div & 0xFF, div >> 8)

    def writebytes(self, *bytes):
        wbuffer = self.wbuffer
        length = self.wlength
        if bytes:
            newlen = length + len(bytes)
            wbuffer[length:newlen] = bytes
            self.wlength = newlen
            return
        if not length:
            return
        if self.debug:
            print("Writing", [hex(x) for x in wbuffer[:length]], file=self.debug)
        wref, transferred, transferredref = self._wbufinfo
        self.Write(wref, length, transferredref)
        if transferred.value != length:
            raise SystemExit("Expected to write %d bytes; only wrote %d" % (length, transferred.value))
        self.wlength = 0

    def readintobuffer(self, length, bufinfo, send_immediate=Commands.send_immediate):
        self.writebytes(send_immediate)
        self.writebytes()
        rbuffer, rref, transferred, transferredref = bufinfo
        self.Read(rref, length, transferredref)
        if transferred.value != length:
            raise SystemExit("Expected to read %d bytes; only read %d" % (length, transferred.value))
        return rbuffer

    def readbytes(self, length):
        rbuffer = self.readintobuffer(length, self._rbufinfo)
        bytes = list(rbuffer[:length])
        if self.debug:
            print("Reading", [hex(x) for x in bytes], file=self.debug)
        return bytes

    def synchronize(self):
        ''' Write an invalid command and check the pattern coming back
        '''
        if windows:  # Broken in Linux driver libftd2xx.so.1.1.12
            self.Purge(self.PURGE_RX | self.PURGE_TX)
        self.writebytes( 0xAA) # Invalid command
        if self.readbytes(2) != [0xFA, 0xAA]:
            raise SystemExit("Error synchronizing FTDI driver")


    def __del__(self):
        if self.isopen:
            self.isopen = False
            try:
                self.set_gpio_mask(0x0)
                self.write_gpio(0xFFFF)
                self.synchronize()
            finally:
                self.Close()

