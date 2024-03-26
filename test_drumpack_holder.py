#!/bin/env python3

import pygame
import curses
from tools import drumPackHolder
from tools import CURSE_INIT



def main_test(stdscr):
    curses.initscr()
    CURSE_INIT(stdscr)

    ddd = drumPackHolder(stdscr)
    ddd.port_i = "28:0"
    print(ddd)

    ddd.Run()


if __name__ == '__main__':
    pygame.mixer.init()
    curses.wrapper(main_test)
    curses.endwin()
