#!/bin/env python3

import os
import sys
assert(sys.version_info.major == 3)
import datetime	## timedelta stuff with ffmpeg
import pygame
import shlex, subprocess
import yaml

from .utils import PYG_SOUND_LOAD, EXECUTE_CMD
from .defaults import DEFAULT_WAV_IN_DIR, DEFAULT_WAV_OUT_DIR, OK_FILE_TYPES, pr_debug


DEFAULT_POS0 = 0.0
DEFAULT_POS1 = 8.0
DEFAULT_BPM     = 120.0
DEFAULT_SHIFT   = 120.0
DEFAULT_LOCK    = 12.0
DEFAULT_RETRIG  = True


class wcSlot():
    ID = 0
    WAV_IN_DIR  = DEFAULT_WAV_IN_DIR
    WAV_OUT_DIR = DEFAULT_WAV_OUT_DIR
    #SRC_OUT_DIR = DEFAULT_SRC_OUT_DIR
    OK_FILE_TYPES   = OK_FILE_TYPES
    CFG_SAVE_ATTRS  = ['pos0', 'pos1', 'bpm', 'shift_tempo', 'infile']

    def __init__(self, **kwa):
        self.id     = wcSlot.ID
        wcSlot.ID   += 1

        self.slotnum    = kwa.get('slotnum', 0)
        self.stdscr     = kwa.get('stdscr', None)
        self.Log        = kwa.get('Log', None)
        self.debug      = kwa.get('debug', 0)

        self.selected   = False
        self.retrigger  = True
        self.lastproc   = None
        self.procs      = list()

        ## would we want 'get next filename' for Recording for example?
        self.slotname   = f"slot{self.slotnum:02d}"
        self.out_path   = os.path.join(self.WAV_OUT_DIR, self.slotname)
        if not os.path.isdir(self.out_path):
            pr_debug(f"make dir {self.out_path}")
            os.mkdir(self.out_path)

        self.outfile = os.path.join(self.out_path, "OUT.wav")
        self.modfile = os.path.join(self.out_path, "MOD.wav")
        self.recfile = os.path.join(self.out_path, "REC.wav")
        self.monfile = os.path.join(self.out_path, "MON.wav")

        self.pitchObj = None

        self.Log(f"{self.slotname} initialized!")

    def __str__(self):
        _files = [self.outfile, self.modfile, self.recfile, self.monfile]
        _infile = os.path.split(self.infile)[1:][0] if self.infile else 'None'

        return " | ".join([
            f"p0={self.pos0:8.2f}",
            f"p1={self.pos1:8.2f}",
            f"{_infile:20}",
            f"d={self.duration:6.4f}",
            f"{self.bpm:6.2f}",
            f"{self.shift_tempo:6.2f}",
            "/".join([("1" if os.path.isfile(y) else "0") for y in _files])
            ])


    ## INFILE and infiles directory
    ###################################################################
    ###################################################################
    @property
    def infile(self):
        if not hasattr(self, '_infile'):	
            self._infile = None
        return self._infile

    @infile.setter
    def infile(self, val):
        self._infile = val
        if val:
            fullpath = os.path.join(self.WAV_IN_DIR, val)
            if os.path.isfile(fullpath):
                self._infile = fullpath


    @property
    def Infiles(self):
        _found = list()
        for ix, ff in enumerate(os.listdir(self.WAV_IN_DIR)):
            if os.path.splitext(ff)[1] in self.OK_FILE_TYPES:
                _found.append(os.path.join(self.WAV_IN_DIR, ff))

        return _found


    def get_infile_next(self, prev=0):
        if len(self.Infiles):
            if not self.infile:
                self.infile = self.Infiles[0]
            elif self.infile in self.Infiles:
                _index = self.Infiles.index(self.infile)
                _index += (-1 if prev else 1)
                _index %= len(self.Infiles)
                self.infile = self.Infiles[_index]
            else:
                return

            return self.infile

    def get_infile_prev(self):
        return self.get_infile_next(prev=1)


    ## POS, duration of last handled outfile/modfile
    ###################################################################
    ###################################################################
    @property
    def pos0(self):
        if not hasattr(self, '_pos0'):  
            self._pos0 = DEFAULT_POS0
        return self._pos0

    @pos0.setter
    def pos0(self, pos):
        self._pos0 = max(pos, 0)
        self.pos1
        if self.lock_length_switch:
            self._pos1 = self._pos0 + self.lock_length
        elif self._pos0 >= self._pos1:
            self._pos1 = self._pos0 + 1.0

    @property
    def pos1(self):
        if not hasattr(self, '_pos1'):  
            self._pos1 = DEFAULT_POS1
        return self._pos1

    @pos1.setter
    def pos1(self, pos):
        self._pos1 = pos
        self.pos0
        if self.lock_length_switch:
            self._pos0 = self._pos1 - self.lock_length
        elif self._pos1 <= self._pos0:
            self._pos0 = self._pos1 - 1.0


    def setPos(self, p0=None, p1=None):
        self.pos0 = p0
        self.pos1 = p1

    @property
    def duration(self):
        if not hasattr(self, '_duration'):
            self._duration = 0.0
        return self._duration

    @duration.setter
    def duration(self, val):
        self._duration = val if val else (self.pos1 - self.pos0)


    @property
    def lock_length(self):
        if not hasattr(self, '_lock_length'):
            self._lock_length = 12.0

        return self._lock_length

    @lock_length.setter
    def lock_length(self, val):
        self._lock_length = max(0.1, val)

    @property
    def lock_length_switch(self):
        if not hasattr(self, '_lock_length_switch'):
            self._lock_length_switch = False

        return self._lock_length_switch

    @lock_length_switch.setter
    def lock_length_switch(self, val):
        self._lock_length_switch = val

    def lock_length_toggle(self):
        self.lock_length_switch = not self.lock_length_switch


    ##  things that get passed to ffmpeg functions
    ###################################################################
    ###################################################################
    @property
    def bpm(self):
        if not hasattr(self, '_bpm'):
            self._bpm = DEFAULT_BPM
        return self._bpm

    @bpm.setter
    def bpm(self, bpm):
        self._bpm = max(bpm, 0)
        self.shift_tempo = bpm	## experiment

    ## does this need a property?  is it good just for consistency with bpm?
    @property
    def shift_tempo(self):
        if not hasattr(self, '_shift_tempo'):
            self._shift_tempo = DEFAULT_SHIFT
        return self._shift_tempo

    @shift_tempo.setter
    def shift_tempo(self, val):
        self._shift_tempo = max(val, 0)


    ## IN/OUT/MOD SOUND do we even need 'setters'?  just set _sound to None right?
    ###################################################################
    ###################################################################
    @property
    def insound(self):
        if not hasattr(self, '_insound'):
            self._insound = None

        if not self._insound:
            self._insound = self._pyg_loader(self.infile)

        return self._insound

    @property
    def outsound(self):
        if not hasattr(self, '_outsound'):
            self._outsound = None

        if not self._outsound:
            self._outsound = self._pyg_loader(self.outfile)

        return self._outsound

    @property
    def modsound(self):
        if not hasattr(self, '_modsound'):
            self._modsound = None

        if not self._modsound:
            self._modsound = self._pyg_loader(self.modfile)

        return self._modsound


    def _pyg_loader(self, _file):
        _obj = PYG_SOUND_LOAD(_file)
        if _obj:
            self.duration = _obj.get_length()

        return _obj


    ## cut, play, stop
    ###################################################################
    ###################################################################
    def run_proc(self, cmd):
        return EXECUTE_CMD(cmd)

    @property
    def cmd_docut_out(self):
        if self.infile:
           return "ffmpeg -ss %s -i %s -t %s -y -c copy %s" %(
               str(datetime.timedelta(seconds=self.pos0)),
               self.infile, 
               str(datetime.timedelta(seconds=(self.pos1 - self.pos0))),
               self.outfile,
               )

    @property
    def cmd_docut_mod(self):
        assert(os.path.isfile(self.outfile))
        if os.path.isfile(self.outfile):
            return "ffmpeg -y -i {} -af atempo={:.2f} {}".format(
                self.outfile,
                (self.shift_tempo / self.bpm), 
                self.modfile,
                )

    @property
    def cmd_doplay_orig(self):
        if self.infile:
            return "ffplay -ss %s -t %s -autoexit -nodisp %s" %(
                str(datetime.timedelta(seconds=self.pos0)),
                self.pos1 - self.pos0,
                self.infile, 
                )


    def doCut3_out(self, mod=False):
        ## checks done in the setters
        #if not self.infile:
        #    return

        cmd = self.cmd_docut_mod if mod else self.cmd_docut_out
        if cmd:
            _result = self.run_proc(cmd)
            self.Log(f"{self.slotname}.doCut mod={mod} | {cmd}")

            if mod: self._modsound = None   ## better to have no setter?
            else:   self._outsound = None

            return True


    def doCut3_mod(self):
        if self.bpm == self.shift_tempo:
            self.Log("WARN: bpm equals shift tempo, converting 1:1")

        return self.doCut3_out(mod=True)


    def doPlay2_mod(self, **kwargs):
        kwargs.update( {'mod':True} )
        return self.doPlay2_out(**kwargs)

    def doPlay2_out(self, stop=False, mod=False, debug=0):     ## with pygame
        _asound = self.modsound if mod else self.outsound
        if _asound:
            if self.retrigger:
                _asound.stop()
                if stop:
                    return True

            (_asound.stop if stop else _asound.play())
            return True

        return False

    def doPlay_orig(self):
        self.procs.append(subprocess.Popen(
            shlex.split(self.cmd_doplay_orig),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            ))

    
    def doStop(self):
        for p in self.procs:
            p and p.terminate()

        self.procs = list()

        self.outsound and self.outsound.stop()
        self.modsound and self.modsound.stop()


    def toggle_retrigger(self):
        self.retrigger = not self.retrigger

############################################################################
############################################################################

    @property
    def cfg_filename(self):
        if not hasattr(self, '_cfg_filename'):
            _file = os.path.splitext(os.path.split(sys.argv[0])[1])[0] + ".yml"
            self._cfg_filename = _file

        return self._cfg_filename


    def CfgSave(self):
        DATA = dict()
        _dict = dict()

        (self.pos0 != DEFAULT_POS0) and _dict.update(dict(pos0=self.pos0))
        (self.pos1 != DEFAULT_POS1) and _dict.update(dict(pos1=self.pos1))
        (self.bpm != DEFAULT_BPM) and _dict.update(dict(bpm=self.bpm))
        (self.shift_tempo != DEFAULT_SHIFT) and _dict.update(dict(shift_tempo=self.shift_tempo))
        self.infile and _dict.update(dict(infile=self.infile))
        (self.lock_length != DEFAULT_LOCK) and _dict.update(dict(lock_length=self.lock_length))
        self.lock_length_switch and _dict.update(dict(lock=self.lock_length_switch))
        (self.retrigger != DEFAULT_RETRIG) and _dict.update(dict(retrigger=self.retrigger))
        
        if _dict:   ## is there non-default data to save?
            if os.path.isfile(self.cfg_filename):
                with open(self.cfg_filename, 'r') as cfgf:
                    DATA = yaml.full_load(cfgf)
            DATA.update({ self.slotname : _dict })

            with open(self.cfg_filename, 'w') as cfgf:
                yaml.dump(DATA, cfgf)

        #self.Log(f"{self.slotname}.CFGSAVE")


    def CfgLoad(self):
        if os.path.isfile(self.cfg_filename):
            with open(self.cfg_filename, 'r') as cfgf:
                DATA = yaml.full_load(cfgf)

            _data = DATA.get(self.slotname, None)
            if _data:
                _val = _data.get('pos0', None)
                if _val:    self.pos0 = _val

                _val = _data.get('pos1', None)
                if _val:    self.pos1 = _val

                _val = _data.get('bpm', None)
                if _val:    self.bpm = _val

                _val = _data.get('shift_tempo', None)
                if _val:    self.shift_tempo = _val

                _val = _data.get('infile', None)
                if _val:    self.infile = _val

                _val = _data.get('lock', None)
                if _val != None:    self.lock_length_switch = _val

                _val = _data.get('lock_length', None)
                if _val:    self.lock_length = _val

                _val = _data.get('retrigger', None)
                if _val != None:    self.retrigger = _val

                #self.Log(f"{self.slotname}.CFGLOAD")
   




