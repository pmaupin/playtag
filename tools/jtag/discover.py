#! /usr/bin/env python3
'''
Simplistic chain discovery

Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''
from playtag.lib.userconfig import basic_startup
from playtag.jtag.discover import Chain

config = basic_startup()

if config.SHOW_CONFIG:
    print(config.dump())

chain = Chain(config.driver)
print(chain)
