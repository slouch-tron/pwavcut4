#!/bin/env python3
import os
import sys

import curses
import pygame
from tools import wcSlot
from tools import slotHolder


def main_test():
    hhh = slotHolder(slot_count=16)
    hhh.port_i = "Arturia"

    aaa = hhh.parse_argv(sys.argv)
    print(aaa)
    print(hhh)
    hhh.selectedSlot.pos1 = 13.0

    hhh.Run()
	

if __name__ == '__main__':
    pygame.mixer.init()
    main_test()

