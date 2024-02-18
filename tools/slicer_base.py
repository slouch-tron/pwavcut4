#!/bin/env python3


import os
import sys
import curses
import argparse
import time
import pygame

from .wcslot import wcSlot
from .portholder import portHolder
from .defaults import (
        DEFAULT_MIDI_LISTEN_CH, DEFAULT_MIDI_LISTEN_CH_MOD, DEFAULT_MIDI_LISTEN_CH_KIT, 
        DEFAULT_SRC_OUT_DIR,
        OK_FILE_TYPES, GET_INFILES,
        CURSE_INIT,
        pr_debug,
        )

from .utils import EW_PROMPT


## table of note pitches
##  for ffmpeg settings when pitch shifting
NOTE_DICT = {       
    "C0"    : 16.35, 
    "C#0"   : 17.32, 
    "D0"    : 18.35, 
    "D#0"   : 19.45, 
    "E0"    : 20.6, 
    "F0"    : 21.83, 
    "F#0"   : 23.12, 
    "G0"    : 24.5, 
    "G#0"   : 25.96, 
    "A0"    : 27.5, 
    "A#0"   : 29.14, 
    "B0"    : 30.87, 
    "C1"    : 32.7, 
    "C#1"   : 34.65, 
    "D1"    : 36.71, 
    "D#1"   : 38.89, 
    "E1"    : 41.2, 
    "F1"    : 43.65, 
    "F#1"   : 46.25, 
    "G1"    : 49, 
    "G#1"   : 51.91, 
    "A1"    : 55, 
    "A#1"   : 58.27, 
    "B1"    : 61.74, 
    "C2"    : 65.41, 
    "C#2"   : 69.3, 
    "D2"    : 73.42, 
    "D#2"   : 77.78, 
    "E2"    : 82.41, 
    "F2"    : 87.31, 
    "F#2"   : 92.5, 
    "G2"    : 98, 
    "G#2"   : 103.83, 
    "A2"    : 110, 
    "A#2"   : 116.54, 
    "B2"    : 123.47, 
    "C3"    : 130.81, 
    "C#3"   : 138.59, 
    "D3"    : 146.83, 
    "D#3"   : 155.56, 
    "E3"    : 164.81, 
    "F3"    : 174.61, 
    "F#3"   : 185, 
    "G3"    : 196, 
    "G#3"   : 207.65, 
    "A3"    : 220, 
    "A#3"   : 233.08, 
    "B3"    : 246.94, 
    "C4"    : 261.63, 
    "C#4"   : 277.18, 
    "D4"    : 293.66, 
    "D#4"   : 311.13, 
    "E4"    : 329.63, 
    "F4"    : 349.23, 
    "F#4"   : 369.99, 
    "G4"    : 392, 
    "G#4"   : 415.3, 
    "A4"    : 440, 
    "A#4"   : 466.16, 
    "B4"    : 493.88, 
    "C5"    : 523.25, 
    "C#5"   : 554.37, 
    "D5"    : 587.33, 
    "D#5"   : 622.25, 
    "E5"    : 659.25, 
    "F5"    : 698.46, 
    "F#5"   : 739.99, 
    "G5"    : 783.99, 
    "G#5"   : 830.61, 
    "A5"    : 880, 
    "A#5"   : 932.33, 
    "B5"    : 987.77, 
    "C6"    : 1046.5, 
    "C#6"   : 1108.73, 
    "D6"    : 1174.66, 
    "D#6"   : 1244.51, 
    "E6"    : 1318.51, 
    "F6"    : 1396.91, 
    "F#6"   : 1479.98, 
    "G6"    : 1567.98, 
    "G#6"   : 1661.22, 
    "A6"    : 1760, 
    "A#6"   : 1864.66, 
    "B6"    : 1975.53, 
    "C7"    : 2093, 
    "C#7"   : 2217.46, 
    "D7"    : 2349.32, 
    "D#7"   : 2489.02, 
    "E7"    : 2637.02, 
    "F7"    : 2793.83, 
    "F#7"   : 2959.96, 
    "G7"    : 3135.96, 
    "G#7"   : 3322.44, 
    "A7"    : 3520, 
    "A#7"   : 3729.31, 
    "B7"    : 3951.07, 
    "C8"    : 4186.01, 
    "C#8"   : 4434.92, 
    "D8"    : 4698.63, 
    "D#8"   : 4978.03, 
    "E8"    : 5274.04, 
    "F8"    : 5587.65, 
    "F#8"   : 5919.91, 
    "G8"    : 6271.93, 
    "G#8"   : 6644.88, 
    "A8"    : 7040, 
    "A#8"   : 7458.62, 
    "B8"    : 7902.13, 
    }

## 210508 - list of tuples sorta makes sense.  values dont change.
##	how does lookup thru list of tuples compare to dict?
## 210513 - shouldnt we just make all the classes 1-pitch dictionaries?
N2TD = [(list(notes).index(k) - list(notes).index('A4'), k, notes[k]) for k in list(notes)]
#print([x[0] for x in N2TD if x[1] == 'C#3'])

def getKeyIx(key):
	return list(notes).index(key) 
	return [x[0] for x in N2TD if x[1] == key]

def prnotes():
	for f in notes:
		print(f)


class Slicer(portHolder):
    ID = 0

    def __init__(self, infile, **kwa):
        self.id         = Slicer.ID
        Slicer.ID += 1

        self.infile     = infile
        self.Log        = kwa.get('Log', None)
        self.stdscr     = kwa.get('stdscr', None)
        self.basedir    = kwa.get('basedir', None) or DEFAULT_SRC_OUT_DIR
        self.ctrl_ch    = kwa.get('ctrl_ch', None) or DEFAULT_MIDI_LISTEN_CH
        self.bpm        = kwa.get('bpm', 92.0)
        self.shift      = kwa.get('shift', 92.0)
        self.multitrig  = False
        self.mono       = False

        self.procs      = list()
        self.pan       = [1, 1]

        if not pygame.get_init():
            pygame.mixer.init()

        self.sounds     = list()
        self.lastRecd   = None
        self.lastSend   = None

        self.Log(f"{self.__class__.__name__}{self.id:02d} INIT")


########################################################################################
########################################################################################
class aSlicer(BasePorts):
	def __init__(self, infile, basedir=BASEDIR2, stdscr=None, inport=None, outport=None, inCh=15, bpm=92.0, shifttempo=92.0):
		self.infile     = infile
		self.stdscr     = stdscr
		self.BASEDIR    = basedir
		self.channel    = inCh
		self.bpm	= bpm	   ## used in Beats and now Pitches
		self.shifttempo = shifttempo    ## should move this to parent class
		self.multitrig  = False
		self.mono       = False	 ## not using yet but plan to distinguish note_off behavior on 'per note' and 'all notes' basis
		self.clocknudge = 4	     ## let a few clocks go by when starting listening drum machine
		self.procs      = []	    
		self.tasks      = []

		self._pan	= [1,1]

		if not pygame.get_init():
			pygame.mixer.init()

		self.sounds     = []    ## pygame sounds 

		self.is_play    = 0

		## surrendering to passing a port at __init__
		##   dont want it to interrupt testing though
		## 201226 - why not staple BasePorts onto here?
		##  reminder outport is needed for passing clock to drum machine
		self.inport     = inport
		self.outport    = outport
		if not inport:      
			self.inport     = self.port_i
		if not outport:     
			self.outport    = self.port_o

		BasePorts.port_namer2(self.inport, cliname=self.__class__.__name__, ptname="Slicer_I")
		BasePorts.port_namer2(self.outport, cliname=self.__class__.__name__, ptname="Slicer_O")

		self.lastrecd   = None
		self.lastsent   = None

		logpr("{}.init: {}".format(self.__class__.__name__, self))
		logpr(self.__doc__)

		## logpr does this now  #########
		## actually no it doesnt if basedir is overridden!!
		if not os.path.isdir(self.BASEDIR):
			try:
				os.system('mkdir -p {}'.format(self.BASEDIR))
			except Exception as ee:
				print(ee)
				time.sleep(4)
				exit()

	def __str__(self):
		return "<aSlicer: basedir={}, ch={}, bpm/s='{}/{}', snds={}, nudge={}, mt={}, mono={}>".format(
			self.BASEDIR,
			self.channel,
			self.bpm, self.shifttempo,
			len(self.sounds),
			self.clocknudge,
			self.multitrig,
			self.mono
			)

	@property
	## newfound knowledge, or breaking fixed things?
	def stdscr(self):
		if not hasattr(self, '_stdscr'):
			self._stdscr = None
		return self._stdscr
	@stdscr.setter
	def stdscr(self, scr):
		if not scr:
			curses.initscr()
			curses.start_color()
			curses.init_color(0,0,0,0)
			self._stdscr = curses.newwin(0,0, 50, 50)
			self._stdscr.nodelay(1)
		else:
			self._stdscr = scr

	@property
	def infile(self):
		if not hasattr(self, '_infile'):
			self._infile = None
		if self._infile:
			return self._infile
	@infile.setter
	def infile(self, filename):
		if filename and os.path.isfile(filename):
			self._infile = filename

	@property
	def CCD(self):		## composed in Slice
		if not hasattr(self, '_CCD'):
			self._CCD = {}
		return self._CCD


	@staticmethod
	def filecheck(filename):
		if filename and os.path.isfile(filename):
			return True


	@property
	def fetch_ch(self):	## return pygame mixer channel with pans set
		ch = pygame.mixer.find_channel()
		if ch:	## might be None if out of channels
			ch.set_volume(*self._pan)
		return ch
		

	def keyCheck(self, iKey, debug=0):
		if iKey == ord('q'):
			return True
		elif iKey == ord('Q'):
			exit()
		elif iKey == ord(' '):
			self.Silence()
		elif iKey == ord('+'):
			self.clocknudge += 1
		elif iKey == ord('-'):
			self.clocknudge -= 1
			self.clocknudge = max(self.clocknudge, 0)
		elif iKey == ord('t'):
			self.multitrig = not self.multitrig
		elif iKey == ord('m'):
			self.mono = not self.mono
		elif iKey in [ord('V'), ord('v')]:
			factor = {ord('V') : 1.2, ord('v') : 0.8}[iKey]
			for s in self.sounds:
				oldvol = s.get_volume()
				s.set_volume(oldvol * factor)
				if debug:
					print(s.get_volume())

		## dont need a lot of properties or functions, just make/maintain the [L,R] here
		elif iKey == curses.KEY_LEFT:
			self._pan = [ min(1, (self._pan[0] * 1.2)), self._pan[1] * 0.8 ]
		elif iKey == curses.KEY_RIGHT:
			self._pan = [ self._pan[0] * 0.8, min(1, (self._pan[1] * 1.2)) ]
		elif iKey == curses.KEY_UP:
			self._pan = [max(0.2, min(1, x * 1.2)) for x in self._pan]
		elif iKey == curses.KEY_DOWN:
			self._pan = [x * 0.8 for x in self._pan]


	def msgCheck(self, msg, debug=0):
		## 210702 - some subclasses are not using the conditional return for anything,
		##  working to add some CC controls here
		if msg:
			if msg.type in ['note_on', 'note_off']:
				if msg.channel == self.channel:
					self.lastrecd = msg
					return True
			elif msg.type == 'control_change':
				if msg.channel == self.channel:
					if msg.control == 20:
						if msg.value != 0:
							self.multitrig = not self.multitrig 
							#print(" multi-trigger changed for {}".format(self.channel))
							print(msg)
					elif msg.control == 21:
						if msg.value != 0:
							self.mono = not self.mono
							#print(" mono-trigger changed for {}".format(self.channel))
							print(msg)
					elif msg.control == 7:		## 220411
						_newvol = msg.value / 127
						[s.set_volume(_newvol) for s in self.sounds]

						
		
				
		
	## 210613 - just taping this here so more classes can be used for
	##   1-off running.  its from BeatPitch
	def Checks(self):
		self.msgCheck(self.inport.poll())
		self.keyCheck(self.stdscr.getch())

	def draw(self, yy=0, xx=0, max_w=48, debug=0):
		volstr = "-"
		if self.sounds and self.sounds[0]:
			volstr = " {:<.3f}".format(self.sounds[0].get_volume())

		## 210616 - 
		try:
			mmstr	= "{:<8} n={:<3d} ch={:<2d} v={:<3d}"
			rstr	= mmstr.format(self.lastrecd.type, self.lastrecd.note, self.lastrecd.channel, self.lastrecd.velocity) if self.lastrecd else None
			sstr	= mmstr.format(self.lastsent.type, self.lastsent.note, self.lastsent.channel, self.lastsent.velocity) if self.lastsent else None
		except Exception as ee:
			print(self.lastrecd)
			print(self.lastsent)
			input(ee)

		#for f in [      
		strlist = [
				'\{:<}'.format('____ {} ____'.format(type(self).__name__)), 
				'ch={:x}, bpm/s={}/{}'.format(self.channel, self.bpm, self.shifttempo),
				'# of sounds: {}'.format(len(self.sounds)),
				'rel_off [t]: {}'.format(self.multitrig),
				'allow_2 [m]: {}'.format(self.mono),
				'nudge [+/-]: {}'.format(self.clocknudge),
				'recd: {}'.format(rstr), 
				'used: {}'.format(sstr), 
				'in   {}'.format(self.inport.name[-5:]),
				'out  {}'.format(self.outport.name[-5:]),
				'pvol {}'.format(volstr),
				'pan  ({:4.2f}, {:4.2f})'.format(self._pan[0], self._pan[1]),
				]

		## 210616 - moved down here to use len of all the stuff to print, for window size
		if not hasattr(self, '_draw_win'):
			self._draw_win = curses.newwin(len(strlist)+1, max_w, yy, xx)

		dscr = self._draw_win

		ll 	= 0
		www	= max_w - 2
		for f in strlist:
			dscr.addstr(ll, 0, "|{}|".format(' '*www))
			dscr.addstr(ll, 1, str(f)[:www])
			ll += 1

		dscr.addstr(ll, 0, '|{}|'.format('_'*(www-1)))
		dscr.refresh()
		return True


	def draw_progress(self, pstr=None, yy=4, xx=40, max_w=80, max_h=30, cattr=None, debug=0):
		## window draw for while slicing since it is a big timeout
		##  with no screen output, also maybe errors.
		##  call this during Slice, when filenames are made and when exceptions happen
		##  call w/no pstr to highlight last line with '->', points at cursor location
		if not hasattr(self, '_progresswin'):
			self._progresswin = curses.newwin(max_h, max_w, yy, xx)
			self._linespw = []

		self._progresswin.clear()       ## blinks but will usually be slow for meaty files

		tstr    = "-- Slice progress: --"
		last    = "    ->"

		aattr   = curses.A_REVERSE
		if cattr:       ## hard to pass
			self._progresswin.attron(cattr)

		if pstr == None:
			self._linespw.append(last)
		else:
			self._linespw.append(str(pstr))

		while len(self._linespw) >= (max_h - 2):
			self._linespw.pop(0)

		self._progresswin.addstr(0, 0, tstr, aattr)

		for ix, line in enumerate(self._linespw):
			if ix == (len(self._linespw) - 1):
				self._progresswin.addstr(ix+1, 0, line, aattr)
			else:
				self._progresswin.addstr(ix+1, 0, line)

			if ix >= (max_h - 2):
				self._linespw.remove(self._linespw[0])
				
		self._progresswin.refresh()
		


	def Listen(self, stdscr=None, ret_if=False, debug=0):
		logpr("{}.Listen\t{}".format(self.__class__.__name__, self))
		stdscr = self.stdscr

		iii = self.inport
		ooo = self.outport

		## 211006 - need to decide which version of this to use, class or imported...
		port_namer(self.inport, mdname="SLICER_I")
		port_namer(self.outport, mdname="SLICER_O")

		## trick so main test loop can get at it
		## 201226 - grappling with this re: contextmanager.  if port is there to pass in we wouldnt need to return it
		if ret_if:
			return iii, ooo
	
		if not (self.sounds and self.sounds[0]):
			print("  no self.sounds, quitting Listen")
			time.sleep(2)
			return

		print("  LISTENING on '{}', ch={}".format(iii.name, self.channel+1)) 
		print(self.lastrecd)
		#print("  FWD to '{}'".format(ooo.name))
		counter = -1
		try:
			while True:
				iKey = stdscr.getch()
				if iKey != -1:
					stdscr.refresh()

				## want to look at specific exceptions now
				self.draw(yy=16, xx=20)

				msg = iii.poll()
				self.msgCheck(msg, debug=debug)

				if msg:
					thrumsg = None

					if msg.type == 'clock' and counter > -1:
						counter -= 1

					if (msg.type == 'stop') or (msg.type == 'songpos' and msg.pos == 0):
						counter = self.clocknudge     ## skip this many midi clocks, to align ex: ER-1
						thrumsg = mido.Message(type='stop')
					if counter == 0:
						thrumsg = mido.Message(type='start')
					elif counter < 0:
						if (msg.type != 'songpos') and (msg.type != 'start'):
							thrumsg = msg.copy()
					else:
						pass #print("skipping")

					if thrumsg:
						## 210822 - trying maybe dont forward notes, clutters things up.  forward clock.
						if thrumsg.type not in ['note_on', 'note_off']:
							ooo.send(thrumsg)
						#if msg.type not in ['clock', 'stop', 'start']:	 ## nicer display
						if 'note' in msg.type:
							self.lastsent = thrumsg

				if self.keyCheck(iKey, debug=debug) == True:
					return

		except KeyboardInterrupt:
			print("\n\n\tgot ctrl-c\n")
			return

	def retPorts(self):     ## 210327 - should put the actual stuff here and call it from Listen.  but is Listen used for ports?
		return self.Listen(ret_if=True)


	def Silence(self, ix=None):
		try:
			for s in self.sounds:
				if s:
					s.stop()
		except IndexError as ee:
			print("Silence {}".format(ee))
			time.sleep(1)




	## pydub play for task making
	## 210517 - might want to go back to this, can tweak the AudioSegments more directly than loaded pygame.mixer sounds
	##   could do it in Wavcut, before Pitch?
	def pdPlay(self, ix):   
		play(self.slices[ix])

	## 210517 - or make the class carry a volume property, and reserve a channel for every play?
	## 210530 - if we retreive a channel from mixer before playing (quick, apparently) we can set L/R
	def pygamePlay(self, ix, stop=False):   
		try:
			if not self.multitrig:  # or self.is_play > 8:
				self.Silence()

			if self.sounds[ix]:
				if stop:	## from 'note_off' in msgCheck
					if self.mono:
						self.sounds[ix].stop()
						self.is_play -= 1
				else:
					if self.fetch_ch:
						self.fetch_ch.play(self.sounds[ix])
						#self.sounds[ix].play()
						self.is_play += 1
					else:
						print("didnt play {}".format(ix))
		except IndexError as ee:
			print("pygamePlay index error: {}".format(ee))
			#time.sleep(1)

			

########################################################################################
########################################################################################
class Beats(aSlicer):
	''' slice a wav into 16 or other sequential slices, trigger with midi   '''

	_resos      = [1.0, 0.1, 0.01]
	_ofilefmt   = '{}/step{:02d}.wav'
	_mfilefmt   = '{}/step{:02d}_mod.wav'       ## modified some way like tempo shift
	_sTypes     = [4, 8, 16, 32, 64]		## x-times to slice over sample

	def __init__(self, infile, **kwargs):
		aSlicer.__init__(self, infile, **kwargs)    ## this seems neater but isnt init a good place for table of attrs?
		#self.multitrig  = False
		#self.nSlice     = 2     ## ix of _sTypes, 16 default
		self.slices     = []
		self.hlight	= []

		self.resolution = 0     ## setter uses ix

		logpr("{}.init: {}".format(self.__class__.__name__, self))
		logpr(self.__doc__)


	@property
	def selected(self):
		if not hasattr(self, '_selected'):
			self._selected = 0
		return self._selected
	@selected.setter
	def selected(self, value):
		self._selected = value%self.nSlice

	@property
	def resolution(self):
		if not hasattr(self, '_resolution'):
			self._resolution = self._resos[0]
		return self._resolution
	@resolution.setter
	def resolution(self, ix):
		self._resolution = self._resos[ix%len(self._resos)]

	@property
	def nSlice(self):
		if not hasattr(self, '_nSlice'):
			## initial resolution of slicing
			self._nSlice = self._sTypes[3]
		return self._nSlice
	@nSlice.setter
	def nSlice(self, ix):
		self._nSlice = self._sTypes[ix%len(self._sTypes)]


	def Slice(self, stomp=True, shifttempo=None, notempo=False, onlyreload=False, debug=0):
		logpr("{}.Slice: {}".format(self.__class__.__name__, self))

		width   = (self.nSlice * 60) / self.bpm
		width   = width / (self.nSlice / 16)
		delta   = 0
		for f in range(self.nSlice):
			outfile  = self._ofilefmt.format(self.BASEDIR, f)
			outfile2 = self._mfilefmt.format(self.BASEDIR, f)

			logpr("{}.Slice: outfile={}".format(self.__class__.__name__, outfile))
			logpr("\tst={}, nt={}, onlyreload={} ".format(shifttempo, notempo, onlyreload))
			if not onlyreload and self.infile and os.path.isfile(self.infile):
				single_split(delta, delta + (width / self.nSlice), self.infile, outfile, debug=0)       ## 0 on purpose

			if (self.shifttempo != self.bpm):
				self.draw_progress(pstr=outfile2)
				## 210513 - was confused by this but if tempo is shifted:
				##	make the file then shift its tempo, in separate functions
				logpr("{}.Slice: source={}, outfile={}\ttempo shift".format(self.__class__.__name__, outfile, outfile2))
				if not onlyreload:	
					doOnlyTempo(source=outfile, outfile=outfile2, tempofactor=(self.shifttempo / self.bpm), debug=debug)
				outfile = outfile2
			else:
				self.draw_progress(pstr=outfile)

			delta += (width / self.nSlice)

			try:
				logpr("{}.Slice: try append '{}' to pygame mixer".format(self.__class__.__name__, outfile))
				logpr("OUTFILE = {}".format(outfile))
				self.sounds.append(pygame.mixer.Sound(outfile))
			except pygame.error as ee:
				self.sounds.append(None)    ## makes correct list len regardless
				self.draw_progress(pstr="pygame.error: {}".format(outfile))
				logpr("{}.Slice: EXCEPTION '{}' with file '{}'".format(self.__class__.__name__, ee, outfile))
			except FileNotFoundError as ff:
				self.sounds.append(None)    ## makes correct list len regardless
				self.draw_progress(pstr="FileNotFound: {}".format(outfile))
				logpr("{}.Slice: EXCEPTION '{}' with file '{}'".format(self.__class__.__name__, ff, outfile))
			#time.sleep(2)
				

		self.draw_progress()
		logpr("{}.Slice: finished {}".format(self.__class__.__name__, outfile, self))


	def msgCheck(self, msg, debug=0):
		if super().msgCheck(msg, debug=debug):
			#ix = (msg.note+16)%len(self.sounds)
			ix = msg.note - 36

			if ix < len(self.sounds):
				if debug:       print("msgCheck: recd '{}', playing '{}'".format(msg, ix))
				self.pygamePlay(ix, stop=((msg.type == 'note_off') or (msg.velocity == 0)))
				(msg.type == 'note_on' and ix not in self.hlight) and self.hlight.append(ix)
				(msg.type == 'note_off' and ix in self.hlight) and self.hlight.remove(ix)


	## for kit picker not workin for Beats yet
	## 210530 - workin ok now!
	def reffromNote(self, note, debug=0):
		ix = note - 36
		if ix < len(self.sounds):
			return self.sounds[ix]
			
	def fnamefromNote(self, note, debug=0):
		ix = note - 36
		if ix < len(self.sounds):
			if self.bpm != self.shifttempo:		
				return self._mfilefmt.format(self.BASEDIR, ix)
			return self._ofilefmt.format(self.BASEDIR, ix)


	def keyCheck(self, iK, debug=0):
		if super().keyCheck(iK, debug=debug):
			return True

		## no curses?
		lrDict = { 260 : -1, 261 : 1 }
		if iK in lrDict.keys():
			self.selected += lrDict[iK]
			if self.stdscr:
				self.stdscr.refresh()

		elif iK == ord(' '):
			play(self.slices[self.selected])

		elif iK in range(ord('0'), ord('9') + 1):
			self.selected = iK - ord('0')
		elif iK in range(ord('a'), ord('f')+ 1):
			self.selected = iK - ord('a') + 10

	## DRAW ####
	###################
	def draw_bar(self, yy=0, xx=0, debug=0):
		CPR = 8		## cells per row
		ffmt = "- {:02d} -"	## regular draw
		sfmt = "->{:02d}<-"	## if selected
		hfmt = "##{:02d}##"	## if active
		MW = len(sfmt.format(0)) * CPR	## max width
		MH = int(self.nSlice / CPR) + 8


		if not hasattr(self, '_barwin'):
			self._barwin = curses.newwin(MH, MW, yy, xx)
			curses.init_pair(20, curses.COLOR_RED, curses.COLOR_BLACK)
			curses.init_pair(21, curses.COLOR_RED, curses.COLOR_WHITE)

		self._barwin.erase()
		self._barwin.addstr(0, 2, "MIDI in: '{}'".format(self.inport.name.split(':')[0]))

		self._barwin.attron(curses.color_pair(20))
		xc = 0
		yc = 1

		for f in range(self.nSlice):
			cell = ffmt.format(f) 
			if self.selected:
				cell = sfmt.format(f) 

			if f in self.hlight:	
				cell = hfmt.format(f) 
				self._barwin.addstr(yc, xc, cell, curses.A_REVERSE)
			else:
				self._barwin.addstr(yc, xc, cell) 

			xc += len(cell)
			if xc >= (CPR * len(cell)):
				xc = 0
				yc += 1

		if f and self.lastrecd:		## 220507 - made printing look a little better but, what is this logic?
			_kwa	= dict( ch=self.lastrecd.channel, nn=self.lastrecd.note, vv=self.lastrecd.velocity )
			_str_dec 	= " ".join(["{}={:3d}".format(k, v) for k, v in _kwa.items()])
			_str_hex 	= " ".join(["{}={:3x}".format(k, v) for k, v in _kwa.items()])
			for i, x in enumerate([_str_dec, _str_hex]):
				_x = "{} {}".format(x, self.lastrecd.type)
				self._barwin.addstr(yc + i + 0, 2, x)
		


		self._barwin.refresh()
		self._barwin.attroff(curses.color_pair(21))


	def draw_rows(self, yy=0, xx=0, debug=0):
		ifmt = "{}={}, {}={}"
		for f in range(len(self.slices)):
			if f == self.selected:
				#self.stdscr.addstr(yy, xx, str(self.slices[f]), curses.A_REVERSE)
				self.stdscr.addstr(50,60, str(dir(self.slices[f])))
			else:
				#self.stdscr.addstr(yy, xx, str(self.slices[f]))
				self.stdscr.addstr(yy, xx, ifmt.format('framrat', self.slices[f].frame_rate, 'frct', self.slices[f].frame_count()))
			yy += 1


	def draw(self, yy=0, xx=0, debug=0):
		if not super().draw(yy=yy, xx=xx, debug=debug):
			return
		yy += 4
		xx += 66
		self.draw_bar(yy=yy, xx=xx, debug=debug)
		#self.draw_rows(yy=yy+2, xx=xx, debug=debug)



########################################################################################
########################################################################################


class Pitches(aSlicer):
	''' making available the pitch from a table for a given note name
		ex: 'A4' = 440Hz	'''

	_ofilefmt = '{}/file_{}.wav'
	_mfilefmt = '{}/file_{}_mod.wav'

	def __init__(self, infile, basenote='A4', **kwargs):
		aSlicer.__init__(self, infile, **kwargs)
		self.BASENOTE   = basenote
		self.multitrig  = True
		self.mono       = True

		logpr("{}.init: {}".format(self.__class__.__name__, self))
		logpr(self.__doc__)


	def Slice(self, stomp=True, shifttempo=None, notempo=False, onlyreload=False, debug=0):
		logpr("{}.Slice: {}".format(self.__class__.__name__, self))

		if not self.filecheck(self.infile):
			self.draw_progress("filecheck fail: {}".format(self.infile))
			self.draw_progress()
			time.sleep(2)
			return

		else:
			self.sounds = []
			self.tails  = []

			## more readable than transforming shifttempo?
			## currently not using kwarg to function in pwavcut
			if shifttempo:
				factor = shifttempo / self.bpm
			else:
				factor = self.shifttempo / self.bpm    

			fstr = self.BASEDIR + "/file_{}.wav"

			if os.path.isfile(fstr.format(self.BASEDIR, self.BASENOTE)) and not stomp:
				print("nostomp, found A4")
				return

			#r1 = getKeyIx(self.BASENOTE) - 24
			#r2 = getKeyIx(self.BASENOTE) + 25 
			for f in range(-24, 25):
				if factor == 1:
					ofn = self._ofilefmt.format(self.BASEDIR, list(notes)[getKeyIx(self.BASENOTE) + f])
				else:
					ofn = self._mfilefmt.format(self.BASEDIR, list(notes)[getKeyIx(self.BASENOTE) + f])

				tailfile = os.path.splitext(ofn)[0] + "_tail.wav" 


				if not onlyreload:
					doffmpeg(f, assumenote=self.BASENOTE, source=self.infile, outfile=ofn, notempo=notempo, shifttempo=factor, debug=debug)
				try:
					logpr("Pitches.Slice: factor={}, st={}, nt={}, onlyreload={}, ".format(factor, shifttempo, notempo, str(onlyreload).upper()) + ofn)
					## need to check if pre-existing: file exists but also its in pyg.mixer.
					## are we mega-reloading redundant files?
					sss = pygame.mixer.Sound(ofn)
					self.sounds.append(sss)
					#self.tails.append(make_tail(ofn, tailfile, debug=debug))
					self.draw_progress(pstr=ofn)
				#except pygame.error as ee:
				#	self.draw_progress(pstr="pygame.error: {}".format(ofn))     ## still got a traceback with 'outfile'
				except FileNotFoundError as ff:
					self.draw_progress(pstr="FileNotFound: {}".format(ofn))

			self.draw_progress()    ## no 'pstr' means done?
			logpr("Pitches.Slice finished\t{}".format(self))

	
	def msgCheck(self, msg, debug=0):
		if super().msgCheck(msg, debug=debug):
			if debug:       print("msgCheck: recd '{}'".format(msg))
		       
			## 210202 - quicker loop?  
			if not hasattr(self, '_msgCheckRange'):
				self._msgCheckRange = range(getKeyIx('A2'), getKeyIx('A6'))
 
			if msg.note in self._msgCheckRange:
				## need to maybe convert between lll.index and msg.note,
				##   right now currently playing note stops when previous note is lifted
				##   (with some settings, other settings are cool)
				self.pygamePlay(self._msgCheckRange.index(msg.note), stop=((msg.type == 'note_off') or (msg.velocity == 0)))

				if debug:
					print("msgCheck: '{}'".format(msg))


	def reffromNote(self, note, debug=0):
		ix = note - getKeyIx('A2')
		if ix < len(self.sounds):
			return self.sounds[ix]

	def fnamefromNote(self, note, debug=0): 
		#note = note - getKeyIx('A2')
		if (note - 33) < len(self.sounds):
			if self.bpm != self.shifttempo:
				return self._mfilefmt.format(self.BASEDIR, list(notes)[note])
			return self._ofilefmt.format(self.BASEDIR, list(notes)[note])




#####################################################################
#####################################################################
class Tempos(Pitches):
	'''
		Tempos(Pitches): similar slicing but no pitch shifting.
	      		count number of keys to match sample tempo with whats playing.
			hopefully parent Pitches methods mostly work
	'''
	def __init__(self, infile, basenote='A4', **kwargs):
		super().__init__(infile, basenote, **kwargs)
		logpr("{}.init: {}".format(self.__class__.__name__, self))
		logpr(self.__doc__)


	def Slice(self, **kwargs):
		logpr("{}.Slice: {}".format(self.__class__.__name__, self))

		onlyreload      = 'onlyreload'  in kwargs and kwargs['onlyreload']
		debug	   = 'debug'       in kwargs and kwargs['debug']

		if self.filecheck(self.infile):
			self.sounds = []

			for f in range(-24, 25):
				ofn = self._ofilefmt.format(self.BASEDIR, list(notes)[getKeyIx(self.BASENOTE) + f])
				factor = 1 + (f * 0.02)

				self.draw_progress(pstr=ofn)

				if not onlyreload:
					#debug = 1
					doOnlyTempo(source=self.infile, outfile=ofn, tempofactor=factor, debug=debug)
				try:
					self.sounds.append(pygame.mixer.Sound(ofn))
				except pygame.error as ee:
					self.draw_progress(pstr=ee)
				except FileNotFoundError as ff:
					self.draw_progress(pstr=ff)

			self.draw_progress(pstr=ofn)


#####################################################################
#####################################################################
class BeatPitch(Beats):
	"""
		BeatPitch(Pitches): attempt to do beat slice, then also slice along pitches.
			then mapping CC# to pitch up/down thru beat slice lists  
	"""
	def __init__(self, infile, basenote='A4', **kwargs):
		super().__init__(infile, **kwargs)
		self.BASEDIR += "/BP"
		if not os.path.isdir(self.BASEDIR):
			os.system("mkdir %s" %self.BASEDIR)
		self.multitrig = True

		self._rolltime 		= 0
		self._rollfactor	= 2
		self.hlight		= []

		logpr("{}.init: {}".format(self.__class__.__name__, self))
		logpr(self.__doc__)


	@property
	def pitchptr(self):
		if not hasattr(self, '_ccval'):
			## idea is this stores CC value but outputs pitch offset like -2, 4, etc
			self._ccval	= 63

		## 'flick' is max num of knob changes in 1 direction before change to next ix
		flick = 1 if self.nlptr == 0 else 8
		nlist = self.nlist
		return nlist[int(self._ccval/flick)%len(nlist)]	
		return nlist[self._ccval%len(nlist)]
	@pitchptr.setter
	def pitchptr(self, val):
		self._ccval	= min(max(0, val), 127)

	@property
	def nlist(self):
		if not hasattr(self, '_nlist'):
			self._nlists 	= [
				range(-24, 25),
				[-12, -9, -5, 0, 3, 7, 12],
				[-12, -9, -5, 0, 3, 7, 12, 7, 3, 0, -5, -9],
				[0, 3, 7, 12, 7, 3, 0, -5, -9, -12, -9, -5],
				[-12, -8, -5, 0, 3, 7, 12, 7, 4, 0, -5, -9],
					]
		return self._nlists[self.nlptr]
	@property
	def nlptr(self):
		if not hasattr(self, '_nlptr'):
			self._nlptr = 2
		return self._nlptr
	@nlptr.setter
	def nlptr(self, ix):
		self._nlptr = ix%len(self._nlists)


	def __str__(self):
		return "<BeatPitch: lCCD={}, pptr={}, ccptr={}>, nslice={}, nlptr={}/{}>".format(
			len(self.CCD.keys()), self.pitchptr, self._ccval, self.nSlice, self.nlptr, len(self._nlists)	)


	def Slice(self, stomp=True, shifttempo=None, notempo=False, onlyreload=False, debug=0):
		logpr("{}.Slice: {}".format(self.__class__.__name__, self))

		if not self.infile or not os.path.isfile(self.infile):
			print("{}.Slice: no infile '{}'".format(self.__class__.__name__, self.infile))
			return
			
		print("BEATPITCH: SLICING")

		astr 	= self.BASEDIR + "/{:02d}_step"
		width	= (self.nSlice * 60) / self.bpm
		width   = width / (self.nSlice / 16)

		#width	= 60 / (self.bpm * 16)	## reduced

		self._CCD = {}
		for pitch in range(-24, 25):
			ix = getKeyIx('A4') + pitch
			hz = notes[list(notes)[ix]]
			tempofactor = hz / notes['A4']

			bstr = astr.format(getKeyIx('A4') + pitch) 		## ex: /tmp/src_o/slot02/53_step.wav

			outfile = "{}.wav".format(bstr)
			if not onlyreload:
				doffmpeg(pitch, source=self.infile, outfile=outfile, debug=1)

			delta = 0
			counter = 0
			self._CCD.update({ pitch : [] })
			for f in range(self.nSlice):
				outfile2 = "{}{:02d}.wav".format(bstr, f)	## ex: /tmp/src_o/slot02/53_step04.wav


				if not onlyreload:
					single_split(delta, delta + (width / self.nSlice), outfile, outfile2, debug=0)       ## 0 on purpose
					delta += (width / self.nSlice)
				try:
					#hhh = pygame.mixer.Sound(outfile2)

					AS = AudioSegment.from_wav(outfile2)
					AS.set_frame_rate(44100)

					#self._CCD[pitch].append([outfile2, AS])
					self._CCD[pitch].append([outfile2, pygame.mixer.Sound(outfile2)])
					lstr = "self._CCD[{}].append([{}, AudioSegment.from_wav({})])".format(pitch, outfile2, outfile2)
					logpr(lstr)
					self.draw_progress(pstr=lstr)
					counter += 1

				except Exception as ee:
					self._CCD[pitch].append([outfile2, None])
					lstr = "self._CCD[{}].append([{}, None]) | AudioSegment or Index fail? '{}')".format(pitch, outfile2, ee)
					logpr(lstr)
					self.draw_progress(pstr=lstr)

			lstr = "BeatPitch Slice DONE ({} sounds)"
			logpr(lstr)
			self.draw_progress(pstr=lstr)

	def Checks(self):
		self.msgCheck(self.inport.poll())
		self.keyCheck(self.stdscr.getch())


	def keyCheck(self, ikey):
		if ikey == -1:
			return
		##  we do want to override Beats (uses self.slots when this will use dict)
		##     but super() will set lastrecd attr
		if super().keyCheck(ikey):
			if self.stdscr:
				curses.endwin()
			print("exiting")
			exit()

		if ikey == ord('r'):
			self.stdscr.clear()
		elif ikey == ord('R'):
			self.stdscr.refresh()


	## CCD is 	{ pitch : [ [filename, asound] ] }
	def msgCheck(self, msg):
		def _STOP(msg):
			if msg and 'note_' in msg.type:		return msg.type == 'note_off' or msg.velocity == 0
			else:					return False

		super().msgCheck(msg)
		if not msg or not hasattr(msg, 'channel') or msg.channel != self.channel:
			return

		PCC = 80	## CC num to respond to 
		PDD = 81	## for roll
		PEE = 82	## to change notelist
		if msg.type in ['note_on', 'note_off']:
			## index 0 of the range (-24, 25) or w/e it is, is note 36
			#self.pygamePlay(msg.note - 36, stop=((msg.type == 'note_off') or (msg.velocity == 0)))
			#print("############################ PLAY ######################")
			ix = msg.note - 36
			self.pygamePlay(msg.note - 36, stop=_STOP(msg))
			self._rolltime = time.time()
			(msg.type == 'note_on' and ix not in self.hlight) and self.hlight.append(ix)
			((msg.type == 'note_off' or msg.velocity == 0) and ix in self.hlight) and self.hlight.remove(ix)

		elif msg.type == 'control_change':
			if msg.control in [PCC, PDD, PEE]:
				print(msg)
				if msg.control == PEE:
					self.nlptr += 1
					self.stdscr.erase()
					return

				#width	= 60 / (self.bpm * 16)	## reduced
				self.pitchptr = msg.value
				if self.lastrecd:
					if msg.control == PCC or (time.time() > self._rolltime + (60 / (self.bpm * self._rollfactor))):
						print("############################ PLAY ###################### (roll={}, factor={})".format(msg.control == PDD, self._rollfactor))
						ix = self.lastrecd.note - 36
						self.pygamePlay(self.lastrecd.note - 36, stop=_STOP(msg))
						self._rolltime = time.time()
						## should we property this

						ix in self.hlight and self.hlight.remove(ix)
						(msg.type == 'note_on' and ix not in self.hlight) and self.hlight.append(ix)
						((self.lastrecd.type == 'note_off' or self.lastrecd.velocity == 0) and ix in self.hlight) and self.hlight.remove(ix)
				
				

		elif msg.type in ['clock', 'start', 'stop', 'songpos']:
			pass
		####

	
	def draw(self, **kwargs):
		self.stdscr.addstr(0, 0, str(self))
		astr = "nlptr={}, nlist={}".format(self.nlptr, self.nlist)
		self.stdscr.addstr(1, 0, astr)
		kwargs['yy'] = 3
		Beats.draw(self, **kwargs)


	def reffromNote(self, ix, debug=0):
		if self.pitchptr in self.CCD:
			try:
				if debug:	logpr(str(self.CCD[self.pitchptr][ix]))
				return self.CCD[self.pitchptr][ix]
			except IndexError:
				if debug:	logpr("failed: " + str(self.CCD[self.pitchptr][ix]))
				return


	def fnamefromNote(self, ix, debug=0): 
		if self.pitchptr in self.CCD:
			pp = self.CCD[self.pitchptr]
			if ix < len(pp):
				pp[ix]
				astr 		= self.BASEDIR + "/{:02d}_step"
				bstr 		= astr.format(getKeyIx('A4') + self.pitchptr)
				outfile2 	= "{}{:02d}.wav".format(bstr, ix)	## ex: /tmp/src_o/slot02/53_step04.wav
				print("stop!  check this function")
				input(outfile2)


	def pygamePlay(self, ix, stop=False):   
		logpr("running pygamePlay ({})".format(self.__class__.__name__))
		try:
			if not self.multitrig: 
				self.Silence()

			if self.pitchptr in self.CCD.keys():
				#if ix in range(getKeyIx('A2'), getKeyIx('A6')):
				if True:
					obj = self.CCD[self.pitchptr][ix]
					if stop:	## from 'note_off' in msgCheck
						if self.mono:
							if obj[1]:
								obj[1].stop()
								self.is_play -= 1
					else:
						if obj[1]:
							self.fetch_ch.play(obj[1])
							#obj[1].play()
							self.is_play += 1
			else:
				print("didnt play {}".format(ix))

		except IndexError as ee:
			print(ee)
			#time.sleep(1)

	def pydubPlay(self, ix, stop=False, debug=0):
		logpr("trying to play note {}".format(ix))
		ref = self.reffromNote(ix, debug=debug)
		if ref and ref[1]:
			try:
				logpr("{} | {}".format(ref[0], ref[1].duration_seconds))
				play(ref[1])
			except ValueError as vv:
				logpr("pydubPlay had trouble with {} | '{}'".format(ref[0] or None, vv))
			



#####################################################################
#####################################################################
class Kit(aSlicer):
	'''     Kit: for selecting various other slices (pitch shift, beat slice) into a set on 1 ch.   '''

	_ofilefmt = '{}/kit/kit_{:02d}.wav'
	MAX_S   = 16

	def __init__(self, **kwargs):
		aSlicer.__init__(self, None, **kwargs)

		kdir = os.path.join(self.BASEDIR, 'kit')
		not os.path.isdir(kdir) and os.mkdir(kdir)

		self.multitrig  = not False
		self.mono       = True

		self.hlight     = []    ## show output when active.  cool for base class?  do we draw enough of them?
		self.pad_desc   = []    ## description of where pad was imported from

		self.loadExisting()

		yy = 2
		xx = 100 
		self._screen = curses.newwin(18, 80, yy, xx)

		logpr("{}.init: {}".format(self.__class__.__name__, self))
		logpr(self.__doc__)


	## roughly, Slice() and Slice(onlyreload)
	def addToKit(self, pObj, note, desc=None, debug=0):
		logpr("{}.addToKit: {}".format(self.__class__.__name__, self))

		if len(self.sounds) > self.MAX_S:
			print("Kit: is full")
			return

		asound = pObj.reffromNote(note)

		## replace with shutil
		cpsrc = pObj.fnamefromNote(note)	## each class can give file name that goes to sound obj from dict or list or w/e
		cpdst = self._ofilefmt.format(self.BASEDIR, len(self.sounds))	## now use self._ofilefmt for dest, with sequential new file name
		copyfile(cpsrc, cpdst)


		'''
		cmd = "cp {} {}".format(pObj.fnamefromNote(note), self._ofilefmt.format(self.BASEDIR, len(self.sounds)))
		input(cmd)
		p = myPopen(cmd)
		o,e = p.communicate()
		if debug:
			print(o,e, cmd)
			print("asound={}".format(asound))
			if debug > 1:
				time.sleep(4)
		'''
		if asound and (asound not in self.sounds):
			self.sounds.append(asound)
			self.pad_desc.append("from slot{:02d}, note='{}'".format(pObj.channel, note))
			if debug:
				print("Kit: adding from pObj<ch={}, note={}>".format(pObj.channel, note))
				if debug > 1:
					time.sleep(1)
			return True

	
	def addToKit_AoF(self, asound=None, filename=None, desc=None, debug=0):	## asound or filename.  doesnt copy to 'KIT0X.wav' yet
		logpr("{}.addToKit_AoF: {}".format(self.__class__.__name__, self))
		if len(self.sounds) > self.MAX_S:
			print("Kit: is full")
			return

		## passing asound seeming less and less ideal
		if asound:
			ref     = asound
			if not desc:    desc = "{}".format(asound)
		elif filename:
			ref     = pygame.mixer.Sound(filename)
			if not desc:    desc = "{}".format(filename)
		else:
			input("addToKit_AoF failed to add: asound={}, filename={}, ref={}".format(asound, filename, ref))
			return

		## not doing the copy to kit_X file which is ok but theyll be gone on quit			
		if ref and (ref not in self.sounds):
			self.sounds.append(ref)
			self.pad_desc.append(desc)
			if debug:
				print("Kit: adding from '{}'".format(desc))
				if debug > 1:   time.sleep(1)

			return True



	def loadExisting(self, debug=0):
		for f in range(self.MAX_S):
			afile = self._ofilefmt.format(self.BASEDIR, f)
			if os.path.isfile(afile):
				self.sounds.append(pygame.mixer.Sound(afile))
				self.pad_desc.append("loaded from existing kit_{:02d}.wav".format(f))
				

	def msgCheck(self, msg, debug=0):
		if msg and msg.type in ['note_on', 'note_off']:       
			ix = msg.note - 36		      ## assuming triggers are notes 36 thru 36+16

			if debug:
				print(ix, msg)
				if debug > 1:
					time.sleep(2)

			#if ix < min(len(self.sounds), 16):
			if ix < len(self.sounds):
				self.pygamePlay(ix, stop=((msg.type == 'note_off') or (msg.velocity == 0)))
				(msg.type == 'note_on' and ix not in self.hlight) and self.hlight.append(ix)
				(msg.type == 'note_off' and ix in self.hlight) and self.hlight.remove(ix)


	def keyCheck(self, iKey, debug=0):
			if iKey == ord('q'):
				return True
			elif iKey == ord('m'):
				self.mono = not self.mono
				self._screen.clear()
			elif iKey == ord('t'):
				self.multitrig = not self.multitrig
				self._screen.clear()
			

	def draw(self, yy=1, xx=50, max_w=40, colorP=None, debug=0):
		#if not hasattr(self, '_screen'):
		#	self._screen = curses.newwin(18, 80, yy, xx)
		## put in init

		dscr = self._screen

		ll   = 0
		dscr.addstr(ll, 0, "KIT: (ch={:1x}) T={}, M={}".format(self.channel, self.multitrig, self.mono))

		if colorP:
			dscr.attron(colorP)

		hlD     = {True:'X', False:' '}
		fstr    = "{:02d}: {}"

		for row in range(16):
			ll += 1
			dscr.addstr(ll, 0, fstr.format(row, " "*max_w))

			ostr = '-none-'
			if row < len(self.sounds):
				ostr = fstr.format(row, self.pad_desc[row]) + " {}".format(hlD[row in self.hlight])
				#ostr = fstr.format(row, self.sounds[row]) 

			dscr.addstr(ll, 0, ostr)

		if colorP:
			dscr.attroff(colorP)

		dscr.refresh()
			
	def selfpr(self):
		for f in self.sounds:
			print(f)
			


class Tones(Pitches):
	'''
		tone holder for list of audio files
		by default Sine from pydub
	'''
	_ofilefmt = "{}/{}.wav"
	def __init__(self, *args, **kwargs):
		kwargs['inCh'] = 1
		Pitches.__init__(self, "", *args, **kwargs)
		self.sounds	= []
		self.BASEDIR 	= '/tmp/source_out/Tones'

		[os.mkdir(x) for x in [self.BASEDIR] if not os.path.isdir(x)]
		if not pygame.mixer.get_init():
			pygame.mixer.init()

	def Slice(self, **kwargs):
		from pydub.generators import Sine

		if 'debug' in kwargs: 	debug = kwargs['debug']
		if 'export' in kwargs: 	export = kwargs['export']

		for p in range(-24, 25):
			nt	= list(notes)[getKeyIx('A4') + p]
			freq 	= notes[nt]
			obj 	= Sine(freq).to_audio_segment(duration=2000)
			estr	= self._ofilefmt.format(self.BASEDIR, nt)

			pg = pygame.mixer.Sound(buffer=obj.raw_data)
			self.sounds += [pg]

			astr = "freq={:> 8.2f}, note= {:<8}".format(freq, nt)
			if export:
				astr += ", export={}".format(estr)
				obj.export(estr)

			self.draw_progress(pstr=astr)

####  FFMPEG		################################################################
########################################################################################

## takes files whole length and shifts pitch.  shifttempo preserves length (therefore apparent tempo)
## even if pydub doesnt exactly do this, this is probably like what it would do (wrap ffmpeg)
def doffmpeg(   pitchix,
		assumenote='A4', 
		source='/tmp/source/slot00.wav', 
		outfile=None, 
		notempo=False, 
		shifttempo=1.0,
		debug=0
		):

	logpr("#"*60)
	logpr("doffmpeg:\n\tpitchix={} aNote={},\t\tsource={},\n\toutfile={},\n\tnotempo={}, shifttempo={}, debug={} ".format(pitchix, assumenote, source, outfile, notempo, shifttempo, debug))
	if debug:
		logpr("ffmpeg:  debug, more logging")
	logpr("#"*60)


	#A4IX = list(notes).index(assumenote)	    ## A4 index, or other note to calc from
	A4IX = getKeyIx(assumenote)
	nix  = max(0, A4IX + pitchix)		   ## also needs 'too high' check
	nkey = list(notes)[nix]			 ## string for the note, needed for filename
	nval = notes[nkey]			      ## numerator value
	head = "ffmpeg -y -i {}".format(source)
	tempofactor = 0


	if not outfile:
		outfile = "/tmp/source_out/DO_FFMPEG-file_{}.wav".format(nkey)    ## might crash
		logpr("doffmpeg: no outfile supplied, setting to '{}'".format(outfile))

	## 211006 - support lofi rate for RPI
	HIFI = check_platform()
	RATE = 44100 if HIFI else 44100 ## 11025

	logpr("doffmpeg: notempo={}".format(notempo))
	if notempo:
		ratefactor      = int(nval) / int(notes[assumenote])
		#cmd = "{} -af asetrate=44100*{} {}".format(head, ratefactor, outfile)   ## kinda like passing the fractions but i dunno
		#cmd = "{} -af asetrate=44100*{}/{} {}".format(head, int(nval * 100), int(notes[assumenote] * 100), outfile)
		cmd = "{} -af asetrate={}*{}/{} {}".format(head, RATE, int(nval * 100), int(notes[assumenote] * 100), outfile)
	else:

		tempofactor = ( int(notes[assumenote]) / int(nval) ) * 1 #shifttempo

		## values passed can only be expressed as powers of 2, ex: 2 or 1/2
		##  extend the command line options to recreate the fraction
		########################################### 
		if tempofactor < 0.5:
			ccc = 0
			while tempofactor < (1 / (2**ccc)):
				ccc += 1
			#tstr = "atempo=1/2,"*(ccc-1) + "atempo={:.8f}".format(tempofactor*(2**(ccc-1)))
			tstr = "atempo={:.8f},".format(tempofactor*(2**(ccc-1))) + "atempo=1/2"*(ccc-1) 

		elif tempofactor > 2:
			ccc = 0
			while tempofactor > (2**ccc):
				ccc += 1
			#tstr = "atempo=2,"*(ccc-1) + "atempo={}*{}/{}".format(tempofactor/(2**(ccc-1)), int(notes[assumenote]*100), int(nval*100))
			tstr = "atempo=2,"*(ccc-1) + "atempo={:.8f}".format(tempofactor/(2**(ccc-1)))
			tstr = "atempo={:.4f}".format(tempofactor)

		else:
			#tstr = "atempo={}/{}".format(int(notes[assumenote]*100), int(nval*100))
			tstr = "atempo={:.4f}".format(tempofactor)

		########################################### 
		if shifttempo < tempofactor:
			tstr += ",atempo={:.4f}".format(shifttempo)
			pass
		else:
			tstr = "atempo={:.4f},".format(shifttempo) + tstr
			pass

		########################################### 
		if tempofactor < 1:
			#cmd = "{} -af asetrate=44100*{}/{},{} {}".format(head, int(nval * 100), int(notes[assumenote] * 100), tstr, outfile)
			cmd = "{} -af asetrate={}*{}/{},{} {}".format(head, RATE, int(nval * 100), int(notes[assumenote] * 100), tstr, outfile)
		else:
			#cmd = "{} -af {},asetrate=44100*{}/{} {}".format(head, tstr, int(nval * 100), int(notes[assumenote] * 100), outfile)
			cmd = "{} -af {},asetrate={}*{}/{} {}".format(head, tstr, RATE, int(nval * 100), int(notes[assumenote] * 100), outfile)

	logpr("do_ffmpeg cmd | {}".format(cmd))

	p = myPopen(cmd)
	o, e = p.communicate()
	if debug:	
		logpr("do_ffmpeg results:\n O:\n{}\n E:\n{}".format(len(o.decode('ascii')), e.decode('ascii')))

	if not os.path.isfile(outfile):		## might exist previously and something failed
		logpr("ERROR: {} doesnt exist after ffmpeg command".format(outfile))



####  FFMPEG OTHER	  #################################################
#############################################################################
def doOnlyTempo(
		source='/tmp/source/slot00.wav', 
		outfile=None, 
		tempofactor=2.0, 
		debug=0
		):
	ddlog = "/tmp/source_out/doOnlyTempo.log"
	cmd = "ffmpeg -y -i {} -af atempo={:.2f} {}".format(source, tempofactor, outfile)	## does this work with low/high shift?
	logpr("doOnlyTempo: [{}]".format(cmd), filename=ddlog)

	if debug:
		print(cmd)
	p = myPopen(cmd)
	o,e = p.communicate()
	
	if debug:
		pass
		#logpr("doOnlyTempo results:\n\tOUT:\n{}\n\tERR:\n{}".format(o.decode('ascii'), e.decode('ascii')))

	logpr("doOnlyTempo: result file size= {}".format(os.stat(outfile).st_size), filename=ddlog)
	return True
	## do we even need setrate here?  could warp audio?
	#if tempofactor < 1:     cmd2  =  "{} -af asetrate=44100,atempo={:.2f} {}".format(head, tempofactor, outfile)
	#else:		   cmd2  =  "{} -af atempo={:.2f},asetrate=44100 {}".format(head, tempofactor, outfile)

def doOnlyPitch(
		source='/tmp/source/slot00.wav', 
		outfile=None, 
		pitchfactor=2, 
		debug=0
		):
	ddlog = "/tmp/source_out/doOnlyPitch.log"
	p1 = getKeyIx('A4')
	p2 = p1 + pitchfactor

	logpr("doOnlyPitch: src={}, out={}, fact={}, (p1,p2)=({},{})".format(source, outfile, pitchfactor, p1, p2), filename=ddlog)
	    
	logpr("doOnlyPitch: calling doffmpeg", filename=ddlog)
	doffmpeg(pitchfactor, source=source, outfile=outfile, notempo=False, debug=debug)

def make2oct(assumenote='A4', source='/tmp/file1.wav', outDir='/tmp', debug=0):
	print(source)
	print(outDir)
	if not os.path.isdir(outDir):
		try:
			os.mkdir(outDir)
		except Exception as ee:
			print(ee)
			exit()

	r1 = getKeyIx('A3') - getKeyIx(assumenote)
	r2 = getKeyIx('A5') - getKeyIx(assumenote) + 1
	for f in range(r1, r2):
		#doffmpeg(f, notempo=True)
		doffmpeg(f, source=source, notempo=False, debug=1)
	
## pydub split a file by sec
def single_split(from_sec, to_sec, infile, outfile, debug=0):
	sslog = "/tmp/source_out/single_split.log"
	iostr = "in='{}' out='{}'".format(infile, outfile)
	logpr("single_split START | {}".format(iostr))	## to default log

	t1 = from_sec * 1000
	t2 = to_sec * 1000

	segment = AudioSegment.from_wav(infile)
	ddd = segment.duration_seconds
			
	logpr("single_split: {} {:05.2f}-{:05.2f} sec, infile_duration={}".format(iostr, from_sec, to_sec, ddd), filename=sslog)

	split   = segment[t1:t2]
	split.export(outfile, format="wav", bitrate=44100)

	if from_sec > ddd or to_sec > ddd:
		logpr("single_split:\twarning, split bounds greater than file length (outfile size={})".format(os.stat(outfile).st_size), filename=sslog)


def make_tail(infile, outfile, pct=0.5, debug=0):
	if os.path.isfile(infile):
		segment = AudioSegment.from_wav(infile)
		length 	= 1000 * segment.duration_seconds

		t1 	= pct * 1000 * segment.duration_seconds
		t2	= 0.9 * 1000 * segment.duration_seconds

		split 	= segment[t1:t2]
		split.export(outfile, format="wav", bitrate=44100)
		return split
		

## gotta be abetter way than copying this around
## 210309 - has it been completely cut out?  delete if so
def getWavLength(filename):
	if not os.path.isfile(filename):
		return 0.0
	cmd = "ffprobe %s -v quiet -print_format json -show_streams -show_format" %filename
	p = myPopen(cmd)
	o, e = p.communicate()
	## has j['streams'] and j['format'] 
	j = json.loads(o)
	duration = 0.0
	if 'duration' in j['format']:
		duration = j['format']['duration']
	return duration

## trying to use basePage version as 'the one'
####  trouble with imports/modules, helpful to just have these simple things here  #####
########################################################################################
def getsafeports(io='I', istr=None):
	names   = ['Uno', 'UM-ONE']
	func    = {     'I' : mido.get_input_names, 
			'O' : mido.get_output_names     }[io]

	for ix, line in enumerate(func()):
		if not istr:
			for name in names:
				if name in line:	
					return line
		else:
			if istr in line:
				return line

def port_namer2(port, mdname=None, ptname=None):	     
	PWIDTH = 8
	if ptname == None:
		ptname = ""
	if mdname: # and port.is_output:
		nstr = "pCM [{}-> {}]".format(port.name.split(':')[0][:PWIDTH], mdname)
	else:
		nstr = "pCM [{}]".format(port.name.split(':')[0][:PWIDTH])
	port._rt.set_client_name(nstr)
	port._rt.set_port_name('PORT_{}{}'.format({True:'I',False:'O'}[port.is_input], ptname))


########################################################################################
########################################################################################
def check_platform():
	try:
		machine = { 'armv7l' : True, 'x86_64' : False}[platform.machine()]
		return machine
	except Exception as ee:
		print("check_platform exception: '{}'".format(ee))


## tired of trying to use logging
def logpr(astr, filename=(BASEDIR2 + '/g_Pitches.log')):
	makeBaseDirs()
	if not os.path.isfile(filename):
		os.system("echo 'LOGFILE INIT' > {}".format(filename))
		
	with open(filename, 'a') as fn:
		ostr = astr + "\n"
		fn.write(ostr)


def fakemsgs():
	counter = 36
	for msg in [mido.Message(type='note_on', note=x, channel=4) for x in range(36, 36+64)]:
		yield msg
		if counter%2 == 0:
			yield mido.Message(type='control_change', control=80, value=counter)
		counter += 1
		time.sleep(0.2)

'''
def makeBaseDirs(BASEDIR=BASEDIR2):
	if not os.path.isdir(BASEDIR):
		try:
			os.system('mkdir -p {}'.format(BASEDIR))
		except Exception as ee:
			print(ee)
			time.sleep(4)
			exit()
'''

def parse_args(argv):
	if 'curses' in globals():
		curses.initscr()
		curses.endwin()
	usage = '''
			argparse to allow selecting midi interface 
		'''

	parser = argparse.ArgumentParser(description="cmd line options for " + argv[0])
	parser.add_argument_group(title='midi interfaces')
	parser.add_argument('-i', dest='inport', type=str, help='midi interface IN')
	parser.add_argument('-o', dest='outport', type=str, help='midi interface OUT (for ex: clock)')
	parser.add_argument('-c', dest='channel', type=int, help='midi listen channel')
	parser.add_argument('-r', dest='reload', action='store_true', help='try to reload previous existing')
	parser.add_argument('-f', dest='infile', type=str, help='use file instead of default')
	parser.add_argument('-B', dest='basedir', type=str, help='base directory for files')
	parser.add_argument('-b', dest='bpm', type=int, help='assume bpm for source file (for slicing)')
	parser.add_argument('-s', dest='shifttempo', type=int, help='shift tempo denominator (for slicing)')
	parser.add_argument('-t', dest='test', type=int, help='test number (for pointing to various tryout "main"s)')
	parser.add_argument('-d', dest='debug', action='store_true', help='show debug for better or worse')

	print('\033[94m')
	args = parser.parse_args(argv[1:])
	print('\033[0m')
	return args




## make pitch set from 1 note sample
## still doesnt work generating its own stdscr but we should make it
def main():			
	fff = '/tmp/wav_out/slot00.wav'
	ppp = Pitches(fff, basedir='/tmp/source_out/test', inCh=1)
	ppp.Slice(debug=1)
	ppp.Listen(debug=1)
	print(ppp)

## slice by bpm into 16 or other
def main2():
	fff = '/tmp/wav_in/BI.wav'
	bbb = Beats(fff)
	bbb.Slice(debug=1)
	bbb.Listen(debug=1)

## bpm slice view
def main3(stdscr):
	fff = '/tmp/TEST.wav'
	bbb = Beats(fff, stdscr=stdscr, basedir='/tmp/ttt', bpm=108, shifttempo=108)
	bbb.Slice(debug=1)
	#bbb.Load()
	
	stdscr.nodelay(1)

	bbb.Listen()
	exit()
	while True:
		bbb.draw()

		msg     = iii.poll()
		iKey    = stdscr.getch()

		if msg:
			stdscr.refresh()

		if iKey > 0:
			bbb.keyCheck(iKey)

## tempo change experiment
def main4():
	fff = '/usr/local/lib/python3.8/dist-packages/simpleaudio/test_audio/c.wav'
	ggg = '/tmp/file1.wav'
	hhh = '/tmp/infile2.wav'
	#doffmpeg(0, assumenote='A4', source=fff, outfile=ggg, debug=1)
	#doOnlyTempo(source=hhh, outfile=ggg, tempofactor=0.5, debug=1)
	#make2oct(source=hhh, outDir='/tmp/uuu')
	#ppp = Pitches(hhh, bpm=92.0)
	#print(ppp)
	#ppp.Slice(shifttempo=120, debug=1)

	#ttt = Tempos(hhh)
	#print(ttt)
	doOnlyPitch(source=hhh, outfile=ggg, pitchfactor=-12, debug=1)

	 
def main5(stdscr=None):
	args = parse_args(sys.argv)

	istr = args.inport if args.inport 	else 'Artu'
	ostr = args.outport if args.outport 	else None
	cstr = args.channel if args.channel	else 4
	fstr = args.infile if args.infile 	else '/tmp/wav_out/slot00.wav'
	Bstr = args.basedir if args.basedir 	else '/tmp/source_out/slot00'
	bstr = args.bpm if args.bpm		else 200
	sstr = args.shifttempo if args.shifttempo else 200
	debug = args.debug if args.debug 	else 0
	
	iii = mido.open_input(getsafeports(istr=istr))
	## not sure we really need to pass outport yet,
	## it is gotten from BasePorts i think

	qqq = BeatPitch(fstr, basedir=Bstr, inport=iii, inCh=cstr, stdscr=stdscr, bpm=bstr, shifttempo=sstr)
	#qqq = Pitches(fstr, basedir=Bstr, inport=iii, inCh=cstr, stdscr=stdscr, bpm=bstr, shifttempo=sstr)
	qqq.Slice(onlyreload=args.reload, debug=debug)

	#for f in fakemsgs():
	#	qqq.msgCheck(f)
	#	qqq.draw()
	stdscr.nodelay(1)
	while True:
		qqq.draw()
		qqq.Checks()
		qqq.stdscr.refresh()

def main6():

	bpm = 88.0
	kwargs = {
		'inport' 	: mido.open_input(getsafeports(istr='Artu')),
		'bpm'		: bpm,
		'shifttempo'	: bpm,
		}

	sss = Tones(**kwargs)
	sss.draw()
	#sss.Slice(export=True)
	sss.Slice(export=False)
	sss.Listen()


logpr(
'''
############################################################################
####									####
####									####
####			START						####
####									####
####									####
############################################################################
''')
if __name__ == '__main__':
	#main6()
	#curses.endwin()
	#exit()

	#print(N2TD)
	#print(BeatPitch.__doc__)
	#print(Tempos.__doc__)
	#exit()

	curses.initscr()
	curses.wrapper(main5)







