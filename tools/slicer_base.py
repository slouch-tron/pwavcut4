#!/bin/env python3


import os
import sys
import curses
import argparse
import time
import pygame

from .wcslot import wcSlot
from .portholder import portHolder
from .defaults import (
        DEFAULT_MIDI_LISTEN_CH, DEFAULT_MIDI_LISTEN_CH_MOD, DEFAULT_MIDI_LISTEN_CH_KIT, 
        DEFAULT_SRC_OUT_DIR,
        CURSE_INIT,
        pr_debug,
        )

from .utils import EW_PROMPT
from .notes import NOTE_DICT


class Slicer(portHolder):
    ID = 0
    COORDS_MAIN = (20, 40, 2, 1)

    STATES = [      ## use Enum?
        'READY',
        'NOFILE',
        'RUN',
        'FAIL',
        ]

    def __init__(self, **kwa):
        self.id         = Slicer.ID
        Slicer.ID += 1

        self.infile     = kwa.get('infile', None)
        self.Log        = kwa.get('Log', None) or print
        #self.stdscr     = kwa.get('stdscr', None)
        self.basedir    = kwa.get('basedir', None) or DEFAULT_SRC_OUT_DIR
        self.ctrl_ch    = kwa.get('ctrl_ch', None) or DEFAULT_MIDI_LISTEN_CH
        self.bpm        = kwa.get('bpm', 92.0)
        self.shift_tempo = kwa.get('shift_tempo', 92.0)
        self.multitrig  = False
        self.mono       = False

        self.procs      = list()
        self.pan       = [1, 1]

        if not pygame.get_init():
            pygame.mixer.init()

        self.sounds     = list()
        self.lastRecd   = None
        self.lastSend   = None

        self.Log(f"{self.__class__.__name__}{self.id:02d} INIT")


    def __str__(self):
        return " | ".join([str(xx) for xx in [
            f"{self.__class__.__name__}{self.id:02d}",
            f"{self.ctrl_ch:x}".upper(),
            self.bpm, 
            self.shift_tempo,
            self.infile,
            len(self.sounds),
            self.multitrig,
            self.mono,
            ]])


    @property
    ## newfound knowledge, or breaking fixed things?
    def stdscr(self):
        if not hasattr(self, '_stdscr'):
            self._stdscr = None
        return self._stdscr

    @stdscr.setter
    def stdscr(self, scr):
        if not scr:
            curses.initscr()
            curses.start_color()
            curses.init_color(0,0,0,0)
            self._stdscr = curses.newwin(0,0, 50, 50)
            self._stdscr.nodelay(1)
            self._stdscr.keypad(1)
        else:
            self._stdscr = scr


    @property
    def infile(self):
        if not hasattr(self, '_infile'):
            self._infile = None

        return self._infile

    @infile.setter
    def infile(self, val):
        if val and os.path.isfile(val):
            self._infile = val


########################################################################################
########################################################################################
	

class PitchesSlicer(Slicer):
    def __init__(self, *args, **kwa):
        super().__init__(*args, **kwa)
        self.basenote = kwa.get('basenote', 'A4')
        self.multitrig  = True
        self.mono       = True
        self.proc       = None


    def Slice(self, onlyreload=False):
        if not self.infile and os.path.isfile(self.infile):
            return





