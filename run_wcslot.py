#!/bin/env python3
import os
import sys
import argparse

import curses
import pygame

from pydub import AudioSegment

from tools import wcSlot
from tools import slotHolder
from tools import PitchesSlicer
from tools import NORMALIZE


PORT_I = os.environ.get('PORT_I', None)


## such as:
## PORT_I="24:0" python3 run_wcslot.py -0 2076 -1 2084 -b 127 -s 97 -i /tmp/wav_in/qqqqqq.wav -S pitch
## PORT_I="24:0" python3 run_wcslot.py -0 1687 -1 1695 -b 127 -s 97 -i /tmp/wav_in/qqqqqq.wav -S pitch


def parse_argv(argv):
    print(f"parse_argv: START from {argv[0]}")
    parser = argparse.ArgumentParser(description="cmd line options for standalone wcSlot demo")
    parser.add_argument('-0', '--pos0', dest='pos0', type=str, help='pos0')
    parser.add_argument('-1', '--pos1', dest='pos1', type=str, help='pos1')
    parser.add_argument('-b', '--bpm', dest='bpm', type=str, help='bpm')
    parser.add_argument('-s', '--shift', dest='shift', type=str, help='shift')
    parser.add_argument('-i', '--infile', dest='infile', type=str, help='infile, to segment')
    parser.add_argument('-S', dest='slicer', type=str, help='type of slicer class to attach')

    args = parser.parse_args(argv[1:])

    return args



def main_test():
    args = parse_argv(sys.argv)
    www = wcSlot(slotnum=99)

    if args.pos0:   www.pos0 = float(args.pos0)
    if args.pos1:   www.pos1 = float(args.pos1)
    if args.infile: www.infile = args.infile
    print(f"\033[33;7m{www}\033[0m", file=sys.stderr)

    www.doCut3_out(mod=False)

    if args.bpm:    www.bpm = float(args.bpm)
    if args.shift:  www.shift_tempo = float(args.shift)
    print(f"\033[33;7m{www}\033[0m", file=sys.stderr)

    www.doCut3_out(mod=True)

    norm_file = "/tmp/wav_out/NORM_OUT.wav"
    NORMALIZE(www.outfile, norm_file)
    norm_file = "/tmp/wav_out/NORM_MOD.wav"
    NORMALIZE(www.modfile, norm_file)
        

    #return


    if args.slicer:
        if args.slicer.upper() == 'PITCH':
            ppp = PitchesSlicer(
                #infile=www.outfile,
                infile=norm_file,
                bpm=www.bpm,
                shift_tempo=www.shift_tempo,
                )

            if PORT_I:
                ppp.port_i = PORT_I

            print(ppp)
            ppp.Slice()
            ppp.Run()
	

if __name__ == '__main__':
    main_test()

