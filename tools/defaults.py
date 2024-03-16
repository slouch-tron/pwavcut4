#!/bin/env python3
import os
import sys
import curses
import platform
import yaml


## ENV
DEBUG       = int(os.environ.get('DEBUG', 1))
DBCOL       = "33;2"
TRANSPARENT = int(os.environ.get('TRANSPARENT', 1))
CFGFILE     = os.environ.get('CFGFILE', None)

#DEFAULT_MIDI_LISTEN_CH      = 13
#DEFAULT_MIDI_LISTEN_CH_OUT  = 13
#DEFAULT_MIDI_LISTEN_CH_MOD  = 14
#DEFAULT_MIDI_LISTEN_CH_KIT  = 15

## Paths
DIR_BASE = "/tmp"
DEFAULT_WAV_IN_DIR  = os.path.join(DIR_BASE, 'wav_in')
DEFAULT_WAV_OUT_DIR = os.path.join(DIR_BASE, 'wav_out')
DEFAULT_SRC_OUT_DIR = os.path.join(DIR_BASE, 'source_out')
DEFAULT_CONVERT_DIR = os.path.join(DIR_BASE, 'wav_convert')

CFG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cfg'))
#LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../log'))
DEFAULT_CFGFILE = os.path.join(CFG_PATH, "cfg.yml")

## What to run on/with
OK_FILE_TYPES   = ['.wav', '.mp3', '.mp4', '.ogg']
OK_ARCHS        = ['armv7l', 'x86_64', 'aarch64']   ## RPI4 uses 'aarch64', old one is 'armv7l'?


## Required
assert(sys.version_info.major == 3)
assert(os.path.isdir(DIR_BASE))
assert(platform.machine() in OK_ARCHS)

## SETUP base cfgfile and load globals from it
##  some messy stuff but maybe we do want to run/check it every time
######################################################################
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

## if we really need to slot in a new DIR_BASE,
## just do it here in this file
_DEFAULT_DIRS = dict(
    DIR_BASE="/tmp",
    WAV_IN=os.path.join(DIR_BASE, 'wav_in'),
    WAV_OUT=os.path.join(DIR_BASE, 'wav_out'),
    SRC_OUT=os.path.join(DIR_BASE, 'source_out'),
    WAV_CONVERT=os.path.join(DIR_BASE, 'wav_convert'),
    )

_DEFAULT_CFG = dict(
    CTRL=dict(
        CCS=_DEFAULT_MIDI_CCS,
        CHS=_DEFAULT_MIDI_CHS,
        supported_filetypes=OK_FILE_TYPES,
        supported_archs=OK_ARCHS,
        ),
    DIRS=_DEFAULT_DIRS,
    )

## Stuff that happens up-front no matter what
## No harm in asserting all the directories exist
## Will we ever really benefit from making it portable?
## Or is it better to bury all this deep inside the class?
## Will we ever try to rapidly switch base dirs?
######################################################################
def pr_debug(txt):
    if DEBUG:
        _file = os.path.splitext(os.path.split(__file__)[-1])[0]
        print(f"\033[%sm{_file} | {txt}\033[0m" %DBCOL, file=sys.stderr)

def cfg2str(cfgdict):
    return str(cfgdict).replace(' ', '').replace("'", '"')

pr_debug(f"DEBUG={DEBUG}")

## default directories, cfgfile
######################################################################
for DIR in [
    DEFAULT_WAV_IN_DIR, DEFAULT_WAV_OUT_DIR, 
    DEFAULT_SRC_OUT_DIR, DEFAULT_CONVERT_DIR,
    CFG_PATH,
    ]:
    if not os.path.isdir(DIR):
        pr_debug(f"MAKE_DEFAULT_DIRS | make {DIR}")
        os.system(f"mkdir {DIR}")


if not os.path.isfile(DEFAULT_CFGFILE):
    pr_debug(f"making default cfg file {DEFAULT_CFGFILE}")
    with open(DEFAULT_CFGFILE, 'w') as fp:
        yaml.dump(_DEFAULT_CFG, fp)

## load config from file
######################################################################
_FILE_CFG = dict()
_cfgfile = CFGFILE if CFGFILE else DEFAULT_CFGFILE
pr_debug(f"loading cfg file {_cfgfile}")

if os.path.isfile(_cfgfile):
    with open(_cfgfile, 'r') as fp:
        _FILE_CFG = yaml.full_load(fp)
else:
    print(f"\033[31mno file '{_cfgfile}', deliberate exception", file=sys.stderr)
    raise FileNotFoundError
    sys.exit()


## set globals from config.  previous defaults preserved as '_' attrs
######################################################################
_CTRL = _FILE_CFG['CTRL']
if 'CHS' in _CTRL:
    DEFAULT_MIDI_LISTEN_CH_OUT = _CTRL['CHS'].get('OUT', _DEFAULT_MIDI_CHS['OUT'])
    DEFAULT_MIDI_LISTEN_CH_MOD = _CTRL['CHS'].get('MOD', _DEFAULT_MIDI_CHS['MOD'])
    DEFAULT_MIDI_LISTEN_CH_KIT = _CTRL['CHS'].get('KIT', _DEFAULT_MIDI_CHS['KIT'])
    DEFAULT_MIDI_LISTEN_CH = DEFAULT_MIDI_LISTEN_CH_OUT

DEFAULT_MIDI_CCS = dict()
if 'CCS' in _CTRL:
    for k, v in _DEFAULT_MIDI_CCS.items():
        DEFAULT_MIDI_CCS.update({ k : v })
        if k in _CTRL['CCS']:
            _val = _CTRL['CCS'][k]
            if _val != v:     ## non-default
                print(f"cfgfile: {k}={_val}, vs default={v}")
                DEFAULT_MIDI_CCS.update({ k : _CTRL['CCS'][k] })

## Best way to 'communicate' with the rest of the module..
## to import globals like DEFAULT_CHANNEL, or a dict like CFG_DICT.get('default_channel')
######################################################################
LOADED_CFG = _FILE_CFG  
pr_debug(cfg2str(LOADED_CFG))


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



if __name__ == '__main__':
    cfg = _FILE_CFG
    ccc = cfg2str(cfg)
    print(ccc)




