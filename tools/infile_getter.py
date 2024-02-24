#!/bin/env python3
import os
import sys
import argparse
import shlex, subprocess
import hashlib      ## non colliding filenames
import time

from enum import Enum, auto
#from .utils import INFILE_CONVERT   
from .defaults import DEFAULT_WAV_IN_DIR

DEBUG       = int(os.environ.get('DEBUG', 1))
RECOPY      = int(os.environ.get('RECOPY', 1))
RECONVERT   = int(os.environ.get('RECONVERT', 1))

DEFAULT_DEST_DIR    = "/tmp/wav_in/"
DEFAULT_CONVERT_DIR = "/tmp/wav_convert/"


class States(Enum):
    INIT        = auto()
    COPY        = auto()
    CONVERT     = auto()
    READY       = auto()
    ERROR       = auto()

class CopyModes(Enum):
    YTDL    = auto()
    SCP     = auto()
    FILE    = auto()
    HTTP    = auto()


class InfileGetter():
    ''' Get file with download, link, name, 
        Convert file to FILE_000.wav, in WAV_IN for the sampler.
    '''
    STATES      = States
    MODES       = CopyModes
    DEST_DIR    = DEFAULT_WAV_IN_DIR
    CONVERT_DIR = DEFAULT_CONVERT_DIR

    not os.path.isdir(CONVERT_DIR) and os.mkdir(CONVERT_DIR)

    def __init__(self, **kwa):
        self.convert_target = kwa.get('convert_target', None)
        self.copy_target    = kwa.get('copy_target', None)
        self.uri            = kwa.get('uri', None)
        self.errors         = []
        self.proc_start     = None
        self.last_cmd       = None


    def __str__(self):

        return " | ".join([
            self.__class__.__name__,
            self.state.name,
            str(self.uri),
            str(self.errors),
            "{:6.2f} sec".format(time.time() - self.proc_start) if self.proc_start else '-',
            ])


    @property
    def state(self):
        if not hasattr(self, '_state'):
            self._state = self.STATES.INIT

        if self._state == self.STATES.ERROR:
            return self._state

        if self._state == self.STATES.COPY:
            _poll = self.proc.poll()
            if _poll == None:   ## still running
                pass
            elif _poll == 0:    ## good result
                self.proc_start = None
                self._state = self.STATES.CONVERT
                self.Convert()
            else:
                self.errors.append(f"FAIL, proc poll={_poll}")
                self._state = self.STATES.ERROR

        elif self._state == self.STATES.CONVERT:
            _poll = self.proc.poll()
            if _poll == None:
                pass
            elif _poll == 0: 
                self.proc_start = None
                self.proc = None
                self._state = self.STATES.READY
            else:
                self.errors.append(f"FAIL, proc poll={_poll}")
                self._state = self.STATES.ERROR

        elif self._state == self.STATES.READY:
            if not os.path.isfile(self.convert_target):
                self.errors.append(f"was READY but file went missing: '{self.convert_target}'")
                self._state = self.STATES.ERROR

        return self._state


    @property
    def proc(self):
        if not hasattr(self, '_proc'):
            self._proc = None

        return self._proc

    @proc.setter
    def proc(self, cmd):

        self.proc

        if not cmd:
            self._proc = False
            #self.last_cmd = None

        else:
            if self._proc:
                self._proc.terminate()
                self._proc = None
                #print("terminated previous proc")

            self.last_cmd = cmd
            self._proc = subprocess.Popen(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                )
            
            self.proc_start = time.time()
            DEBUG and print(f"\033[33m## {cmd}\033[0m", file=sys.stderr)


    def Convert(self, reconvert=False):
        def _print(txt, err=0):
            DEBUG and print(f"\033[33mConvert | {txt}\033[0m", file=sys.stderr)
            err and self.errors.append(err)

        if os.path.isfile(self.copy_target):
            _reconvert = reconvert or RECONVERT
            _print(f"{self.convert_target}")
            _print(f"isfile={os.path.isfile(self.convert_target)}, reconvert={_reconvert}")
            _cmd = "sleep 0.3"
            if _reconvert or not os.path.isfile(self.convert_target):
                _cmd = 'ffmpeg -y -i "{}" -ar 44100 -map_metadata -1 "{}"'.format(
                    self.copy_target, self.convert_target)

            self.proc = _cmd
            return True

        else:
            _print(f"no file copy_target='{self.copy_target}'", err=1)


    def _WebCopy(self, mode=CopyModes.SCP, recopy=False):
        def _print(txt, err=0):
            DEBUG and print(f"\033[33mCopy | {txt}\033[0m", file=sys.stderr)
            err and self.errors.append(err)

        _recopy = recopy or RECOPY
        _print(f"mode={str(mode)}, recopy={_recopy}")

        if self.uri:
            _filename           = hashlib.md5(self.uri.encode()).hexdigest() + '.wav'
            self.copy_target    = os.path.join(self.CONVERT_DIR, "_" + _filename)
            self.convert_target = os.path.join(self.DEST_DIR, _filename)

            _dest = self.copy_target
            _cmd = {
                self.MODES.SCP  : f"scp {self.uri} {_dest}",
                self.MODES.FILE : f"cp {self.uri} {_dest}",
                self.MODES.YTDL : f"youtube-dl {self.uri} -x --audio-format wav -o {_dest}",
                self.MODES.HTTP : f"wget -O {_dest} {self.uri}",
                }.get(mode, None)

            if _cmd:
                _print(f"{self.copy_target}")
                _print(f"isfile={os.path.isfile(self.copy_target)}")
                if not _recopy and os.path.isfile(self.copy_target):
                    _cmd = "sleep 0.2"

                self.proc = _cmd
                self._state = self.STATES.COPY
                return True

            else:
                _print(f"invalid mode='{mode}'", err=1)

        else:
            _print(f"invalid uri='{self.uri}'", err=1)

        self._state = self.STATES.ERROR


    def Copy_SCP(self):        return self._WebCopy(self.MODES.SCP)
    def Copy_YTDL(self):       return self._WebCopy(self.MODES.YTDL)
    def Copy_FILE(self):       return self._WebCopy(self.MODES.FILE)
    def Copy_HTTP(self):       return self._WebCopy(self.MODES.HTTP)


    def parse_argv(self, argv):
        parser = argparse.ArgumentParser(
            description=f"cmd line options for {self.__class__.__name__} demo")

        parser.add_argument('-f', dest='file', type=str, help='filename to import')
        parser.add_argument('-y', dest='ytdl', type=str, help='youtube-dl')
        parser.add_argument('-s', dest='scp', type=str, help='scp')
        parser.add_argument('-w', dest='wget', type=str, help='wget')

        args = parser.parse_args(argv[1:])
        return args


    def as_cli(self):
        args = self.parse_argv(sys.argv)
        
        if   args.file:         self.uri = args.file;   self.Copy_FILE()
        elif args.ytdl:         self.url = args.ytdl;   self.Copy_YTDL()
        elif args.scp:          self.uri = args.scp;    self.Copy_SCP()
        elif args.wget:         self.uri = args.wget;   self.Copy_HTTP()
        else:   
            print("\033[34m use '-h' to see options\033[0m", file=sys.stderr)
            return

        return True


