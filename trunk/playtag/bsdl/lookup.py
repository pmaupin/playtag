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


class PartInfo(object):
    partfile = os.path.join(root, 'data', 'partindex.txt')
    mfgfile = os.path.join(root, 'data', 'manufacturers.txt')
    partcache = {}
    mfgcache = {}

    @classmethod
    def initcaches(cls, int=int):
        partcache = cls.partcache
        def expand_x(s):
            if 'x' in s:
                a, b = s.rsplit('x', 1)
                for a in expand_x(a):
                    s = (a, b)
                    yield '0'.join(s)
                    yield '1'.join(s)
            else:
                yield s

        for idcode, ir_capture, partname in readfile(cls.partfile):
            for idcode in expand_x(idcode):
                partcache[int(idcode, 2)] = ir_capture, partname

        mfgcache = cls.mfgcache
        for line in readfile(cls.mfgfile):
            index = int(line.next(), 2)
            mfgcache[index] = ' '.join(line)

    def __init__(self, index):
        try:
            index = int(index, 2)
        except TypeError:
            pass

        self.ir_capture, self.name = self.partcache.get(index, ('', '(unknown part)'))
        self.manufacturer = self.mfgcache.get((index >> 1) & ((1 << 11) - 1),
                                                             '(unknown manufacturer)')

    def __str__(self):
        return '%s %s (ir_capture = %s)' % (self.manufacturer, self.name,
                                                         repr(self.ir_capture))

PartInfo.initcaches()

if __name__ == '__main__':
    import sys
    for item in sys.argv[1:]:
        print '%s -- %s' % (item, str(PartInfo(item)))
