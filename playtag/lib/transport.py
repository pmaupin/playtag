'''
This module provides a 'connection' function which listens on a TCP/IP
socket for a connection.

This module was abstracted from the GDB transport module in order to
allow use by the Xilinx xvc driver; when I get a chance to test, I might
make GDB use this.

Call the connection function with a reference to a command processor.

TODO: Add ability to have multiple connections to different cores.

Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''

import re
import select
import socket
import socketserver
import collections
import time

def logger(what):
    print(what)

def socketrw(socket, logger=None, readsize=2048):
    recv, send = socket.recv, socket.send
    try:
        POLLIN = select.POLLIN
    except AttributeError:
            def poll(timeout):
                return select.select([socket], [], [], timeout/1000.0)[0]
    else:
        poll = select.poll()
        poll.register(socket, POLLIN)
        poll = poll.poll

    def read(timeout=None):
        if timeout is not None and not poll(timeout):
            return None
        data=recv(readsize)
        if logger is not None:
            logdata = data
            if len(logdata) > 40:
                logdata = "%s..." % repr(logdata[:40])
            else:
                logdata = repr(logdata)
            logger("Received %s" % logdata)
        return data

    def write(data, packetize=None):
        if logger is not None:
            logdata = data
            if len(logdata) > 40:
                logdata = "%s..." % repr(logdata[:40])
            else:
                logdata = repr(logdata)
            logger("Sending %s%s\n" % (packetize and 'packet ' or '', logdata))
        if packetize is not None:
            data = packetize(data)
        while data:
            data = data[send(data):]

    return read, write

def connection(cmdprocess, procname, address, run=True, logpackets=True, logger=logger, readsize=2048):

    class RequestHandler(socketserver.BaseRequestHandler):
        def setup(self):
            logger("Connected to %s:%s -- now serving %s" % (self.client_address + (procname,)))
            # Ask the network driver to send packets and acks immediately
            self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
            self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Only handle this one request at a time.
            # (In theory, we could get more than one request, but the goal here
            # is to let the slow human know as soon as possible that the socket
            # is occupied, so it's no big deal.)
            self.server.socket.shutdown(socket.SHUT_RDWR)
            self.server.socket.close()
            self.server_closed = True

        def finish(self):
            self.request.close()
            logger("Client disconnected.\n")

        def handle(self):
            read, write = socketrw(self.request, logpackets and logger or None, readsize)
            cmdprocess(read, write)

    while 1:
        server = socketserver.TCPServer(('', address), RequestHandler)
        server.server_closed = False

        if not run:
            break

        logger("Waiting for %s connection on %s:%s  (Ctrl-C to exit)" %
                ((procname,) + server.server_address))
        try:
            server.handle_request()
        except KeyboardInterrupt:
            if not server.server_closed:
                server.socket.shutdown(socket.SHUT_RDWR)
                server.socket.close()
                server.server_closed = True
            logger("\nKeyboard Interrupt received; exiting...\n")
            break

        # This sleep seems to ensure that the rebind has no issues.
        time.sleep(1)
    return server
