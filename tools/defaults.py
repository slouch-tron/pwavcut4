#!/bin/env python3
import os
import sys
assert(sys.version_info.major == 3)
import curses
import platform
import yaml
from enum import Enum

DEBUG = int(os.environ.get('DEBUG', 1))

DEFAULT_MIDI_LISTEN_CH      = 13
DEFAULT_MIDI_LISTEN_CH_OUT  = 13
DEFAULT_MIDI_LISTEN_CH_MOD  = 14
DEFAULT_MIDI_LISTEN_CH_KIT  = 15

DIR_BASE = "/tmp"
DEFAULT_WAV_IN_DIR  = os.path.join(DIR_BASE, 'wav_in')
DEFAULT_WAV_OUT_DIR = os.path.join(DIR_BASE, 'wav_out')
DEFAULT_SRC_OUT_DIR = os.path.join(DIR_BASE, 'source_out')
DEFAULT_CONVERT_DIR = os.path.join(DIR_BASE, 'wav_convert')

CFG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cfg'))
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../log'))
DEFAULT_CFGFILE = os.path.join(CFG_PATH, "cfg.yml")

OK_FILE_TYPES   = ['.wav', '.mp3', '.mp4', '.ogg']
OK_ARCHS        = ['armv7l', 'x86_64', 'aarch64']   ## RPI4 uses 'aarch64', old one is 'armv7l'?

## import to other places for consistency
DEBUG       = int(os.environ.get('DEBUG', 1))
TRANSPARENT = int(os.environ.get('TRANSPARENT', 1))


## SETUP base cfgfile and load globals from it
##  some messy stuff but maybe we do want to run/check it every time
_DEFAULT_MIDI_CHS = dict(
    OUT=15,
    MOD=14,
    KIT=13,
    )

_DEFAULT_MIDI_CCS = dict(
    volume=7,
    pan=10,
    ptr0=20,
    ptr1=21,
    ptr2=22,
    ptr3=23,
    fxn0=30,
    fxn1=31,
    fxn2=32,
    fxn3=33,
    )

_DEFAULT_CFG = dict(CTRL=dict(
    CHS=_DEFAULT_MIDI_CCS,
    CCS=_DEFAULT_MIDI_CHS,
    supported_filetypes=OK_FILE_TYPES,
    supported_archs=OK_ARCHS,
    ))

## put 'try' here to maybe give up on missing cfg file?  otherwise program wont start without
not os.path.isdir(CFG_PATH) and os.mkdir(CFG_PATH)
if not os.path.isfile(DEFAULT_CFGFILE):
    with open(DEFAULT_CFGFILE, 'w') as fp:
        yaml.dump(_DEFAULT_CFG, fp)

_FILE_CFG = dict()
with open(DEFAULT_CFGFILE, 'r') as fp:
    _FILE_CFG = yaml.full_load(fp)

_CTRL = _FILE_CFG['CTRL']
if 'CCS' in _CTRL:
    DEFAULT_MIDI_LISTEN_CH_OUT = _CTRL['CHS'].get('OUT', _DEFAULT_MIDI_CHS['OUT'])
    DEFAULT_MIDI_LISTEN_CH_MOD = _CTRL['CHS'].get('MOD', _DEFAULT_MIDI_CHS['MOD'])
    DEFAULT_MIDI_LISTEN_CH_KIT = _CTRL['CHS'].get('KIT', _DEFAULT_MIDI_CHS['KIT'])

DEFAULT_MIDI_CCS = dict()
if 'CHS' in _CTRL:
    for k, v in _DEFAULT_MIDI_CCS.items():
        DEFAULT_MIDI_CCS.update({ k : v })
        if k in _CTRL['CCS']:
            _val = _CTRL['CCS'][k]
            if _val != v:     ## non-default
                print(f"cfgfile: {k}={_val}, vs default={v}")
                DEFAULT_MIDI_CCS.update({ k : _CTRL['CCS'][k] })

print(DEFAULT_MIDI_LISTEN_CH_OUT)
print(DEFAULT_MIDI_CCS)
input()


## Enum is simple but DB is changeable if we are loading from a file
'''
from collections import namedtuple
DEFAULT_MIDI_CHS_TUP = namedtuple('CHS', ['OUT', 'MOD', 'KIT'])(15,14,13)
class DEFAULT_MIDI_CHS_ENUM(Enum):
    OUT = 15
    MOD = 14
    KIT = 13
'''


######################################################################
######################################################################
def CURSE_INIT(stdscr):
    ## dont see these 2 in p_wavcut3
    ## ok to do here, since 'global'?
    #curses.initscr()
    #curses.start_color()
    curses.init_color(0,0,0,0)
    curses.curs_set(0)
    curses.noecho()

    TRANSPARENT and curses.use_default_colors()

    for c in range(1, curses.COLORS):
        curses.init_pair(c, c, -1 if TRANSPARENT else 0)

    stdscr.nodelay(1)
    stdscr.keypad(1)
    return stdscr


def MAKE_DEFAULT_DIRS():
    pr_debug(f"MAKE DEFAULT_DIRECTORIES")

    for DIR in [
        DEFAULT_WAV_IN_DIR, 
        DEFAULT_WAV_OUT_DIR, 
        DEFAULT_SRC_OUT_DIR,
        CFG_PATH,
        LOG_PATH,
        ]:
        if not os.path.isdir(DIR):
            cmd = f"mkdir {DIR}"
            pr_debug(f"MAKE_DEFAULT_DIRS | {cmd}")
            os.system(cmd)




def GET_CFG(cfgfile=None, dump=False)->dict:   ## cfgfile = yaml filename string
    ''' 
        dump = write default_cfg to cfgfile (initialize the cfg file for editing)

        ## Q: is GLOBALS sort of same as passing a dictionary around?
        ## A: good for midi CCs or repetitively named tables.
        ##  itll be easy enough to edit in the cfgfile...
    '''

    def _print(txt):
        pr_debug(f"GET_CFG | {txt}")

    default_cfg = dict(
        DEFAULT_MIDI_CCS=DEFAULT_MIDI_CCS,
        DEFAULT_MIDI_CHS=DEFAULT_MIDI_CHS,
        )

    if cfgfile == True:
        cfgfile = DEFAULT_CFGFILE

    if cfgfile and os.path.isfile(cfgfile):
        _print(f"using cfgfile='{cfgfile}'")
        file_cfg = dict()
        with open(cfgfile, 'r') as fp:
            file_cfg = yaml.full_load(fp)

        for k, v in file_cfg.items():
            if k not in default_cfg:
                _print(f"new key  cfg['{k}'] (holds {type(v)})")
                default_cfg.update({ k : {} })

            if v != default_cfg.get(k, None):
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        if k2 not in default_cfg.get(k, []):
                            _print(f"new key  cfg[{k}]['{k2}'] (holds {type(v2)})")

                        if v2 != default_cfg.get(k, {}).get(k2, None):
                            _print(f"updating cfg[{k}][{k2}] : {v2}")
                            default_cfg[k].update({ k2 : v2 })

                        #default_cfg[k].update({ k2 : v2 })

                else:
                    _print(f"updating cfg[{k}] : {v} ({type(v)})")
                    default_cfg.update({ k : v})
            else:
                ## seeind this loading default_midi_chs 
                print("weird situaton?")
                print(" | ".join([str(x) for x in [k, v]]))

    elif dump:
        cfgfile = cfgfile or DEFAULT_CFGFILE
        _print(f"creating {cfgfile}")
        with open(cfgfile, 'w') as fp:
            yaml.dump(default_cfg, fp)

    else:
        _print("returning default_cfg from file unmodified")
        _print(default_cfg)
        
    return default_cfg


def CFG_LOAD_GLOB(cfg):
    if 'DEFAULT_MIDI_CHS' in cfg:
        print(cfg)
        global DEFAULT_MIDI_CHS
        DEFAULT_MIDI_CHS = cfg['DEFAULT_MIDI_CHS']
        global DEFAULT_MIDI_LISTEN_CH_OUT
        DEFAULT_MIDI_LISTEN_CH_OUT = DEFAULT_MIDI_CHS.get('listen', 2)
        global DEFAULT_MIDI_LISTEN_CH_MOD
        global DEFAULT_MIDI_LISTEN_CH_KIT
        DEFAULT_MIDI_LISTEN_CH_MOD = DEFAULT_MIDI_CHS.get('mod', DEFAULT_MIDI_LISTEN_CH_MOD)
        DEFAULT_MIDI_LISTEN_CH_KIT = DEFAULT_MIDI_CHS.get('kit', DEFAULT_MIDI_LISTEN_CH_KIT)
        print(DEFAULT_MIDI_LISTEN_CH_OUT)



    if 'DEFAULT_MIDI_CCS' in cfg:
        global DEFAULT_MIDI_CCS
        DEFAULT_MIDI_CCS = cfg['DEFAULT_MIDI_CCS']


######################################################################
######################################################################
def pr_debug(txt):
    if DEBUG:
        _file = os.path.splitext(os.path.split(__file__)[-1])[0]
        print(f"\033[33m{_file} | {txt}\033[0m", file=sys.stderr)


def cfg2str(cfgdict):
    return str(cfgdict).replace(' ', '').replace("'", '"')


## why not just have it always happen,
##  instead of burying it in a class property.
## class 'needs to know' but surely we can have some assumptions about a set-up env
MAKE_DEFAULT_DIRS()
assert(platform.machine() in OK_ARCHS)
if os.path.isfile(DEFAULT_CFGFILE):
    print("load cfg")
    CFG = GET_CFG(cfgfile=True)
    CFG_LOAD_GLOB(CFG)
else:
    print("new cfg")
    GET_CFG(dump=1)

input(DEFAULT_MIDI_LISTEN_CH_OUT)
if __name__ == '__main__':
    #cfg = GET_CFG(DEFAULT_CFGFILE)
    cfg = GET_CFG("./cfg/ttt.yml")
    #cfg = GET_CFG()
    ccc = cfg2str(cfg)
    print(ccc)




