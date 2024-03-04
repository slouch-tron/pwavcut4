#!/bin/env python3
import os
import sys
import argparse
import shlex, subprocess
import hashlib      ## non colliding filenames
import time
import curses
import yaml

from enum import Enum, auto
from .utils import INFILE_CONVERT_CMD_FMT   
from .defaults import DEFAULT_WAV_IN_DIR, CFG_PATH, pr_debug, DEBUG
from .log_setup import GET_LOGGER
from .cfg_setup import CFGSAVE, CFGLOAD

#RECOPY      = int(os.environ.get('RECOPY', 1))
#RECONVERT   = int(os.environ.get('RECONVERT', 1))

DEFAULT_DEST_DIR    = "/tmp/wav_in/"
DEFAULT_CONVERT_DIR = "/tmp/wav_convert/"


class States(Enum):
    INIT        = auto()    ## maybe theres 'uri', could be link or filename
    COPY        = auto()    ## copy working (wget, local FS copy), save to copy_target
    CONVERT     = auto()    ## convert working, ffmpeg convert copy_target to convert_target
    READY       = auto()    ## ready for use by pwavcut/etc
    ERROR       = auto()    ## check self.errors
    CANCEL      = auto()    ## was cancelled

class CopyModes(Enum):
    YTDL    = auto()
    SCP     = auto()
    FILE    = auto()
    HTTP    = auto()

STATECOLORS = dict(
    INIT    = 28,
    COPY    = 190,
    CONVERT = 190,
    READY   = 40,
    ERROR   = 124,
    CANCEL  = 186,
    )

BLINKCOLORS = [56, 66, 76, 86]
BLINKCOLORS = [232, 238, 244, 250, 255, 231, 230, 229, 228, 227, 226, 225, 232, 232, 232, 232]
BLINKCOLORS = [226, 232, 227, 232, 228, 232, 229, 232, 230, 232, 231, 232]

DEFAULT_MODE_IX = 1


class InfileGetter():
    ''' Get file with download, link, name, 
        Convert file to FILE_000.wav, in WAV_IN for the sampler.
    '''
    ID          = 0
    STATES      = States
    MODES       = CopyModes
    DEST_DIR    = DEFAULT_WAV_IN_DIR
    CONVERT_DIR = DEFAULT_CONVERT_DIR
    not os.path.isdir(CONVERT_DIR) and os.mkdir(CONVERT_DIR)
    COORDS_INFO = (20, 48, 22, 61)
    DEFAULT_CFG = dict(
        copy_mode_val=DEFAULT_MODE_IX, 
        recopy=True, reconvert=True, 
        uri=None,
        )


    def __init__(self, **kwa):
        self.id = InfileGetter.ID
        InfileGetter.ID += 1
        self.devname        = f"{self.__class__.__name__}{self.id:02d}"

        self.convert_target = kwa.get('convert_target', None)
        self.copy_target    = kwa.get('copy_target', None)
        self.uri            = kwa.get('uri', None)
        #self.stdscr         = kwa.get('stdscr', None)

        self.Log            = kwa.get('Log', print)
        self.logger         = kwa.get('logger', GET_LOGGER(appname=self.__class__.__name__))
        self.errors         = []
        self.proc_start     = None
        self.proc_end       = None
        self.last_cmd       = None
        self.proc_out       = None
        self.proc_err       = None

        self.recopy     = int(os.environ.get('RECOPY', 1))
        self.reconvert  = int(os.environ.get('RECONVERT', 1))

        self.copy_mode      = self.MODES.FILE


    def __str__(self):

        return " | ".join([
            self.__class__.__name__,
            self.state.name if self.state else "",
            str(self.uri),
            f"err: ({len(self.errors)})",
            f"{self.proc_runtime:6.2f} sec" if self.proc_runtime else '-',
            ])

    def __del__(self):
        self.proc = False

    #def Log(self, msg, level='debug'):
    #    _func = getattr(self.logger, level, None) or self.logger.debug
    #    _func(msg)


    def logDecor(func, *aa, **kwa):
        def inner(self, *aa, **kwa):
            _head = f"{self.__class__.__name__}.{func.__name__}("
            _ostr = _head
            _ostr += f"{str(aa)}" if aa else ""
            _ostr += f", {str(kwa)}" if kwa else ""
            _ostr += ")"
            self.Log(_ostr)

            _start  = time.time()
            _return = func(self, *aa, **kwa)
            _finish = (time.time() - _start) #* 1000

            ## makes no sense for proc-starter function that returns immediately
            #_ostr = _head + f", return '{_return}', {_finish:.2f} sec elapsed"
            #self.Log(_ostr)
            return _return

        return inner


    @property
    def state(self):
        if not hasattr(self, '_state'):
            self._state = self.STATES.INIT
            self.Log(f"{self.__class__.__name__}.state = {self._state.name}")
            #self.Log(f"state = {self._state}")

        return self._state 

    @state.setter
    def state(self, val):
        _old = self.state 
        self._state = val

        if self._state != _old:
            self.Log(f"{self.__class__.__name__}.state: {_old.name}->{self._state.name}")


    def Update(self):
        if self.state in [self.STATES.ERROR, self.STATES.CANCEL, self.STATES.INIT]:
            #self.proc = False
            return 

        if self.state in [self.STATES.COPY, self.STATES.CONVERT]:
            _poll = self.proc.poll()
            if _poll == None:   ## still running
                return

            if _poll != 0:
                self.Log(f"{self.state.name.upper()} FAIL, proc poll={_poll}")
                self.state = self.STATES.ERROR
                #return

            self.Log(" ".join([
                f"{self.state.name.upper()} proc poll={_poll}",
                "{:5.2f} sec elapsed".format(self.proc_runtime or 0),
                ]))

            if _poll == 0:    ## good result
                if self.state == self.STATES.COPY:
                    self.state = self.STATES.CONVERT
                    self.Convert()
                elif self.state == self.STATES.CONVERT:
                    self.state = self.STATES.READY
                else:
                    raise TypeError

        elif self.state == self.STATES.READY:
            if not os.path.isfile(self.convert_target):
                self.Log("state was READY but file went missing: '{self.convert_target}'")
                #self.errors.append(f"was READY but file went missing: '{self.convert_target}'")
                self.state = self.STATES.ERROR

        else:
            raise TypeError



    @property
    def copy_mode(self):
        if not hasattr(self, '_copy_mode'):
            self._copy_mode = self.MODES.FILE

        return self._copy_mode

    @copy_mode.setter
    def copy_mode(self, val):
        if not isinstance(val, self.MODES):
            self.Log(f"copy_mode.setter: value '{val}' is not {self.MODES}")
            raise TypeError     ## value is not instance of 'CopyMode'?

        self._copy_mode = val

    @property
    def copy_mode_val(self):
        return self.copy_mode.value

    @copy_mode_val.setter
    def copy_mode_val(self, ix):
        self.copy_mode = self.MODES(ix)

    #######################################################################

    @property
    def proc(self):
        if not hasattr(self, '_proc'):
            self._proc = None

        return self._proc

    @proc.setter
    def proc(self, cmd):

        #self.proc
        if self.proc:   
            if self.proc_runtime:
                self.Log(f"proc.setter | end after {self.proc_runtime:5.2f} sec")

            self._proc.terminate()
            self._proc = None

        if not cmd:
            self._proc = False
            #self.last_cmd = None

        else:

            self.last_cmd = cmd
            self._proc = subprocess.Popen(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                )
            
            self.proc_start = time.time()
            self.Log("proc.setter CMD")
            self.Log(f"\t{cmd}")

    @property
    def proc_runtime(self):
        if self.proc and self.state in [self.STATES.COPY, self.STATES.CONVERT]:
            return time.time() - self.proc_start


    ## this seems to 'block', oh well do we or do we not want to see the output?
    ## (in a screen view panel thing?  Not.)
    def pr_poll(self):
        if not self.proc:
            return 
        

        p = self.proc
        _recent_output = False
        for line in list(iter(p.stdout.readline, "")):
            if line == b'':
                continue
            print(f"\033[36;1m{line}\033[0m", end="")
            _recent_output = True

        for line in iter(p.stderr.readline, ""):
            if line == b'':
                continue
            print(f"\033[33;2m{line}\033[0m", end="")
            _recent_output = True


    #######################################################################

    @logDecor
    def _WebCopy(self, mode=CopyModes.SCP):
        def _print(txt, err=0):
            self.Log(f"Copy | {txt}")
            err and self.errors.append(txt)

        #_recopy = recopy or RECOPY
        _recopy = self.recopy
        _print(f"mode={str(mode)}, recopy={_recopy}")

        _YTDL = "youtube-dl"
        _YTDL = "/tmp/yt-dlp/yt-dlp.sh"

        if self.uri:
            _filename           = hashlib.md5(self.uri.encode()).hexdigest() + '.wav'
            self.copy_target    = os.path.join(self.CONVERT_DIR, "_" + _filename)
            self.convert_target = os.path.join(self.DEST_DIR, _filename)

            _dest = self.copy_target
            _cmd = {
                self.MODES.SCP  : f"scp {self.uri} {_dest}",
                self.MODES.FILE : f"cp {self.uri} {_dest}",
                #self.MODES.YTDL : f"youtube-dl {self.uri} -x --audio-format wav -o {_dest}",
                self.MODES.YTDL : f"{_YTDL} {self.uri} -x --audio-format wav -o {_dest}",
                self.MODES.HTTP : f"wget -O {_dest} {self.uri}",
                }.get(mode, None)

            if _cmd:
                _print(f"FROM: {self.uri}")
                _print(f"TO:   {self.copy_target} (isfile={os.path.isfile(self.copy_target)})")
                if not _recopy and os.path.isfile(self.copy_target):
                    _cmd = "sleep 0.01"

                self.proc = _cmd
                self.state = self.STATES.COPY
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
    def Copy(self):            return self._WebCopy(self.copy_mode)


    @logDecor
    def Convert(self, reconvert=False):
        def _print(txt, err=0):
            self.Log(f"Convert | {txt}         ")
            err and self.errors.append(err)

        if os.path.isfile(self.copy_target):
            #_reconvert = reconvert or RECONVERT
            _reconvert = self.reconvert
            _print(f"reconvert={_reconvert}")
            _print(f"FROM: {self.copy_target}")
            _print(f"TO:   {self.convert_target} (isfile={os.path.isfile(self.convert_target)})")
            _cmd = "sleep 0.01"      ## cmd for proc that does nothing!
            if _reconvert or not os.path.isfile(self.convert_target):
                _cmd = INFILE_CONVERT_CMD_FMT.format(self.copy_target, self.convert_target)

            self.proc = _cmd
            return True

        else:
            _print(f"no file copy_target='{self.copy_target}'", err=1)


    def Cancel(self):
        self.Log(f"cancel running {self.__class__.__name__}")
        self.proc = False
        self.proc_start = None
        self.state = self.STATES.CANCEL

    #######################################################################

    @property
    def InfoWin(self):
        if not hasattr(self, '_InfoWin'):
            self._InfoWin = None
            self.InfoWin = None

        return self._InfoWin

    @InfoWin.setter
    def InfoWin(self, coords):
        _coords = coords if coords != None else self.COORDS_INFO
        self._InfoWin = curses.newwin(*_coords)
        #self._InfoWin.keypad(1)
            

    @property
    def StateColors(self):
        if not hasattr(self, '_StateColors'):
            self._StateColors = dict()

    def Draw(self, **kwa):
        blink = kwa.get('blink', BLINKCOLORS)

        _time = time.time()
        #_bix  = int(_time * 100) % len(blink)
        #_bcol = curses.color_pair(_bix)
        #_attr = curses.color_pair(86)
        _attr = curses.color_pair(56)

        _ee = "elapsed:    "
        _ee += f"{self.proc_runtime:6.2f} sec" if self.proc_runtime else "none          "

        _cc = 'None'
        _cv = 'None'
        if self.copy_target:    _cc = os.path.splitext(os.path.split(self.copy_target)[-1])[0]
        if self.convert_target: _cv = os.path.splitext(os.path.split(self.convert_target)[-1])[0]

        _attr2 = _attr
        if self.state in [self.STATES.CONVERT, self.STATES.COPY]:
        #if False:
            _bix  = int(_time * 100) % len(blink)
            _bcol = curses.color_pair(_bix)
            _attr2 = curses.color_pair(_bix)
        else:
            _col = STATECOLORS.get(self.state.name, None)
            if _col:
                _attr2 = curses.color_pair(_col)

        self.InfoWin.addstr(0, 0, self.__class__.__name__, _attr)
        self.InfoWin.addstr(1, 0, "state:    ", _attr)
        #self.InfoWin.addstr(1, 0, "state:                ", _attr)
        self.InfoWin.addstr(1, 10, self.state.name + "  ", _attr2)
        self.InfoWin.addstr(1, 10, self.state.name + "  ", _attr2)
        _yy = 2

        _lines = [
            f"mode:     {self.copy_mode.name}     ",
            f"recopy:   {self.recopy == 1}",
            f"reconv:   {self.reconvert == 1}",
            f"uri:      {str(self.uri)}",
            #f"copy:     {_cc}",
            f"convert:  {_cv[:10]}",
            f"dest_dir: {self.DEST_DIR}",
            _ee,
            f"errors:   {len(self.errors)}",
            ]

        len(self.errors) > 0 and [_lines.append(x) for x in self.errors]

        for ix, line in enumerate(_lines):
            self.InfoWin.addstr(ix+_yy, 0, str(line), _attr)



    #######################################################################
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
        elif args.ytdl:         self.uri = args.ytdl;   self.Copy_YTDL()
        elif args.scp:          self.uri = args.scp;    self.Copy_SCP()
        elif args.wget:         self.uri = args.wget;   self.Copy_HTTP()
        else:   
            print("\033[34m use '-h' to see options\033[0m", file=sys.stderr)
            return

        return True


    #def Initiate(self):

    def prompt_for_filename(self):
        def _print(txt):
            self.Log(f"prompt_for_filename: {txt}")

        if 'curses' in globals():
            curses.endwin()

        if self.state in [self.STATES.COPY, self.STATES.CONVERT]:
            _print(f"terminate proc still running, poll={self.proc.poll()}")
            self.Cancel()
            return

        if self.uri and not self.proc:
            _print(f"try Copy:{self.copy_mode.name}")
            self.Copy()
            return

        print(f"enter URI to import using {self.copy_mode.name} method")
        print("ctrl-C to reset to INIT state")
        print(f"Enter to use prev: '{self.uri}'")

        try:
            value = input((" "*20) + '> ')
            if value in ['\n', '']:
                if self.uri:    ## previously used or unset?
                    print()
                    _val = input(f"use prev '{self.uri}'?")
                    if _val not in ['\n', '']:
                        raise KeyboardInterrupt
            else:
                if not value:
                    return

                _value = str(value)
                _print(f"URI = '{_value}'")
                self.uri = _value
                self.state = self.STATES.INIT

        except KeyboardInterrupt:
            self.state = self.STATES.INIT
            _print("cancelled file prompt")
        except TypeError:
            _print(f"value must be string: '{value}'")
            

    ## config
    #######################################################################
    @property
    def cfg_filename(self):
        if not hasattr(self, '_cfg_filename'):
            _file = os.path.splitext(os.path.split(sys.argv[0])[1])[0] + ".yml"
            #self._cfg_filename = _file
            self._cfg_filename = os.path.join(CFG_PATH, _file)

        return self._cfg_filename

    @property
    def CfgDict(self):
        return dict(
            uri=self.uri,
            copy_target=self.copy_target,
            convert_target=self.convert_target,
            copy_mode_val=self.copy_mode_val,
            recopy=self.recopy,
            reconvert=self.reconvert,
            )

    def CfgSave(self):  CFGSAVE(self, self.devname)
    def CfgLoad(self):  CFGLOAD(self, self.devname)

    '''
    @property
    def uri(self):
        if not hasattr(self, '_uri'):
            self._uri = None
        return self._uri

    @uri.setter
    def uri(self, val):
        self._uri = val
    '''

    def CfgSave2(self):
        PREV = dict()
        DATA = dict()

        _condition = self.uri or self.copy_target or self.convert_target
        _condition          and DATA.update(dict(copy_mode=self.copy_mode.value))
        self.uri            and DATA.update(dict(uri=self.uri))
        self.copy_target    and DATA.update(dict(copy_target=self.copy_target))
        self.convert_target and DATA.update(dict(convert_target=self.convert_target))
        
        
        if DATA:
            ## collate w/ existing file data
            if os.path.isfile(self.cfg_filename):
                with open(self.cfg_filename, 'r') as cfgf:
                    PREV = yaml.full_load(cfgf)

                PREV.update({ self.__class__.__name__ : DATA})

            with open(self.cfg_filename, 'w') as cfgf:
                yaml.dump(PREV, cfgf)

    def CfgLoad2(self):
        DATA = dict()
        if os.path.isfile(self.cfg_filename):
            with open(self.cfg_filename, 'r') as cfgf:
                DATA = yaml.full_load(cfgf)

        _data = DATA.get(self.__class__.__name__, {})
        if _data:
            self.uri     = _data.get('uri', self.uri)
            self.copy_target    = _data.get('copy_target', self.copy_target)
            self.convert_target = _data.get('convert_target', self.convert_target)
            _val = _data.get('copy_mode', None)
            if _val: 
                self.copy_mode = self.MODES(_val)




