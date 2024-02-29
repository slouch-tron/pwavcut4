import os
import curses

class DrawSlotsClass():
    def DrawSlots(self, **kwa):
        _col0 = kwa.get('col0', None) or curses.color_pair(24)      ## unselected, regular
        _col1 = kwa.get('col1', None) or curses.color_pair(51)      ## highlighted field
        _col2 = kwa.get('col2', None) or curses.color_pair(118)     ## toggled

        #_ym, _xm = self.mainWin.getmaxyx()
        _header2 = "_|_".join([
            'SS', 
            'POS0    ',
            'POS1    ',
            'INFILE              ',
            'CH',
            'LEN      ',
            'LLOCK',
            'OUT',
            'MOD',
            "OBJ",
            "",

            ])

        self.mainWin.addstr(0, 0, _header2)

        _yy = 1
        _ll = 'LLOCK'
        for ix, f in enumerate(self.slots):
            _infile = 'None'
            if f.infile:
                _infile = os.path.splitext(os.path.split(f.infile)[-1:][0])[0]

            _pos0   = f"{f.pos0:8.2f}"
            _pos1   = f"{f.pos1:8.2f}"
            _ch     = f"{f.ctrl_ch:2x}"
            _ff     = f"{_infile[:10]:^20s}"
            _dd     = f"{f.duration:9.4f}"
            _bb     = f"{f.bpm:6.2f}"
            _ss     = f"{f.shift_tempo:6.2f}"
            _po     = f.pitchObj.state if f.pitchObj else 'None'

            _attr = _col0
            if ix == self.selected_ix:
                _attr |= curses.A_REVERSE

            _xx = 0
            _ostr = f"{ix:02d}"
            self.mainWin.addstr(_yy+ix, 0, _ostr, _attr);   _xx += len(_ostr)
            self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            for ig, g in enumerate([_pos0, _pos1, _ff, _ch]): ## _ff
                _tmpattr = _attr
                if self.field_ix == ig and ix == self.selected_ix:
                    _tmpattr = _col1 | curses.A_REVERSE

                self.mainWin.addstr(_yy+ix, _xx, g, _tmpattr);  _xx += len(g)
                self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            #for ih, h in enumerate([_dd, _bb, _ss]):
            for ih, h in enumerate([_dd, ]):
                self.mainWin.addstr(_yy+ix, _xx, h, _attr);     _xx += len(h)
                self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            _attr3 = _attr
            #_attr3 = _col2
            if f.lock_length_switch:
                if ix == self.selected_ix:
                    _attr3 = _col1
                _attr3 |= curses.A_REVERSE

            self.mainWin.addstr(_yy+ix, _xx, _ll, _attr3);  _xx += len(_ll)
            self.mainWin.addstr(_yy+ix, _xx, ' | ', _attr); _xx += len(" | ")

            for _fix, _file in enumerate([f.outfile, f.modfile, _po]):
                _attr2 = _attr
                _ostr = '   '
                if os.path.isfile(_file):
                    _attr2 = _col2
                    _ostr = 'OUT' if _fix == 0 else 'MOD'

                #try:
                if True:
                    self.mainWin.addstr(_yy+ix, _xx, _ostr, _attr2);    _xx += len(_ostr)
                    self.mainWin.addstr(_yy+ix, _xx, " | ", _attr);     _xx += len(' | ')
                #except curses.error as cc:
                #    curses.endwin()
                #    print(cc)


