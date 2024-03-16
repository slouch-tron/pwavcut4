#!/bin/env python3
import os, sys
import time
import shlex, subprocess
import curses
import pygame
from pygame.midi import midi_to_ansi_note
#from pygame.midi import midi_to_frequency

from pydub import AudioSegment
from typing import Iterator

from .defaults import DEFAULT_WAV_IN_DIR, DEFAULT_SRC_OUT_DIR, DEFAULT_CONVERT_DIR
from .notes import midi_to_frequency2 as midi_to_frequency
from .log_setup import GET_LOGGER

## should stay 'in scope' and connected throughout program run?
#UTILS_LOGGER    = GET_LOGGER(appname="utils")
#DOFFMPEG_LOGGER = GET_LOGGER(appname="DoFFMPEG")

## experimenting with only init-ing them when needed.  though why not just init them.
UTILS_LOGGER    = None
DOFFMPEG_LOGGER = None

## where to keep this, if we phase 'utils' out.  defaults?
## A: maybe here is fine, happy medium where all files converted same way but also,
##   handling of the Process is in the class
INFILE_CONVERT_CMD_FMT = 'ffmpeg -y -i "{}" -ar 44100 -map_metadata -1 "{}"'


def _Log(txt, toconsole=1):
    global UTILS_LOGGER
    if not UTILS_LOGGER:
        UTILS_LOGGER = GET_LOGGER(appname="utils")

    UTILS_LOGGER.debug(txt)
    toconsole and print(txt)

def INFILE_CONVERT(infile, outfile_fullpath):
    #_cmd = f"ffmpeg -y -i \"{infile}\" -ar 44100 -map_metadata -1 \"{outfile_fullpath}\""
    _cmd = INFILE_CONVERT_CMD_FMT.format(infile, outfile_fullpath)
    _Log("InfileConvert: cmd")
    _Log("  " + _cmd)
    return EXECUTE_CMD(_cmd)
    

def PYG_SOUND_LOAD(filename):
    def _log(txt): _Log("PYG_SL: " + txt)
    #if not pygame.mixer.get_init():
    #    pygame.mixer.init()

    if os.path.isfile(filename):
        _log(f"try loading '{filename}'")
        try:
            _sound = pygame.mixer.Sound(filename)
        except pygame.error as ee:
            curses.endwin()
            _log(f"error loading '{filename}', did we log it?")
            raise ee

        _log(f"OK loading '{filename}'")
        return _sound


def NORMALIZE(filename, outfile="/tmp/norm1.wav"):
    def _log(txt): _Log("NORMALIZE: " + txt)
    if os.path.isfile(filename):
        _log(f"{filename} to {outfile}")
        if filename == outfile:
            _log("(copy dodge)")
            _tmpfile = os.path.join(DEFAULT_CONVERT_DIR, "_normalize_tmp.wav")
            os.system(f"cp {filename} {_tmpfile}")
            filename = _tmpfile


        seg = AudioSegment.from_wav(filename)
        norm = seg.normalize()
        norm.export(outfile)
        _log(f"{outfile} seems ok")


## no longer using this?
'''
def RUN_PROC(cmd, debug=1):     ## less used now

    if debug:
        curses.endwin()
        print(f"\033[33mRUN_PROC: {cmd}\033[0m", file=sys.stderr)

    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = p.communicate()

    if debug:
        for txt in [
            "\033[32m{}\033[0m".format("\n".join(o.decode('utf-8').splitlines())),
            "\033[34m{}\033[0m".format("\n".join(e.decode('utf-8').splitlines())),
            f"\033[33mreturncode={p.returncode}\033[0m",
            ]:
            print(txt, file=sys.stderr)

    return p.returncode == 0
'''

##	so now: channel split by pydub to temp file, ffmpeg processes to 'standard' file.
##	pydub probably does this too but some places we are not in a Class
''' # mark as 'unchecked' for now
def DO_STEREO(source='/tmp/wav_in/file1.wav', keep_pan=True, debug=0):
    def _print(txt):
        print(f"dostereo: {txt}")

    if not os.path.isfile(source):
        _print(f"not a file '{source}'")
        return

    tempfile = os.path.join(DEFAULT_WAV_IN_DIR, 'DSTEMP.wav')
    _print(f"START source={source}")
    _print(f"tempfile={tempfile}")

    segment = AudioSegment.from_wav(source)

    for ix, ch in enumerate(segment.split_to_mono()):
        _sourcefile = os.path.splitext(os.path.split(source)[1])[0]
        _sourcefile += '_' + ('L' if ix == 0 else 'R') + '_wav'

        destfile = os.path.join(DEFAULT_WAV_IN_DIR, _sourcefile)

        panned_ch = ch.pan([-1, 1][ix]) if keep_pan else ch
        panned_ch.export(tempfile)

        cmd = "ffmpeg -y -i {} -ar 44100 -map_metadata -1 {}".format(tempfile, destfile)
        _print(f"do cmd | {cmd}")
        EXECUTE_CMD(cmd)


        if os.path.isfile(destfile):
            _cmd = f"rm {tempfile}"
            _print(f"created '{destfile}', {_cmd}")
            os.system(_cmd)
        else:
            _print(f"create '{destfile}' FAIL")
            raise TypeError

    return True

'''
#"ffmpeg -y -i {} -ar 44100 -map_metadata -1 {}".format(os.path.join(tdir, pfilename), os.path.join(pdir, wfilename)),



def EXECUTE_CMD(cmd, sout=1, serr=1, timeout=16, endwin=0):
    endwin and curses.endwin()

    sout and print(f"\033[36;1mtrying: {cmd}\033[0m", end="")

    p = subprocess.Popen(
        shlex.split(cmd), 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
        )

    _start	= time.time()
    _end  	= _start + timeout

    _poll	= None
    while _poll == None:
        _poll = p.poll()

        ## neat to look at but need to do stuff inside the 'for' loop
        #[pr_out(line) for line in iter(p.stdout.readline, "")]
        #[pr_err(line) for line in iter(p.stderr.readline, "")]

        for line in iter(p.stdout.readline, ""):
            sout and print(f"\033[36;1m{line}\033[0m", end="")
            _recent_output = True

        for line in iter(p.stderr.readline, ""):
            serr and print(f"\033[33;2m{line}\033[0m", end="")
            _recent_output = True

        if _recent_output:
            _recent_output = False
            _end = time.time() + timeout	## reset timeout target time
            continue

        if time.time() > _end:
            print(f"\033[31m(timed out after {timeout} sec)\n\033[31m")
            break

    _elapsed = time.time() - _start
    sout and print(f"\033[36;1mpoll={_poll}\n{_elapsed:.4f} sec elapsed\n\033[0m", end="")
    
    return _poll



## Used by pitch slicer class
def DOFFMPEG(
    pitch_ix, source, 
    ## might want to make some of the kwa into args but for now, testing
    basenote_ix=69, ## midi note 'A4', pitch 440hz
    notempo=False,
    shift_tempo=1.0,
    outfile=None,   ## overrides dest_dir and label
    debug=0,
    Log=None
    ):

    def _log(txt):
        global DOFFMPEG_LOGGER
        if not DOFFMPEG_LOGGER:
            DOFFMPEG_LOGGER = GET_LOGGER(appname="DoFFMPEG")

        DOFFMPEG_LOGGER.debug(txt)

    ## maybe keep named loggers in the main class?
    #logger = GET_LOGGER(appname="doffmpeg")

    nkey = midi_to_ansi_note(pitch_ix)
    if not outfile:
        outfile = os.path.join(DEFAULT_SRC_OUT_DIR, f"TEST-file_{pitch_ix:03d}_{nkey}.wav")

    hifi = True     ## platform check here?
    rate = 44100 if hifi else 22050
    
    cmd_head = f"ffmpeg -y -i {source}"

    if notempo:
        cmd = cmd_head 
        #cmd += " -af asetrate={}*{}/{} ".format(rate, int(nval*100)
        #cmd += outfile
    else:
        tempo_factor    = midi_to_frequency(basenote_ix) / midi_to_frequency(pitch_ix)

        if tempo_factor < 0.5:
            _ccc = 0
            while tempo_factor < (1 / (2**_ccc)):
                _ccc += 1
            tempo_str = "atempo={:.8f},".format(tempo_factor*(2**(_ccc-1)))
            tempo_str += "atempo=1/2"*(_ccc-1)
        elif tempo_factor > 2:
            tempo_str = "atempo={:.4f}".format(tempo_factor)
        else:
            tempo_str = "atempo={:.4f}".format(tempo_factor)

        if shift_tempo < tempo_factor:  ## does this overwrite the 0.5 case?
            tempo_str += ",atempo={:.4f}".format(shift_tempo)
        else:
            tempo_str = "atempo={:.4f},".format(shift_tempo) + tempo_str

        ## not sure where we miss a comma but it does!
        ##  -af asetrate=44100*209300/44000,atempo=1.0000,atempo=0.84089823,atempo=1/2atempo=1/2
        while 'atempo=1/2atempo=1/2' in tempo_str:
            tempo_str = tempo_str.replace('atempo=1/2atempo=1/2', 'atempo=1/2,atempo=1/2')

        if tempo_factor < 1:
            cmd = cmd_head + " -af asetrate={}*{}/{},{} {}".format(
                    rate, 
                    int(midi_to_frequency(pitch_ix)) * 100,
                    int(midi_to_frequency(basenote_ix)) * 100,
                    tempo_str,
                    outfile,
                    )
        else:
            cmd = cmd_head + " -af {},asetrate={}*{}/{} {}".format(
                    tempo_str,
                    rate,
                    int(midi_to_frequency(pitch_ix)) * 100,
                    int(midi_to_frequency(basenote_ix)) * 100,
                    outfile,
                    )

        _freq = midi_to_frequency(pitch_ix)
        #_Log(f"midi_to_frequency({pitch_ix}) = {_freq}", level='debug')
        _log(f"{cmd}")

        return cmd

    
def EW_PROMPT(prompt="enter a value: ", vtype=float):
    curses.endwin()
    _Log(f"EW_PROMPT '{prompt}'")
    value = input(prompt)
    if value and value != '\n':
        try:
            return vtype(value)
        except ValueError:
            pass


def DRAWHELPWIN(obj, dict_name='keyDict'):
    '''Print Help Window for keyboard'''
    _win = curses.newwin(40, 80, 10, 10)
    _attr = curses.color_pair(37) | curses.A_REVERSE
    _yy = 0

    _kDict = getattr(obj, dict_name, None)
    if not isinstance(_kDict, dict):
        return 

    for k, v in _kDict.items():
        _k = str(k) 
        _v = v[0] if isinstance(v, list) else v
        _ostr = f"'{_k:2s}' | {_v.__doc__ or _v.__name__}"
        _win.addstr(_yy, 0, _ostr, _attr)
        _yy += 1

    _win.refresh()
    ik = 0
    while ik < 1:
        ik = obj.stdscr.getch()


''' ## like to 'tail a file' for log window, but doesnt work...
def TAIL(filename):
    line = ''
    while True:
        tmp = file.readline()
        if tmp is not None and tmp != "":
            line += tmp
            if line.endswith("\n"):
                yield line
                line = ''
'''
