#!/bin/env python3

import os
import sys
import argparse
import datetime	## timedelta stuff with ffmpeg
import pygame
import shlex, subprocess
import time
import yaml


from .defaults import (
        DEFAULT_WAV_IN_DIR, DEFAULT_WAV_OUT_DIR, 
        OK_FILE_TYPES, pr_debug,
        CFGSAVE, CFGLOAD,
        )

from .log_setup import GET_LOGGER
## ought to just have our own EXECUTE_CMD maybe?  phase the 'utils' file out?
from .utils import PYG_SOUND_LOAD, EXECUTE_CMD, NORMALIZE
from .slicer_pitches import PitchesSlicer


## to compare when saving cfg, dont save defaults
DEFAULT_POS0    = 0.0
DEFAULT_POS1    = 8.0
DEFAULT_BPM     = 120.0
DEFAULT_SHIFT   = 120.0
DEFAULT_LOCK    = 12.0
DEFAULT_LOCK_ST = False
DEFAULT_RETRIG  = True
DEFAULT_CTRL_CH = 1

DEFAULT_CFG_DICT = dict(
    pos0=DEFAULT_POS0,
    pos1=DEFAULT_POS1,
    bpm=DEFAULT_BPM,
    shift_tempo=DEFAULT_SHIFT,
    ctrl_ch=DEFAULT_CTRL_CH,
    infile=None,
    lock_length=DEFAULT_LOCK,
    lock_length_switch=DEFAULT_LOCK_ST,
    retrigger=DEFAULT_RETRIG,
    )


class wcSlot():
    ID = 0
    CH_MAX = 12     ## reserve some
    WAV_IN_DIR  = DEFAULT_WAV_IN_DIR
    WAV_OUT_DIR = DEFAULT_WAV_OUT_DIR
    #SRC_OUT_DIR = DEFAULT_SRC_OUT_DIR  ## 'need to know' basis?
    OK_FILE_TYPES   = OK_FILE_TYPES
    #CFG_SAVE_ATTRS  = ['pos0', 'pos1', 'bpm', 'shift_tempo', 'infile']
    DEFAULT_CFG = DEFAULT_CFG_DICT

    FIELDS = ['OUT', 'MOD', 'OBJ']

    def __init__(self, **kwa):
        self.id     = wcSlot.ID
        wcSlot.ID   += 1

        self.slotnum    = kwa.get('slotnum', 0)
        self.slotname   = f"slot{self.slotnum:02d}"
        #self.stdscr     = kwa.get('stdscr', None)
        self._Log        = kwa.get('Log', None)
        #self.logger     = kwa.get('logger', GET_LOGGER(appname=self.slotname))
        self.logger     = GET_LOGGER(appname=self.slotname)
        #self.logger     = kwa.get('logger', None)

        self.ctrl_ch    = kwa.get('ctrl_ch', self.ctrl_ch)
        self.selected   = False
        self.retrigger  = 1
        self.lastproc   = None
        self.procs      = list()    ## only for 'playOriginal'

        #assert(self.logger)

        ## would we want 'get next filename' for Recording for example?
        self.out_path   = os.path.join(self.WAV_OUT_DIR, self.slotname)
        if not os.path.isdir(self.out_path):
            #pr_debug(f"make dir {self.out_path}")
            self.Log(f"make dir {self.out_path}")
            os.mkdir(self.out_path)

        self.outfile = os.path.join(self.out_path, "OUT.wav")
        self.modfile = os.path.join(self.out_path, "MOD.wav")
        self.recfile = os.path.join(self.out_path, "REC.wav")
        self.monfile = os.path.join(self.out_path, "MON.wav")

        ## ought to probably detect from pygame.sound
        self.is_playing_out = False
        self.is_playing_mod = False
        self.is_playing_pobj = False
        self.is_playing_orig = False

        #self.Log(f"{self.slotname} initialized!")


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


    ## have to pass the 'logger' back for proper appname to show up
    ## 240322 - but now hard to use standalone, we have to pass all these logger objs in.
    ##  are any useful log msgs from slots going to 'visual' level?
    ##  could just improve function return values, or have a 'state' for each slot
    def Log(self, msg, **kwa):
        if not self._Log:
            _func = getattr(self.logger, kwa.get('level', 'debug'), None)
            assert(_func)
            _func(msg)
        else:
            kwa.update(dict(logger=self.logger))
            kwa.update(dict(level=kwa.get('level', 'debug')))
            self._Log(msg, **kwa)


    ## was thinking of better ways to pass playing status.. but not that big a deal to just work w/ each case in the Draw function
    def get_objs(self):
        return [self.outfile, self.modfile, self.pitchObj]

    def get_field(self, ix):
        if not hasattr(self, '_field_flags'):
            self._field_flags = [
                'is_playing_out', 'is_playing_mod', 'is_playing_pobj', 'is_playing_orig']

        return dict(
            ix=_ix,
            name=self.FIELDS[ix],
            flag=self._field_flags[_ix],
            )

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
            self._pos0 = self.DEFAULT_CFG['pos0']
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
            self._pos1 = self.DEFAULT_CFG['pos1']
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
            self._lock_length = self.DEFAULT_CFG['lock_length']

        return self._lock_length

    @lock_length.setter
    def lock_length(self, val):
        self._lock_length = max(0.1, val)

    @property
    def lock_length_switch(self):
        if not hasattr(self, '_lock_length_switch'):
            self._lock_length_switch = self.DEFAULT_CFG['lock_length_switch']

        return self._lock_length_switch

    @lock_length_switch.setter
    def lock_length_switch(self, val):
        self._lock_length_switch = val

    def lock_length_toggle(self):
        self.lock_length_switch = not self.lock_length_switch


    def toggle_retrigger(self):
        self.retrigger = not self.retrigger


    ##  things that get passed to ffmpeg functions
    ###################################################################
    ###################################################################
    @property
    def bpm(self):
        if not hasattr(self, '_bpm'):
            self._bpm = self.DEFAULT_CFG['bpm']
        return self._bpm

    @bpm.setter
    def bpm(self, bpm):
        self._bpm = max(bpm, 0)
        self.shift_tempo = bpm	## experiment

    @property
    def shift_tempo(self):
        if not hasattr(self, '_shift_tempo'):
            self._shift_tempo = self.DEFAULT_CFG['shift_tempo']
        return self._shift_tempo

    @shift_tempo.setter
    def shift_tempo(self, val):
        self._shift_tempo = max(val, 0)

    @property
    def ctrl_ch(self):
        if not hasattr(self, '_ctrl_ch'):
            self._ctrl_ch = self.DEFAULT_CFG['ctrl_ch']

        return self._ctrl_ch

    @ctrl_ch.setter
    def ctrl_ch(self, val):
        self._ctrl_ch = val % self.CH_MAX

    def inc_ctrl_ch(self):          self.ctrl_ch += 1
    def dec_ctrl_ch(self):          self.ctrl_ch -= 1

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
        ## ought to just put our own popen and logging here
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
        print(self.outfile)
        #assert(os.path.isfile(self.outfile))
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
        cmd = self.cmd_docut_mod if mod else self.cmd_docut_out
        self.Log(f"doCut | mod={mod}")
        self.Log(f"{cmd}")
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
            if mod:     self.is_playing_mod = not bool(stop)
            else:       self.is_playing_out = not bool(stop)

            if self.retrigger or stop:
                _asound.stop()
                if stop:
                    return True

            _asound.play()
            return True


    def doPlay_orig(self):
        assert(self.cmd_doplay_orig)    ## return?  do nothing?
        self.procs.append(subprocess.Popen(
            shlex.split(self.cmd_doplay_orig),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
            ))

    
    def doStop(self):
        self.is_playing_out = False
        self.is_playing_mod = False
        self.is_playing_orig = False

        if len(self.procs) > 0:
            [self.Log(f"terminate {p.pid}") for p in self.procs if p]
            [p.terminate() for p in self.procs if p]

        #self.procs = list()
        _lout = "doStop"
        if self.outsound:
            self.outsound.stop()
            _lout += " OUT"

        if self.modsound:
            self.modsound.stop()
            _lout += " MOD"

        self.Log(_lout)


    ############################################################################
    ############################################################################

    @property
    def CfgDict(self):
        return dict(
            pos0=self.pos0,
            pos1=self.pos1,
            bpm=self.bpm,
            shift_tempo=self.shift_tempo,
            ctrl_ch=self.ctrl_ch,
            #infile=self.infile,
            infile=(os.path.split(self.infile)[-1] if self.infile else self.infile),
            lock_length=self.lock_length,
            lock_length_switch=self.lock_length_switch,
            retrigger=self.retrigger,
            )

    @CfgDict.setter
    def CfgDict(self, cfg):
        _float_attrs = ['bpm', 'shift_tempo', 'lock_length', 'pos0', 'pos1']
        for k in cfg.keys():
            assert(hasattr(self, k))
            setattr(self, k, float(cfg[k]) if k in _float_attrs else cfg[k])


    def CfgLoad(self):  
        self.Log("loading cfg")
        self.CfgDict = CFGLOAD(self.slotname)
        #CFGLOAD(self, self.slotname)

    def CfgSave(self):
        _cfgdict = self.CfgDict
        self.slotnum == self.ctrl_ch and _cfgdict.pop('ctrl_ch')
        _data = CFGSAVE(self.slotname, _cfgdict, cfgdict_default=DEFAULT_CFG_DICT)
        _data and self.Log(f"saved config: {_data}", level='visual')
        self.Log(f"saved config: {_data}", level='debug')

        #_cfgdict = None     ## unneccessary but i dont like it saving default ch!
        #if self.slotnum == self.ctrl_ch:
        #    _cfgdict = self.CfgDict
        #    _cfgdict.pop('ctrl_ch')
        #    CFGSAVE(self, self.slotname, cfgdict=_cfgdict)
        #else:
        #    CFGSAVE(self, self.slotname)


    ############################################################################
    ############################################################################

    @property
    def PitchObj(self):
        if not hasattr(self, '_PitchObj'):
            self._PitchObj = None

        return self._PitchObj

    @PitchObj.setter
    def PitchObj(self, ptype):
        _infile = self.outfile if (self.bpm == self.shift_tempo) else self.modfile
        if os.path.isfile(_infile):
            self._PitchObj = None


            _Class = PitchesSlicer
            self.Log(f"instantiating: {_Class}")

            self._PitchObj = _Class(
                infile=_infile, 
                bpm=self.bpm, 
                shift_tempo=self.shift_tempo,
                ctrl_ch=self.slotnum,
                Log=self._Log,
                )

            self.Log(f"instantiated: {self._PitchObj}")


    def SetupPitchObj(self):
        if self.PitchObj:
            self.PitchObj.Slice()
        else:
            #_infile = self.outfile if (self.bpm == self.shift_tempo) else self.modfile
            self.PitchObj = PitchesSlicer#(
                #infile=_infile, 
                #bpm=self.bpm, 
                #shift_tempo=self.shift_tempo,
                #ctrl_ch=self.slotnum,
                #Log=self.Log,
                #)

    ############################################################################
    ############################################################################

    def parse_argv(self, argv):
        print(f"parse_argv: START from {argv[0]}")
        parser = argparse.ArgumentParser(
                description="cmd line options for standalone wcSlot demo")

        parser.add_argument('-0', '--pos0', dest='pos0', type=str, help='pos0')
        parser.add_argument('-1', '--pos1', dest='pos1', type=str, help='pos1')
        parser.add_argument('-b', '--bpm', dest='bpm', type=str, help='bpm')
        parser.add_argument('-s', '--shift', dest='shift', type=str, help='shift')
        parser.add_argument('-i', '--infile', dest='infile', type=str, help='infile, to segment')

        return parser.parse_args(argv[1:])


    def as_cli(self):
        def _print(txt):
            print(f"\033[33m{txt}\033[0m", file=sys.stderr)

        args = self.parse_argv(sys.argv)
        self.slotnum = 99

        if args.pos0:   self.pos0 = float(args.pos0)
        if args.pos1:   self.pos1 = float(args.pos1)
        if args.infile: self.infile = args.infile
        _print(f"{self}")
        if not args.infile:
            _print("no infile")
            return

        _print("DOCUT out")
        _print(f"in:  {self.infile}")
        _print(f"out: {self.outfile}")
        self.doCut3_out(mod=False)

        if args.bpm:    self.bpm = float(args.bpm)
        if args.shift:  self.shift_tempo = float(args.shift)
        if args.bpm or args.shift:
            _print(f"{self}")

            _print("DOCUT mod")
            _print(f"in:  {self.infile}")
            _print(f"out: {self.modfile}")
            self.doCut3_out(mod=True)

        norm_file = "/tmp/wav_out/NORM_OUT.wav"
        _print("NORMALIZE:")
        _print(f"in:  {self.outfile}")
        _print(f"out: {norm_file}")
        ## need to put this after the Cutter automatically
        NORMALIZE(self.outfile, norm_file)
        
        if args.bpm or args.shift:
            norm_file = "/tmp/wav_out/NORM_MOD.wav"
            _print("NORMALIZE:")
            _print(f"in:  {self.modfile}")
            _print(f"out: {norm_file}")
            NORMALIZE(self.modfile, norm_file)


