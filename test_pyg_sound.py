#!/bin/env python3

import os
import pygame
from tools import INFILE_CONVERT

from

filename = "/tmp/wav_out/slot00/OUT.wav"

pygame.mixer.init()

assert(os.path.isfile(filename))
_sound = None

try:
    _sound = pygame.mixer.Sound(filename)
except Exception as ee:
    print(ee)



