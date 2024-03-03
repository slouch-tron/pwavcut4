#!/bin/env python3

import os
import sys
import re
import mido
import argparse

DEBUG = int(os.environ.get('DEBUG', 0))


class portHolder():

    @property
    def port_i(self):
        if not hasattr(self, '_port_i'):
            self._port_i = None

        return self._port_i

    @property
    def port_o(self):
        if not hasattr(self, '_port_o'):
            self._port_o = None

        return self._port_o

    @property
    def port_c(self):
        if not hasattr(self, '_port_c'):
            self._port_c = None

        return self._port_c

    @property
    def port_f(self):
        if not hasattr(self, '_port_f'):
            self._port_f = None

        return self._port_f

    @port_i.setter
    def port_i(self, hint):
        self._port_i = GET_PORT(hint, iotype=0)

    @port_c.setter
    def port_c(self, hint):
        self._port_c = GET_PORT(hint, iotype=0)

    @port_o.setter
    def port_o(self, hint):
        self._port_o = GET_PORT(hint, iotype=1)

    @port_f.setter
    def port_f(self, hint):
        self._port_f = GET_PORT(hint, iotype=1)


    @staticmethod
    def GETPORT(*arg, **kwa):
        return GET_PORT(*arg, *kwa)

    ## not needed here, the slots may want to change channel though
    '''
    @property
    def ctrl_ch(self):
        if not hasattr(self, '_ctrl_ch'):
            self._ctrl_ch = 1

        return self._ctrl_ch

    @ctrl_ch.setter
    def ctrl_ch(self, val):
        self._ctrl_ch = val % 16

    def inc_ctrl_ch(self):          self.ctrl_ch += 1
    def dec_ctrl_ch(self):          self.ctrl_ch -= 1
    '''

    ## last msg holders, adds to lists
    ###################################################################
    @property
    def last_msg_i(self):
        if not hasattr(self, '_last_msg_i'):
            self._last_msg_i = None

        return self._last_msg_i
      
    @last_msg_i.setter
    def last_msg_i(self, msg):
        self._last_msg_i = msg
        msg and self.msgs_i.append(msg)

    @property
    def last_msg_o(self):
        if not hasattr(self, '_last_msg_o'):
            self._last_msg_o = None
 
        return self._last_msg_o
      
    @last_msg_o.setter
    def last_msg_o(self, msg):
        self._last_msg_o = msg
        msg and self.msgs_o.append(msg)

    @property
    def last_msg_c(self):
        if not hasattr(self, '_last_msg_c'):
            self._last_msg_c = None
 
        return self._last_msg_c
      
    @last_msg_c.setter
    def last_msg_c(self, msg):
        self._last_msg_c = msg
        msg and self.msgs_c.append(msg)

    @property
    def last_msg_f(self):
        if not hasattr(self, '_last_msg_f'):
            self._last_msg_f = None
 
        return self._last_msg_f
      
    @last_msg_f.setter
    def last_msg_f(self, msg):
        self._last_msg_f = msg
        msg and self.msgs_f.append(msg)

    ## lists of previous msgs, for display in the app to see ports working
    ###################################################################
    @property
    def msgs_i(self):
        if not hasattr(self, '_msgs_i'):
            self._msgs_i = []
     
        return self._msgs_i
     
    @msgs_i.setter
    def msgs_i(self, val):
        self._msgs_i = val

    @property
    def msgs_c(self):
        if not hasattr(self, '_msgs_c'):
            self._msgs_c = []
     
        return self._msgs_c
     
    @msgs_c.setter
    def msgs_c(self, val):
        self._msgs_c = val

    @property
    def msgs_o(self):
        if not hasattr(self, '_msgs_o'):
            self._msgs_o = []
     
        return self._msgs_o
     
    @msgs_o.setter
    def msgs_o(self, val):
        self._msgs_o = val

    @property
    def msgs_f(self):
        if not hasattr(self, '_msgs_f'):
            self._msgs_f = []
     
        return self._msgs_f
     
    @msgs_f.setter
    def msgs_f(self, val):
        self._msgs_f = val


    @property
    def msgs_ct_report(self):
        return "ICOF | " + " | ".join([f"{len(xx):4d}" for xx in [
            self.msgs_i,
            self.msgs_c,
            self.msgs_o,
            self.msgs_f,
            ]])




    ############################################################################
    ############################################################################
    ## call from main/run function
    def parse_argv(self, argv):
        print(f"parse_argv: START from {argv[0]}")
        parser = argparse.ArgumentParser(description="cmd line options for p_wavcut")
        parser.add_argument('-i', '--port_i', dest='port_i', type=str, help='midi port in')
        parser.add_argument('-c', '--port_c', dest='port_c', type=str, help='midi port ctrl')
        parser.add_argument('-o', '--port_o', dest='port_o', type=str, help='midi port out')
        parser.add_argument('-f', '--port_f', dest='port_f', type=str, help='midi port fwd/thru')
        parser.add_argument('-C', '--channel', dest='channel', 
                type=int, help='midi ch for control')

        args = parser.parse_args(argv[1:])

        self.port_i = args.port_i
        self.port_o = args.port_o
        self.port_c = args.port_c
        self.port_f = args.port_f
        if args.channel:
            self.ctrl_ch = args.channel

        return args



#### cant reach these like properties in the subclasses of this..
'''
class portHolder2222():
    def __init__(self):
        self.port_i = None
        self.port_c = None
        self.port_o = None
        self.port_f = None

    def set_port_i(self, hint): self.port_i = GET_PORT(hint, iotype=0)
    def set_port_c(self, hint): self.port_i = GET_PORT(hint, iotype=0)
    def set_port_o(self, hint): self.port_i = GET_PORT(hint, iotype=1)
    def set_port_f(self, hint): self.port_i = GET_PORT(hint, iotype=1)
'''



def dbprint(txt):
    if DEBUG:
        print(f"\033[33m{__file__}: {txt}\033[0m", file=sys.stderr)


def GET_PORT(hint, iotype=0):
    dbprint(" | ".join([
        "GET_PORT",
        f"hint={hint}",
        f"iotype={iotype}",
        ]))

    if hint == None:
        return

    _func = {
        0 : [mido.get_input_names, mido.open_input],
        1 : [mido.get_output_names, mido.open_output],
        2 : [mido.get_ioport_names, mido.open_ioport],
        }.get(iotype, None)

    if _func:
        for p in _func[0]():
            if re.search(hint.lower(), p.lower()):
                dbprint(p)
                return _func[1](p)

