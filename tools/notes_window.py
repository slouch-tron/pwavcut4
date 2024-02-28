#!/bin/env python3
import curses
import mido
import time
from pygame.midi import midi_to_ansi_note

from .defaults import CURSE_INIT
from .portholder import GET_PORT




class NotesWin():
   
    COORDS_NNW  = (20, 120, 22, 1)
    COORDS_CCW  = (20, 120, 2, 1)
    MAX_NOTE    = 127

    BLINK   = 100
    COL0    = 18       ## off
    COL1    = 46       ## on
    COL_TITLE = 36

    MODES   = ['DEC', 'HEX', 'ANSI', 'BIN']
    LAYOUTS = ['DRUM8', 'KEY12']

    OUT_FMTS = {
            0 : "{:<3d}".format,
            1 : "{:<2x}".format,
            2 : midi_to_ansi_note,
            3 : "{:>08b}".format,
            }

    def __init__(self, **kwa):
        self.stdscr     = kwa.get('stdscr', curses.wrapper(CURSE_INIT))
        self.test_port  = kwa.get('test_port', None)
        self.last_func  = 'None'
        self.lastRecd   = None
        self.loop_ct    = 0

        print(self)

    def __str__(self):
        return " | ".join([
            self.__class__.__name__,
            f"{self.mode:6s}",
            f"{self.layout:8s}",
            f"offset={self.note_offset:2d}",
            f"{self.last_func:20s}",
            f"{self.loop_ct:6d}",
            ])

    ################
    @property
    def mode(self):
        return self.MODES[self.mode_ptr]

    @property
    def mode_ptr(self):
        if not hasattr(self, '_mode_ptr'):
            self._mode_ptr = 0

        return self._mode_ptr

    @mode_ptr.setter
    def mode_ptr(self, ix):
        self._mode_ptr = ix % len(self.MODES)

    def inc_mode_ptr(self): self.mode_ptr += 1
    def dec_mode_ptr(self): self.mode_ptr -= 1


    @property
    def layout(self):
        return self.LAYOUTS[self.lo_ptr]

    @property
    def lo_ptr(self):   ## Layouts pointer
        if not hasattr(self, '_lo_ptr'):
            self._lo_ptr = 0

        return self._lo_ptr

    @lo_ptr.setter
    def lo_ptr(self, val):
        self._lo_ptr = val % len(self.LAYOUTS)

    def inc_lo_ptr(self):   self.lo_ptr += 1
    def dec_lo_ptr(self):   self.lo_ptr -= 1


    @property
    def note_offset(self):
        if not hasattr(self, '_note_offset'):
            self._note_offset = -4

        return self._note_offset

    @note_offset.setter
    def note_offset(self, val):
        self._note_offset = val

    def inc_note_offset(self):  self.note_offset += 1
    def dec_note_offset(self):  self.note_offset -= 1

    ################
    @property
    def KeyDict(self):
        if not hasattr(self, '_KeyDict'):
            self._KeyDict = {
                'm' : self.inc_mode_ptr,
                'M' : self.dec_mode_ptr,
                'n' : self.inc_lo_ptr,
                'N' : self.dec_lo_ptr,
                'o' : self.inc_note_offset,
                'O' : self.dec_note_offset,
                }

        return self._KeyDict

    def KeyCheck(self, ik):
        if ik > 0:
            _func = self.KeyDict.get(chr(ik), None)
            if _func:
                _func()
                self.last_func = _func.__name__
                self.NNWin.clear()
                self.CCWin.clear()
                self.stdscr.clear()

    ################
    @property
    def notes_on(self):
        if not hasattr(self, '_notes_on'):
            self._notes_on = {}

        return self._notes_on

    @notes_on.setter
    def notes_on(self, val):
        self._notes_on = val

    @property
    def disp_notes(self):
        return str(list(self.notes_on))

    @property
    def CCDict(self):
        if not hasattr(self, '_CCDict'):
            self._CCDict = {
                30 : [self.inc_mode_ptr, self.dec_mode_ptr],
                31 : [self.inc_lo_ptr, self.dec_lo_ptr],
                32 : [self.inc_note_offset, self.dec_note_offset],
                }

        return self._CCDict


    def MsgCheck(self, msg):
        if not msg: 
            return

        #print(msg)
        if msg.type == 'note_on':
            self.notes_on.update({ msg.note : None })
        elif msg.type == 'note_off':
            self.notes_on.update({ msg.note : self.BLINK })
        elif msg.type == 'control_change':
            if msg.control in [96, 97]:
                _funcs = self.CCDict.get(msg.value, None)
                if _funcs:
                    _func = _funcs[1 if msg.control == 97 else 0]
                    _func()
                    self.last_func = _func.__name__
                    ## clear windows?



    ################
    @property
    def NNWin(self):
        if not hasattr(self, '_NNWin'):
            self._NNWin = None

        return self._NNWin

    @NNWin.setter
    def NNWin(self, coords):
        _coords = coords if coords else self.COORDS_NNW
        self._NNWin = curses.newwin(*_coords)

    @property
    def CCWin(self):
        if not hasattr(self, '_CCWin'):
            self._CCWin = None

        return self._CCWin

    @CCWin.setter
    def CCWin(self, coords):
        _coords = coords if coords else self.COORDS_CCW
        self._CCWin = curses.newwin(*_coords)

    ################
    def Draw(self):
        if self.stdscr:
            _attr = curses.color_pair(self.COL_TITLE) | curses.A_REVERSE
            self.stdscr.addstr(0, 0, str(self), _attr)
            self.stdscr.addstr(1, 0, self.disp_notes, _attr)
            if self.loop_ct % 500 == 0:
                self.stdscr.clear()
                pass

        self.Draw_NNWin()
        self.Draw_CCWin()


    def Draw_NNWin(self):
        self.NNWin.box()

        _func = {
            0 : self._draw_nnwin_drum8,
            1 : self._draw_nnwin_key12,
            }.get(self.lo_ptr, None)

        if _func:
            _func()
            
            self.NNWin.refresh()

    def _draw_nnwin_key12(self):
        _ofmt = self.OUT_FMTS.get(self.mode_ptr, None)
        _attr = curses.color_pair(self.COL0)
        _yy = 1

        for column in range(11):
            for row in range(12):
                _note   = (column * 12) + row + self.note_offset + 4
                if _note < 0 or _note > self.MAX_NOTE:
                    continue 

                _column = (column *  10) + 2
                _attr   = curses.color_pair(
                        self.COL0 if _note not in self.notes_on else self.COL1 )

                self.NNWin.addstr(row+_yy, _column, _ofmt(_note), _attr)

    def _draw_nnwin_drum8(self):
        _ofmt = self.OUT_FMTS.get(self.mode_ptr, None)
        _attr = curses.color_pair(self.COL0)
        _yy = 2

        for row in range(18):
            for column in range(8):
                _note   = (row * 8) + column + self.note_offset
                if _note < 0 or _note > self.MAX_NOTE:
                    continue 

                _column = (column *  10) + 2
                _row =  16 - row
                _attr   = curses.color_pair(
                        self.COL0 if _note not in self.notes_on else self.COL1 )

                self.NNWin.addstr(_row+_yy, _column, _ofmt(_note), _attr)


    def Draw_CCWin(self):
        self.CCWin.addstr(0, 0, str(self))
        pass


    ################
    def BlinkUpdate(self):
        self.loop_ct += 1
        for k in list(self.notes_on.keys()):    ## avoid iterate error by using list(keys)
            if self.notes_on[k] == None:
                continue

            self.notes_on[k] -= 1
            if self.notes_on[k] <= 1:
                self.notes_on.pop(k)
        

    def Run(self):

        self.NNWin    = None
        self.CCWin      = None

        try:
            while True:
                msg = None
                if self.test_port:
                    msg = self.test_port.poll()
                    msg and self.MsgCheck(msg)

                if self.stdscr:
                    ik = self.stdscr.getch()
                    ik > 0 and self.KeyCheck(ik)

                self.Draw()
                self.BlinkUpdate()

        except KeyboardInterrupt:
            return




