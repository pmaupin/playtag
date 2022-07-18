#! /usr/bin/env python3

from playtag.jtag.states import states
from binascii import unhexlify

# From Aug 2018 UG 470, page 173

xilinx_jtag_cmds = '''
EXTEST       100110 Enables boundary-scan EXTEST operation.
EXTEST_PULSE 111100 Enables boundary-scan EXTEST_PULSE operation for transceivers
EXTEST_TRAIN 111101 Enables boundary-scan EXTEST_TRAIN operation for transceivers
SAMPLE       000001 Enables boundary-scan SAMPLE operation.
USER1        000010 Access user-defined register 1.
USER2        000011 Access user-defined register 2.
USER3        100010 Access user-defined register 3.
USER4        100011 Access user-defined register 4.
CFG_OUT      000100 Access the configuration bus for readback.
CFG_IN       000101 Access the configuration bus for configuration.
USERCODE     001000 Enables shifting out user code.
IDCODE       001001 Enables shifting out of ID code.
HIGHZ_IO     001010 3-state I/O pins only, while enabling the Bypass register.
JPROGRAM     001011 Equivalent to and has the same effect as PROGRAM.
JSTART       001100 Clocks the startup sequence when StartClk is TCK.
JSHUTDOWN    001101 Clocks the shutdown sequence.
XADC_DRP     110111 XADC DRP access through JTAG. See the DRP interface section in UG480, XADC Dual 12-Bit 1 MSPS Analog-to-Digital Converter User Guide for the 7 series.
ISC_ENABLE   010000 Marks the beginning of ISC configuration. Full shutdown is executed.
ISC_PROGRAM  010001 Enables in-system programming.
XSC_PGM_KEY  010010 Change security status from secure to non-secure mode and vice versa.
XSC_DNA      010111 Read 57-bit Device DNA value.
FUSE_DNA     110010 Read 64-bit Device DNA value.
ISC_NOOP     010100 No operation.
ISC_DISABLE  010110 Completes ISC configuration. Startup sequence is executed.
BYPASS       111111 Enables BYPASS.
'''

xilinx_jtag_cmds = (x.split() for x in xilinx_jtag_cmds.splitlines())
xilinx_jtag_cmds = dict(reversed(x[:2]) for x in xilinx_jtag_cmds if x)

def printhex(header,mylist):
    mylist = [str(x) for x in mylist]
    mylist = [mylist[i:i+8] for i in range(0, len(mylist), 8)]
    mylist = (int(''.join(reversed(x)), 2) for x in mylist)
    mylist = ''.join('%02X' % x for x in mylist)
    mylist = [mylist[i:i+64] for i in range(0, len(mylist), 64)]
    mylist = '\n     '.join(mylist)
    print('%s: %s' % (header, mylist))

with open('log_xvc.txt', 'rt') as f:
    data = f.read().split('\n\n')

headers = 'DLY NUM TMS TDI TDO'
headers = [x + ':' for x in headers.split()]

state = states.reset

tdilist, tdolist = [], []

for block in data:
    block = [x for x in block.replace('\n    ', '').split('\n') if x]
    if not block:
        continue
    assert len(block) == 5, block
    block = [x.split() for x in block]
    assert [x[0] for x in block] == headers

    dly, numbits, tmsvec, tdivec, tdovec = (x[1] for x in block)
    numbits = int(numbits)
    tmsvec = unhexlify(tmsvec)
    tdivec = unhexlify(tdivec)
    tdovec = unhexlify(tdovec)

    for bit in range(numbits):
        tms = (tmsvec[bit//8] >> (bit & 7)) & 1
        tdi = (tdivec[bit//8] >> (bit & 7)) & 1
        tdo = (tdovec[bit//8] >> (bit & 7)) & 1
        prevstate, state = state, state[tms]
        if prevstate in (states.shift_ir, states.shift_dr):
            tdilist.append(tdi)
            tdolist.append(tdo)
        if state in (states.update_ir, states.update_dr):
            if state == states.update_ir or len(tdilist) < 64:
                tdi = ''.join(str(x) for x in reversed(tdilist))
                tdo = ''.join(str(x) for x in reversed(tdolist))
                if state == states.update_ir:
                    cmd = xilinx_jtag_cmds.get(tdi[:6], '<unknown>')
                else:
                    cmd = ''
                print(state, cmd, tdi, tdo)
            else:
                print(state)
                printhex('TDI', tdilist)
                printhex('TDO', tdolist)
                print()
            tdilist, tdolist = [], []


    print('**********')
