'''
This package provides "IO templates."

There are two kinds of IO templates:

   Cable-independent IO templates are built using higher-level JTAG or SPI code.
   They are then transformed into cable-specific IO templates.

   This init file contains the base class for the cable independent IO template.
   The package directory can contain useful pieces for building cable-specific
   templates, but there are no real rules on where that code goes -- if a cable
   is so weird that its functions won't be useful for any other cable, that code
   could go in the cable-specific directory.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/LICENSE.txt
'''

class IOTemplate(object):
    ''' The default template uses JTAG-specific identifiers for internal
        variables.  Should still work for SPI, although I haven't yet
        worked out the MSB/LSB logic.

        Variable attributes:

            tms -- A list of integer 1 and 0 values, one per clock
            tdi -- A list of two different kinds of items:
                     - strings of ones and zeros
                          - output to the device rightmost character first
                     - an integer number of bits to send
            tdo -- a list of two-item tuples:
                     - Start offset in bits from previous tuple start
                     - number of bits to retrieve
            prevread -- starting position of last tuple in tdo list
            devtemplate -- Device-specific template

        Note:  tdo entries are maintained with offsets from previous
               entries to make it easier to splice templates together.
    '''
    prevread = 0          # Location of previous read
    devtemplate = None    # Translated device-specific template

    def __init__(self, cable=None, cmdname='', proto_info=None):
        self.cable=cable
        self.cmdname = cmdname
        self.tms = []
        self.tdi = []
        self.tdo = []
        self.protocol_init(proto_info)
    def protocol_init(self, proto_info):
        pass

    def __len__(self):
        return len(self.tms)

    def copy(self):
        new = type(self)(self.cable, self.cmdname)
        new.tms = list(self.tms)
        new.tdi = list(self.tdi)
        new.tdo = list(self.tdo)
        new.prevread = self.prevread
        return self.protocol_copy(new)
    def protocol_copy(self, new):
        return new

    def __add__(self, other):
        self = self.copy()
        tms, tdi, tdo = self.tms, self.tdi, self.tdo
        otms, otdi, otdo = other.tms, other.tdi, other.tdo
        if not otms:
            return self
        if tdi and otdi and isinstance(tdi[-1], str) and isinstance(otdi[0], str):
            tdi[-1] = otdi[0] + tdi[-1]
            otdi = otdi[1:]
        tdi += otdi
        if otdo:
            otdo = list(otdo)
            tdoofs, tdolen = otdo[0]
            tdoofs += len(tms) - self.prevread
            otdo[0] = tdoofs, tdolen
            tdo += otdo
            self.prevread = len(tms) + other.prevread
        tms += otms
        return self.protocol_add(other)
    def protocol_add(self, other):
        return self

    def __mul__(self, multiplier):
        assert multiplier >= 0 and int(multiplier) == multiplier, multiplier
        if multiplier == 0:
            return type(self)(self.cable)
        self = self.copy()
        tms, tdi, tdo = self.tms, self.tdi, self.tdo
        if multiplier == 1:
            return self
        if tdi and isinstance(tdi[-1], str) and isinstance(tdi[0], str):
            tdilast = tdi.pop()
            if tdi:
                tdi2 = list(tdi)
                tdi2[0] = tdi2[0] + tdilast
                tdi += (multiplier-1) * tdi2
            else:
                tdilast *= multiplier
            tdi.append(tdilast)
        else:
            tdi *= multiplier
        if tdo:
            tdo2 = list(tdo)
            tdoofs, tdolen = tdo2[0]
            tdoofs += len(tms) - self.prevread
            tdo2[0] = tdoofs, tdolen
            tdo += (multiplier-1) * tdo2
            self.prevread += (multiplier-1) * len(tms)
        tms *= multiplier
        return self.protocol_mul(multiplier)
    def protocol_mul(self, multiplier):
        return self

    __rmul__ = __mul__

    def __call__(self, tdi=[]):
        devtemplate = self.devtemplate
        if devtemplate is None:
            devtemplate = self.devtemplate = self.cable.make_template(self)
            self.apply_template = self.cable.apply_template
        return self.apply_template(devtemplate, tdi)

class TemplateFactory(object):
    TemplateClass = IOTemplate
    proto_info = None

    def __init__(self, cable=None):
        self.cable = cable
    def __getattr__(self, name):
        result = self.TemplateClass(self.cable, name, self.proto_info)
        setattr(self, name, result)
        return result
    @property
    def new(self):
        return self.TemplateClass(self.cable, '<unknown>', self.proto_info)
