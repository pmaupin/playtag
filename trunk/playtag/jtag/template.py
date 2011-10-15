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
    '''

    vars().update(vars(jtagstates))

    loopstack = None

    def protocol_init(self, proto_info):
        self.states = [self.unknown]

    def protocol_copy(self, new):
        new.loopstack = self.loopstack
        new.states = list(self.states)
        return new

    def protocol_add(self, other):
        states, ostates = self.states, other.states
        assert states[-1][ostates[1]] == ostates[0][ostates[1]], (
            "Mismatched state transitions on add:  %s -> %s not same TMS values as %s -> %s" %
            (states[-1], ostates[1], ostates[0], ostates[1]))
        states.extend(ostates[1:])
        return self

    def protocol_mul(self, multiplier):
        states = self.states
        assert states[-1][states[1]] == states[0][states[1]], (
            "Mismatched state transitions on multiply:  %s -> %s not same TMS values as %s -> %s" %
            (states[-1], states[1], states[0], states[1]))
        endstate = states.pop()
        states *= multiplier
        states.append(endstate)
        return self

    def loop(self):
        prev = type(self)(self.cable)
        prev.states = [self.states[-1]]
        prev.__dict__, self.__dict__ = self.__dict__, prev.__dict__
        self.loopstack = prev
        return self

    def endloop(self, count):
        prev, self.loopstack = self.loopstack, None
        assert type(prev) is type(self)
        self.__dict__ = (prev + count * self).__dict__
        return self

    def update(self, state, tdi=None, adv=None, read=False):
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
                tdi = 0
            assert not read
        self.tdi.append((numbits, tdi))
        if read:
            self.tdo.append((tmslen - self.prevread, numbits))
            self.prevread = tmslen
        return self

    def enter_state(self, state):
        if self.states[-1] != state:
            self.update(state)
        return self

    def exit_state(self, adv):
        if adv:
            self.update(self.select_dr)
        return self

    def writei(self, numbits, tdi=None, adv=True):
        return self.enter_state(self.shift_ir).update(numbits, tdi, adv).exit_state(adv)
    def writed(self, numbits, tdi=None, adv=True):
        return self.enter_state(self.shift_dr).update(numbits, tdi, adv).exit_state(adv)
    def readi(self, numbits, adv=True, tdi=0):
        return self.enter_state(self.shift_ir).update(numbits, tdi, adv, True).exit_state(adv)
    def readd(self, numbits, adv=True, tdi=0):
        return self.enter_state(self.shift_dr).update(numbits, tdi, adv, True).exit_state(adv)

class JtagTemplateFactory(iotemplate.TemplateFactory):
    TemplateClass = JtagTemplate
