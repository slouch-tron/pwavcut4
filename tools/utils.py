#!/bin/env python3
import os, sys
import time
import shlex, subprocess
import curses
import pygame

from pydub import AudioSegment

from .defaults import DEFAULT_WAV_IN_DIR




def PYG_SOUND_LOAD(filename):
    #if not pygame.mixer.get_init():
    #    pygame.mixer.init()

    if os.path.isfile(filename):
        try:
            _sound = pygame.mixer.Sound(filename)
        except pygame.error as ee:
            curses.endwin()
            raise ee

        return _sound


def RUN_PROC(cmd, debug=1):

    if debug:
        curses.endwin()
        print(f"\033[33mRUN_PROC: {cmd}\033[0m", file=sys.stderr)

    p = subprocess.Popen(
        shlex.split(cmd), 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
        )

    ## might want to, end curses screen, poll and print update until done here
    o, e = p.communicate()

    if debug:
        for txt in [
            "\033[32m{}\033[0m".format("\n".join(o.decode('utf-8').splitlines())),
            "\033[34m{}\033[0m".format("\n".join(e.decode('utf-8').splitlines())),
            f"\033[33mreturncode={p.returncode}\033[0m",
            ]:
            print(txt, file=sys.stderr)

    return p.returncode == 0


##	so now: channel split by pydub to temp file, ffmpeg processes to 'standard' file.
##	pydub probably does this too but some places we are not in a Class
def DO_STEREO(source='/tmp/wav_in/file1.wav', keep_pan=True, debug=0):
    try:
        curses.endwin()
    except Exception as ee:
        print("\033[31m something went wrong with this check! \033[0m")
        input()

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


def INFILE_CONVERT(infile, outfile_fullpath, debug=1):
    _cmd = f"ffmpeg -y -i \"{infile}\" -ar 44100 -map_metadata -1 \"{outfile_fullpath}\""

    if debug:
        curses.endwin()
        print(f"INFILE_CONVERT: cmd={_cmd}")

    return EXECUTE_CMD(_cmd)
    

def EW_PROMPT(prompt="enter a value: ", vtype=float):
    curses.endwin()
    value = input(prompt)
    if value and value != '\n':
        try:
            return vtype(value)
        except ValueError:
            pass



