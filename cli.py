#!/bin/env python3
import os
import sys

import curses
import pygame
from tools import wcSlot
from tools import slotHolder
from tools import GET_LOGGER


def _LOG(txt, **kwa):
    if not globals().get('LOGGER', None):
        global LOGGER 
        LOGGER = GET_LOGGER()
        LOGGER.debug("created LOGGER")

    LOGGER.debug(txt)

def main_test():
    #LOGGER = GET_LOGGER()
    _LOG("line to initialize the log")
    sss = wcSlot(slotnum=4)
    sss.Log("testing init 2")
    _LOG("another")

    args = sss.parse_argv(sys.argv)
    print(sss.slotname)
    sss.pos1 = 100
    sss.ctrl_ch = 3

    print(sss.CfgDict)
    sss.CfgSave()
    #sss.CfgLoad()
    #ccc = CFGLOAD_LITE(sss.slotname, CFG_FILENAME)
    #sss.CfgDict = ccc
    #input(ccc)
    print(sss.CfgDict)
    print(sss)
    #CFGLOAD_LITE(sss.slotname, CFG_FILENAME)

if __name__ == '__main__':
    pygame.mixer.init()
    main_test()

