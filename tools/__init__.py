import sys
from .wcslot import wcSlot
from .slotholder import slotHolder
from .slicer_base import Slicer
from .slicer_pitches import PitchesSlicer
from .infile_getter import InfileGetter
from .notes_window import NotesWin
from .portholder import GET_PORT
from .log_setup import GET_LOGGER

from .utils import INFILE_CONVERT, NORMALIZE
from .defaults import CURSE_INIT


## found this in log_setup also
'''
import logging
logging.addLevelName(12, 'VISUAL')
def _visual(self, msg, *AA, **KWA):
    if self.isEnabledFor(12):
        self._log(12, msg, AA, **KWA)

print(f"\033[36m22 {__file__} | adding VISUAL log level\033[0m", file=sys.stderr)
logging.Logger.visual = _visual
'''
