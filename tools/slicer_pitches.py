#!/bin/env python3
import time

import os

import pygame
from pygame.midi import midi_to_ansi_note
#from pygame.midi import midi_to_frequency

from .slicer_base import Slicer
from .utils import DOFFMPEG, PYG_SOUND_LOAD

########################################################################################
########################################################################################
	

class PitchesSlicer(Slicer):
    def __init__(self, *args, **kwa):
        super().__init__(*args, **kwa)
        self.basenote = kwa.get('basenote', 'A4')
        self.basenote_ix = 69   # 'A4'
        self.multitrig  = True
        self.mono       = True

        self.note_range = range(69 - 36, 69 + 36)

        self.Log("INIT")
        #self.Log = kwa.get('Log')   ## this wasnt working when just put in base class

    @property
    def NoteMap(self):
        if not hasattr(self, '_NoteMap'):
            self._NoteMap = {}

        return self._NoteMap


    def Reload22(self):
        self._state = self.STATES.LOADING
        self.Draw()
        self.stdscr.refresh()

        self.Slice(only_reload=True)


    def Slice(self, **kwa):
        if not self.infile:
            return False

        self.Log(f"{self.devname}.Slice: START, {kwa}")
        _only_reload = kwa.get('reload', False)
        _shift_tempo = kwa.get('shift_tempo', self.shift_tempo)
        _bpm         = self.bpm
        _force_rerun = kwa.get('force_rerun', False)

        self.sounds = dict()

        _path = os.path.join(self.basedir, self.owner)
        not os.path.isdir(_path) and os.mkdir(_path)
        #self.Log(_path)

        if not _only_reload or _force_rerun:
            if len(self.CmdQueue) > 0:  ## already running dont requeue the same cmds
                return

        #if self.proc:   ## running last cmd though cmdqueue is empty
        #    return

        ## A4 = note 69, note 24 is lowest ABS goes.  36 seems to be the sweet spot.  old was 24
        #for f in range(-48, 49):
        for f in range(-24, 25):
        #for f in range(-36, 37):
            _nix  = self.basenote_ix + f
            if _nix < 0:
                continue 

            _nkey = midi_to_ansi_note(_nix)
            _name = f"note_{_nix:03d}_{_nkey}"
            _name += ".wav" if self.bpm == self.shift_tempo else "_mod.wav"
            
            _outfile = os.path.join(_path, _name)
            if _only_reload:
                if os.path.isfile(_outfile):
                    #try:
                    _sound = pygame.mixer.Sound(_outfile)
                    self.sounds.update({ _nix : _sound})
            else:
                self.CmdQueueAdd(DOFFMPEG(
                    self.basenote_ix + f, 
                    self.infile, 
                    outfile=_outfile,
                    basenote_ix=self.basenote_ix,
                    Log=self.Log,
                    ))

                self.Log(f"add cmd to Slice to {_name}          ")

        return True



    def msgCheck(self, msg):
        
        #if super().msgCheck(msg):  ## checking channel happens in slotholder atm
        if msg.type in ['note_on', 'note_off']:
            self.lastRecd = msg
            if msg.note in self.note_range:
                _condition = msg.type == 'note_off' or msg.velocity == 0
                self.pygPlay(msg.note, stop=_condition)

                return True

        else:
            super().msgCheck(msg)




    

