#! /usr/bin/env python3
'''
Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''
import time
from playtag.lib.userconfig import basic_startup
from playtag.fpga.fpgabus import BusDriver, OneBus

config = basic_startup()

if config.SHOW_CONFIG:
    print(config.dump())

bus = BusDriver(config.driver)
print('\nConnected to JTAG chain.\n')

switches = -1

eye_pattern = [1 << x for x in range(8)]
eye_pattern += list(reversed(eye_pattern))[1:-1]

ledsw = OneBus(bus, 3, 2, 2)

while True:
    try:
        for led in eye_pattern:
            ledsw[0] = led
            switches, old_sw = ledsw[0], switches
            if switches != old_sw:
                print('Switches:', hex(switches))
            time.sleep(0.1)
    except KeyboardInterrupt:
        raise SystemExit('\nExiting...\n')

