#! /usr/bin/env python
'''
Simplistic chain discovery
'''

import sys
sys.path.append('../..')

from playtag.cables.digilent import Jtagger
from playtag.jtag.discover import Discover

print Discover(Jtagger())
