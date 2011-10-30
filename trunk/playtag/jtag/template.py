'''
This module provides a JtagTemplate class and a JtagTemplateFactory class.

It relies on the jtagstates module to provide it state information.

When you instantiate a JtagTemplate instance, you must pass it the
function to use for JTAG transport.

Copyright (C) 2011 by Patrick Maupin.  All rights reserved.
License information at: http://playtag.googlecode.com/svn/trunk/LICENSE.txt
'''

from .states import states as jtagstates
from .. import iotemplate

class JtagTemplate(iotemplate.IOTemplate):
    ''' A JtagTemplate object is used to define
        a path through the JTAG state machine with
        definitions for TMS, TDI, and TDO.

        In theory, the IOTemplate base class ought to be
        usable for SPI and other things besides JTAG.
        In this class, we add JTAG-specific functions.
    '''

    # Get the jtag state vars from the states module
    vars().update(vars(jtagstates))

    def protocol_init(self, proto_info):
        ''' Called by __init__.  Sets up protocol-specific instance info.
        '''
        self.states = [self.unknown]

    def protocol_copy(self, new):
        ''' Called by self.copy().  Copy our protocol
            specific stuff to new object.
        '''
        new.states = list(self.states)
        return new

    def protocol_add(self, other):
        ''' Called when adding two instances together.
            Makes sure they are compatible (ending state of first
            == starting state of second) and then add them together.
        '''
        states, ostates = self.states, other.states
        assert states[-1][ostates[1]] == ostates[0][ostates[1]], (
            "Mismatched state transitions on add:  %s -> %s not same TMS values as %s -> %s" %
            (states[-1], ostates[1], ostates[0], ostates[1]))
        states.extend(ostates[1:])
        return self

    def protocol_mul(self, multiplier):
        ''' Called when multiplying an instance by an integer.
            Make sure this is legal (ending state same as startin
            state), and then do the multiply on our states.
        '''
        states = self.states
        assert states[-1][states[1]] == states[0][states[1]], (
            "Mismatched state transitions on multiply:  %s -> %s not same TMS values as %s -> %s" %
            (states[-1], states[1], states[0], states[1]))
        endstate = states.pop()
        states *= multiplier
        states.append(endstate)
        return self

    def update(self, state, tdi=None, adv=None, read=False):
        ''' update is the primary function that adds information to the
            template.  Other functions call update.
            'state' is either a number of times to remain in the current
            state or a new state to move to.
            tdi is the tdi value to use.
            adv is set True to advance out of the state (e.g. IR_SHIFT
            or DR_SHIFT) on the last clock.
            read is set true to add information to the template to capture
            TDO for the time of the update.
        '''
        self.devtemplate = None
        tmslist = self.tms
        tmslen = len(tmslist)
        states = self.states
        oldstate = states[-1]
        if isinstance(state, str) and state.isdigit() and tdi is None:
            tdi = state
            state = len(tdi)
        if isinstance(state, int):
            numbits = state
            assert oldstate.shifting
            tmslist.extend(oldstate.cyclestate(numbits))
            if adv:
                tmslist[-1] ^= 1
                states.append(oldstate[tmslist[-1]])
        else:
            assert adv is None
            newtms = oldstate[state]
            states.append(state)
            tmslist.extend(newtms)
            numbits = len(newtms)
            if tdi is None:
                tdi = numbits * '*'
            assert not read
        self.tdi.append((numbits, tdi))
        if read:
            self.tdo.append((tmslen - self.prevread, numbits))
            self.prevread = tmslen
        return self

    def enter_state(self, state):
        ''' Use update to go to a state if we are not already there.
        '''
        if self.states[-1] != state:
            self.update(state)
        return self

    def exit_state(self, adv):
        ''' Use update to exit the state to the select_dr state.
            Will probably change later to add other options.
        '''
        if adv:
            self.update(self.select_dr)
        return self

    def writei(self, numbits, tdi=None, adv=True):
        ''' Write to the JTAG instruction register
        '''
        return self.enter_state(self.shift_ir).update(numbits, tdi, adv).exit_state(adv)

    def writed(self, numbits, tdi=None, adv=True):
        ''' Write to the JTAG data register
        '''
        return self.enter_state(self.shift_dr).update(numbits, tdi, adv).exit_state(adv)

    def readi(self, numbits, adv=True, tdi=0):
        ''' Read from the JTAG instruction register
        '''
        return self.enter_state(self.shift_ir).update(numbits, tdi, adv, True).exit_state(adv)

    def readd(self, numbits, adv=True, tdi=0):
        ''' Read from the JTAG data register.
        '''
        return self.enter_state(self.shift_dr).update(numbits, tdi, adv, True).exit_state(adv)
