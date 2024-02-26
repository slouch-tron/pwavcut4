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
from .defaults import (
        DEFAULT_MIDI_LISTEN_CH, DEFAULT_MIDI_LISTEN_CH_MOD, DEFAULT_MIDI_LISTEN_CH_KIT, 
        CURSE_INIT, 
        )

from .utils import EW_PROMPT


class slotHolder(portHolder):
    EDITFIELDS  = ['pos0', 'pos1', 'infile']
    RESOLUTIONS = [1.0, 0.1, 0.01]
    COORDS_MAIN = (20, 100, 2, 1)
    COORDS_INFO = (20, 48, 22, 1)
    COORDS_LOG  = (19, 100, 40, 1)

    MIDI_CH_CTL = DEFAULT_MIDI_LISTEN_CH
    MIDI_CH_MOD = DEFAULT_MIDI_LISTEN_CH_MOD
    MIDI_CH_KIT = DEFAULT_MIDI_LISTEN_CH_KIT

    def __init__(self, **kwa):
        self.slot_count = kwa.get('slot_count', 8)

        self.slots = []
        for s in range(self.slot_count):
            self.slots.append(wcSlot(slotnum=s, ctrl_ch=s, Log=self.Log))

        self.stdscr     = curses.wrapper(CURSE_INIT)
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
        _slot = self.selectedSlot
        _func = _slot.doCut3_mod if mod else _slot.doCut3_out
        _func()

    def DoCutMod(self):
        self.DoCutOut(mod=True)


    def DoPlayOut(self, mod=False):
        _slot = self.selectedSlot
        _func = _slot.doPlay2_mod if mod else _slot.doPlay2_out

        _func()


    def DoPlayMod(self, mod=False):
        self.DoPlayOut(mod=True)


    def DoPlayOrig(self):
        self.selectedSlot.doPlay_orig()


    def StopAll(self):
        #[f.doStop() for f in self.slots]
        for f in self.slots:
            f.doStop()


    def IncCursor(self, dec=False):
        if self.field_ix == 0:
            self.selectedSlot.pos0 += self.resolution * (-1 if dec else 1)
        elif self.field_ix == 1:
            self.selectedSlot.pos1 += self.resolution * (-1 if dec else 1)
        elif self.field_ix == 2:
            if dec:     self.selectedSlot.get_infile_prev()
            else:       self.selectedSlot.get_infile_next()

    def DecCursor(self):
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


    def DrawSlots(self, **kwa):
        _col0 = kwa.get('col0', None) or curses.color_pair(24)      ## unselected, regular
        _col1 = kwa.get('col1', None) or curses.color_pair(51)      ## highlighted field
        _col2 = kwa.get('col2', None) or curses.color_pair(118)     ## toggled

        #_ym, _xm = self.mainWin.getmaxyx()
        _header2 = "_|_".join([
            'SS', 
            'POS0    ',
            'POS1    ',
            'INFILE              ',
            'CH',
            'LEN      ',
            'LLOCK',
            'OUT',
            'MOD',
            "OBJ",
            "",

            ])

        self.mainWin.addstr(0, 0, _header2)

        _yy = 1
        _ll = 'LLOCK'
        for ix, f in enumerate(self.slots):
            _infile = 'None'
            if f.infile:
                _infile = os.path.splitext(os.path.split(f.infile)[-1:][0])[0]

            _pos0   = f"{f.pos0:8.2f}"
            _pos1   = f"{f.pos1:8.2f}"
            _ch     = f"{f.ctrl_ch:2x}"
            _ff     = f"{_infile[:10]:^20s}"
            _dd     = f"{f.duration:9.4f}"
            _bb     = f"{f.bpm:6.2f}"
            _ss     = f"{f.shift_tempo:6.2f}"
            _po     = f.pitchObj.state if f.pitchObj else 'None'

            _attr = _col0
            if ix == self.selected_ix:
                _attr |= curses.A_REVERSE

            _xx = 0
            _ostr = f"{ix:02d}"
            self.mainWin.addstr(_yy+ix, 0, _ostr, _attr);   _xx += len(_ostr)
            self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            for ig, g in enumerate([_pos0, _pos1, _ff, _ch]): ## _ff
                _tmpattr = _attr
                if self.field_ix == ig and ix == self.selected_ix:
                    _tmpattr = _col1 | curses.A_REVERSE

                self.mainWin.addstr(_yy+ix, _xx, g, _tmpattr);  _xx += len(g)
                self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            #for ih, h in enumerate([_dd, _bb, _ss]):
            for ih, h in enumerate([_dd, ]):
                self.mainWin.addstr(_yy+ix, _xx, h, _attr);     _xx += len(h)
                self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            _attr3 = _attr
            #_attr3 = _col2
            if f.lock_length_switch:
                if ix == self.selected_ix:
                    _attr3 = _col1
                _attr3 |= curses.A_REVERSE

            self.mainWin.addstr(_yy+ix, _xx, _ll, _attr3);  _xx += len(_ll)
            self.mainWin.addstr(_yy+ix, _xx, ' | ', _attr); _xx += len(" | ")

            for _fix, _file in enumerate([f.outfile, f.modfile, _po]):
                _attr2 = _attr
                _ostr = '   '
                if os.path.isfile(_file):
                    _attr2 = _col2
                    _ostr = 'OUT' if _fix == 0 else 'MOD'

                #try:
                if True:
                    self.mainWin.addstr(_yy+ix, _xx, _ostr, _attr2);    _xx += len(_ostr)
                    self.mainWin.addstr(_yy+ix, _xx, " | ", _attr);     _xx += len(' | ')
                #except curses.error as cc:
                #    curses.endwin()
                #    print(cc)


    def DrawLogWin(self, **kwa):
        _attr = kwa.get('col0', None) or curses.color_pair(20)

        _ymax, _ = self.logWin.getmaxyx() 
        while len(self.log_lines) > (_ymax - 6):
            self.log_lines.pop(0)

        self.logWin.addstr(0, 0, f"#### LOG   ######## {self.COORDS_LOG} ####", _attr)
        for ix, f in enumerate(self.log_lines):
            self.logWin.addstr(ix+1, 0, f, _attr)


    def DrawInfoWin(self, **kwa):
        _ym, _xm = self.infoWin.getmaxyx() 
        _attr = kwa.get('col0', curses.color_pair(36))

        _slot = self.selectedSlot

        _ratio = _slot.shift_tempo / _slot.bpm
        _infile = os.path.split(_slot.infile)[-1] if _slot.infile else 'None'
        _lines = [
            f"#### {_slot.slotname.upper()} ######## {self.COORDS_INFO} ####",
            f"pos0:         {_slot.pos0:6.2f}",
            f"pos1:         {_slot.pos1:6.2f}",
            f"infile:       {_infile}",
            f"p_delta:      {_slot.pos1 - _slot.pos0}",
            f"duration:     {_slot.duration}",
            f"bpm/shift:    {_slot.bpm:6.2f} / {_slot.shift_tempo:6.2f} / {_ratio:6.4f}",
            f"lock_length:  {_slot.lock_length} ({_slot.lock_length_switch})",
            f"retrigger:    {_slot.retrigger}",
            f"outfile:      {os.path.isfile(_slot.outfile)}",
            f"modfile:      {os.path.isfile(_slot.modfile)}",
            f"pitchObj:     {_slot.pitchObj != None}",
            f"ctrl_ch:      {_slot.ctrl_ch:02x}",
            ]

        _yy = ix = 0
        for ix, line in enumerate(_lines):
            _line = f"{ix:02d} | {line}"
            _line += '_'*(_xm - 1 - len(_line))
            self.infoWin.addstr(ix+_yy, 0, _line, _attr)

        _yy = ix


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
                }

        self._keyDict.update({
            'r' : self.selectedSlot.toggle_retrigger,
            'l' : self.selectedSlot.lock_length_toggle,
            })

        return self._keyDict


    def keyCheck(self, ikey):
        _func = self.keyDict.get(chr(ikey), None)
        if _func:
            self.last_func = _func.__name__
            _func()
            return True

        ## doesnt work but why??
        ## maybe- need to pass in same 'stdscr' to anything with windowing?
        if   ikey == curses.KEY_LEFT:   self.dec_field_ix
        elif ikey == curses.KEY_RIGHT:  self.inc_field_ix
        elif ikey == curses.KEY_UP:     self.IncCursor
        elif ikey == curses.KEY_DOWN:   self.DecCursor
        else:
            return

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

        if self.port_c:
            msg_c = self.port_c.poll()
            if msg_c:
                self.msgCheck(msg_c)


    def msgCheck(self, msg):
        if msg.type == 'control_change':
            if msg.control in [96, 97]:
                _funcs = self.msgDict.get(msg.value, None)
                if _funcs:
                    _func = _funcs[1] if (msg.control == 97) else _funcs[0]
                    self.last_func = _func.__name__
                    self.last_msg_c = msg
                    _func()
                    return True


############################################################################
############################################################################
	

