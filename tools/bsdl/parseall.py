#!/usr/bin/env python3
'''

Parse a whole directory full of BSDL files just to get the info we care about.
Dump the info into allchips.txt for later analysis by makeindex.py

Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''

import sys
import os
import random
import traceback

sys.path.append('../../')
from playtag.bsdl.parser import FileParser, BSDLError

filedir = 'downloads/'

debug = False

try:
    badfiles = set(open('badfiles.txt', 'rt').read().split())
except:
    badfiles = set()

def go(doall=False, debug=True):
    count = 0
    fnames = (filedir + x for x in os.listdir(filedir))
    fnames = sorted(set(fnames)- badfiles)
    if not doall and len(fnames) > 50:
        for i in range(10):
            random.shuffle(fnames)
        fnames = fnames[:50]

    chips = []

    for fname in fnames:
        count += 1
        print('  %d\r' % count, end='')
        sys.stdout.flush()
        try:
            fdata = FileParser(fname)
        except KeyboardInterrupt:
            raise
        except BSDLError as s:
            print()
            print(fname)
            print(s)
            print()
            if not debug:
                badfiles.add(fname)
        except Exception as s:
            print()
            print(fname)
            traceback.print_exc()
            print()
            if not debug:
                badfiles.add(fname)
        else:
            chips += fdata.chips
            warnings = '\n        '.join('Line %s -- %s' % x for x in fdata.warnings)
            if warnings:
                print('\n%s had warnings:\n    %s\n' % (fname, warnings))
    print()
    print()
    #attrs = 'instruction_length instruction_capture instruction_opcode bsdl_file_name'.split()
    attrs = 'idcode_register instruction_length instruction_capture bsdl_file_name parsed_ok'.split()
    update = doall and not debug
    if update:
        outf = open('allchips.txt', 'wt')
    for chip in chips:
        fname = chip.bsdl_file_name
        missing = [x for x in attrs if not hasattr(chip, x)]
        if missing:
            print("File %s, chip %s is missing %s" % (fname, chip.name, ', '.join(sorted(missing))))
        if update:
            if missing:
                badfiles.add(fname)
            else:
                print(chip.name, file=outf)
                for attr in attrs:
                    print('    %s = %s' % (attr, getattr(chip, attr)), file=outf)
    if update:
        outf.close()

    if update and badfiles:
        f = open('badfiles.txt', 'wt')
        f.write('\n'.join(sorted(badfiles)))
        f.write('\n')
        f.close()

if debug:
    go()
else:
    go(True, False)
