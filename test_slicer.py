#!/bin/env python3
import os
import sys

import curses
import pygame
from tools import wcSlot
from tools import slotHolder
from tools import Slicer

fff = "/tmp/wav_out/slot00/OUT.wav"

def main_test():
    sss = Slicer()
    sss.infile = fff
    print(sss)
	

if __name__ == '__main__':
    pygame.mixer.init()
    main_test()

