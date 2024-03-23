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
DIR_BASE    = os.environ.get('DIR_BASE', "/tmp")

USE_TOPLEVEL_CONFIG_FILE = 0

## Paths
#DIR_BASE = "/tmp"
DEFAULT_WAV_IN_DIR  = os.path.join(DIR_BASE, 'wav_in')
DEFAULT_WAV_OUT_DIR = os.path.join(DIR_BASE, 'wav_out')
DEFAULT_SRC_OUT_DIR = os.path.join(DIR_BASE, 'source_out')
DEFAULT_CONVERT_DIR = os.path.join(DIR_BASE, 'wav_convert')

CFG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cfg'))
DEFAULT_CFGFILE = os.path.join(CFG_PATH, "cfg.yml")
CFG_FILENAME = os.path.join(
    CFG_PATH, os.path.splitext(os.path.split(sys.argv[0])[1])[0] + ".yml")

## What to run on/with
OK_FILE_TYPES   = ['.wav', '.mp3', '.mp4', '.ogg']
OK_ARCHS        = ['armv7l', 'x86_64', 'aarch64']   ## RPI4 uses 'aarch64', old one is 'armv7l'?

## Required
assert(sys.version_info.major == 3)
assert(os.path.isdir(DIR_BASE))
assert(platform.machine() in OK_ARCHS)

## SETUP default cfg, exists to check against whether used
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

_DEFAULT_CFG = dict(
    CTRL=dict(
        CCS=_DEFAULT_MIDI_CCS,
        CHS=_DEFAULT_MIDI_CHS,
        supported_filetypes=OK_FILE_TYPES,
        supported_archs=OK_ARCHS,
        ),
    )

## function needs to go up here if doing stuff in global scope
######################################################################
def pr_debug(txt):
    if DEBUG: 
        _file = os.path.splitext(os.path.split(__file__)[-1])[0]
        print(f"\033[%sm{_file} | {txt}\033[0m" %DBCOL, file=sys.stderr)

pr_debug(f"DEBUG={DEBUG}")

for DIR in [
    DEFAULT_WAV_IN_DIR, DEFAULT_WAV_OUT_DIR, 
    DEFAULT_SRC_OUT_DIR, DEFAULT_CONVERT_DIR,
    CFG_PATH,
    ]:
    if not os.path.isdir(DIR):
        pr_debug(f"MAKE_DEFAULT_DIRS | make {DIR}")
        os.mkdir(DIR)


## 240323 - set defaults in case we want to skip this whole crazy cfgfile thing
########################################################
DEFAULT_MIDI_LISTEN_CH_OUT  = _DEFAULT_MIDI_CHS['OUT']
DEFAULT_MIDI_LISTEN_CH_MOD  = _DEFAULT_MIDI_CHS['MOD']
DEFAULT_MIDI_LISTEN_CH_KIT  = _DEFAULT_MIDI_CHS['KIT']
DEFAULT_MIDI_LISTEN_CH      = DEFAULT_MIDI_LISTEN_CH_OUT
DEFAULT_MIDI_CCS            = _DEFAULT_MIDI_CCS

LOADED_CFG = _DEFAULT_CFG

if USE_TOPLEVEL_CONFIG_FILE:


    ## create default directories, cfgfile
    ######################################################################

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

    ## set globals from config. note missing, same, or different for debug 
    ######################################################################
    _CTRL = _FILE_CFG['CTRL']
    if 'CHS' in _CTRL:
        _CHS = _CTRL['CHS']
        DEFAULT_MIDI_LISTEN_CH_OUT = int(_CHS.get('OUT', _DEFAULT_MIDI_CHS['OUT']))
        DEFAULT_MIDI_LISTEN_CH_MOD = int(_CHS.get('MOD', _DEFAULT_MIDI_CHS['MOD']))
        DEFAULT_MIDI_LISTEN_CH_KIT = int(_CHS.get('KIT', _DEFAULT_MIDI_CHS['KIT']))
        DEFAULT_MIDI_LISTEN_CH = DEFAULT_MIDI_LISTEN_CH_OUT

        for k, v in _DEFAULT_CFG['CTRL']['CHS'].items():
            _v = _CHS.get(k, None)
            _txt = f"CHS.{k:8} "

            if _v == None:  _txt += f"{v:3} (default, not in cfgfile)"
            elif _v != v:   _txt += f"{_v:3} (non-default, vs '{v}' from cfgfile)"
            else:           _txt += f"{v:3}" ## pass

            pr_debug(_txt)


    DEFAULT_MIDI_CCS = dict()
    if 'CCS' in _CTRL:
        _CCS = _CTRL['CCS']
        for k, v in _DEFAULT_MIDI_CCS.items():
            DEFAULT_MIDI_CCS.update({ k : v })

            _txt = f"CCS.{k:8} "
            if k in _CCS:
                _val = _CCS[k]
                if _val != v:     ## non-default
                    _txt += f"{_val:3} (non-default, vs default '{v}')"
                    DEFAULT_MIDI_CCS.update({ k : _CCS[k] })
                else:
                    #continue
                    _txt += f"{v:3}"
            else:
                DEFAULT_MIDI_CCS.update({ k : v })
                _txt += f"{v:3} (default, not in cfgfile)"

            pr_debug(_txt)


    ## Best way to 'communicate' with the rest of the module..
    ## to import globals like DEFAULT_CHANNEL, or a dict like CFG_DICT.get('default_channel')
    ######################################################################
    LOADED_CFG = _FILE_CFG  

###################################################
###################################################


## Smaller and not using 'self'
##################################################
def CFGSAVE(cfgname, cfgdict, cfgfilename=CFG_FILENAME, cfgdict_default={}, trim=True):
    #_data = _cfg_dict_trim(cfgdict, cfgdict_default) if trim else cfgdict
    _data = cfgdict
    if trim:
        _data = {}
        for k, v in cfgdict.items():
            if v == None or (cfgdict_default and k not in cfgdict_default):
                continue

            _v = cfgdict_default.get(k, None)
            if v == _v and not isinstance(_v, type(None)):
                continue

            _data.update({ k : v })

    DATA = {}
    if os.path.isfile(cfgfilename):
        with open(cfgfilename, 'r') as fp:
            DATA = yaml.full_load(fp)

    DATA.update({ cfgname : _data })

    if _data:
        with open(cfgfilename, 'w') as fp:
            yaml.dump(DATA if DATA else _data, fp)

        return _data
        

def CFGLOAD(cfgname, cfgfilename=CFG_FILENAME):
    if os.path.isfile(cfgfilename):
        with open(cfgfilename, 'r') as fp:
            DATA = yaml.full_load(fp)

        if cfgname in DATA:
            return DATA[cfgname]

    return {}

   
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


def _cfg2str(cfgdict):
    return str(cfgdict).replace(' ', '').replace("'", '"')

######################################################################
if __name__ == '__main__':
    cfg = LOADED_CFG
    ccc = _cfg2str(cfg)
    print(ccc)




