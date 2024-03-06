#!/bin/env python3
import os, shlex, subprocess, time
import re, mido
from tools import PitchesSlicer

TESTFILE    = "/tmp/wav_out/slot05/OUT.wav"
TESTOWNER   = "MINI_SLICE2"
TESTPLAY    = "ffplay -autoexit -nodisp "

def test_linear():
    _bstart = time.time()

    cmds = PitchesSlicer.minislicer(TESTFILE, owner=TESTOWNER, nrange=70)

    for cmd in cmds:
        _start = time.time()

        p = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            )

        _poll = None
        while _poll == None:
            _poll = p.poll()

        _col = "\033[32m" if _poll == 0 else "\033[31m"
        _sec = time.time() - _start
        print(f"{_poll} {_sec:6.4f} | {_col}{cmd}\033[0m")

    _sec = time.time() - _bstart
    print(f"{_sec:6.4f} sec total")



def Listen():
    port_i = None
    for port in mido.get_input_names():
        if re.search('24:0', port):
            port_i = mido.open_input(port)

    _path = os.path.join(PitchesSlicer.SRC_OUT_DIR, TESTOWNER)
    notefiles = os.listdir(_path)
    notefiles.sort()
    NDICT = dict()
    PROCS = dict()
    PLAY = list()

    for f in notefiles:
        ix = int(os.path.splitext(os.path.split(f)[-1])[0].split('_')[1])
        NDICT.update({ ix : os.path.join(_path, f) })


    print(port_i)
    try:
        while True:
            msg = port_i.poll()
            if msg:
                if msg.type == 'note_on':
                    _file = NDICT.get(msg.note, None)
                    if _file:
                        print(f"\033[36;7m{_file}\033[0m")
                        PROCS.update({ msg.note : subprocess.Popen(
                            shlex.split(TESTPLAY + f"{_file}"),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            )}) 

                elif msg.type == 'note_off':
                    if msg.note in PROCS:
                        print(f"\033[36m{_file}\033[0m")
                        proc = PROCS.pop(msg.note)
                        proc.terminate()
                        proc = None

    except KeyboardInterrupt as ee:
        print(ee)




        
if __name__ == '__main__':
    test_linear()
    Listen()
   
