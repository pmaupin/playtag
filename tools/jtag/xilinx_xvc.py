#! /usr/bin/env python3
import sys
import ctypes
import time

from playtag.lib.userconfig import UserConfig, basic_startup
from playtag.jtag.discover import Chain
from playtag.lib.transport import connection
from playtag.iotemplate import IOTemplate, TDIVariable

'''
This program discovers the cable and chain, then runs a server
that can be used by Xilinx tools for jtag, as discussed here:

http://debugmo.de/2012/02/xvcd-the-xilinx-virtual-cable-daemon/
https://github.com/tmbinc/xvcd/tree/ftdi/src

For example, to use this with impact, choose cable setup, then
check the "Open Cable Plug-in" box, and enter the following
text in the dialog below there:

xilinx_xvc host=localhost:2542 disableversioncheck=true

Because the Xilinx tools themselves already know about the
JTAG protocol, this code plays dumb.  If the issue discussed
in that first website crops up with current versions of Xilinx
tools, then we can modify the code to fix the Xilinx bug.

Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''

def getcmdinfo(data, numbytes, tdivar=TDIVariable()):

    class CmdStruct(ctypes.LittleEndianStructure):
        _pack_ = 1
        _fields_ = (
                ("cmdstr",   ctypes.c_char * 6),
                ("numbits",  ctypes.c_uint32),
                ("tmsbytes", ctypes.c_uint8 * numbytes),
        )
    headersize = ctypes.sizeof(CmdStruct)
    assert headersize == len(data)

    class TdioStruct(ctypes.LittleEndianStructure):
        _pack_ = 1
        _fields_ = (
                ("data",    (numbytes + 7) // 8 * ctypes.c_uint64),
        )

    cmdinfo = CmdStruct.from_buffer_copy(data)

    numbits = cmdinfo.numbits
    tmsbuf = cmdinfo.tmsbytes
    bitmap = [min(numbits-i, 64) for i in range(0, numbits, 64)]

    assert cmdinfo.cmdstr == b'shift:', cmdinfo.cmdstr
    assert (numbits + 7) // 8 == numbytes, (numbits, numbytes)

    template = IOTemplate(config.driver)
    template.tms = [((tmsbuf[i//8] >> (i % 8)) & 1) for i in range(numbits)]
    template.tdi = [(j, tdivar) for j in bitmap]
    template.tdo = [(i>0 and 64 or 0, j) for (i,j) in enumerate(bitmap)]

    StrClass = ctypes.c_char * numbytes
    tdodata = TdioStruct()
    tdidata = TdioStruct()
    tdodata64 = tdodata.data
    tdidata64 = tdidata.data
    tdodata_ch = StrClass.from_buffer(tdodata)
    tdidata_ch = StrClass.from_buffer(tdidata)

    tdimask = (2 << ((numbits-1) % 64)) - 1

    tdi_slice = slice(headersize, headersize + numbytes)
    def run_jtag(data):
        tdidata_ch.value = data[tdi_slice]
        tdidata64[-1] &= tdimask
        processtime = -time.time()
        result = template(tdidata64)
        processtime += time.time()
        tdodata64[:] = list(result)
        return tdodata_ch.raw, processtime

    return run_jtag

def printbytes(header, data):
    data = data.hex()
    data = '\n    '.join(data[x:x+64] for x in range(0, len(data), 64))
    print('%s: %s' % (header, data), file=dumpf)

def cmdproc(read, write):
    maxdata = 120000
    class CmdStruct(ctypes.LittleEndianStructure):
        _pack_ = 1
        _fields_ = (
                ("cmdstr",   ctypes.c_char * 6),
                ("numbits",  ctypes.c_uint32),
        )
    headersize = ctypes.sizeof(CmdStruct)

    cmdcache = {}
    cmdcacheget = cmdcache.get
    connecttime = -time.time()
    readtime = 0.0
    writetime = 0.0
    processtime = 0.0
    data = b''
    while True:
        if len(data) < headersize:
            readtime -= time.time()
            newdata = read()
            readtime += time.time()
            if not newdata:
                break
            data += newdata

        if data.startswith(b'getinfo:'):
            writetime -= time.time()
            write(b"xvcServer_v1.0:%d\n" % maxdata)
            writetime += time.time()
            data = b''
            continue

        if data.startswith(b'settck:'):
            writetime -= time.time()
            write(data[7:])
            writetime += time.time()
            data = b''
            continue

        while len(data) < headersize:
            readtime -= time.time()
            newdata = read()
            readtime += time.time()
            if not newdata:
                break
            data += newdata

        cmdinfo = CmdStruct.from_buffer_copy(data)
        assert cmdinfo.cmdstr == b'shift:', cmdinfo.cmdstr
        numbits = cmdinfo.numbits
        numbytes = (cmdinfo.numbits + 7) // 8
        while len(data) < headersize + 2 * numbytes:
            readtime -= time.time()
            newdata = read()
            readtime += time.time()
            if not newdata:
                break
            data += newdata

        header_and_tms = data[:headersize + numbytes]
        run_jtag = cmdcacheget(header_and_tms)
        if run_jtag is None:
            run_jtag = cmdcache[header_and_tms] = getcmdinfo(header_and_tms, numbytes)
        result, _ = run_jtag(data)
        processtime += _
        writetime -= time.time()
        write(result)
        writetime += time.time()
        if dumpf:
            global now
            prev, now = now, time.time()
            print('DLY: %0.1f' % (now-prev), file=dumpf)
            print('NUM: %d' % numbits, file=dumpf)
            printbytes('TMS', data[headersize:headersize + numbytes], file=dumpf)
            printbytes('TDI', data[headersize + numbytes:headersize + 2*numbytes], file=dumpf)
            printbytes('TDO', result, file=dumpf)
            print('', file=dumpf)
            dumpf.flush()
        data = data[headersize + 2 * numbytes:]
    connecttime += time.time()
    print('Connection finished: time = %0.1f reading = %0.1f writing = %0.1f processing = %0.1f, jtag = %0.1f' %
          (connecttime, readtime, writetime, connecttime-readtime-writetime, processtime))
    sys.stdout.flush()

# Default the socket to standard Xilinx XVC address, then get our cable
UserConfig.SOCKET_ADDRESS = 2542
config = basic_startup()

if config.SHOW_CONFIG:
    print(config.dump())

print(Chain(config.driver))

dumpf = config.LOG_PACKETS and open('log_xvc.txt', 'wt')
now = time.time()
connection(cmdproc, 'xvc', config.SOCKET_ADDRESS, readsize=4096, logpackets=config.LOG_PACKETS)
