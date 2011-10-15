'''
This module contains conversions from strings to integers and back,
including arrays of integers, for dealing with string-based drivers.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/LICENSE.txt
'''

def tdi_processor(tdiinfo, total_bits, isinstance=isinstance, str=str, len=len):
    index = 0
    strings = []
    for numbits, value in tdiinfo:
        if value is None:
            value = ('{0[%d]:0%db}' % (index, numbits))
            index += 1
        else:
            if not isinstance(value, str):
                if value < 0:
                    assert value == -1, value
                    value = (1 << numbits) - 1
                value = '{0:0{1}b}'.format(value, numbits)
            assert len(value) == numbits, (value, numbits)
        strings.append(value)
    strings.reverse()
    format = ''.join(strings).format

    def tditostr(tdi):
        if len(tdi) != index:
            raise ValueError("Expected %d TDI elements; got %d" % (index, len(tdi)))
        tdistr = format(tdi)
        assert len(tdistr) == total_bits, (total_bits, len(tdistr))
        return tdistr
    return tditostr

def tdo_processor(tdoinfo, numbits, slice=slice, len=len, int=int):
    if not tdoinfo:
        return None
    template = []
    append = template.append
    strloc = numbits
    for offset, slicelen in tdoinfo:
        strloc -= offset
        append(slice(strloc-slicelen,strloc))

    def tdofromstr(tdostr):
        assert len(tdostr) == numbits, (numbits, len(tdostr))
        return [int(tdostr[x], 2) for x in template]
    return tdofromstr

class StringXferMixin(object):
    ''' A cable driver helper that can convert cable-independent
        templates and data into long strings, and back
        from long strings.

        This is designed to be a mix-in class.  It assumes that
        it can simply call self() in order to transfer data
        to/from the underlying driver object.  It is used,
        e.g. by the digilent driver.
    '''

    @staticmethod
    def make_template(base_template, str=str):
        tms_template = ''.join(str(x) for x in reversed(base_template.tms))
        tditostr = tdi_processor(base_template.tdi, len(tms_template))
        tdofromstr = tdo_processor(base_template.tdo, len(tms_template))
        return tms_template, tditostr, tdofromstr

    def apply_template(self, template, tdi_array):
        tms_template, tditostr, tdofromstr = template
        tdistr = tditostr(tdi_array)
        tdostr = self(tms_template, tdistr, tdofromstr)
        if tdofromstr:
            return tdofromstr(tdostr)
