#!/bin/env python3
import os
import sys
import curses
import platform


DEFAULT_MIDI_LISTEN_CH      = 15
DEFAULT_MIDI_LISTEN_CH_MOD  = 14
DEFAULT_MIDI_LISTEN_CH_KIT  = 13

DEFAULT_WAV_IN_DIR  = '/tmp/wav_in'
DEFAULT_WAV_OUT_DIR = '/tmp/wav_out'
DEFAULT_SRC_OUT_DIR = '/tmp/source_out' ## fed to pitch objs

OK_FILE_TYPES   = ['.wav', '.mp3', '.mp4', '.ogg']
OK_ARCHS        = ['armv7l', 'x86_64']

DEBUG       = int(os.environ.get('DEBUG', 0))
TRANSPARENT = int(os.environ.get('TRANSPARENT', 1))


def CURSE_INIT(stdscr):
    curses.initscr()
    curses.start_color()
    curses.init_color(0,0,0,0)
    curses.curs_set(0)

    TRANSPARENT and curses.use_default_colors()

    for c in range(1, curses.COLORS):
        curses.init_pair(c, c, -1 if TRANSPARENT else 0)

    stdscr.nodelay(1)
    stdscr.keypad(1)
    return stdscr


def MAKE_DEFAULT_DIRS():
    _print = pr_debug
    _print("MAKE DEFAULT DIRECTORIES")

    for DIR in [
        DEFAULT_WAV_IN_DIR, 
        DEFAULT_WAV_OUT_DIR, 
        DEFAULT_SRC_OUT_DIR,
        ]:
        if not os.path.isdir(DIR):
            cmd = f"mkdir {DIR}"
            _print(cmd)
            os.system(cmd)



def pr_debug(txt):
    DEBUG and \
    print(f"\033[32m{txt}\033[0m", file=sys.stderr)




## why not just have it always happen,
##  instead of burying it in a class property.
## class 'needs to know' but surely we can have some assumptions about a set-up env
MAKE_DEFAULT_DIRS()
assert(platform.machine() in OK_ARCHS)
