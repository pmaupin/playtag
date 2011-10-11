#!/usr/bin/env python
'''
A tool for checking our database against the urjtag database.
'''

import os
import sys
from collections import defaultdict

sys.path.append('../../')
from playtag.bsdl.lookup import PartInfo, readfile

topdir = '/usr/share/urjtag'

def checkpart(part, mfgcodes):
    y = int(part, 2) << 12
    possible = [(x << 28) + y + z for x in range(16) for z in mfgcodes]
    possible = [PartInfo(x) for x in possible]
    actual = [x for x in possible if x.ir_capture]
    print actual and actual[0] or possible[0]

def do_mfg():
    by_mfg = defaultdict(list)

    for line in readfile(os.path.join(topdir, 'MANUFACTURERS')):
        index, name = list(line)[:2]
        by_mfg[name].append((int(index,2) << 1) + 1)

    for name, items in sorted(by_mfg.iteritems()):
        print
        print name, items
        subdir = os.path.join(topdir, name)
        partfile = os.path.join(subdir, 'PARTS')
        if not os.path.exists(partfile):
            print "No parts"
            continue
        parts = list(list(x)[0] for x in readfile(partfile))
        if not parts:
            print "No parts (2)"
            continue

        for part in parts:
            checkpart(part, items)
do_mfg()
