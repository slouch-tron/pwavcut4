#!/bin/env python3
import os
import sys

import curses
import pygame
from tools import wcSlot
from tools import slotHolder
from tools import CURSE_INIT


def main_test():
    hhh = slotHolder(slot_count=12)
    hhh.port_i = "Arturia"

    aaa = hhh.parse_argv(sys.argv)
    print(aaa)
    print(hhh)
    hhh.selectedSlot.pos1 = 13.0

    hhh.Run()


def main_test2(stdscr):
    curses.initscr()
    CURSE_INIT(stdscr)
    #stdscr.keypad(1)

    hhh = slotHolder(stdscr, slot_count=12)
    hhh.port_i = "Arturia"

    aaa = hhh.parse_argv(sys.argv)
    print(aaa)
    print(hhh)
    hhh.selectedSlot.pos1 = 13.0

    #input(hhh.CfgDict)

    hhh.Run()


if __name__ == '__main__':
    pygame.mixer.init()
    #main_test()
    curses.wrapper(main_test2)
    curses.endwin()

