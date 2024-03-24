#!/bin/env python3
import time

import os
import shlex, subprocess

import pygame
from pygame.midi import midi_to_ansi_note
#from pygame.midi import midi_to_frequency

from .slicer_base import Slicer
from .utils import DOFFMPEG, PYG_SOUND_LOAD
from .defaults import DEFAULT_SRC_OUT_DIR

########################################################################################
########################################################################################
	

class PitchesSlicer(Slicer):
    #SRC_OUT_DIR = DEFAULT_SRC_OUT_DIR

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


    @staticmethod
    def minislicer(src, bpm_ratio=1, base_note=69, owner='PitchSlicer00', nrange=36):
        _outpath = os.path.join(PitchesSlicer.SRC_OUT_DIR, owner)
        not os.path.isdir(_outpath) and os.system(f"mkdir -p {_outpath}")
        if not os.path.isfile(src):
            print(f"no file '{src}'", file=sys.stderr)
            return

        cmds = []
        for f in range(-nrange, nrange+1):

            _nix = base_note + f            ## 69 is note 'A4'
            if _nix < 0 or _nix > 118:      ## note 118 is where DOFFMPEG starts breakin down
                #print(f"\033[33m   nix={_nix}\033[0m")
                continue

            _nkey = midi_to_ansi_note(_nix)
            _name = f"note_{_nix:03d}_{_nkey}"
            _name += ".wav" if bpm_ratio == 1 else "_mod.wav"

            _outfile = os.path.join(_outpath, _name)
            cmds.append(DOFFMPEG(
                _nix,
                src,
                outfile=_outfile,
                basenote_ix=base_note,
                ))

        return cmds


    def _get_note_outfile(self, note, shift=1.0):
        if not self.infile:
            return 

        _nix = self.basenote_ix + note
        _name = f"note{_nix:03d}_{midi_to_ansi_note(_nix)}"
        _name += ".wav" if shift == 1.0 else "_mod.wav"
        return _name


    def _Cmd1Note(self, note):
        ## sort of need the _outfile for checking if isfile, in other functions
        _nfile = self._get_note_outfile(note)
        if _nfile:
            return DOFFMPEG(
                note, 
                self.infile,
                outfile=os.path.join(self.outfile_dir, _nfile),
                basenote_ix=self.basenote_ix,
                Log=self.Log,
                )


    '''
    def CutPlay1Note(self, note, bpm_ratio=1, re_cut=0):
        _existing = self.sounds.get(_nix, None)
        if _existing:
            if re_cut or _existing.to_update:
                cmd = self._Cmd1Note(note)
                os.system(cmd)
                _outfile = os.path.join(self.outfile_dir, self._get_note_outfile(_nix))
            else:
                pass ## do play
        else:
            if os.path.isfile(_outfile):
                ## load to dict
                pass
            else:
                self._Cmd1Note(note)
    '''

    def pygPlay(self, ix, stop=False, ix_offset=0, recurse=0, re_cut=0):
        ''' trying to determine if note needs cut/loading at time of midi key press '''
        if not self.multitrig:
            self.Silence()

        assert(recurse < 2)
        if ix not in self.note_range:
            print(f"{ix} not in {self.note_range}")
            return

        if stop:
            _proc = self.procs_old.get(ix, None)
            if _proc:
                self.Log(f"stopping band-aid proc for note {ix}")
                _proc.terminate()
                self.procs_old.pop(ix)

        _ix = ix + ix_offset
        _sound = self.sounds.get(_ix, None)
        if _sound:
            self.Log(f"{self.devname} %s {ix}" %('STOP' if stop else 'PLAY'))
            if stop:
                if self.mono:
                    _sound.stop()
                    self.playing_ct -= 1
                    _ix in self.notes_on and self.notes_on.remove(_ix)
            else:
                if self.fetch_ch:
                    self.fetch_ch.play(_sound)
                    self.playing_ct += 1
                    _ix not in self.notes_on and self.notes_on.append(_ix)
        else:
            _outfile = os.path.join(self.outfile_dir, self._get_note_outfile(_ix))
            if re_cut or not os.path.isfile(_outfile):
                cmd = self._Cmd1Note(_ix)
                _proc = subprocess.Popen(
                    shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _proc.communicate()

            assert(os.path.isfile(_outfile))
            self.Log(f"starting band-aid proc for note {ix}")
            self._doplay_orig(_ix, _outfile)

            _sound = pygame.mixer.Sound(_outfile)
            self.sounds.update({ _ix : _sound})
            return

            self.pygPlay(
                _ix, stop=stop, ix_offset=ix_offset, re_cut=re_cut,
                recurse=(recurse+1),
                )
            

    def _doplay_orig(self, ix, filename):
        self.procs_old.update ({ ix : subprocess.Popen(
            shlex.split(f"ffplay -autoexit -nodisp {filename}"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ) })



            
