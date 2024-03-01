#!/bin/env python3
import os
import sys
import argparse
import time

import curses
import pygame

from pydub import AudioSegment

from tools import wcSlot
from tools import slotHolder
from tools import PitchesSlicer
from tools import NORMALIZE


PORT_I = os.environ.get('PORT_I', None)
SLICER = os.environ.get('SLICER', None)


## such as:
## PORT_I="24:0" python3 run_wcslot.py -0 2076 -1 2084 -b 127 -s 97 -i /tmp/wav_in/qqqqqq.wav -S pitch
## PORT_I="24:0" python3 run_wcslot.py -0 1687 -1 1695 -b 127 -s 97 -i /tmp/wav_in/qqqqqq.wav -S pitch


def main_test():
    www = wcSlot(slotnum=99)
    www.as_cli()
    print(www)
    print(SLICER)

    def _print(txt):
        print(f"\033[33m{txt}\033[0m", file=sys.stderr)

    norm_file = "/tmp/wav_out/NORM_OUT.wav"
    NORMALIZE(www.outfile, norm_file)
    if SLICER == 'PITCH':
        _print(f"slicer=PITCH")
        _infile = norm_file
        if not os.path.isfile(_infile):
            _print("no file {_infile} for SLICER to work on")

        ppp = PitchesSlicer(
            #infile=self.outfile,
            infile=_infile,
            bpm=www.bpm,
            shift_tempo=www.shift_tempo,
            )

        if PORT_I:
            _print(f"set PORT_I = {PORT_I}")
            ppp.port_i = PORT_I

        print(ppp)
        _print(f"{str(ppp)} SLICE START")
        if ppp.Slice():
            while ppp.state != ppp.STATES.READY:
                ppp.CmdQueueUpdate()
                print(ppp)
                time.sleep(.1)

        else:
            _print("SLICE not started")
	

if __name__ == '__main__':
    main_test()

