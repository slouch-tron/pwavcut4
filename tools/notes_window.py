#!/bin/env python3
import curses
import mido
import time
from pygame.midi import midi_to_ansi_note

from .defaults import CURSE_INIT




class NotesWin():
   
    COORDS_NOTE = (20, 120, 22, 1)

    ## cycles to stay visually 'on', otherwise might be too fast to see
    BLINK = 1000     
    COL0 = 18       ## off
    COL1 = 46       ## on

    MODES = ['DEC', 'HEX', 'ANSI', 'BIN']
    OUT_FMTS = {
            0 : "{:>3d}".format,
            1 : "{:>2x}".format,
            2 : midi_to_ansi_note,
            3 : "{:>08b}".format,
            }


    def __init__(self, **kwa):
        self.stdscr     = kwa.get('stdscr', curses.wrapper(CURSE_INIT))
        self.last_func  = 'None'

        print(self)

    def __str__(self):
        return " | ".join([
            self.__class__.__name__,
            f"{self.mode:6s}",
            f"{self.last_func:20s}",
            str(self.notes_on),
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

    ################
    @property
    def KeyDict(self):
        if not hasattr(self, '_KeyDict'):
            self._KeyDict = {
                'm' : self.inc_mode_ptr,
                'M' : self.dec_mode_ptr,
                }

        return self._KeyDict

    def KeyCheck(self, ik):
        if ik > 0:
            _func = self.KeyDict.get(chr(ik), None)
            if _func:
                _func()
                self.last_func = _func.__name__
                self.InfoWin.clear()
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

    def MsgCheck(self, msg):
        if msg.type == 'note_on':
            self.notes_on.update({ msg.note : self.BLINK })
        elif msg.type == 'note_off':
            msg.note in self.notes_on and self.notes_on.remove(msg.note)

    ################
    @property
    def InfoWin(self):
        if not hasattr(self, '_InfoWin'):
            self.InfoWin = None

        return self._InfoWin

    @InfoWin.setter
    def InfoWin(self, coords):
        _coords = coords if coords else self.COORDS_NOTE
        self._InfoWin = curses.newwin(*_coords)


    ################
    def Draw(self, header=1):
        _ofmt = self.OUT_FMTS.get(self.mode_ptr, None)
        _attr = curses.color_pair(self.COL0)
        _yy = 0
        if header:
            self.InfoWin.addstr(0, 0, str(self), _attr | curses.A_REVERSE)
            _yy = 2

        for column in range(10):
            for row in range(12):
                _note   = (column * 12) + row
                _column = column *  10
                _attr   = curses.color_pair(
                        self.COL0 if _note not in self.notes_on else self.COL1 )

                self.InfoWin.addstr(row+_yy, _column, _ofmt(_note), _attr)

        self.InfoWin.refresh()


    def Update(self):
        for k in list(self.notes_on.keys()):    ## avoid iterate error by using list(keys)
            self.notes_on[k] -= 1
            if self.notes_on[k] < 1:
                del self.notes_on[k]
        

    def Run(self):
        try:
            while True:
                self.Draw()
                msg = None
                msg and self.MsgCheck(msg)

                ik = self.stdscr.getch()
                ik > 0 and self.KeyCheck(ik)
                self.Update()

        except KeyboardInterrupt:
            return




if __name__ == '__main__':
        note0 = mido.Message('note_on', note=50)
        note1 = mido.Message('note_on', note=51)

        #nnn = NotesWin()
        nnn = NotesWin(stdscr=curses.wrapper(CURSE_INIT))
        nnn.MsgCheck(note0)
        nnn.MsgCheck(note1)
        nnn.Run()
        curses.endwin()





