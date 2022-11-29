#! /usr/bin/env python
'''

Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt

This was originally part of the LEON stuff, but was simplified and migrated over
here.

It shows usage of the JTAG template system.  It works with the code
in the playtag/fpga directory on the Nexys Video Artix.

It is pretty basic and could probably use some work.
'''

from ..jtag.discover import Chain
from ..jtag.template import JtagTemplate, TDIVariable
from ..jtag.states import states

class BusDriver(dict):
    ''' The BusDriver class enables reading to and writing from the Artix FPGA
        USER4 RTL.

        It has 4 functions to read and write single or multiple items.
        Each item can be 8, 16, or 32 bits (chosen at call-time).

        This class is a subclass of dict, because every time a particular
        pattern is read or written, a new template is created and memoized
        for that pattern for efficiency.
    '''

    # These defaults can be overridden either by subclassing, or by
    # passing new values when instantiating the class.

    PART = 'xc7a200t'
    USER_INSTR = '100011' # USER4 instruction


    data_var = TDIVariable(1)

    def __init__(self, jtagrw, part=None, user_instr=None):
        partname = part or self.PART
        user_instr = user_instr or self.USER_INSTR
        chain = Chain(jtagrw)
        part = chain[0] if len(chain) == 1 else None
        if not part or partname not in part.name.split('/'):
            print(str(chain))
            raise SystemExit('Expected chain with single XC7A200T device in it')
        if len(user_instr) != len(part.ir_capture):
            print(str(chain))
            raise SystemExit('Part has IR length of %s but user instruction %s is %s bits long' %
                             (len(part.ir_capture), user_instr, len(user_instr)))

        # USER4 instruction selects our JTAG register.
        # Make sure last bit shifted in when switching to data register is a 1
        JtagTemplate(jtagrw).writei(len(user_instr), user_instr).update(states.capture_dr).update(states.shift_dr,1)()
        self.jtagrw = jtagrw

    def __missing__(self, key):
        ''' Create a JTAG command template to read or write
            any number of bytes, words, or dwords.

            NOTE:  It may be advantageous at a higher level to reduce the total
                   number of templates in the system and/or to reduce the maximum
                   transmission size, but this class has no opinion about that.  It
                   will happily create a template for any size read/write you give it.
        '''
        write, size, length = key
        assert False <= write <= True
        assert size in (1, 2, 4)

        name = '%s_%d_%d' % ('write' if write else 'read', size, length)
        cmd = JtagTemplate(self.jtagrw, name, startstate=states.shift_dr)
        data = self.data_var if write else size * 8 * '1'
        rw = cmd.writed if write else cmd.readd

        def innerloop(length):
            ''' Read/Write up to 256 bytes
            '''
            total = length * size
            assert total <= 256
            sizebyte = '{0:08b}'.format(total % 256)
            assert len(sizebyte) == 8

            cmd.writed(1, 0, adv=False)         # Start bit
            cmd.writed(3, adv=False)            # Space
            cmd.writed(4, write, adv=False)     # R/W command
            cmd.writed(32, adv=False)           # Address
            cmd.writed(8, sizebyte, adv=False)  # Size
            cmd.loop()
            rw(size*8, tdi=data, adv=False)
            cmd.endloop(length)
            if write:
                # Need at least one bit to get past delay cell in the FPGA
                # but 8 seem to work better.  Probably an RTL bug.
                cmd.writed(8,'11111111', adv=False)

        maxwrite = 256 // size
        multiple, single = divmod(length, maxwrite)
        if multiple:
            cmd.loop()
            innerloop(maxwrite)
            cmd.endloop(multiple)
        if single:
            innerloop(single)

        # A single loop is easy
        loops = multiple + bool(single)
        if loops == 1:
            self[key] =cmd
            return cmd

        # For multiple loops, we return a function that will
        # call the underlying command processor with
        # replicated space/address information

        def do_loops(addrspace, *extra):
            space, addr = addrspace
            addrspace = 2 * loops * [space]
            addrspace[1::2] = range(addr, addr + 256 * loops, 256)
            return cmd(addrspace, *extra)

        self[key] = do_loops
        return do_loops

    def readmultiple(self, space, addr, length, size=1):
        return self[False, size, length]([space, addr])

    def readsingle(self, space, addr, size=1):
        return next(self[False, size, 1]([space, addr]))

    def writemultiple(self, space, addr, value, size=1):
        self[True, size, len(value)]([space, addr], value)

    def writesingle(self, space, addr, value, size=1):
        self[True, size, 1]([space, addr], [value])


def get_hexnum(bits):

    class HexNum(int):
        def __repr__(self):
            return fmt % self
        __str__ = __repr__

    fmt = '0x%%0%dx' % ((bits + 3) // 4)
    return HexNum

class OneBus(object):
    ''' This abuses Python slicing in order to facilitate easy access
        to the hardware.

        bus[1] -- a single byte/word/dword, depending on default_size
                  set for the bus.
        bus[1::4] -- a 32 bit quantity starting at address 1
        bus[32:64:4] -- 8 32-bit values
        bus[32:64] -- when reading, either 32 bytes, 16 16 bit values, or 8 32 bit
                      values, depending on default_size
                      when writing, size is determined from list passed in.

    '''

    class JustReading(object):
        ''' Most of the logic for reading and writing is identical,
            so __getitem__ and __setitem__ share a function
            This class is the default parameter for the function,
            to distinguish a call to __getitem__ from a call to
            __setitem__ with a bad parameter of None.
        '''
        pass


    valid_sizes = set([1, 2, 4])

    formatter = dict((x, get_hexnum(x*8)) for x in valid_sizes)

    def __init__(self, driver, space, space_length, default_size, min_size=1):
        ''' space -- the address space to pass to the space driver for
                     all accesses
            space_length -- validate all reads and writes against this
                            (in terms of bytes)
            default_size -- element size for reads/writes if step
                            not given (in terms of min_size)
            min_size     -- Minimum size of read or write in bytes
                            All addresses, etc. are in terms of this
                            min_size.
        '''
        assert 0 <= space <= 7
        assert 0 < space_length <= 2**32
        assert min_size in self.valid_sizes
        assert (default_size * min_size) in self.valid_sizes

        self.driver = driver
        self.space = space
        self.space_length = space_length # (in bytes)
        self.default_size = default_size  # (In multiples of min_size)
        self.min_size = min_size

    def __setitem__(self, index, value=JustReading):
        ''' The same function is used for setitem and getitem.
        '''

        min_size = self.min_size
        single_item = isinstance(index, int)
        writing = value is not self.JustReading

        if single_item:
            start = index
            stop = None
            step = None
        elif isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step
            if start is None:
                start = 0
        else:
            raise TypeError("Invalid index type: %s" % type(index))
        del index

        if writing:
            if single_item:
                if not isinstance(value, int):
                    raise TypeError('A single element can only be assigned an int')
                value = [value]
            try:
                element_count = len(value)
            except TypeError:
                # Could have a generator.  Wrap it in a list and try again,
                # and just propagate the TypeError if it still fails.
                value = list(value)
                element_count = len(value)

            if stop is None:
                if step is None:
                    step = self.default_size
                stop = start + element_count * step
            else:
                if step is None:
                    step = max((stop - start) // element_count, 1)

            if element_count != (stop - start) // step:
                raise ValueError("Expected %s elements; got %s" % ((stop-start), element_count))
        else:
            if step is None:
                step = self.default_size
            if stop is None:
                stop = start + step

        start *= min_size
        stop *= min_size
        step *= min_size

        if start < 0:
            raise IndexError('Memory starts at zero')
        if stop > self.space_length:
            raise IndexError('Memory ends at 0x%08x' % (self.space_length // min_size))
        if (stop - start) & (step - 1):
            raise IndexError('Stop - start must be multiple of index size')
        if step not in self.valid_sizes:
            raise IndexError('Invalid step size')

        # This is not a real restriction of the hardware, but
        # the hardware _will_ write to the same word twice when
        # crossing the 256 byte boundary, so breaking here keeps
        # the user from scratching his head later.
        if stop - start > 256 and start & (step-1):
            raise IndexError('Cannot read/write misaligned data across 256 byte boundary')

        if writing:
            value_index = 0
            wfunc = self.driver.writemultiple
            if min(value) < 0 or max(value) >= 2 ** (8 * step):
                raise OverflowError('Not all items fit in %s byte(s)' % step)
        else:
            result = []
            formatter = self.formatter[step]
            rfunc = self.driver.readmultiple

        # Each possible number of bytes read/written can result in up
        # to 6 templates (read vs. write, size = (1,2,4))

        # Having templates is good (they can be reused), but
        # too many templates could be bad, and reading/writing
        # too much data at a time could overflow buffers, etc.

        # So we limit the templates to:
        #  - Any number of elements <= 16
        #  - Powers of two above 16 up to 16K elements

        # This gives us up to 6 * (16 + 10) = 156 templates,
        # all of a reasonable size.

        # This limiting is done by sizing the chunks appropriately in
        # this loop.

        items_left = (stop - start) // step
        space = self.space
        while items_left:
            chunk_items = items_left & 0x0F or min(items_left - (items_left & (items_left-1)), 16384)
            if writing:
                write_slice = value[value_index : value_index + chunk_items]
                wfunc(space, start, write_slice, step)
                value_index += chunk_items
            else:
                read_slice = rfunc(space, start, chunk_items, step)
                result += map(formatter, read_slice)
            start += chunk_items * step
            items_left -= chunk_items
        return None if writing else (result[0] if single_item else result)

    __getitem__ = __setitem__
