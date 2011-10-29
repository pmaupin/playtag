'''
This module contains a mixin object to map JTAG strings into
FTDI MPSSE commands.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/LICENSE.txt
'''
from .mpsse_jtag_commands import mpsse_jtag_commands
from ...iotemplate.stringconvert import TemplateStrings, StringXferMixin

class MpsseTemplate(TemplateStrings):

    def customize_template(self):
        info = mpsse_jtag_commands(self.tms_string, self.tdi_xstring, self.tdo_xstring)
        self.tdi_xstring, self.tdo_xstring = info
        del self.tms_string

    def get_xfer_func(self):
        tditostr = self.tdi_combiner
        tdofromstr = self.tdo_extractor
        tdo_length = len(self.tdo_xstring)
        vars(self).clear()

        def func(driver, tdi_array):
            tdostr = driver(tditostr(tdi_array), tdo_length)
            if tdo_length:
                return tdofromstr(tdostr)
        return func
