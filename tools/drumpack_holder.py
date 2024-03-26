#!/bin/env python3
import pygame
import curses

from .defaults import CURSE_INIT
from .log_setup import GET_LOGGER
from .portholder import portHolder




class drumPackHolder(portHolder):
    COORDS_MAIN = (20, 100, 3, 1)
    COORDS_INFO = (20, 48, 22, 1)
    COORDS_LOG  = (19, 100, 40, 1)
    ID = 0

    def __init__(self, stdscr):
        self.id         = drumPackHolder.ID; drumPackHolder.ID += 1
        self.devname    = f"{self.__class__.__name__}{self.id:02d}"
        self.logger     = GET_LOGGER(appname=self.devname)
        self.stdscr     = stdscr
        self.mainWin = None


    def Log(self, msg, **kwa):
        ''' Pass this function to a class like wcSlot or InfileGetter.
            Defaults to printing on logWin.
        '''
        level   = kwa.get('level', 'visual')
        also    = kwa.get('also', 1)
        appname = kwa.get('appname', None)
        logger  = kwa.get('logger', self.logger)

        if level == 'visual':   
            self.logWin and self.logWin.clear()
            _ww = 80
            if len(msg) < _ww:
                self.log_lines.append(msg)
            else:
                for f in [msg[i:i+_ww] for i in range(0, len(msg), _ww)]:
                    self.log_lines.append(f)

            if not also:    
                return

        _func = getattr(logger, level, None) or self.logger.debug
        _func(msg)


    @property
    def mainWin(self):
        if not hasattr(self, '_mainWin'):
            self._mainWin = None

        return self._mainWin

    @mainWin.setter
    def mainWin(self, coords):
        _coords = coords if coords != None else self.COORDS_MAIN
        self._mainWin = curses.newwin(*_coords)
            
    @property
    def logWin(self):
        if not hasattr(self, '_logWin'):
            self._logWin = None

        return self._logWin

    @logWin.setter
    def logWin(self, coords):
        _coords = coords if coords != None else self.COORDS_LOG
        self._logWin = curses.newwin(*_coords)
            
    @property
    def infoWin(self):
        if not hasattr(self, '_infoWin'):
            self._infoWin = None

        return self._infoWin

    @infoWin.setter
    def infoWin(self, coords):
        _coords = coords if coords != None else self.COORDS_INFO
        self._infoWin = curses.newwin(*_coords)
    
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
                'I' : self.ImportFile,
                'H' : self.DrawHelpWin,
                260 : self.dec_selected_ix,
                261 : self.inc_selected_ix,
                'u' : self.dec_focus_ix,
                'U' : self.inc_focus_ix,
                'R' : self.SlotsReload,
                }

        self._keyDict.update({
            'r' : self.selectedSlot.toggle_retrigger,
            'l' : self.selectedSlot.lock_length_toggle,
            'P' : self.selectedSlot.SetupPitchObj,
            })

        return self._keyDict


    def keyCheck(self, ikey):
        _func = self.keyDict.get(chr(ikey), None)
        if _func:
            self.last_func = _func.__name__
            self.Log(f"'{chr(ikey)}' - '{self.last_func}'", level='debug')
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

    def msgCheck(self, msg):
        if msg.type == 'control_change':
            print(msg)


    ############################################################################
    ############################################################################

    def field_ix(self):
        if not hasattr(self, '_field_ix'):
            self._field_ix = 0

        return self._field_ix

    def ptr_ix(self):
        if not hasattr(self, '_ptr_ix'):
            self._ptr_ix = 0

        return self._ptr_ix




    ############################################################################
    ############################################################################
    def Draw(self):
        self.mainWin.addstr(0, 0, "MAIN")
        self.mainWin.refresh()


    def Run(self):
        while True:
            if self.port_i:
                msg_i = self.port_i.poll()
                if msg_i:
                    self.msgCheck(msg)

            ikey = self.stdscr.getch()
            if ikey > 0:
                self.keyCheck(ikey)

            self.Draw()
