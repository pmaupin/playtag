#!/usr/bin/env python
'''
Look up a JTAG ID in the database
'''

import os

root = os.path.dirname(__file__)

def readfile(fname):
    f = open(fname, 'rb')
    data = f.read()
    f.close()
    for line in data.splitlines():
        line = line.split('#',1)[0].split()
        if line:
            yield iter(line)

def expand_x():
    def expand_x(s):
        if 'x' in s:
            a, b = s.rsplit('x', 1)
            for a in expand_x(a):
                s = (a, b)
                yield '0'.join(s)
                yield '1'.join(s)
        else:
            yield s
    def str_or_num(s):
        if not isinstance(s, str):
            value, mask = s
            value, mask = '{0:032b} {1:032b}'.format(value, mask).split()
            s = ''.join((x if y == '1' else'x') for (x,y) in zip(value, mask))
        return expand_x(s)
    return str_or_num
expand_x = expand_x()

class PartInfo(object):
    partfile = os.path.join(root, 'data', 'partindex.txt')
    mfgfile = os.path.join(root, 'data', 'manufacturers.txt')
    partcache = {}
    mfgcache = {}

    @classmethod
    def addparts(cls, partinfo, int=int, expand_x=expand_x):
        partcache = cls.partcache

        for idcode, ir_capture, partname in partinfo:
            for idcode in expand_x(idcode):
                partcache[int(idcode, 2)] = ir_capture, partname

    @classmethod
    def addmfgs(cls, mfginfo, int=int):
        mfgcache = cls.mfgcache
        for line in mfginfo:
            index = int(line.next(), 2)
            mfgcache[index] = ' '.join(line)

    @classmethod
    def initcaches(cls, int=int):
        cls.addparts(readfile(cls.partfile))
        cls.addmfgs(readfile(cls.mfgfile))

    def __init__(self, index):
        try:
            index = int(index, 2)
        except TypeError:
            pass

        self.ir_capture, self.name = self.partcache.get(index, ('', '(unknown part)'))
        self.manufacturer = self.mfgcache.get((index >> 1) & ((1 << 11) - 1),
                                                             '(unknown manufacturer)')

    def possible_ir(self, int=int):
        ir_capture = self.ir_capture
        if not ir_capture:
            return []
        size = len(ir_capture)
        return [(size, int(x, 2)) for x in expand_x(ir_capture)]

    def __str__(self):
        return '%s %s (ir_capture = %s)' % (self.manufacturer, self.name,
                                                         repr(self.ir_capture))

PartInfo.initcaches()

if __name__ == '__main__':
    import sys
    for item in sys.argv[1:]:
        print '%s -- %s' % (item, str(PartInfo(item)))
