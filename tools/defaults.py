#!/bin/env python3
import os
import sys
import curses
import platform
import yaml

DEFAULT_MIDI_LISTEN_CH      = 15
DEFAULT_MIDI_LISTEN_CH_MOD  = 14
DEFAULT_MIDI_LISTEN_CH_KIT  = 13

DIR_BASE = "/tmp"
DEFAULT_WAV_IN_DIR  = os.path.join(DIR_BASE, 'wav_in')
DEFAULT_WAV_OUT_DIR = os.path.join(DIR_BASE, 'wav_out')
DEFAULT_SRC_OUT_DIR = os.path.join(DIR_BASE, 'source_out')

CFG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cfg'))
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../log'))
DEFAULT_CFGFILE = os.path.join(CFG_PATH, "cfg.yml")

OK_FILE_TYPES   = ['.wav', '.mp3', '.mp4', '.ogg']
OK_ARCHS        = ['armv7l', 'x86_64']

## import to other places for consistency
DEBUG       = int(os.environ.get('DEBUG', 0))
TRANSPARENT = int(os.environ.get('TRANSPARENT', 1))

DEFAULT_MIDI_CHS = dict(
    listen=15,
    mod=14,
    kit=13,
    )

DEFAULT_MIDI_CCS = dict(
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


######################################################################
######################################################################
def CURSE_INIT(stdscr):
    curses.initscr()
    curses.start_color()
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
    col = "\033[33m"; end = "\033[0m"
    print(f"{col}MAKE DEFAULT DIRECTORIES{end}", file=sys.stderr)

    for DIR in [
        DEFAULT_WAV_IN_DIR, 
        DEFAULT_WAV_OUT_DIR, 
        DEFAULT_SRC_OUT_DIR,
        CFG_PATH,
        LOG_PATH,
        ]:
        if not os.path.isdir(DIR):
            cmd = f"mkdir {DIR}"
            print(f"{col} {cmd}{end}", file=sys.stderr)
            os.system(cmd)


def GET_CFG(cfgfile=None, dump=False)->dict:   ## cfgfile = yaml filename string
    ''' 
        dump = write default_cfg to cfgfile (initialize the cfg file for editing)

        ## Q: is GLOBALS sort of same as passing a dictionary around?
        ## A: good for midi CCs or repetitively named tables.
        ##  itll be easy enough to edit in the cfgfile...
    '''

    def _print(txt):
        print(f"\033[33;2mGET_CFG | {txt}\033[0m", file=sys.stderr)

    default_cfg = dict(
        DEFAULT_MIDI_CCS=DEFAULT_MIDI_CCS,
        DEFAULT_MIDI_CHS=DEFAULT_MIDI_CHS,
        )

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
                print("weird situaton?")

    elif dump:
        cfgfile = cfgfile or DEFAULT_CFGFILE
        _print(f"creating {cfgfile}")
        with open(cfgfile, 'w') as fp:
            yaml.dump(default_cfg, fp)

    else:
        _print("returning default_cfg unmodified")
        
    return default_cfg


######################################################################
######################################################################
def pr_debug(txt):
    DEBUG and print(f"\033[32m{txt}\033[0m", file=sys.stderr)


def cfg2str(cfgdict):
    return str(cfgdict).replace(' ', '').replace("'", '"')


## why not just have it always happen,
##  instead of burying it in a class property.
## class 'needs to know' but surely we can have some assumptions about a set-up env
MAKE_DEFAULT_DIRS()
assert(platform.machine() in OK_ARCHS)
not os.path.isfile(DEFAULT_CFGFILE) and GET_CFG(dump=1)


if __name__ == '__main__':
    #cfg = GET_CFG(DEFAULT_CFGFILE)
    cfg = GET_CFG("./cfg/ttt.yml")
    #cfg = GET_CFG()
    ccc = cfg2str(cfg)
    print(ccc)




