#!/bin/env python3
import os
import sys
import argparse
import shlex, subprocess

from enum import Enum, auto
from .utils import INFILE_CONVERT
from .defaults import DEFAULT_WAV_IN_DIR


DEFAULT_DEST_DIR = "/tmp/wav_in/"
DEFAULT_CONVERT_DIR = "/tmp/wav_convert/"
CFORMAT = "FILE_{:04d}.wav"


class States(Enum):
    INIT        = auto()
    DOWNLOAD    = auto()
    CONVERT     = auto()
    READY       = auto()


class InfileGetter():
    ''' Get file with download, link, name, put into 'filename',
        Save to Convert dir, with source filename.
        Convert file to FILE_000.wav, in WAV_IN for the sampler.
    '''
    STATES      = States
    DEST_DIR    = DEFAULT_WAV_IN_DIR
    CONVERT_DIR = DEFAULT_CONVERT_DIR

    not os.path.isdir(CONVERT_DIR) and os.mkdir(CONVERT_DIR)

    def __init__(self, filename):
        self.filename = filename




    def __str__(self):
        return " | ".join([
            self.__class__.__name__,
            self.state.name,
            f"{self.filename}",
            self.filename_dest,
            f"{self.lastcmd}",
            ])

    @property
    def state(self):
        if not hasattr(self, '_state'):
            self._state = self.STATES.INIT

        if os.path.isfile(self.filename_dest):
            self._state = self.STATES.READY
        elif self._state == self.STATES.DOWNLOAD:
            assert(self.proc)
            _poll = self.proc.poll()
            if _poll == None:   ## still running
                print("RUN")
                pass
            elif _poll == 0:    ## DL done
                print("DONE!")
                self._state = self.STATES.CONVERT
                self.InfileImport()
            else:
                print(f"FAIL, poll={_poll}")
                sys.exit()


        return self._state

    @property
    def filename(self):
        if not hasattr(self, '_filename'):
            self._filename = None

        return self._filename

    @property
    def filename_dest(self):
        assert(os.path.isdir(self.DEST_DIR))
        for f in range(99):
            _outfile = os.path.join(f"IMPORT_{f:03d}.wav")
            if os.path.isfile(_outfile):
                continue

            return _outfile


    def InfileImport(self):
        INFILE_CONVERT(self.filename, self.filename_dest)
        if os.path.isfile(self.filename_dest):
            self._filename = self.filename_dest


    @property
    def lastcmd(self):
        if not hasattr(self, '_lastcmd'):
            self._lastcmd = None

        return self._lastcmd


    @property
    def proc(self):
        if not hasattr(self, '_proc'):
            self._proc = None

        return self._proc

    @proc.setter
    def proc(self, cmd):

        self.proc

        if not cmd:
            self._proc = cmd
        else:
            if self._proc:
                self._proc.terminate()
                self._proc = None
                print("terminated previous proc")

            self._lastcmd = cmd
            self._proc = subprocess.Popen(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                )


    def Update(self):
        self.state


    def TestDL(self, src="rpi5:Music/FFSBSL.mp3"):
        self._state = self.STATES.DOWNLOAD
        self.proc = f"scp {src} {self.CONVERT_DIR}"


    def TestYTDL(self, link):
        self._state = self.STATES.DOWNLOAD
        self.proc = f"cd {self.CONVERT_DIR}; youtube-dl {link}"



    def parse_argv(self, argv):
        parser = argparse.ArgumentParser(
            description=f"cmd line options for {self.__class__.__name__} demo")
        parser.add_argument('-i', '--infile', dest='infile', type=str, help='infile')
        args = parser.parse_args(argv[1:])
        return args



