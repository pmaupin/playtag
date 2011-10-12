#! /usr/bin/env python
'''
Simplistic chain discovery
'''

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from playtag.cables.digilent import Jtagger
from playtag.jtag.discover import Chain

print Chain(Jtagger())
