
import os
import curses
import mido
from tools import NotesWin, GET_PORT

PORT_I = None
PORT_I = GET_PORT(os.environ.get('PORT_I', "24:0"))

if __name__ == '__main__':
        nnn = NotesWin(test_port=PORT_I)
        #note0 = mido.Message('note_on', note=50)
        #note1 = mido.Message('note_on', note=51)
        nnn.Run()
        curses.endwin()


