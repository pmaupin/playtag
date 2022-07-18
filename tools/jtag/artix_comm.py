#! /usr/bin/env python3
'''
Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''
import time
from playtag.lib.userconfig import basic_startup
from playtag.fpga.fpgabus import BusDriver

config = basic_startup()

if config.SHOW_CONFIG:
    print(config.dump())

bus = BusDriver(config.driver)
print('Connected to JTAG chain.')

bus.writesingle(3, 0, 0)
bus.writesingle(3, 0, 0xA5)
print(hex(bus.readsingle(0, 0, 4)))
print(hex(bus.readsingle(1, 0, 4)))
print(hex(bus.readsingle(2, 0, 4)))
print(hex(bus.readsingle(0, 0, 4)))
bus.writesingle(3, 0, 0x5A)
print(hex(bus.readsingle(0, 0, 4)))
print(hex(bus.readsingle(1, 0, 4)))
print(hex(bus.readsingle(2, 0, 4)))
print(hex(bus.readsingle(0, 0, 4)))

if 1:
    start = time.time()
    for x in range(1024):
        bus.writesingle(3, 0, x % 256)
        time.sleep(0.01)
#        bus.writemultiple(3, 0, [x % 256] * 256)
#        bus.readsingle(3, 0)
    print(time.time() - start)
#    print(config.driver.read_wait)
