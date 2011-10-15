'''
This module contains conversions from strings to integers and back,
including arrays of integers, for dealing with string-based drivers.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/LICENSE.txt
'''

class TdiEntry(object):
    ''' A TdiEntry object can be called to return a
        binary string representation of an integer of
        a given length.
        When you call the string, pass it the next()
        function of an iterator.
        It will either pull its value from there, or
        will not pull a value from there and will
        return a representation of a fixed value.
        We cache these objects since they are amenable
        to reuse.
    '''
    def __new__(cls, numbits, value, cache={}):
        key = numbits, value
        self = cache.get(key)
        if self is None:
            self = object.__new__(cls)
            self.numbits = numbits
            self.convert = ('{0:0%sb}' % numbits).format
            cache[key] = self
        return self
    def __call__(self, next_value, len=len):
        result = self.convert(next_value())
        if len(result) != self.numbits:
            raise ValueError("TDI value too large for number of bits")
        return result
    def test(self, s):
        return self.numbits * s


class CallableStr(str):
    ''' The purpose of this class is to provide placeholder objects
        that have the same signature as variable TdiEntry objects.
    '''
    def __new__(cls, numbits, value, cache={}):
        key = numbits, value
        self = cache.get(key)
        if self is None:
            value = ('{0:0%sb}' % numbits).format(value)
            self = str.__new__(cls, value)
            assert len(self) == numbits
            cache[key] = self
        return self
    def __call__(self, *whatever):
        return self
    def test(self, s):
        return self

def make_tdi_template(tdiinfo):
    prevbits = prevvalue = 0
    for numbits, value in tdiinfo:
        if value is None:
            if prevbits:
                yield CallableStr(prevbits, prevvalue)
                prevbits = prevvalue = 0
            yield TdiEntry(numbits, value)
        else:
            if isinstance(value, str):
                value = int(value, 2)
            elif value < 0:
                assert value == -1, value
                value = (1 << numbits) - 1
            prevvalue += value << prevbits
            prevbits += numbits
    if prevbits:
        yield CallableStr(prevbits, prevvalue)

def tditostr(tdi, numbits, tdi_template, len=len, reversed=reversed):
    itertdi = reversed(tdi)
    nexttdi = itertdi.next
    tdistr = ''.join(x(nexttdi) for x in reversed(tdi_template))
    for x in itertdi:
        raise ValueError("Not all TDI values consumed")
    assert len(tdistr) == numbits, (numbits, len(tdistr))
    return tdistr

def make_tdo_template(tdoinfo, numbits, slice=slice):
    strloc = numbits
    for offset, slicelen in tdoinfo:
        strloc -= offset
        yield slice(strloc-slicelen,strloc)

def tdofromstr(tdostr, numbits, tdo_template, len=len, int=int):
    assert len(tdostr) == numbits, (numbits, len(tdostr))
    return [int(tdostr[x], 2) for x in tdo_template]

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
        numbits = len(tms_template)
        tdi_template = list(make_tdi_template(base_template.tdi))
        tdo_template = list(make_tdo_template(base_template.tdo, numbits))
        return numbits, tms_template, tdi_template, tdo_template

    def apply_template(self, template, tdi_array, len=len, tditostr=tditostr, tdofromstr=tdofromstr):
        numbits, tms_template, tdi_template, tdo_template = template
        tdistr = tditostr(tdi_array, numbits, tdi_template)
        tdostr = self(tms_template, tdistr, tdo_template)
        if tdo_template:
            return tdofromstr(tdostr, numbits, tdo_template)
