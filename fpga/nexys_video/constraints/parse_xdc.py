#! /usr/bin/env python3

'''
A part of playtag.

Reads Nexys Video master .xdc file, and creates two outputs:

  - A .tcl file that can be inserted in the flow after synthesis
    and before implementation.  This file has the same commands
    as an .xdc file would, but also has conditionals in it so that
    it only tries to assign signals to ports if the signals actually
    exist at the top of the design.

  - A .txt file that can be inserted into the top level module as the
    port list.  Uncomment and change from inputs as necessary after insertion.
    This file has ports named the same as the .xdc/.tcl file.

Most of the port names in the .tcl/.txt files are faithful to the names in
the master .xdc file.  This script does edit the names slightly, including:

  - removing the _cc_ and _m2c_ designations from net names, and adding the
    _cc_ nets to the fmc lpc bus.
  - removing leading zeros from subscripts, because, you know, the Xilinx tools
    don't like that.
  - Setting the xa_ and fmc_ net voltage standards to LVCMOS18
  - Changing UPPER_CASE_NAMES to not be so shouty.
'''

import re
from collections import defaultdict

verilog_names = defaultdict(set)
allnames = set()

name_splitter = re.compile(r'(_cc_|_m2c_|[0-9]+)').split

with open('Nexys-Video-Master.xdc', 'rt') as inpf, open('portmap.tcl', 'wt') as outf:
    for line in inpf:
        line = line.rstrip()
        if not line.startswith('#set_property -dict'):
            print(line, file=outf)
            continue
        line = line[1:]
        oldname = line.split('get_ports { ')[-1].split('}')[0].strip()

        newname = [x for x in name_splitter(oldname.lower()) if x]
        if len(newname) > 1:
            assert len(newname) in (3,4), newname
            if len(newname) == 4:
                assert newname[2] in ('_cc_', '_m2c_')
                newname = ['%s_%s' % (newname[0], newname[3]), '[', newname[1], ']']
            elif newname[0][-1:] == '[':
                assert newname[2] == ']'
                newname = [newname[0][:-1], '[', newname[1], ']']
            else:
                newname = [''.join(newname)]
        if len(newname) > 1:
            suffix = int(newname[2])
            newname[2] = str(suffix)
        else:
            suffix = None

        verilog_names[newname[0]].add(suffix)

        newname = ''.join(newname)

        if newname in allnames:
            print('WARNING -- could not rename %s to %s' % (oldname, newname))
            continue
        allnames.add(newname)

        line = line.replace(oldname, newname, 1)
        if newname.startswith('xa_'):
            line = line.replace('LVCMOS33', 'LVCMOS18')
        else:
            line = line.replace('LVCMOS12', 'LVCMOS18')

        print('if {[get_ports -quiet %s] != ""} {\n    %s\n}' % (newname, line), file=outf)

with open('ports.txt', 'wt') as outf:
    for name, indices in sorted(verilog_names.items()):
        if None in indices:
            assert len(indices) == 1, (name, indices)
            indices = ''
        else:
            hi = max(indices)
            lo = min(indices)
            assert hi - lo + 1 == len(indices)
            indices = '[%s:%s]' % (hi, lo)
        print('// input wire %-8s %s,' % (indices, name), file=outf)
