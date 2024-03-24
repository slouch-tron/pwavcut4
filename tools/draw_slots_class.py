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
        _lock = 'LLOCK'
        for ix, f in enumerate(self.slots):
            _infile = 'None'
            if f.infile:
                _infile = os.path.splitext(os.path.split(f.infile)[-1:][0])[0]

            _pos0   = f"{f.pos0:8.2f}"
            _pos1   = f"{f.pos1:8.2f}"
            _ch     = f"{f.ctrl_ch:2x}"
            _ff     = f"{_infile[:10]:^20s}"
            _dd     = f"{f.duration:9.4f}"
            _ll     = f"{f.lock_length:9.4f}"
            _bb     = f"{f.bpm:6.2f}"
            _ss     = f"{f.shift_tempo:6.2f}"
            #_po     = f.PitchObj.state if f.PitchObj else 'None'

            _attr = _col0
            if ix == self.selected_ix:
                _attr |= curses.A_REVERSE

            _ostr = "   |          |          |                      |    |           |       |"
            #self.mainWin.addstr(_yy+ix, 0, _ostr, _attr)

            _xx = 0
            _ostr = f"{ix:02d}"
            self.mainWin.addstr(_yy+ix, 0, _ostr, _attr);   _xx += len(_ostr) + 3
            #self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            for ig, g in enumerate([_pos0, _pos1, _ff]): ## _ff
                _tmpattr = _attr
                if self.field_ix == ig and ix == self.selected_ix:
                    _tmpattr = _col1 | curses.A_REVERSE

                self.mainWin.addstr(_yy+ix, _xx, g, _tmpattr);  _xx += len(g) + 3
                #self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            #_ostr = f"{_ch}   {_ll}   "
            #self.mainWin.addstr(_yy+ix, _xx, _ostr, _attr)
            #_xx += len(_ostr)

            for ih, h in enumerate([_ch, _ll, ]):
                self.mainWin.addstr(_yy+ix, _xx, h, _attr);     _xx += len(h) + 3
                #self.mainWin.addstr(_yy+ix, _xx, " | ", _attr); _xx += len(" | ")

            _attr3 = _attr
            #_attr3 = _col2
            if f.lock_length_switch:
                if ix == self.selected_ix:
                    _attr3 = _col1
                _attr3 |= curses.A_REVERSE

            self.mainWin.addstr(_yy+ix, _xx, _lock, _attr3);  _xx += len(_lock) + 3
            #self.mainWin.addstr(_yy+ix, _xx, ' | ', _attr); _xx += len(" | ")

            #continue

            #for _fix, _file in enumerate([f.outfile, f.modfile, f.PitchObj]):
            for _fix, _file in enumerate([f.outsound, f.modsound, f.PitchObj]):

                ## os.path.isfile is probably killin the loop time by ~400hz
                #if (_fix == 2 and _file != None) or (_file and os.path.isfile(_file)):
                if (_fix == 2 and _file != None) or (_file):
                    _ostr = ['OUT', 'MOD', 'OBJ'][_fix]
                    _attr2 = _col2
                else:
                    _ostr = '   '
                    _attr2 = _attr

                if   _fix == 0: _blink = f.is_playing_out
                elif _fix == 1: _blink = f.is_playing_mod
                elif _fix == 2: _blink = f.is_playing_pobj
                else:   _blink = False

                if _blink:
                    if (self.cyc_ct % 200) - 80 < 0:
                        #_attr2 = curses.color_pair(124)
                        _attr2 = curses.A_REVERSE
                    
                self.mainWin.addstr(_yy+ix, _xx, _ostr, _attr2);    _xx += len(_ostr) + 3
                #self.mainWin.addstr(_yy+ix, _xx, " | ", _attr);     _xx += len(' | ')


    def DrawLogWin(self, **kwa):
        _attr = kwa.get('col0', None) or curses.color_pair(20)

        _ymax, _ = self.logWin.getmaxyx() 
        while len(self.log_lines) > (_ymax - 6):
            self.log_lines.pop(0)

        self.logWin.addstr(0, 0, f"#### LOG   ######## {self.COORDS_LOG} ####", _attr)
        for ix, f in enumerate(self.log_lines):
            self.logWin.addstr(ix+1, 0, f, _attr)


    def DrawInfoWin(self, **kwa):
        _ym, _xm = self.infoWin.getmaxyx() 
        _attr = kwa.get('col0', curses.color_pair(36))

        _slot = self.selectedSlot

        _ratio = _slot.shift_tempo / _slot.bpm
        _infile = os.path.split(_slot.infile)[-1] if _slot.infile else 'None'
        _lines = [
            f"#### {_slot.slotname.upper()} ######## {self.COORDS_INFO} ####",
            f"pos0:         {_slot.pos0:6.2f}",
            f"pos1:         {_slot.pos1:6.2f}",
            f"infile:       {_infile}",
            f"p_delta:      {_slot.pos1 - _slot.pos0}",
            f"duration:     {_slot.duration}",
            f"bpm/shift:    {_slot.bpm:6.2f} / {_slot.shift_tempo:6.2f} / {_ratio:6.4f}",
            f"lock_length:  {_slot.lock_length} ({_slot.lock_length_switch})",
            f"retrigger:    {_slot.retrigger}",
            f"outfile:      {os.path.isfile(_slot.outfile)}",
            f"modfile:      {os.path.isfile(_slot.modfile)}",
            f"PitchObj:     {_slot.PitchObj.devname if _slot.PitchObj else 'none'}",
            f"ctrl_ch:      {_slot.ctrl_ch:02x}",
            ]

        _yy = ix = 0
        for ix, line in enumerate(_lines):
            _line = f"{ix:02d} | {line}"
            _line += '_'*(_xm - 1 - len(_line))
            self.infoWin.addstr(ix+_yy, 0, _line, _attr)

        _yy = ix


	

