#!/bin/env python3
import os
import sys
import time

import curses
import pygame
from tools import wcSlot
from tools import slotHolder
from tools import Slicer, PitchesSlicer
from tools import CURSE_INIT

fff = os.environ.get('INFILE', "/tmp/wav_out/slot00/OUT.wav")

CURSE = int(os.environ.get('CURSE', 0))

def main_test():
    sss = PitchesSlicer()
    sss.parse_argv(sys.argv)
    sss.infile = fff
    print(sss)
    #sss.Slice()
    #sss.StartSliceTask()
    sss.Run(terminal=(not CURSE))

    
    print(sss)
    print(sss.port_i)
    print(sss.port_c)
    print(sss.port_o)
    print(sss.port_f)

    for f in sss.sounds.keys():
        print(f"{f} | {sss.sounds[f]}")
	

if __name__ == '__main__':
    pygame.mixer.init()
    main_test()

