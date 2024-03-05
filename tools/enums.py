#!/bin/env python3
from enum import Enum, auto
import curses


class FocusStates(Enum):
    MAIN    = 0
    SLICER  = 1

class EditFields(Enum):
    POS0    = 0
    POS1    = 1
    INFILE  = 2

class IGStates(Enum):
    INIT        = auto()    ## maybe theres 'uri', could be link or filename
    COPY        = auto()    ## copy working (wget, local FS copy), save to copy_target
    CONVERT     = auto()    ## convert working, ffmpeg convert copy_target to convert_target
    READY       = auto()    ## ready for use by pwavcut/etc
    ERROR       = auto()    ## check self.errors
    CANCEL      = auto()    ## was cancelled

    @property
    def color(self):
        _col = IGStateColors.get(self.name, 0)
        return curses.color_pair(_col)

    @property
    def blink(self):
        return []


IGStateColors = dict(
    INIT    = 38,
    COPY    = 190,
    CONVERT = 190,
    READY   = 40,
    ERROR   = 124,
    CANCEL  = 186,
    )

class IGCopyModes(Enum):
    YTDL    = auto()
    SCP     = auto()
    FILE    = auto()
    HTTP    = auto()

