#! /usr/bin/env python
'''
This module provides a LeonMem class that can read and write memory on a LEON processor
through JTAG.  It directly relies on the jtagcommands module, and when you instantiate
a LeonMem instance, you must pass it a cable driver that it can use for physical communication.

Currently it is pretty stupid.  Assumes a single LEON is the only thing in the JTAG chain.

Future refactoring should include:

  - Splitting out special memory byte-handling stuff into a separate module, so we
    can use both JTAG and SPI transports without duplicating code.
  - Allowing other devices in the JTAG chain.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/LICENSE.txt
'''

from ..bsdl.lookup import readfile, PartParameters, PartInfo
from ..jtag.discover import Chain
from ..jtag.template import JtagTemplateFactory

class LeonPart(PartParameters):
    ''' Reads part from standard Gaisler Research config file.
    '''
    # DevName DevID DevIDMask IRlength hasdebug cmdi datai

    def __init__(self, line):
        linetext = ' '.join(line)
        try:
            name = line.pop(0)
            params = [int(x, 0) for x in line]
            idcode, mask, irlen, hasdebug = params[:4]
            if hasdebug:
                self.is_leon = True
                self.cmdi, self.datai = params[4:]
            idcode = idcode, mask
            ir_capture = 'x' * (irlen - 1) + '01'
            self.base_init(idcode, ir_capture, name)
        except:
            print "\nError processing line: %s\n" + linetext
            raise

class LeonMem(object):
    def __init__(self, jtagrw, UserConfig):
        PartInfo.addparts(LeonPart(x) for x in readfile(UserConfig.JTAGID_FILE))
        chain = Chain(jtagrw)
        leons = [x for x in chain if hasattr(chain[0].parameters, 'is_leon')]
        err = len(chain) != 1
        if err or UserConfig.SHOW_CHAIN or not leons:
            print str(chain)
            if not leons:
                raise SystemExit("Did not find LEON3 processor in chain")
            if not chain:
                raise SystemExit("Did not find devices in JTAG chain")
            if len(chain) > 1:
                raise SystemExit("Multi-device chains not yet supported")

        leon = leons[0]
        self.ilength = len(leon.ir_capture)
        self.cmdi = leon.parameters.cmdi
        self.datai = leon.parameters.datai
        if not self.ilength or not self.cmdi or not self.datai:
            raise SystemExit("Invalid LEON parameters")
        self.cmds = JtagTemplateFactory(jtagrw)

    def write(self, addr, value):
        ''' Write a word-aligned 32 bit value or list of 32 bit values
        '''
        assert not addr & 3
        try:
            value + 0
        except TypeError:
            return self._writearray(addr, value)
        write = self.cmds._writeword
        if not write:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            write.writei(ilength, cmdi).writed(32, adv=0).writed(3, 6).writei(ilength, datai).writed(32, adv=0).writed(1, 0)
        write([addr, value])


    def writehalf(self, addr, value):
        ''' Write a halfword-aligned 16 bit value or list of 16 bit values
        '''
        assert not addr & 1
        try:
            value + 0
        except TypeError:
            return self._writearrayh(addr, value)
        write = self.cmds._writehalf
        if not write:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            write.writei(ilength, cmdi).writed(32, adv=0).writed(3, 5).writei(ilength, datai).writed(32, adv=0).writed(1, 0)
        write([addr, (value << 16) >> (8 * (addr & 2))])

    def writebyte(self, addr, value):
        ''' Write a list of bytes
        '''
        try:
            value + 0
        except TypeError:
            return self._writearrayb(addr, value)
        write = self.cmds._writebyte
        if not write:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            write.writei(ilength, cmdi).writed(32, adv=0).writed(3, 4).writei(ilength, datai).writed(32, adv=0).writed(1, 0)
        write([addr, (value << 24) >> (8 * (addr & 3))])

    def _writearrayb(self, addr, value):
        start = 0
        while (addr & 3) and start < len(value):
            self.writebyte(addr, value[start])
            addr += 1
            start += 1
        words = zip(value[start::4], value[start+1::4], value[start+2::4], value[start+3::4])
        words = [(a<<24) + (b<<16) + (c<<8) + d for (a,b,c,d) in words]
        self._writearray(addr, words)
        start += 4 * len(words)
        addr += 4 * len(words)
        while start < len(value):
            self.writebyte(addr, value[start])
            addr += 1
            start += 1

    def _writearrayh(self, addr, value):
        assert not addr & 1
        start = 0
        while (addr & 2) and start < len(value):
            self.writehalf(addr, value[start])
            addr += 2
            start += 1
        words = zip(value[start::2], value[start+1::2])
        words = [(a<<16) + b for (a,b) in words]
        self._writearray(addr, words)
        start += 2 * len(words)
        addr += 4 * len(words)
        while start < len(value):
            self.writehalf(addr, value[start])
            addr += 2
            start += 1

    def _writechunk(self, addr, value):
        writelen = len(value)
        if writelen == 1:
            return self.write(addr, value[0])
        outerloop = (writelen + 255) / 256
        innerloop = (writelen + 255) % 256
        write = getattr(self.cmds, '_write%d' % writelen)
        if not write:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            write.update(write.select_dr).loop()
            write.writei(ilength, cmdi).writed(32, adv=0).writed(3, 6).writei(ilength, datai)
            write.loop().writed(32, adv=0).writed(1, 1).endloop(innerloop)
            write.writed(32, adv=0).writed(1, 0).endloop(outerloop)
        data = []
        for index in range(0, outerloop * 256, 256):
            data.append(addr + index * 4)
            data.extend(value[index:index+256])
        write(data)

    def _writearray(self, addr, value):
        assert not addr & 3
        start=0
        while start < len(value):
            chunksize = ((0x3FF-addr) & 0x3FF) + 1
            chunksize = min(chunksize/4, len(value) - start)
            if chunksize & 15:
                chunksize &= 15
            else:
                chunksize &= ~(chunksize-1)
            assert 256 >= chunksize >= 1
            if chunksize == 256:
                chunksize = min((len(value) - start) / chunksize, 16) * chunksize
                chunksize &= ~(chunksize-1)
            end = start + chunksize
            self._writechunk(addr, value[start:end])
            start = end
            addr += chunksize * 4

    def read(self, addr, count=None):
        assert not addr & 3
        if count is not None:
            return self._readarray(addr, count)
        read = self.cmds._readword
        if not read:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            read.writei(ilength, cmdi).writed(32, adv=0).writed(3, 2).writei(ilength, datai).readd(32, adv=0).writed(1, 0)
        return read([addr])[0]

    def readhalf(self, addr, count=None):
        assert not addr & 1
        if count is not None:
            return self._readarrayh(addr, count)
        read = self.cmds._readhalf
        if not read:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            read.writei(ilength, cmdi).writed(32, adv=0).writed(3, 1).writei(ilength, datai).readd(32, adv=0).writed(1, 0)
        return ((read([addr])[0] << (8 * (addr & 2))) >> 16) & 0xFFFF

    def readbyte(self, addr, count=None):
        if count is not None:
            return self._readarrayb(addr, count)
        read = self.cmds._readbyte
        if not read:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            read.writei(ilength, cmdi).writed(32, adv=0).writed(3, 0).writei(ilength, datai).readd(32, adv=0).writed(1, 0)
        return ((read([addr])[0] << (8 * (addr & 3))) >> 24) & 0xFF

    def _readarrayb(self, addr, count):
        start = 0
        result = []
        while (addr & 3) and start < count:
            result.append(self.readbyte(addr))
            addr += 1
            start += 1
        words = self._readarray(addr, count/4)
        numbytes = len(words) * 4
        bytes = numbytes * [None]
        bytes[0::4] = ((x>>24)        for x in words)
        bytes[1::4] = ((x>>16) & 0xFF for x in words)
        bytes[2::4] = ((x>>8)  & 0xFF for x in words)
        bytes[3::4] = ( x      & 0xFF for x in words)
        result.extend(bytes)
        start += numbytes
        addr += numbytes
        while start < count:
            result.append(self.readbyte(addr))
            addr += 1
            start += 1
        return result

    def _readarrayh(self, addr, count):
        assert not addr & 1
        start = 0
        result = []
        while (addr & 2) and start < count:
            result.append(self.readhalf(addr))
            addr += 2
            start += 1
        words = self._readarray(addr, count/2)
        numhalves = len(words) * 2
        halves = numhalves * [None]
        halves[0::2] = (x>>16   for x in words)
        halves[1::2] = (x & 0xFFFF for x in words)
        result.extend(halves)
        start += numhalves
        addr += numhalves * 2
        while start < count:
            result.append(self.readhalf(addr))
            addr += 2
            start += 1
        return result

    def _readchunk(self, addr, readlen):
        if readlen == 1:
            return [self.read(addr)]
        outerloop = (readlen + 255) / 256
        innerloop = (readlen + 255) % 256
        read = getattr(self.cmds, '_read%d' % readlen)
        if not read:
            ilength, cmdi, datai = self.ilength, self.cmdi, self.datai
            read.update(read.select_dr).loop()
            read.writei(ilength, cmdi).writed(32, adv=0).writed(3, 2).writei(ilength, datai)
            read.loop().readd(32, adv=0).writed(1, 1).endloop(innerloop)
            read.readd(32, adv=0).writed(1, 0).endloop(outerloop)
        return read([addr+index for index in range(0, outerloop*1024, 1024)])

    def _readarray(self, addr, count):
        assert not addr & 3
        result = []
        while len(result) < count:
            chunksize = ((0x3FF-addr) & 0x3FF) + 1
            chunksize = min(chunksize/4, count - len(result))
            if chunksize & 15:
                chunksize &= 15
            else:
                chunksize &= ~(chunksize-1)
            assert 256 >= chunksize >= 1
            if chunksize == 256:
                chunksize = min((count - len(result)) / chunksize, 16) * chunksize
                chunksize &= ~(chunksize-1)
            result.extend(self._readchunk(addr, chunksize))
            addr += chunksize * 4
        return result
