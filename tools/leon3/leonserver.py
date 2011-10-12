#! /usr/bin/env python
'''
Simplistic GDB server for LEON.
'''

import os
import sys

root = os.path.dirname(__file__)
cfgname = 'leongdb.cfg'

if not os.path.exists(cfgname):
    cfgname = os.path.join(root, cfgname)

if not os.path.exists(cfgname):
    raise SystemExit("\nCannot find configuration file %s\n" % cfgname)

class UserConfig(object):
    LOGPACKETS = False
    CABLENAME = None
    SHOW_CHAIN = True

    try:
        f = open(cfgname, 'rb')
        cfgdata = f.read()
        f.close()
        del f

        exec cfgdata
        del cfgdata
    except:
        print "\nError processing %s:\n" % cfgname
        raise

if not os.path.exists(os.path.join(UserConfig.PLAYTAG_PATH, 'playtag/__init__.py')):
    raise SystemExit("Path to playtag not configured correctly in %s" % cfgname)

sys.path.insert(0, UserConfig.PLAYTAG_PATH)

from playtag.gdb.transport import connection
from playtag.leon3.jtag_ahb import LeonMem
from playtag.leon3.gdbproc import CmdProcessor
from playtag.cables.digilent import Jtagger

if not os.path.exists(UserConfig.JTAGID_FILE) and '/' not in UserConfig.JTAGID_FILE:
    UserConfig.JTAGID_FILE = os.path.join(root, UserConfig.JTAGID_FILE)

if not os.path.exists(UserConfig.JTAGID_FILE):
    raise SystemExit("Cannot find LEON JTAG ID file %s" % UserConfig.JTAGID_FILE)

processor = CmdProcessor(LeonMem(Jtagger(UserConfig.CABLENAME), UserConfig), UserConfig)
connection(processor, logpackets=UserConfig.LOGPACKETS)
