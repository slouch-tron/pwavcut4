#!/bin/env python3

import os
import sys
import curses
import argparse
import time
import shlex, subprocess
#from multiprocessing import Process
from enum import Enum, auto

import pygame

#from .wcslot import wcSlot
from .portholder import portHolder
from .defaults import (
        DEFAULT_MIDI_LISTEN_CH, DEFAULT_MIDI_LISTEN_CH_MOD, DEFAULT_MIDI_LISTEN_CH_KIT, 
        DEFAULT_SRC_OUT_DIR,
        CURSE_INIT,
        pr_debug,
        )

from .utils import EW_PROMPT, DRAWHELPWIN
from .notes import NOTE_DICT
from .log_setup import GET_LOGGER

DEFAULT_CTRL_CH = 1


class States(Enum):
    INIT    = auto()
    NOFILE  = auto()
    LOADED  = auto()
    SLICING = auto()
    READY   = auto()
    FAIL    = auto()
    ERROR   = auto()
    CANCEL  = auto()
    LOADING = auto()

    def __str__(self):
        return self.name




class Slicer(portHolder):
    ID = 0
    COORDS_MAIN = (20, 80, 2, 1)
    COORDS_INFO = (8, 80, 16, 0)

    STATES = States

    CH_MAX = 10

    def __init__(self, **kwa):
        self.id         = Slicer.ID
        Slicer.ID += 1
        self.devname    = f"{self.__class__.__name__}{self.id:02d}"
        #self.owner      = kwa.get('owner', 'SLICER')
        self.owner      = kwa.get('owner', self.devname)

        self.infile     = kwa.get('infile', None)
        self._Log       = kwa.get('Log')
        self.logger     = GET_LOGGER(appname=self.devname)
        #self.stdscr     = stdscr
        ## this class may need to just slice, without stdscr
        self.stdscr     = kwa.get('stdscr', None) or curses.wrapper(CURSE_INIT)
        self.basedir    = kwa.get('basedir', None) or DEFAULT_SRC_OUT_DIR
        self.bpm        = kwa.get('bpm', 92.0)
        self.shift_tempo = kwa.get('shift_tempo', 92.0)
        self.ctrl_ch    = kwa.get('ctrl_ch', DEFAULT_CTRL_CH)
        self.multitrig  = False
        self.mono       = False

        self.proc       = None
        self.pan        = [1, 1]

        #self.sliced     = False     ## works as a non-property
        #self.alarms     = list()   

        self.sounds     = dict()
        self.playing_ct = 0
        self.lastRecd   = None
        self.lastSent   = None
        self.notes_on   = list()
        self.last_func  = None

        self.CmdQueue   = list()
        self.last_cmd   = None

        if not pygame.get_init():
            pygame.mixer.init()

        self.Log(f"{self.devname} INIT")


    def __str__(self):
        return " | ".join([str(xx) for xx in [
            self.devname,
            f"{self.ctrl_ch:x}".upper(),
            #self.bpm, 
            #self.shift_tempo,
            self.infile,
            len(self.sounds),
            #self.multitrig,
            #self.mono,
            self.last_func,
            repr(self.state),
            #self.sliced,
            str(len(self.CmdQueue)),
            ]])


    def Log(self, msg, **kwa):
        kwa.update(dict(logger=self.logger))
        self._Log(msg, **kwa)

    @property
    def state(self):
        if not hasattr(self, '_state'):
            self._state = self.STATES.INIT

        _old = self._state

        if not self.infile:
            self._state = self.STATES.NOFILE
        elif len(self.CmdQueue) > 0:
            self._state = self.STATES.SLICING
        elif self._state == self.STATES.SLICING:
            self._state = self.STATES.LOADING
        elif self._state == self.STATES.LOADING:
            if len(self.sounds) > 0:
                self._state = self.STATES.READY
        #    self._state = self.STATES.FAIL  ## how can we check

        if _old != self._state:
            self.stdscr.clear()

        return self._state


    @property
    def ctrl_ch(self):
        if not hasattr(self, '_ctrl_ch'):
            self._ctrl_ch = DEFAULT_CTRL_CH

        return self._ctrl_ch

    @ctrl_ch.setter
    def ctrl_ch(self, val):
        self._ctrl_ch = val % self.CH_MAX

    def inc_ctrl_ch(self):          self.ctrl_ch += 1
    def dec_ctrl_ch(self):          self.ctrl_ch -= 1


    def CmdQueueAdd(self, cmd):
        self.CmdQueue.append(cmd)

    def CmdQueueUpdate(self):
        if self.proc:
            _poll = self.proc.poll()
            if _poll == None:   ## one from before is still running
                return  
            elif _poll == 0:    ## good result
                self.proc = None
                #self.Log("CmdQueueUpdate OK", level='debug')
                #self.Log("CmdQueueUpdate OK")
            else:
                self.Log("CmdQueueUpdate ERROR")
                pass            ## error state?
                self.proc = None
                self.Log(f"#\t{self.last_cmd}", level='error')

        if not self.proc:
            if len(self.CmdQueue) > 0:
                cmd = self.CmdQueue.pop(0)
                os.system(f'echo "{cmd}"  >> /tmp/file2.log')
                self.proc = subprocess.Popen(
                    shlex.split(cmd),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    )

                self.Log(f"CmdQueue START, {len(self.CmdQueue)} cmds waiting", level='debug')
                #self.Log(f"#SLICER BASE#\t{cmd}", level='debug')
                self.last_cmd = cmd
                if len(self.CmdQueue) == 0:
                    self.Log("CmdQueue complete!", level='debug')
                    self.Reload()

            
    def CmdQueueCancel(self):
        self.CmdQueue = list()
        if self.proc:
            self.proc.terminate()

        self.proc = None


    @property
    def infile(self):
        if not hasattr(self, '_infile'):
            self._infile = None

        return self._infile

    @infile.setter
    def infile(self, val):
        if val and os.path.isfile(val):
            self._infile = val


    ## DRAW / KEYCHECK / MSGCHECK
    ############################################################################
    ############################################################################
    @property
    def infoWin(self):
        if not hasattr(self, '_infoWin'):
            self._infoWin = None

        return self._infoWin

    @infoWin.setter
    def infoWin(self, coords):
        _coords = coords if coords else self.COORDS_INFO
        self._infoWin = curses.newwin(*_coords)

    def DrawInfoWin(self, **kwa):
        _col0 = kwa.get('col0', curses.color_pair(99))

        _line0 = " | ".join([str(x) for x in [
            self.devname,
            f"{self.state:8s}",
            f"{self.ctrl_ch:x}".upper(),
            self.infile,
            f"({len(self.sounds)} sounds)",
            ]])

        _line1 = " | ".join([str(x) for x in [
            self.bpm, 
            self.shift_tempo,
            #f"sliced={self.sliced}",
            f"mt={self.multitrig}",
            f"mo={self.mono}",
            self.last_func,
            ]])

        _line2 = f"cmdqueue={len(self.CmdQueue)}    "

        for ix, line in enumerate([
            _line0, _line1, _line2,
            f"{self.lastRecd}",
            f"{self.lastSent}",
            str(self.notes_on),

            ]):
            self.infoWin.addstr(ix, 0, line, _col0)
        

    def Draw(self):
        if self.infoWin:
            self.DrawInfoWin()
            self.infoWin.refresh()
        else:
            self.infoWin = None


    def TermDraw(self):
        print(self)


    @property
    def MsgDict(self):
        if not hasattr(self, '_MsgDict'):
            self._MsgDict = {
                    20 : [self.multitrig_toggle]*2,
                    21 : [self.mono_toggle]*2,
                }

        return self._MsgDict

    def msgCheck(self, msg):
        if not msg:
            return

        if msg.type == 'control_change':
            if msg.control in [96, 97]:
                _funcs = self.MsgDict.get(msg.value, None)
                if _funcs:
                    _func = _funcs[1 if msg.control == 97 else 0]
                    self.last_func = _func.__name__
                    _func()
                    return True

            elif msg.control == 7:
                pass ## volume ctrl
            else:
                return

            return True


    @property
    def keyDict(self):
        if not hasattr(self, '_keyDict'):
            self._keyDict = {
                'n' : self.multitrig_toggle,
                'm' : self.mono_toggle,
                'c' : self.dec_ctrl_ch,
                'C' : self.inc_ctrl_ch,
                '\\' : self.Silence,
                'B' : self.SetBpm,
                'S' : self.SetShift,
                '\n' : self.Slice,
                ' ' : self.Reload,
                'z' : self.CmdQueueCancel,
                '1' : self.stdscr.clear,
                'Q' : self.Quit,
                'H' : self.DrawHelpWin,
                #27 : self.Quit,
                }

        return self._keyDict


    def keyCheck(self, ikey):
        _func = self.keyDict.get(chr(ikey), None)
        if _func:
            self.last_func = _func.__name__
            _func()
            return True


    ## FUNCTIONS 
    ############################################################################
    ############################################################################
    def Silence(self, ix=None):
        if ix == None:
            [v.stop() for k, v in self.sounds.items() if v]
        else:
            _sound = self.sounds.get(ix, None)
            _sound and _sound.stop()

    def multitrig_toggle(self):     self.multitrig = not self.multitrig
    def mono_toggle(self):          self.mono = not self.mono

    def SetBpm(self):
        value = EW_PROMPT(f"{self.devname} | enter BPM (float:{self.bpm:6.2f}): ")
        if value:
            self.bpm = value

    def SetShift(self):
        value = EW_PROMPT(
            f"{self.devname} | enter SHIFT_TEMPO (float:{self.shift_tempo:6.2f}): ")
        if value:
            self.shift_tempo = value

    def Quit(self):
        raise KeyboardInterrupt

    def DrawHelpWin(self):
        DRAWHELPWIN(self, 'keyDict')

    ## PLAY / SLICE
    ############################################################################
    ############################################################################
    @property
    def fetch_ch(self):
        ch = pygame.mixer.find_channel()
        if ch:
            ch.set_volume(*self.pan)
            return ch


    def pygPlay(self, ix, stop=False, ix_offset=0):
        if not self.multitrig:
            self.Silence()

        ix += ix_offset
        _sound = self.sounds.get(ix, None)
        if _sound:
            if stop:
                if self.mono:
                    _sound.stop()
                    self.playing_ct -= 1
                    ix in self.notes_on and self.notes_on.remove(ix)
            else:
                if self.fetch_ch:
                    self.fetch_ch.play(_sound)
                    self.playing_ct += 1
                    ix not in self.notes_on and self.notes_on.append(ix)
            

    def Slice(self, *args, **kwa):
        raise TypeError ## should override this in each subclass


    def Reload(self):
        ## cant see this state, pyg loading blocks and when its done status is 'ready'
        self.Log(f"{self.devname}.Reload()")
        self._state = self.STATES.LOADING
        self.sounds = dict()
        self.Draw()
        self.stdscr.refresh()

        self.Slice(reload=True)


    def Run(self, terminal=0):  ## standalone demo
        try:
            self.TermDraw()

            while True:

                msg = None
                if self.port_i:
                    msg = self.port_i.poll()

                if msg:
                    if self.msgCheck(msg):
                        self.stdscr.clear()
                    if terminal:
                        self.TermDraw()

                if not terminal:
                    self.Draw()

                    ik = self.stdscr.getch()
                    if ik > 0:
                        self.keyCheck(ik)
                        self.stdscr.clear()

                self.CmdQueueUpdate()

        except KeyboardInterrupt as ee:
            curses.endwin()
            print(ee)

        #not terminal and curses.endwin()


########################################################################################
########################################################################################
	


