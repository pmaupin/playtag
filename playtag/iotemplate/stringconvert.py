'''
This module contains code to optimize application of I/O templates for
drivers which expect binary data.  This module handles everything in
strings, including converting TDI integer data from the application into
strings, and extracting TDO integer data for the application from strings.

All the strings are binary, consisting of '1' and '0' characters, and sometimes
'x' to denote variable data and '*' to denote don't care data.

Repository revision 23 contains an earlier version of this code which is
designed for the digilent cable.  It is much shorter (1/3 the size) and
thus perhaps a bit more understandable.  This code has now been generalized
to be able to support the FTDI MPSSE.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/LICENSE.txt
'''
import re
import itertools
from ..iotemplate import TDIVariable

x_splitter = re.compile('(x+)').split

class TemplateStrings(object):
    ''' This class contains code to help compile device-independent template
        information into device-specific data.  This progresses in stages:
          1) First, long strings are generated for tms, tdi, and tdo.
               - 'x' denotes variable information
               - '*' denotes "don't care" information
               - The only valid characters in the tms string are '0' and '1'
               - The only valid characters in the tdi string are '0', '1', '*', and 'x'
               - The only valid characters in the tdo string are '*' and 'x'.
          2) Then, a device-specific customize_template method is called.  For
             the digilent cable, this does nothing.  For the FTDI cables, this
             will insert commands into the tdi string, and massage the tdo string
             to match expected data coming back.
          3) Then the strings are examined to create values for the tdi_combiner
             and tdo_extractor functions, and a template is created with the
             functions to call to send/receive data from the driver.
          4) Finally, the template is applied (possibly multiple times) to
             send/receive data.
    '''
    tdo_extractor = None

    def set_tdi_xstring(self, tdi_template, isinstance=isinstance, str=str, len=len, TDIVariable=TDIVariable):
        ''' Create a string of '0', '1', and 'x' based on the
            template TDI.  This string might later be modified by
            driver-specific code to insert commands for the JTAG
            cable.
        '''
        strings = []
        for numbits, value in tdi_template:
            if isinstance(value, TDIVariable):
                value = numbits * 'x'
            elif not isinstance(value, str):
                if value < 0:
                    assert value == -1, value
                    value = (1 << numbits) - 1
                value = '{0:0{1}b}'.format(value, numbits)
            assert len(value) == numbits, (value, numbits)
            strings.append(value)
        strings.reverse()
        self.tdi_xstring = ''.join(strings)
        assert len(self.tdi_xstring) == self.transaction_bit_length

    def set_tdi_converter(self, tdi_template, len=len):
        ''' Create a converter that will eat the input
            variable TDI data integers and create a single
            boolean string with all the data concatenated.

            The original design for the Digilent driver
            just interspersed the format information between
            constant information.  But the FTDI chip doesn't
            necessarily keep bits from a single input value
            together because of the way it handles exiting
            DR_SHIFT or IR_SHIFT, so we just convert all the
            input variables into a single variable string,
            and then merge it with the constant string now.
        '''
        strings = []
        index = 0
        total_bits = 0
        for numbits, value in tdi_template:
            if isinstance(value, TDIVariable):
                strings.append('{0[%d]:0%db}' % (index, numbits))
                index += 1
                total_bits += numbits
        strings.reverse()
        format = ''.join(strings).format
        del strings

        def tdi_converter(tdi):
            ''' Dump all the TDI data into one big honking boolean string.
            '''
            if len(tdi) != index:
                raise ValueError("Expected %d TDI elements; got %d" % (index, len(tdi)))
            tdistr = format(tdi)
            assert len(tdistr) == total_bits, (total_bits, len(tdistr))
            return tdistr
        self.tdi_converter = tdi_converter

    def set_tdi_combiner(self, len=len, slice=slice):
        ''' Create a combiner function that will use the
            tdi_converter and the tdi_string to merge the
            constant and variable portions of the TDI
            data together.
        '''
        strings = x_splitter(self.tdi_xstring)
        first_string = strings[0]
        const_str = strings[2::2]
        bitlens = (len(x) for x in itertools.islice(strings, 1, None, 2))
        nextindex = 0
        slices = []
        for x in bitlens:
            index = nextindex
            nextindex = index + x
            slices.append(slice(index, nextindex))
        assert len(slices) == len(const_str)
        del strings, bitlens

        tdi_converter = self.tdi_converter
        izip = itertools.izip
        join = ''.join

        def tdi_combiner(tdi):
            ''' Return small easily digestible string chunks.
                Let other devices have their way with them.
            '''
            yield first_string
            variables = tdi_converter(tdi)
            for var, const in izip(slices, const_str):
                yield variables[var]
                yield const
        self.tdi_combiner = tdi_combiner

    def set_tdo_xstring(self, tdo_template):
        ''' Sets '*' for bit positions where we do not require input,
            or 'x' for those positions requiring input.  This string
            might later be modified by driver-specific code before
            being used.
        '''
        self.tdo_bits = [x[1] for x in tdo_template]
        self.tdo_bits.reverse()
        if not tdo_template:
            self.tdo_xstring = self.transaction_bit_length * '*'
            return
        strings = []
        strloc = 0
        prevlen = 0
        total = 0
        for offset, slicelen in tdo_template:
            offset -= prevlen
            assert offset >= 0
            strings.append('*' * offset)
            strings.append('x' * slicelen)
            prevlen = slicelen
            total += offset + slicelen
        strings.append('*' * (self.transaction_bit_length - total))
        strings.reverse()
        self.tdo_xstring = ''.join(strings)
        assert len(self.tdo_xstring) == self.transaction_bit_length

    def get_tdo_extractor_slices(self, len=len, slice=slice):
        ''' This function is somewhat complicated by support for
            things like the FTDI driver, where the input bits for
            a word might not be all together.

            The output of this function is two lists of slices.
            The first list, "keep", defines the slices to keep
            from the string coming from the driver.  These slices
            are then concatenated together before extracting each
            tdo value individually using the "extract" list.
            To reduce the number of slice operations involved,
            the "keep" list will keep returned data between valid
            words.  In some cases, this might mean keeping all
            the data.
        '''
        strings = x_splitter(self.tdo_xstring)
        constbits = (len(x) for x in itertools.islice(strings, 0, None, 2))
        varbits = (len(x) for x in itertools.islice(strings, 1, None, 2))
        wordbits = list(self.tdo_bits)
        source_index = 0
        extract_index = 0
        collected = 0
        keep_start = [None]
        keep_stop = []
        extract = []
        for inc, size in itertools.izip(constbits, varbits):
            source_index += inc
            if collected:
                keep_start.append(source_index)
            else:
                extract_index += inc
            source_index += size
            collected += size
            while collected and collected >= wordbits[-1]:
                length = wordbits.pop()
                collected -= length
                extract.append(slice(extract_index, extract_index + length))
                extract_index += length
            if collected:
                keep_stop.append(source_index)
        keep_stop.append(None)
        keep = [slice(x,y) for (x,y) in itertools.izip(keep_start, keep_stop)]
        extract.reverse()
        return keep, extract

    def set_tdo_extractor(self, len=len, int=int):
        ''' Define a function that will extract a list of integers
            from the TDO string from the driver.
        '''
        keep, extract = self.get_tdo_extractor_slices()
        sourcesize = len(self.tdo_xstring)
        join=''.join
        def tdo_extractor(s):
            s = ''.join(s)
            assert len(s) == sourcesize, (len(s), sourcesize)
            s = join(s[x] for x in keep)
            return (int(s[x], 2) for x in extract)
        self.tdo_extractor = tdo_extractor

    def __init__(self, base_template, str=str):
        self.tms_string = ''.join(str(x) for x in reversed(base_template.tms))
        self.transaction_bit_length = len(self.tms_string)
        self.set_tdi_xstring(base_template.tdi)
        self.set_tdi_converter(base_template.tdi)
        self.set_tdo_xstring(base_template.tdo)
        self.customize_template()
        self.set_tdi_combiner()
        if self.tdo_bits:
            self.set_tdo_extractor()

    def customize_template(self):
        self.tdi_xstring = self.tdi_xstring.replace('*', '0')

    def get_xfer_func(self):
        tms_template = self.tms_string
        tditostr = self.tdi_combiner
        tdofromstr = self.tdo_extractor
        vars(self).clear()

        join = ''.join

        def func(driver, tdi_array):
            tdostr = driver(tms_template, join(tditostr(tdi_array)), tdofromstr)
            if tdofromstr:
                return tdofromstr(tdostr)
        return func

class StringXferMixin(object):
    ''' A cable driver helper that can convert cable-independent
        templates and data into long strings, and back
        from long strings.

        This is designed to be a mix-in class.  It assumes that
        it can simply call self() in order to transfer data
        to/from the underlying driver object.  It is used,
        e.g. by the digilent driver.
    '''
    TemplateStrings = TemplateStrings
    def make_template(self, base_template):
        return self.TemplateStrings(base_template).get_xfer_func()
    def apply_template(self, template, tdi_array):
        return template(self, tdi_array)
