#!/bin/env python

import os
import sys
import curses
import argparse
import time
import pygame

from .wcslot import wcSlot
from .portholder import portHolder
from .infile_getter import InfileGetter
from .slicer_pitches import PitchesSlicer
from .defaults import (
        DEFAULT_MIDI_LISTEN_CH_OUT, DEFAULT_MIDI_LISTEN_CH_MOD, DEFAULT_MIDI_LISTEN_CH_KIT, 
        CURSE_INIT, 
        )


from .utils import EW_PROMPT, DRAWHELPWIN
from .draw_slots_class import DrawSlotsClass


class slotHolder(portHolder):
    EDITFIELDS  = ['pos0', 'pos1', 'infile']
    RESOLUTIONS = [1.0, 0.1, 0.01]
    COORDS_MAIN = (20, 100, 2, 1)
    COORDS_INFO = (20, 48, 22, 1)
    COORDS_LOG  = (19, 100, 40, 1)

    MIDI_CH_CTL = DEFAULT_MIDI_LISTEN_CH_OUT
    MIDI_CH_MOD = DEFAULT_MIDI_LISTEN_CH_MOD
    MIDI_CH_KIT = DEFAULT_MIDI_LISTEN_CH_KIT

    def __init__(self, stdscr, **kwa):
        self.slot_count     = kwa.get('slot_count', 8)
        self.slicer_count   = kwa.get('slicer_count', 4)

        self.slots = []
        for s in range(self.slot_count):
            self.slots.append(wcSlot(slotnum=s, ctrl_ch=s, Log=self.Log))

        self.slicers = []

        ## 240229 - curse.wrapper(main), initscr, then make SlotHolder and Run
        ##  otherwise arrow keys might not work
        self.stdscr     = stdscr
        #self.stdscr     = curses.wrapper(CURSE_INIT)
        self.last_func  = 'None'
        self.last_msg_i = None
        self.last_msg_c = None
        self.cyc_ct = 0


    def __str__(self):
        y0 = x0 = yy = xx = None

        if self.mainWin:
            y0, x0 = self.mainWin.getbegyx()
            yy, xx = self.mainWin.getmaxyx()

        return " | ".join([
            f"SLOT {self.selected_ix:>2d}/{self.slot_count:02d}",
            f"FIELD {self.field:6}",
            f"RES {self.resolution:4.2f}",
            f"{self.last_func:^20s}",
            f"cyc={self.cyc_ct:>9d}",
            f"mwcoord=({y0},{x0},{yy},{xx})",
            ])


    def TermPrint(self):
        curses.endwin()
        print("____")
        print(self)
        for f in self.slots:
            print(f)


    @property
    def log_lines(self):
        if not hasattr(self, '_log_lines'):
            self._log_lines = list()
            self.Log("BEGIN")

        return self._log_lines

    def Log(self, txt, level='DEBUG'):
        self.log_lines.append(txt)
        #while len(self.log_lines) > 16:
        #    self.log_lines.pop(0)


    def Quit(self):
        self.TermPrint()
        sys.exit()


    ## changeable with input like keys or midi messages
    #############################################################
    #############################################################
    @property
    def selectedSlot(self):
        return self.slots[self.selected_ix]

    @property
    def resolution(self):
        return self.RESOLUTIONS[self.resolution_ix]

    @property
    def field(self):
        return self.EDITFIELDS[self.field_ix]

    @property
    def selected_ix(self):
        if not hasattr(self, '_selected_ix'):
            self._selected_ix = 0

        return self._selected_ix

    @selected_ix.setter
    def selected_ix(self, val):
        self._selected_ix = val % len(self.slots)

    @property
    def resolution_ix(self):
        if not hasattr(self, '_resolution_ix'):
            self._resolution_ix = 0

        return self._resolution_ix

    @resolution_ix.setter
    def resolution_ix(self, val):
        self._resolution_ix = val % len(self.RESOLUTIONS)

    @property
    def field_ix(self):
        if not hasattr(self, '_field_ix'):
            self._field_ix = 0

        return self._field_ix

    @field_ix.setter
    def field_ix(self, val):
        self._field_ix = val % len(self.EDITFIELDS)

    ## windows
    #############################################################
    #############################################################
    @property
    def mainWin(self):
        if not hasattr(self, '_mainWin'):
            self._mainWin = None

        return self._mainWin

    @mainWin.setter
    def mainWin(self, coords):
        _coords = coords if coords != None else self.COORDS_MAIN
        self._mainWin = curses.newwin(*_coords)
        #self._mainWin.keypad(1)
            
    @property
    def logWin(self):
        if not hasattr(self, '_logWin'):
            self._logWin = None

        return self._logWin

    @logWin.setter
    def logWin(self, coords):
        _coords = coords if coords != None else self.COORDS_LOG
        self._logWin = curses.newwin(*_coords)
        #self._logWin.keypad(1)
            
    @property
    def infoWin(self):
        if not hasattr(self, '_infoWin'):
            self._infoWin = None

        return self._infoWin

    @infoWin.setter
    def infoWin(self, coords):
        _coords = coords if coords != None else self.COORDS_INFO
        self._infoWin = curses.newwin(*_coords)
        #self._infoWin.keypad(1)
            
    
    ## seems to be the thing to do: use setters internally, provide public functions externally
    def inc_selected_ix(self):      self.selected_ix += 1
    def dec_selected_ix(self):      self.selected_ix -= 1
    def inc_resolution_ix(self):    self.resolution_ix += 1
    def dec_resolution_ix(self):    self.resolution_ix -= 1
    def inc_field_ix(self):         self.field_ix += 1
    def dec_field_ix(self):         self.field_ix -= 1


    ## Slot functions
    ############################################################################
    def DoCutOut(self, mod=False):
        '''Cut selectedSlot INFILE with region p0-p1'''
        _slot = self.selectedSlot
        _func = _slot.doCut3_mod if mod else _slot.doCut3_out
        _func()

    def DoCutMod(self):
        '''Cut selectedSlot INFILE with region p0-p1, use BPM/SHIFT ratio'''
        self.DoCutOut(mod=True)


    def DoPlayOut(self, mod=False):
        '''Play OUT file'''
        _slot = self.selectedSlot
        _func = _slot.doPlay2_mod if mod else _slot.doPlay2_out

        _func()


    def DoPlayMod(self, mod=False):
        '''Play MOD file'''
        self.DoPlayOut(mod=True)


    def DoPlayOrig(self):
        '''Play selectedSlot INFILE with region p0-p1, no cutting'''
        self.selectedSlot.doPlay_orig()


    def StopAll(self):
        #[f.doStop() for f in self.slots]
        for f in self.slots:
            f.doStop()


    def IncCursor(self, dec=False):
        '''Increment Field by Resolution'''
        if self.field_ix == 0:
            self.selectedSlot.pos0 += self.resolution * (-1 if dec else 1)
        elif self.field_ix == 1:
            self.selectedSlot.pos1 += self.resolution * (-1 if dec else 1)
        elif self.field_ix == 2:
            if dec:     self.selectedSlot.get_infile_prev()
            else:       self.selectedSlot.get_infile_next()

    def DecCursor(self):
        '''Decrement Field by Resolution'''
        self.IncCursor(dec=True)


    def IncSlotCtrlCh(self):    self.selectedSlot.inc_ctrl_ch()
    def DecSlotCtrlCh(self):    self.selectedSlot.dec_ctrl_ch()


    def SetSlotBpm(self):
        value = EW_PROMPT(f"enter BPM (float:{self.selectedSlot.bpm:6.2f}): ")
        if value:
            self.selectedSlot.bpm = value

    def SetSlotShift(self):
        value = EW_PROMPT(f"enter SHIFT TEMPO (float:{self.selectedSlot.shift_tempo:6.2f}): ")
        if value:
            self.selectedSlot.shift_tempo = value

    def SetSlotPos0(self):
        value = EW_PROMPT(f"enter POS0 (float:{self.selectedSlot.pos0:6.2f}): ")
        if value:
            self.selectedSlot.pos0 = value

    def SetSlotPos1(self):
        value = EW_PROMPT(f"enter POS1 (float:{self.selectedSlot.pos1:6.2f}): ")
        if value:
            self.selectedSlot.pos1 = value

    def SetSlotLockLength(self):
        value = EW_PROMPT(f"enter LOCK LENGTH (float:{self.selectedSlot.lock_length:6.2f}): ")
        if value:
            self.selectedSlot.lock_length = value

    ## Importer
    ############################################################################
    ############################################################################
    @property
    def Importer(self):
        if not hasattr(self, '_Importer'):
            self._Importer = None

        if not self._Importer:
            self.Importer = InfileGetter(Log=self.Log)

        return self._Importer

    @Importer.setter
    def Importer(self, val):
        self._Importer = val

    def ImportFile(self):
        if self.Importer:
            self.Importer.prompt_for_filename()


    ############################################################################
    ############################################################################

    def Run(self):
        self.mainWin    = None
        self.logWin     = None
        self.infoWin    = None

        try:
            while True:
                ik = self.stdscr.getch()
                if ik > 0 and self.keyCheck(ik):
                    self.stdscr.clear()

                self.msgPoll()
                self.Draw()
                self.cyc_ct += 1

        except KeyboardInterrupt:
            curses.endwin()
            print("\033[33mgot ctrl-C\033[0m")


    def Draw(self):
        self.stdscr.addstr(0, 0, str(self))
        #self.stdscr.addstr(1, 0, str(list(self.keyDict.keys())))
        self.stdscr.addstr(1, 0, str(self.port_i))

        self.DrawSlots()
        self.DrawLogWin()
        self.DrawInfoWin()
        if self.Importer:
            self.Importer.Draw()
            self.Importer.InfoWin.refresh()

        self.stdscr.refresh()
        self.mainWin.refresh()
        self.logWin.refresh()
        self.infoWin.refresh()


    ## incredible this works.  probably terrible practice?
    ## one bad thing from the prev. over-complicated project was, too many files for 1 'draw'
    def DrawSlots(self, **kwa):     DrawSlotsClass.DrawSlots(self, **kwa)
    def DrawLogWin(self, **kwa):    DrawSlotsClass.DrawLogWin(self, **kwa)
    def DrawInfoWin(self, **kwa):   DrawSlotsClass.DrawInfoWin(self, **kwa)
    def DrawHelpWin(self):
        DRAWHELPWIN(self, 'keyDict')
        #DRAWHELPWIN(self, 'msgDict')
	

    def CfgSaveLoad(self):
        self.stdscr.addstr(2, 0, "(s)ave or (l)oad config?", curses.A_REVERSE)
        while True:
            self.stdscr.refresh()
            ik = self.stdscr.getch()
            if ik > 0:
                _chr = chr(ik)
                if _chr not in 'SsLl':
                    self.stdscr.clear()
                    return

                for s in self.slots:
                    s.CfgSave() if _chr in 'Ss' else s.CfgLoad()

                if self.Importer:
                    self.Importer.CfgSave() if _chr in 'Ss' else self.Importer.CfgLoad()

                self.Log("CONFIG SAVED" if _chr in 'Ss' else "CONFIG LOADED")
                return True


    ############################################################################
    ############################################################################
    @property
    def keyDict(self):
        if not hasattr(self, '_keyDict'):
            self._keyDict = {
                'w' : self.dec_selected_ix,
                's' : self.inc_selected_ix,
                'a' : self.dec_field_ix,
                'd' : self.inc_field_ix,
                'e' : self.IncCursor,
                'q' : self.DecCursor,
                'F' : self.dec_resolution_ix,
                'f' : self.inc_resolution_ix,
                '[' : self.DoPlayOrig,
                ']' : self.DoCutOut,
                "'" : self.DoCutMod,
                ' ' : self.DoPlayOut,
                ';' : self.DoPlayMod,
                'Q' : self.Quit,
                '\\': self.StopAll,
                'B' : self.SetSlotBpm,
                'S' : self.SetSlotShift,
                'L' : self.SetSlotLockLength,
                '!' : self.SetSlotPos0,
                '@' : self.SetSlotPos1,
                'C' : self.CfgSaveLoad,
                '-' : self.DecSlotCtrlCh,
                '=' : self.IncSlotCtrlCh,
                '+' : self.IncSlotCtrlCh,
                'F' : self.ImportFile,
                'H' : self.DrawHelpWin,
                260 : self.dec_selected_ix,
                261 : self.inc_selected_ix,
                }

        self._keyDict.update({
            'r' : self.selectedSlot.toggle_retrigger,
            'l' : self.selectedSlot.lock_length_toggle,
            })

        return self._keyDict

    @property
    def arrowKeyDict(self):
        if not hasattr(self, '_arrowKeyDict'):
            self._arrowKeyDict = {
                curses.KEY_LEFT     : self.dec_field_ix,
                curses.KEY_RIGHT    : self.inc_field_ix,
                curses.KEY_UP       : self.IncCursor,
                curses.KEY_DOWN     : self.DecCursor,
                curses.KEY_BACKSPACE : self.StopAll,
                }

        return self.arrowKeyDict


    def keyCheck(self, ikey):
        _func = self.arrowKeyDict.get(ikey, None)
        if _func:
            self.last_func = _func.__name__
            _func()
            return True

        _func = self.keyDict.get(chr(ikey), None)
        if _func:
            self.last_func = _func.__name__
            _func()
            return True


    ############################################################################
    ############################################################################
    @property
    def msgDict(self):
        if not hasattr(self, '_msgDict'):
            self._msgDict = {
                30 : [self.dec_field_ix, self.inc_field_ix],
                31 : [self.dec_resolution_ix, self.inc_resolution_ix],
                32 : [self.dec_selected_ix, self.inc_selected_ix],
                }

        return self._msgDict


    def msgPoll(self):
        if self.port_i:
            msg_i = self.port_i.poll()
            if msg_i:
                self.last_msg_i = msg_i
                if self.port_f:
                    self.port_f.send(msg_i.copy())

                self.msgCheck_NN(msg_i)

        if self.port_c:
            msg_c = self.port_c.poll()
            if msg_c:
                self.last_msg_c = msg
                self.msgCheck_CC(msg_c)


    def msgCheck_CC(self, msg):
        if msg.type == 'control_change':
            if msg.control in [96, 97]:
                _funcs = self.msgDict.get(msg.value, None)
                if _funcs:
                    _func = _funcs[1] if (msg.control == 97) else _funcs[0]
                    self.last_func = _func.__name__
                    _func()
                    return True


    def msgCheck_NN(self, msg):
        if msg.type in ['note_on', 'note_off']:
            if msg.channel in [self.MIDI_CH_CTL, self.MIDI_CH_MOD]:
                _ix     = msg.note % len(self.slots)
                _mod    = msg.channel == self.MIDI_CH_MOD
                _stop   = msg.type == 'note_off'

                _func = self.slots[_ix].doPlay2_out
                self.last_func = _func.__name__

                _func(mod=_mod, stop=_stop)

                self.Log(" | ".join([str(x) for x in [
                    self.slots[_ix].slotname,
                    msg.note,
                    msg.channel,
                    msg.velocity,
                    ]]))

                return True


############################################################################
############################################################################

