'''
This module provides a driver to connect to a Xilinx XVC server

Copyright (C) 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''
import sys
import socket
import array

from ..iotemplate.stringconvert import TemplateStrings

# Initial version.  Make it work at all, then make it faster...
# (Most obvious optimization is to use 64 bit ints rather than chars)
# Also could maybe pipeline.

test = __name__ == '__main__'
profile = False

class XvcDefaults(object):
    def __init__(self, cable_name):
        cable_name = cable_name.split()
        if len(cable_name) > 2:
            raise SystemExit('Invalid cable name: %s' % ' '.join(cable_name))
        self.XVC_HOST_NAME = 'localhost' if not cable_name else cable_name[0]
        self.XVC_PORT_NUM = 2542 if len(cable_name) < 2 else int(cable_name[1])

class Jtagger(TemplateStrings.mix_me_in()):
    sock = None
    maxbits = 120000 # Match other end for now; dynamically determine later

    def __init__(self, config):
        config.add_defaults(XvcDefaults(config.CABLE_NAME))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Ask the network driver to send packets and acks immediately
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        hostport = (config.XVC_HOST_NAME, config.XVC_PORT_NUM)
        print('\nConnecting to %s:%s...' % hostport)
        try:
            sock.connect(hostport)
        except ConnectionRefusedError:
            raise SystemExit('\nConnection refused -- exiting.\n')
        self.sock = sock

    def __del__(self):
        sock, self.sock = self.sock, None
        if sock is not None:
            sock.close()

    def getspeed(self):
        return 1000000

    def setspeed(self, newspeed):
        return 1000000

    def __call__(self, tms, tdi, usetdo):
        '''  Passed tms, tdi.  Returns tdo.
             All these are strings of '0' and '1'.
             First bit sent is the last bit in the string...
        '''
        numbits = len(tms)
        if not numbits:
            return
        assert 0 < numbits == len(tdi) <= self.maxbits
        numchars = (numbits + 7) // 8
        cmd = b'shift:%s%s%s' % (
            numbits.to_bytes(4, 'little'),
            int(tms,2).to_bytes(numchars, 'little'),
            int(tdi,2).to_bytes(numchars, 'little'))
        self.sock.sendall(cmd)
        data = array.array('B')
        while len(data) < numchars:
            newdata = self.sock.recv(min(4096, numchars - len(data)))
            if not newdata:
                raise SystemExit('Remote socket closed')
            data.frombytes(newdata)

        if usetdo:
            data = '{0:0b}'.format(int.from_bytes(data, 'little'))
            if len(data) < numbits:
                data = (numbits - len(data)) * '0' + data
            elif len(data) > numbits:
                data = data[len(data)-numbits:]
            return data

def showdevs():
    print('''
The xvc cable driver requires a hostname and an optional
port number.
''')
