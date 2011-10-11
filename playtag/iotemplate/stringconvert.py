'''
This module contains conversions from strings to integers and back,
including arrays of integers, for dealing with string-based drivers.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/COPYRIGHT.TXT
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
    def __new__(cls, numbits, value=None, cache={}):
        key = numbits, value
        self = cache.get(key)
        if self is None:
            convert = ('{0:0%sb}' % numbits).format
            if value is None:
                self = object.__new__(cls)
                self.convert = convert
                self.numbits = numbits
            else:
                if not isinstance(value, str):
                    if value < 0:
                        assert value == -1, value
                        value = (1 << numbits) - 1
                    value = convert(value)
                self = CallableStr(value)
                assert len(self) == numbits
            cache[key] = self
        return self
    def __call__(self, next_value, len=len, repr=repr):
        result = self.convert(next_value())
        assert len(result) == self.numbits, (len(result), self.numbits, repr(result))
        return result
    def test(self, s):
        return self.numbits * s


class CallableStr(str):
    ''' The purpose of this class is to provide placeholder objects
        that have the same signature as variable TdiEntry objects.
    '''
    def __call__(self, *whatever):
        return self
    def __add__(self, other):
        return type(self)(str(self) + other)
    def __radd__(self, other):
        return type(self)(other + str(self))
    def test(self, s):
        return self

def tditostr(tdi, numbits, tdi_template, len=len, reversed=reversed):
    itertdi = reversed(tdi)
    nexttdi = itertdi.next
    tdistr = ''.join(x(nexttdi) for x in reversed(tdi_template))
    for x in itertdi:
        raise ValueError("Not all TDI values consumed")
    assert len(tdistr) == numbits, (numbits, len(tdistr))
    return tdistr

def tdofromstr(tdostr, numbits, tdo_template, len=len, int=int):
    assert len(tdostr) == numbits, (numbits, len(tdostr))
    tdo = []
    append = tdo.append
    strloc = numbits
    for offset, slicelen in tdo_template:
        strloc -= offset
        append(int(tdostr[strloc-slicelen:strloc], 2))
    return tdo

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
        tms = ''.join(str(x) for x in reversed(base_template.tms))
        return tms, base_template.tdi, base_template.tdo

    def apply_template(self, template, tdi_array, len=len, tditostr=tditostr, tdofromstr=tdofromstr):
        tmsstr, tdi_template, tdo_template = template
        numbits = len(tmsstr)
        tdistr = tditostr(tdi_array, numbits, tdi_template)
        tdostr = self(tmsstr, tdistr, tdo_template)
        if tdo_template:
            return tdofromstr(tdostr, numbits, tdo_template)
