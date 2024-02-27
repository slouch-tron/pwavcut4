
import curses
import mido
from tools import NotesWin

if __name__ == '__main__':
        note0 = mido.Message('note_on', note=50)
        note1 = mido.Message('note_on', note=51)

        #nnn = NotesWin()
        nnn = NotesWin()
        nnn.MsgCheck(note0)
        nnn.MsgCheck(note1)
        nnn.Run()
        curses.endwin()

