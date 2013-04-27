#! /usr/bin/env python
import array
import time
from discover import driver
from playtag.lib.transport import connection
from playtag.iotemplate import IOTemplate, TDIVariable
from playtag.jtag.states import states as jtagstates

'''
This program builds on the discover module.  After the cable
and chain are discovered, it runs a server that can be used
by Xilinx tools for jtag, as discussed here:

http://debugmo.de/2012/02/xvcd-the-xilinx-virtual-cable-daemon/
https://github.com/tmbinc/xvcd/tree/ftdi/src

For example, to use this with impact, choose cable setup, then
check the "Open Cable Plug-in" box, and enter the following
text in the dialog below there:

xilinx_xvc host=localhost:2542 disableversioncheck=true



'''

def cmdproc(read, write):
    tmsbuf = ['{0:08b}'.format(x)[-1::-1] for x in range(256)]
    cmdcache = {}
    makearray = array.array
    tdivar = TDIVariable()
    states = [jtagstates.reset]
    starttime = time.time()
    while True:
        data = read()
        #print repr(data[:40])
        if not data:
            return
        header = data[:10]
        try:
            numbits, strlen, tmsslice, tdislice, tmscache = cmdcache[header]
        except KeyError:
            assert header[:6] == 'shift:', "Invalid command received: %s" % repr(data[:40])
            numbits = sum(ord(j) << (8 * i) for (i, j) in enumerate(data[6:10]))
            numbytes = (numbits + 7) / 8
            tmsslice = slice(len(header), len(header) + numbytes)
            tdislice = slice(tmsslice.stop, tmsslice.stop + numbytes)
            strlen = tdislice.stop
            tmscache = {}
            cmdcache[header] = numbits, strlen, tmsslice, tdislice, tmscache
            #print cmdcache[header]
        assert len(data) == strlen, (strlen, len(data), data)
        tmsstr = data[tmsslice]
        tdistr = data[tdislice]
        try:
            template, states = tmscache[tmsstr, states[-1]]
        except KeyError:
            template = IOTemplate(driver)
            tmsbuf = makearray('B', tmsstr)
            bitmap = [min(numbits-i, 8) for i in range(0, numbits, 8)]
            template.tms = [((tmsbuf[i/8] >> (i % 8)) & 1) for i in range(numbits)]
            template.tdi = [(j, tdivar) for j in bitmap]
            template.tdo = [(i>0 and 8 or 0, j) for (i,j) in enumerate(bitmap)]
            states = states[-1:]
            for value in template.tms:
                states.append(states[-1][value])
            tmscache[tmsstr, states[0]] = template, states
        #print '%0.1f' % (time.time() - starttime), states
        result = list(template(makearray('B', tdistr)))
        if len(template.tdo) > 1 and 0:
            print [hex(x) for x in result]
            print template.tdo
        write(makearray('B', result).tostring())

connection(cmdproc, 'xvc', 2542, readsize=4096, logpackets=False)

